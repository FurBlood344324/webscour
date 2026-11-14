"""The on-disk cache: `<cwd>/.webscour/`, one markdown file per fetched URL.

The reason this exists is a context budget, not a disk. An agent that reads a page twice pays
for the bytes twice; a page it read an hour ago is still the answer, and a file on disk is
cheaper than a second deployment of the same tool. So:

* saving is **off by default** (`--save`, `--save-only`), because a tool that writes without
  being asked is a tool you cannot run in a directory you care about;
* reading is **on** with a 24 hour TTL, because that is the case the cache was built for, and
  `--fresh`, `--ttl` and `--no-cache` are all one flag away;
* the directory is `<cwd>/.webscour/`, so a repo that keeps its captures keeps them together,
  and a `.gitignore` with `*` is written on creation so git never sees them.

`index.json` is the only shared mutable file, and it is replaced by rename. A process killed
between "temp written" and "renamed" leaves the old index and an orphan temp file behind, never
a half-parsed JSON. The file itself is written the same way, for the same reason.
"""

import hashlib
import json
import os
import re
import shutil
import time
import urllib.parse

DIRNAME = ".webscour"
INDEX = "index.json"
GITIGNORE = "*\n"
DEFAULT_TTL = 24 * 3600
MAX_BYTES = 5 * 1024 * 1024
TMP_PREFIX = ".tmp-"


class CacheError(Exception):
    pass


def cache_dir(cwd=None):
    """`<cwd>/.webscour`, always under the working directory and never inside the package."""
    return os.path.join(os.path.abspath(cwd or os.getcwd()), DIRNAME)


def normalize(url):
    """The cache key: case-folded scheme and host, no fragment, no default port, no trailing /.

    Query strings stay: `?page=2` is a different page, and a cache that merges it with page one
    would answer a question about a different document.
    """
    p = urllib.parse.urlsplit((url or "").strip())
    scheme = (p.scheme or "https").lower()
    host = (p.hostname or "").lower()
    if p.port and not (
        (scheme == "http" and p.port == 80) or (scheme == "https" and p.port == 443)
    ):
        host = "%s:%d" % (host, p.port)
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((scheme, host, path, p.query, ""))


def slug_for(url):
    """Host plus path, non-alphanumerics collapsed to one hyphen, each segment capped at 40."""
    p = urllib.parse.urlsplit(normalize(url))
    segments = [s for s in (p.hostname or "").split(".") if s]
    segments += [s for s in p.path.split("/") if s]
    if not segments:
        segments = ["index"]
    out = []
    for seg in segments:
        clean = re.sub(r"[^A-Za-z0-9]+", "-", seg).strip("-") or "x"
        out.append(clean[:40].strip("-") or "x")
    return "-".join(out)


def file_name(url):
    """`<first 8 of sha256>-<slug>.md`. The hash is the identity; the slug is for the reader."""
    key = normalize(url)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
    return "%s-%s.md" % (digest, slug_for(key))


def _atomic_write(path, data):
    """Write beside the target, then rename. A killed process leaves a temp file, never a half."""
    tmp = os.path.join(os.path.dirname(path), TMP_PREFIX + os.path.basename(path))
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def ensure_dir(cwd=None):
    """Create the directory and its `.gitignore` once. An existing .gitignore is never rewritten."""
    path = cache_dir(cwd)
    os.makedirs(path, exist_ok=True)
    ignore = os.path.join(path, ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w", encoding="utf-8") as fh:
            fh.write(GITIGNORE)
    return path


def read_index(cwd=None):
    """{} when there is no index; a corrupt index is reported, never silently replaced."""
    path = os.path.join(cache_dir(cwd), INDEX)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        raise CacheError("%s is unreadable (%s); delete it and fetch again" % (path, e)) from e
    return data if isinstance(data, dict) else {}


def write_index(index, cwd=None):
    path = os.path.join(ensure_dir(cwd), INDEX)
    _atomic_write(path, json.dumps(index, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


def save(url, text, fmt="markdown", route="", status=200, cwd=None, max_bytes=MAX_BYTES, size=None):
    """Store one fetched body and update the index. Returns the index entry.

    Refuses, with a reason, rather than writing a partial file: a truncated capture is worse than
    no capture, because the next read cannot tell the difference from a short page.
    """
    body = text or ""
    size = len(body.encode("utf-8")) if size is None else size
    if size > max_bytes:
        raise CacheError(
            "%d bytes is over the %d byte save limit; raise it with --max-size" % (size, max_bytes)
        )
    path = ensure_dir(cwd)
    name = file_name(url)
    _atomic_write(os.path.join(path, name), body)
    index = read_index(cwd)
    entry = {
        "file": name,
        "fetched_at": int(time.time()),
        "format": fmt,
        "bytes": size,
        "route": route or "",
        "status": int(status or 0),
    }
    index[normalize(url)] = entry
    write_index(index, cwd)
    return entry


def lookup(url, ttl=DEFAULT_TTL, now=None, cwd=None):
    """(text, entry, age_seconds) when the entry exists and is inside the TTL, else None.

    `ttl=None` means "ignore freshness": `cache get` wants the file that is there, whatever its
    age, and an index row without its file is a miss rather than an error (someone deleted a
    capture, or the index outlived the directory), because the honest answer is "fetch it".
    """
    if ttl == 0:
        return None
    index = read_index(cwd)
    entry = index.get(normalize(url))
    if not entry:
        return None
    now = time.time() if now is None else now
    age = now - float(entry.get("fetched_at") or 0)
    if ttl is not None and (age > ttl or age < 0):
        return None
    path = os.path.join(cache_dir(cwd), entry.get("file") or "")
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read(), entry, age
    except OSError:
        return None


def forget(url, cwd=None):
    """Drop one entry and its file, if present. Returns whether anything was removed."""
    index = read_index(cwd)
    entry = index.pop(normalize(url), None)
    if not entry:
        return False
    try:
        os.unlink(os.path.join(cache_dir(cwd), entry.get("file") or ""))
    except OSError:
        pass
    write_index(index, cwd)
    return True


def parse_duration(text):
    """`7d`, `24h`, `30m`, `90s`, or a bare number of seconds. Returns seconds as int."""
    text = (text or "").strip().lower()
    m = re.match(r"^(\d+)\s*([smhdw]?)$", text)
    if not m:
        raise CacheError("%r is not a duration (examples: 30m, 12h, 7d)" % text)
    n = int(m.group(1))
    return n * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[m.group(2)]


def human_age(seconds):
    seconds = int(max(0, seconds))
    if seconds < 90:
        return "%ds" % seconds
    if seconds < 5400:
        return "%dm" % (seconds // 60)
    if seconds < 172800:
        return "%dh" % (seconds // 3600)
    return "%dd" % (seconds // 86400)


def prune(older_than, now=None, cwd=None):
    """Delete entries older than `older_than` seconds. Returns [(url, file, bytes)]."""
    index = read_index(cwd)
    now = time.time() if now is None else now
    gone, keep = [], {}
    for url, entry in index.items():
        age = now - float(entry.get("fetched_at") or 0)
        if age < older_than:
            keep[url] = entry
            continue
        name = entry.get("file") or ""
        try:
            os.unlink(os.path.join(cache_dir(cwd), name))
        except OSError:
            pass
        gone.append((url, name, int(entry.get("bytes") or 0)))
    if gone:
        write_index(keep, cwd)
    return gone


def orphans(cwd=None):
    """Files in the directory that the index does not name. Reported by `cache list`, not deleted."""
    try:
        names = set(os.listdir(cache_dir(cwd)))
    except OSError:
        return []
    known = {(e.get("file") or "") for e in read_index(cwd).values()}
    return sorted(
        n
        for n in names
        if n not in known and n not in (INDEX, ".gitignore") and not n.startswith(TMP_PREFIX)
    )


def clear(cwd=None):
    """Remove the whole directory. Only `cache prune --all` calls this, and it says so first."""
    path = cache_dir(cwd)
    shutil.rmtree(path, ignore_errors=True)
    return path
