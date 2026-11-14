"""Everything that talks to the network, and the pacing that keeps it polite.

One HTTP client (`http_raw`), the local SearXNG client with its start-and-retry policy, the
fallback scrapers, the JSON APIs and the render engines. `FetchError` is the failure type of
this layer and every caller above it catches exactly that.

The output helpers live here rather than in `cli.py` because `searx.py` also prints: keeping
them at the bottom of the import graph means `cli.py` can re-export them without a cycle.
The graph is one-way: extract <- backends <- searx <- cli.
"""

import gzip
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

from . import render_venv
from .extract import (
    _run,
    _url,
    parse_arxiv,
    parse_bing,
    parse_ddg_html,
    parse_ddg_lite,
    parse_discourse_search,
    parse_github_issues,
    parse_github_repos,
    parse_hn,
    parse_searxng,
    parse_so,
)

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


TIMEOUT = 15


MAX_BYTES = 6_000_000


# Local SearXNG: the first web backend. A loopback call, so it is cheap; upstream engines
# are what would notice a hammering client, and they are behind one process, not us.
SEARX_BASE = os.environ.get("WEBSEARCH_SEARXNG", "http://127.0.0.1:8888").rstrip("/")


SEARX_UNIT = "searxng-local"


SEARX_TIMEOUT = 15  # > the server-side 6 s cap, so a slow answer is not a dead port


SEARX_START_WAIT = 8.0


SEARX_RETRY_BELOW = 5  # fewer merged rows than this means an upstream flapped, not an empty web


# At most one live web query per second, across processes: this tool must never look like
# a scraper. The stamp lives in the cache dir so a shell loop respects it too.
PACE_SECONDS = 1.0


PACE_FILE = os.path.join(
    os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "web", "last-live"
)


class FetchError(Exception):
    """A network failure the caller can act on. `status` is the HTTP code when there was one.

    The status is carried rather than parsed back out of the message because `fetch --archive`
    has to tell a dead page (404, 410) from a page that answered, and string matching on
    "HTTP 404" is how that distinction rots the first time the message is reworded.
    """

    def __init__(self, message, status=None):
        Exception.__init__(self, message)
        self.status = status


def http_raw(url, data=None, accept=None, timeout=TIMEOUT, method=None, ua=None):
    """GET (or POST when data is given). Returns (raw_bytes, content_type, headers, charset).
    Raw bytes on purpose: a PDF must not be decoded as text before it is routed."""
    hdrs = {"User-Agent": ua or UA, "Accept-Language": "en-US,en;q=0.9"}
    if accept:
        hdrs["Accept"] = accept
    if data is not None:
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    if method == "HEAD":
        data = None
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(MAX_BYTES)
            enc = (r.headers.get("Content-Encoding") or "").lower()
            if enc == "gzip":
                raw = gzip.decompress(raw)
            elif enc == "deflate":
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            return (
                raw,
                r.headers.get_content_type(),
                r.headers,
                r.headers.get_content_charset() or "utf-8",
            )
    except urllib.error.HTTPError as e:
        raise FetchError("HTTP %s" % e.code, status=e.code) from e
    except urllib.error.URLError as e:
        raise FetchError("URLError %s" % (e.reason,)) from e
    except Exception as e:  # timeout, ssl, decode
        raise FetchError("%s: %s" % (type(e).__name__, str(e)[:120])) from e


def http(url, data=None, accept=None, timeout=TIMEOUT, method=None, ua=None):
    """GET (or POST when data is given). Returns (body_text, content_type, headers)."""
    raw, ctype, hdrs, cs = http_raw(
        url, data=data, accept=accept, timeout=timeout, method=method, ua=ua
    )
    return raw.decode(cs, "replace"), ctype, hdrs


WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"

# web.archive.org treats a browser-shaped User-Agent as a scraper (measured 2026-11-14: Chrome's
# UA got 429 on every snapshot while `webscour/0.1 (+...)` got 200 on the same URL, four times
# out of four). The browser UA is what every other request in this file uses, because a plain
# urllib UA is refused by most sites; the archive is the one host where the honest one works
# better. So it gets its own, and it is still honest.
ARCHIVE_UA = "webscour/%s (+https://github.com/FurBlood344324/webscour)" % "0.1"


def wayback_body(url, timeout=30):
    """Fetch an archived page's bytes, tolerating the archive's rate limiter.

    A 429 from the snapshot host is a burst, and a burst is what resolving a dead link and then
    opening the snapshot looks like. One retry after a short wait turns the common case back into
    a success; a second 429 is reported, because looping against a rate limiter is the behaviour
    the pacing rules exist to avoid.
    """
    last = None
    for attempt in range(2):
        try:
            return http_raw(
                url, accept="text/html,text/plain;q=0.9,*/*;q=0.5", timeout=timeout, ua=ARCHIVE_UA
            )
        except FetchError as e:
            last = e
            if e.status != 429:
                raise
            if attempt == 0:
                vwarn("archive: rate limited, retrying once in 3s")
                time.sleep(3)
    raise last


def wayback_snapshot(url, timeout=20):
    """Latest 200 snapshot of `url` -> (timestamp, archive_url), or None when there is none.

    Two queries, cheapest first: the URL as written, then its whole path as a prefix. A site that
    moved a page under a new slug still has the old one under the same directory, and that is
    what a reader of a dead link actually wants. `id_` in the returned URL means "the archived
    bytes, not the Wayback toolbar wrapped around them".
    """
    p = urllib.parse.urlsplit(url)
    if not p.hostname:
        return None
    candidates = [url]
    if p.path and p.path != "/":
        depth = p.path.rsplit("/", 1)[0] or "/"
        if depth != "/":
            candidates.append("%s://%s%s/*" % (p.scheme or "https", p.netloc, depth))
    for target in candidates:
        q = urllib.parse.urlencode(
            {
                "url": target,
                "output": "json",
                "limit": "-5",
                "fl": "timestamp,original,statuscode",
                "filter": "statuscode:200",
            }
        )
        try:
            body, _, _ = http(
                "%s?%s" % (WAYBACK_CDX, q),
                accept="application/json",
                timeout=timeout,
                ua=ARCHIVE_UA,
            )
        except FetchError:
            continue
        try:
            rows = json.loads(body or "[]")
        except ValueError:
            continue
        hits = [
            r for r in (rows or []) if isinstance(r, list) and len(r) >= 2 and r[2:3] == ["200"]
        ]
        if hits:
            stamp, original = hits[-1][0], hits[-1][1]
            return stamp, "https://web.archive.org/web/%sid_/%s" % (stamp, original)
    return None


def searx_news(query, limit):
    """The SearXNG `news` category as rows, for `--fresh`. Empty when there is no local SearXNG."""
    rows = searx_web(query, limit, category="news")
    return [dict(r, published=r.get("published") or "") for r in rows]


# Diagnostics are opt-in: a caller that redirects stdout to a file must not get a paragraph on
# stderr explaining a decision that turned out fine. `-v` is the only switch, and it is per run.
VERBOSE = False


def set_verbose(on):
    global VERBOSE
    VERBOSE = bool(on)


def is_verbose():
    """The live flag. A re-exported global is a snapshot, so a nested command asks here."""
    return VERBOSE


def warn(msg):
    """A failure or a lost capability: the line the caller needs when the exit code is not 0."""
    print(msg, file=sys.stderr)


def vwarn(msg):
    """A diagnostic that explains a choice. Silent unless `-v` was asked for."""
    if VERBOSE:
        print(msg, file=sys.stderr)


def _q(query):
    return urllib.parse.quote_plus(query)


def _pace_delay(last, now):
    """Seconds to wait so that two live queries are never closer than PACE_SECONDS."""
    return max(0.0, PACE_SECONDS - (now - last))


def pace():
    """Sleep just enough to keep <= 1 live web query per second, in this process and the next."""
    now = time.time()
    try:
        with open(PACE_FILE, encoding="utf-8") as fh:
            last = float(fh.read().strip() or 0)
    except (OSError, ValueError):
        last = 0.0
    delay = _pace_delay(last, now)
    if delay > 0:
        vwarn("pace: waiting %.1fs so two live queries stay %.0fs apart" % (delay, PACE_SECONDS))
        time.sleep(delay)
    try:
        os.makedirs(os.path.dirname(PACE_FILE), exist_ok=True)
        with open(PACE_FILE, "w", encoding="utf-8") as fh:
            fh.write("%.3f" % time.time())
    except OSError:
        pass


def _searx_netloc():
    p = urllib.parse.urlparse(SEARX_BASE)
    return p.hostname or "127.0.0.1", p.port or 8888


def _port_open(host, port):
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _searx_json(path, timeout=SEARX_TIMEOUT, live=False):
    if live:
        pace()
    body, _, _ = http(SEARX_BASE + path, accept="application/json", timeout=timeout)
    return json.loads(body)


def _searx_start():
    """The port may refuse because the user unit is stopped: start it once, wait, re-check."""
    host, port = _searx_netloc()
    if _port_open(host, port):
        return True
    try:
        subprocess.run(
            ["systemctl", "--user", "start", SEARX_UNIT],
            timeout=25,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    deadline = time.time() + SEARX_START_WAIT
    while time.time() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(0.25)
    return False


def _dedupe(rows):
    seen, out = set(), []
    for r in rows:
        key = r["url"].split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _on_topic(query, rows):
    """Same criterion as related() and as the acceptance test: a query term in the title or url.
    A snippet match alone is not evidence that the row is about the query."""
    words = [x.lower() for x in re.findall(r"[0-9a-zA-Z_+-]{4,}", query)]
    if not words:
        return list(rows)
    return [r for r in rows if any(w in (r["title"] + " " + r["url"]).lower() for w in words)]


def _prefer_on_topic(query, rows, limit):
    """A merged set carries drift: an engine can answer a neighbouring query, and a row with no
    query term in its title or url is not evidence for anything. Keep those out as soon as one
    on-topic row exists; with none at all, return what came back and let related() judge."""
    rows = _dedupe(rows)
    on = _on_topic(query, rows)
    return (on if on else rows)[:limit]


def _searx_ask(params):
    """One SearXNG query -> (rows, down engines). Starts the unit once if the port refuses."""
    try:
        data = _searx_json("/search?" + params, live=True)
    except (FetchError, ValueError) as first:
        if not _searx_start():
            raise FetchError(
                "local SearXNG %s not answering (%s) and %s did not start"
                % (SEARX_BASE, first, SEARX_UNIT)
            ) from first
        try:
            data = _searx_json("/search?" + params, live=True)
        except ValueError as e:
            raise FetchError("local SearXNG returned invalid JSON (%s)" % e) from e
    rows, dead = parse_searxng(data)
    for r in rows:
        r["url"] = _url(r["url"])
    return [r for r in rows if r["url"]], dead


def searx_web(query, limit, category=""):
    # timeout_limit caps how long the server waits for its engines; without it a suspended
    # upstream can hold the whole response to its own timeout. A category is opt-in because it
    # changes which engines answer, and so changes what the answer is; it is not reliably slower
    # (both shapes measured 1 s to the 6 s cap on the same afternoon).
    params = {"q": query, "format": "json", "safesearch": "0", "timeout_limit": "6"}
    if category:
        params["categories"] = category
    params = urllib.parse.urlencode(params)
    got, dead = _searx_ask(params)
    if dead:
        vwarn("searxng: %d engine(s) down: %s" % (len(dead), ", ".join(dead[:8])))
    # An engine that timed out or was suspended at that instant does not mean the web is empty,
    # and it does not mean the answer is unrelated either. One retry only: a loop here would be
    # exactly the scraper behaviour this tool avoids.
    if len(got) < SEARX_RETRY_BELOW or not related(
        query, _prefer_on_topic(query, got, limit) or got
    ):
        again, dead2 = _searx_ask(params)
        if len(again) > len(got) or (
            again and related(query, _prefer_on_topic(query, again, limit))
        ):
            got, dead = again, dead2
    got = _prefer_on_topic(query, got, limit)
    if not got:
        raise FetchError("no results (%d engines down)" % len(dead))
    if not related(query, got):
        raise FetchError("results unrelated to the query")
    return got


BLOCK_MARKS = (
    "anomaly-modal",
    "Wait A Moment",
    "unusual traffic",
    "are you a robot",
    "captcha",
    "Enable JavaScript and cookies to continue",
)


def blocked(page):
    """True when the answer is a bot check, not a result list. Silence would look like 0 hits."""
    return any(m in page for m in BLOCK_MARKS)


def related(query, results):
    """A scraped engine can serve an unrelated cached page. Refuse to pass that off as a hit."""
    terms = [t.lower() for t in re.findall(r"[0-9a-zA-Z_+-]{4,}", query)]
    if not terms:
        return True
    blob = " ".join((r["title"] + " " + r["snippet"] + " " + r["url"]).lower() for r in results)
    return any(t in blob for t in terms)


def web_lite(query, limit):
    body = urllib.parse.urlencode({"q": query}).encode()
    page, _, _ = http("https://lite.duckduckgo.com/lite/", data=body)
    if blocked(page):
        raise FetchError("blocked by bot check")
    got = parse_ddg_lite(page)[:limit]
    if got and not related(query, got):
        raise FetchError("results unrelated to the query")
    return got


def web_html(query, limit):
    page, _, _ = http("https://html.duckduckgo.com/html/?q=" + _q(query))
    if blocked(page):
        raise FetchError("blocked by bot check")
    got = parse_ddg_html(page)[:limit]
    if got and not related(query, got):
        raise FetchError("results unrelated to the query")
    return got


def web_bing(query, limit):
    page, _, _ = http("https://www.bing.com/search?q=%s&count=%d" % (_q(query), max(limit, 10)))
    if blocked(page):
        raise FetchError("blocked by bot check")
    got = parse_bing(page)[:limit]
    if not got and "There are no results for" in page:
        raise FetchError("the engine returned an empty result page")
    if got and not related(query, got):
        raise FetchError("results unrelated to the query")
    return got


def gh_repos(query, limit):
    doc, _, hdrs = http(
        "https://api.github.com/search/repositories?per_page=%d&q=%s" % (limit, _q(query)),
        accept="application/vnd.github+json",
    )
    return parse_github_repos(json.loads(doc)), hdrs.get("x-ratelimit-remaining")


def gh_issues(query, limit):
    doc, _, hdrs = http(
        "https://api.github.com/search/issues?per_page=%d&q=%s" % (limit, _q(query)),
        accept="application/vnd.github+json",
    )
    return parse_github_issues(json.loads(doc)), hdrs.get("x-ratelimit-remaining")


def so_search(query, limit):
    url = (
        "https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&site=stackoverflow"
        "&pagesize=%d&q=%s" % (limit, _q(query))
    )
    doc, _, _ = http(url)
    return parse_so(json.loads(doc))


def hn_search(query, limit):
    doc, _, _ = http(
        "https://hn.algolia.com/api/v1/search?hitsPerPage=%d&query=%s" % (limit, _q(query))
    )
    return parse_hn(json.loads(doc))


def arxiv_search(query, limit):
    url = "https://export.arxiv.org/api/query?max_results=%d&search_query=%s" % (
        limit,
        urllib.parse.quote("all:" + query),
    )
    doc, _, _ = http(url)
    return parse_arxiv(doc)


def discourse_search(base, query, limit):
    doc, _, _ = http("%s/search.json?q=%s" % (base.rstrip("/"), _q(query)))
    return parse_discourse_search(json.loads(doc), base)[:limit]


RENDER_ENGINES = ("lightpanda", "playwright")


PLAYWRIGHT_SCRIPT = r'''
import glob
import os
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
limit = int(sys.argv[2])


def candidate_browsers():
    """A playwright package and its browser build can drift apart (package wants 1208, cache
    has 1223). Launch what is actually installed rather than telling the caller to download."""
    home = os.path.expanduser("~/.cache/ms-playwright")
    pats = ["chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
            "chromium-*/chrome-linux64/chrome",
            "chromium-*/chrome-linux/chrome"]
    found = []
    for pat in pats:
        found += sorted(glob.glob(os.path.join(home, pat)), reverse=True)
    return found


with sync_playwright() as p:
    browser = None
    errors = []
    for kwargs in [{}] + [{"executable_path": b} for b in candidate_browsers()]:
        try:
            browser = p.chromium.launch(headless=True, **kwargs)
            break
        except Exception as e:
            errors.append(str(e).splitlines()[0] if str(e) else type(e).__name__)
    if browser is None:
        sys.stderr.write("; ".join(errors))
        sys.exit(3)
    try:
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(url, wait_until="load", timeout=45000)
        page.wait_for_timeout(1200)
        print(page.inner_text("body")[:limit])
    finally:
        browser.close()
'''


_PW_PYTHON = []


def playwright_python():
    """The interpreter that can `import playwright`, or ''. Probed once and cached.

    Resolution lives in `render_venv`: the env var, then the venv this tool owns, then the
    running interpreter, then `python3`. The pyenv glob that used to be here is gone on
    purpose: a public tool must not search the operator's environment managers for a package
    it did not install.
    """
    if _PW_PYTHON:
        return _PW_PYTHON[0]
    _PW_PYTHON.append(render_venv.find())
    return _PW_PYTHON[0]


def render_page(url, engine="auto", max_chars=6000):
    """Real browser -> (text, engine name). Raises FetchError naming why a backend was unusable:
    a render request that silently degrades is worse than one that fails."""
    order = RENDER_ENGINES if engine in ("", "auto") else (engine,)
    reasons = []
    for name in order:
        if name == "lightpanda":
            exe = shutil.which("lightpanda")
            if not exe:
                reasons.append("lightpanda not on PATH (it is the required render engine)")
                continue
            text, err = _run(
                [
                    exe,
                    "fetch",
                    "--dump",
                    "markdown",
                    "--dump-max-bytes",
                    str(max(2000, max_chars * 8)),
                    url,
                ],
                timeout=90,
            )
            if text.strip():
                return text, name
            reasons.append("lightpanda: %s" % (err or "empty dump"))
        else:
            py = playwright_python()
            if not py:
                reasons.append("playwright: not available. %s" % render_venv.SETUP_HINT)
                continue
            d = tempfile.mkdtemp(prefix="web-pw-")
            try:
                script = os.path.join(d, "render.py")
                with open(script, "w", encoding="utf-8") as fh:
                    fh.write(PLAYWRIGHT_SCRIPT)
                text, err = _run([py, script, url, str(max(2000, max_chars * 4))], timeout=120)
            finally:
                shutil.rmtree(d, ignore_errors=True)
            if text.strip():
                return text, "playwright (%s)" % os.path.basename(
                    os.path.dirname(os.path.dirname(py))
                )
            reasons.append("playwright: %s" % (err or "empty text"))
    raise FetchError(
        "no render backend worked: "
        + "; ".join(reasons or ["none requested"])
        + ". lightpanda is the required render engine (install it, `wsc setup` prints how);"
        " playwright is the fallback for a page lightpanda cannot render."
    )
