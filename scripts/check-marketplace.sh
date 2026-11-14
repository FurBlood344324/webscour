#!/usr/bin/env bash
# check-marketplace.sh [path] - is the Claude Code marketplace file installable, offline?
#
# The file is served verbatim from https://wsc.ashina.live/marketplace.json, so a bad entry is not
# a build error here: it is a failed install on a reader's machine, with a message that names
# neither the file nor the field. Two facts are checked, and both are about `source`:
#
#   1. a string source is a path relative to the marketplace root, and that directory exists here
#   2. an object source (`git-subdir`) carries a `path` key, the path is relative and stays inside
#      the repository, and when the `url` names this repository the directory exists in this commit
#
# The second rule is the one that has teeth: it is what rejects the shapes that look right and fail
# at `claude plugin install`. A `git-subdir` entry whose `path` is a typo installs nothing.
#
# Usage:
#   ./scripts/check-marketplace.sh                          # .claude-plugin/marketplace.json
#   ./scripts/check-marketplace.sh _site/marketplace.json    # the copy, before Pages deploys it
#
# Exit 0 with one `PASS`-shaped line per plugin, exit 1 with the reason on stderr.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
PY="${PYTHON:-python3}"

FILE="${1:-.claude-plugin/marketplace.json}"

exec "$PY" -I - "$FILE" <<'PY'
import json, os, subprocess, sys

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as handle:
        market = json.load(handle)
except OSError as exc:
    sys.exit("%s: %s" % (path, exc.strerror or exc))
except json.JSONDecodeError as exc:
    sys.exit("%s: not JSON: %s" % (path, exc))

if not market.get("name"):
    sys.exit("%s has no marketplace name" % path)

plugins = market.get("plugins")
if not isinstance(plugins, list) or not plugins:
    sys.exit("%s lists no plugins; `claude plugin marketplace add` would offer nothing" % path)
if not market.get("owner"):
    sys.exit("%s has no owner" % path)


def slug(url):
    """'git@github.com:a/b.git' and 'https://github.com/a/b' both become 'a/b'."""
    text = url.strip().rstrip("/")
    if text.endswith(".git"):
        text = text[: -len(".git")]
    parts = text.replace(":", "/").split("/")
    return "/".join(parts[-2:]).lower()


def origin_slug():
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"], capture_output=True, text=True
        ).stdout.strip()
    except OSError:
        return ""
    return slug(url) if url else ""


here = origin_slug()
problems = []
for plugin in plugins:
    name = plugin.get("name")
    if not name:
        problems.append("a plugin entry has no name")
        continue
    source = plugin.get("source")
    if isinstance(source, str):
        # The documented string form: a directory inside the marketplace, written from its root.
        rel = source[2:] if source.startswith("./") else source
        if not rel or os.path.isabs(rel) or not os.path.isdir(rel):
            problems.append("%s: source %r is not a directory in this repository" % (name, source))
            continue
        print("%s: directory %s" % (name, rel))
        continue

    if not isinstance(source, dict):
        problems.append("%s: source is %r; a path string or a source object is required" % (name, source))
        continue

    kind = source.get("source")
    rel = source.get("path")
    if not kind:
        problems.append("%s: source object has no 'source' type" % name)
        continue
    if not isinstance(rel, str) or not rel:
        problems.append("%s: %s source has no 'path'" % (name, kind))
        continue
    if os.path.isabs(rel):
        problems.append("%s: %s path %r is absolute" % (name, kind, rel))
        continue
    normal = os.path.normpath(rel)
    if normal == ".." or normal.startswith("../"):
        problems.append("%s: %s path %r escapes the repository" % (name, kind, rel))
        continue

    url = source.get("url") or ""
    remote = slug(url) if url else ""
    if remote and here and remote != here:
        # Somebody else's repository: the path is real for them and unknowable from here.
        print("%s: %s %s at %s (remote, not checked here)" % (name, kind, normal, remote))
        continue
    if not os.path.isdir(normal):
        problems.append("%s: %s path %r is not a directory in this repository" % (name, kind, rel))
        continue
    print("%s: %s %s" % (name, kind, normal))

if problems:
    sys.exit("%s: %s" % (path, "; ".join(problems)))
print("%s: %s, %d plugin(s)" % (path, market["name"], len(plugins)))
PY
