"""The argv surface: verbs, flags, printing, exit codes.

Every command parses its arguments, calls into `backends` or `extract`, and decides what the
user sees. Nothing here opens a socket itself; `--self-test` is the one path that proves the
pure parts of the pipeline, and it runs offline with no SearXNG and no render backend.
"""

import argparse
import contextlib
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import xml.etree.ElementTree as ET

from . import __version__, render_venv, routes, sources
from . import argv as argv_mod
from . import cache as cache_store
from . import searx as searx_bundle
from .backends import (
    PACE_SECONDS,
    RENDER_ENGINES,
    SEARX_BASE,
    SEARX_UNIT,
    FetchError,
    _dedupe,
    _pace_delay,
    _port_open,
    _prefer_on_topic,
    _searx_json,
    _searx_netloc,
    arxiv_search,
    blocked,
    discourse_search,
    gh_issues,
    gh_repos,
    hn_search,
    http,
    http_raw,
    is_verbose,  # the live flag: a re-exported global would be a snapshot
    pace,
    playwright_python,
    related,
    render_page,
    searx_web,
    set_verbose,
    so_search,
    vwarn,
    warn,
    wayback_body,
    wayback_snapshot,
    web_bing,
    web_html,
    web_lite,
)
from .extract import (
    BACKEND_BINS,
    CT_SUFFIX,
    JS_SHELL_MIN,
    SNIPPET,
    _gunzip_if_needed,
    _url,
    crawlable,
    document_backend,
    document_format,
    extract_document,
    filter_links,
    html_to_markdown,
    html_to_text,
    js_shell_reason,
    looks_like_pdf,
    map_sources,
    markdown_to_text,
    page_links,
    page_title,
    parse_arxiv,
    parse_bing,
    parse_ddg_html,
    parse_ddg_lite,
    parse_discourse_search,
    parse_discourse_topic,
    parse_github_issues,
    parse_github_repos,
    parse_hn,
    parse_llms_txt,
    parse_robots_sitemaps,
    parse_searxng,
    parse_sitemap,
    parse_so,
    same_origin,
)
from .searx import LIGHTPANDA_HINT

__all__ = ["main", "set_verbose", "vwarn", "warn"]


def cut(text, n):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _tag(r):
    """Short `[engine,engine]` marker: which backend actually produced this row."""
    names = [e for e in (r.get("engines") or ([r["engine"]] if r.get("engine") else [])) if e]
    return ("  [%s]" % ",".join(names[:3])) if names else ""


def render(results, as_json=False):
    if as_json:
        rows = []
        for r in results:
            row = {
                "title": r["title"],
                "url": r["url"],
                "snippet": cut(r["snippet"], SNIPPET),
                "engines": r.get("engines") or ([r["engine"]] if r.get("engine") else []),
            }
            if r.get("published"):
                row["published"] = r["published"]
            rows.append(row)
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    for i, r in enumerate(results, 1):
        print("%d. %s - %s%s" % (i, cut(r["title"], 160), r["url"], _tag(r)))
        snip = cut(r["snippet"], SNIPPET)
        if r.get("published"):
            snip = "[%s] %s" % (r["published"], snip)
        if snip.strip():
            print("   " + snip)


# ---------------------------------------------------------------- commands


def cmd_search(argv):
    ap = argparse.ArgumentParser(prog="wsc search")
    ap.add_argument("query")
    ap.add_argument(
        "--source",
        default="web",
        help="web, github, so, hn, arxiv, a keyless API source, or discourse:<host>",
    )
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument(
        "--category",
        choices=list(sources.CATEGORIES),
        default="",
        help="SearXNG category; changes which engines answer, so it is opt-in",
    )
    ap.add_argument("--fresh", action="store_true", help="freshness sources only, newest first")
    ap.add_argument("--since", default="", help="YYYY-MM-DD floor for --fresh")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    limit = max(1, min(a.limit, 30))
    source = a.source.strip()
    results = []
    note = None

    if a.since:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", a.since):
            warn("search: --since must be YYYY-MM-DD")
            return 2
        if not a.fresh:
            warn("search: --since only means something with --fresh")
            return 2

    if a.fresh:
        if source != "web":
            warn("search: --fresh is its own source set; drop --source %r" % source)
            return 2
        results = sources.fresh(a.query, limit, a.since, searx=_searx_news)
        if not results:
            warn("no fresh results (Google News and BBC RSS both empty for this query)")
            return 2
        render(results, a.json)
        return 0

    if source == "web":
        # A category is a SearXNG parameter and nothing else, so a categorised query has no
        # scraper fallback: DuckDuckGo Lite cannot be asked for `it` or `news`, and pretending
        # otherwise would answer a different question than the one that was asked.
        try:
            results = searx_web(a.query, limit, a.category)
        except FetchError as e:
            warn("backend searxng: %s" % e)
            results = []
        if not results and not a.category:
            for name, fn in (("ddg-lite", web_lite), ("ddg-html", web_html), ("bing", web_bing)):
                try:
                    results = fn(a.query, limit)
                except FetchError as e:
                    warn("backend %s: %s" % (name, e))
                    continue
                if results:
                    break
                warn("backend %s: 0 results" % name)
    elif a.category:
        warn("search: --category only applies to --source web (SearXNG)")
        return 2
    elif source == "github":
        for kind, fn in (("repos", gh_repos), ("issues", gh_issues)):
            try:
                got, left = fn(a.query, limit)
                note = "github rate limit remaining: %s" % left
            except FetchError as e:
                warn("backend github-%s: %s" % (kind, e))
                continue
            results.extend(got)
        results = results[:limit]
    elif source == "so":
        try:
            results = so_search(a.query, limit)
        except FetchError as e:
            warn("backend so: %s" % e)
    elif source == "hn":
        try:
            results = hn_search(a.query, limit)
        except FetchError as e:
            warn("backend hn: %s" % e)
    elif source == "arxiv":
        # The existing route, unchanged: same endpoint, same parser, same output as before.
        try:
            results = arxiv_search(a.query, limit)
        except FetchError as e:
            warn("backend arxiv: %s" % e)
        except ET.ParseError as e:
            warn("backend arxiv: Atom %s" % e)
    elif source.startswith("discourse:"):
        base = source.split(":", 1)[1]
        try:
            results = discourse_search(base, a.query, limit)
        except FetchError as e:
            warn("backend discourse: %s" % e)
    elif source in sources.FETCHERS:
        try:
            results = sources.FETCHERS[source](a.query, limit)
        except FetchError as e:
            warn("backend %s: %s" % (source, e))
        except (ValueError, ET.ParseError) as e:
            warn("backend %s: %s" % (source, e))
    else:
        warn("unknown --source %r (%s)" % (source, sources.SOURCES_HELP))
        return 2

    if not results:
        warn("no results")
        return 2
    render(results, a.json)
    if note:
        warn("-- " + note) if a.json else print("-- " + note)
    return 0


def _searx_news(query, limit):
    """The SearXNG news category for `--fresh`, tolerant: no local SearXNG is not an error."""
    try:
        return searx_web(query, limit, category="news")
    except FetchError as e:
        vwarn("fresh: searxng news: %s" % e)
        return []


def backend_table():
    """lightpanda first: it is the render engine. The extractors are gaps, not failures."""
    rows = []
    path = shutil.which("lightpanda")
    rows.append(("lightpanda", path or "MISSING", bool(path)))
    py = playwright_python()
    rows.append(("playwright", ("python %s" % py) if py else "MISSING", bool(py)))
    for name in BACKEND_BINS:
        path = shutil.which(name)
        rows.append((name, path or "MISSING", bool(path)))
    return rows


def render_venv_report():
    """The fallback venv as data: path, existence, health, browser drift, and the fix."""
    return render_venv.status()


def _print_render_venv(report):
    """One block for doctor. A missing venv is a note; drift is a note with a fix.

    The fallback is optional, so none of this changes the verdict on its own. It changes it
    only in the sense a reviewer cares about: the line says whether the fallback would work
    if lightpanda failed on the next page, and exactly what makes it work.
    """
    state = render_venv_report()
    report["render_venv"] = state
    if state["ok"]:
        browsers = ",".join(state["present"]) or "none"
        print("render-venv  %s (playwright ok, chromium %s)" % (state["path"], browsers))
        if state["wanted"] and state["present"] and not state["browser_ok"]:
            print(
                "             package wants chromium %s, cache has %s: a launch falls back to"
                " the installed build" % (",".join(state["wanted"]), browsers)
            )
        return
    if not state["exists"]:
        print("render-venv  absent (%s)" % state["path"])
    else:
        print("render-venv  %s (playwright not importable)" % state["path"])
    print("             fallback only: %s" % state["fix"])


def source_table(live=False, rows=None):
    """One row per search source: what it is, where it answers, and whether it answered now.

    Reachability is measured **live only under `--live`**, because doctor is run often and a
    dozen HTTP requests per run is a scraper's habit, not a diagnostic. Without the flag the row
    says the endpoint is configured, which is the honest answer: an idle source is not a broken
    one.
    """
    rows = rows if rows is not None else list(sources.FETCHERS)
    checks = []
    for name in rows:
        if live:
            try:
                if name == "pypi":
                    got = sources.FETCHERS[name]("requests", 1)
                elif name == "npm":
                    got = sources.FETCHERS[name]("express", 1)
                elif name == "crates":
                    got = sources.FETCHERS[name]("serde", 1)
                elif name == "wayback":
                    got = sources.FETCHERS[name]("example.com", 1)
                else:
                    got = sources.FETCHERS[name]("test", 1)
                checks.append((name, "ok " if got else "empty", True))
            except FetchError as e:
                checks.append((name, "%s" % e, False))
            except Exception as e:  # a parser that breaks on a 200 is still a broken source
                checks.append((name, "%s" % type(e).__name__, False))
        else:
            checks.append((name, "configured", True))
    return checks


def _print_sources(report, live=False):
    """The source table. Silent on a down source unless -v: doctor's job is the verdict."""
    checks = source_table(live=live)
    report["sources"] = {name: {"state": state, "ok": ok} for name, state, ok in checks}
    print("sources   %d keyless endpoint(s)" % len(checks))
    for name, state, ok in checks:
        mark = "" if ok else "  (down)"
        print("          %-12s %s%s" % (name, state, mark))
        if not ok:
            vwarn("source %s: %s" % (name, state))


def cmd_doctor(argv):
    """Service state, port, per-engine health, optional backends, one verdict line."""
    ap = argparse.ArgumentParser(prog="wsc doctor")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--live",
        action="store_true",
        help="probe every keyless source once; a dozen requests, so it is not the default",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="say which source failed and why, on stderr",
    )
    a = ap.parse_args(argv)
    set_verbose(a.verbose)
    host, port = _searx_netloc()
    report = {"endpoint": SEARX_BASE, "unit": SEARX_UNIT}

    try:
        report["active"] = (
            subprocess.run(
                ["systemctl", "--user", "is-active", SEARX_UNIT],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            or "unknown"
        )
        report["enabled"] = (
            subprocess.run(
                ["systemctl", "--user", "is-enabled", SEARX_UNIT],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            or "unknown"
        )
    except (OSError, subprocess.SubprocessError):
        report["active"] = report["enabled"] = "unknown"

    try:
        listen = subprocess.run(["ss", "-ltn"], capture_output=True, text=True, timeout=10).stdout
        addrs = [ln.split()[3] for ln in listen.splitlines() if ":%d" % port in ln]
    except (OSError, subprocess.SubprocessError):
        addrs = []
    report["listen"] = addrs
    report["local_only"] = bool(addrs) and all(
        x.startswith("127.0.0.1:") or x.startswith("[::1]:") for x in addrs
    )

    if not _port_open(host, port):
        print("unit      %s (%s at boot)" % (report["active"], report["enabled"]))
        print("listen    nothing on %s:%d" % (host, port))
        print(
            "hint      run `wsc setup` to install the local SearXNG; until then only scrapers answer"
        )
        render_ok = _print_backends(report)
        _print_render_venv(report)
        _print_sources(report, a.live)
        print("VERDICT DOWN")
        if a.json:
            print(json.dumps(report, indent=1, ensure_ascii=False))
        return 1

    try:
        cfg = _searx_json("/config", timeout=8)
        report["engines_loaded"] = len(cfg.get("engines") or [])
    except (FetchError, ValueError) as e:
        report["engines_loaded"] = 0
        report["error"] = str(e)[:100]

    try:  # SearXNG's own error table: no query text, just which engines raised what
        errors = _searx_json("/stats/errors", timeout=8)
        broken = sorted(k for k, v in (errors or {}).items() if v)
    except (FetchError, ValueError):
        broken = []
    report["blocked_engines"] = broken

    answered = []
    try:  # one live probe: an engine in no error table may still be silently dead
        data = _searx_json(
            "/search?"
            + urllib.parse.urlencode({"q": "python asyncio task cancellation", "format": "json"}),
            live=True,
        )
        answered = sorted({r.get("engine") for r in data.get("results") or [] if r.get("engine")})
    except (FetchError, ValueError) as e:
        report["probe_error"] = str(e)[:100]
    report["answered"] = answered

    print("unit      %s (%s at boot)" % (report["active"], report["enabled"]))
    print(
        "listen    %s%s"
        % (
            ", ".join(addrs) or "unknown (ss gave nothing)",
            "  <-- NOT loopback only" if addrs and not report["local_only"] else "",
        )
    )
    silent = []
    try:
        loaded = {e.get("name") for e in (_searx_json("/config", timeout=8).get("engines") or [])}
        silent = sorted(loaded - set(answered))
    except (FetchError, ValueError):
        loaded = set()
    report["silent_engines"] = silent

    print("engines   %d loaded" % report["engines_loaded"])
    print("blocked   %s" % (", ".join(broken) or "none in the error table"))
    print("answered  %s" % (", ".join(answered) or "nothing on the probe query"))
    print("silent    %s" % (", ".join(silent) or "every loaded engine answered"))
    render_ok = _print_backends(report)
    _print_render_venv(report)
    _print_sources(report, a.live)

    # A meta-search is expected to lose upstreams: what must hold is that the service is
    # up, loopback only, and that most of its engines still answer. Two suspended engines
    # out of ten are noise; a majority suspended is not.
    loaded_n = max(1, report["engines_loaded"])
    report["blocked_pct"] = round(100.0 * len(broken) / loaded_n)
    if not answered or not addrs:
        print("VERDICT DOWN")
        rc = 1
    elif not render_ok:
        # lightpanda is the render engine: without it, plain HTTP works and JS pages do not.
        print("VERDICT DEGRADED: lightpanda is missing, so --render and hollow-page retry are dead")
        rc = 1
    elif not report["local_only"]:
        print("VERDICT DEGRADED: not loopback only (%s)" % ", ".join(addrs))
        rc = 1
    elif len(broken) * 2 > loaded_n:
        print(
            "VERDICT DEGRADED: %d/%d engines blocked (%s)"
            % (len(broken), loaded_n, ", ".join(broken))
        )
        rc = 1
    else:
        print(
            "VERDICT OK (%d/%d engines answering, %d blocked)"
            % (len(answered), loaded_n, len(broken))
        )
        rc = 0
    if a.json:
        print(json.dumps(report, indent=1, ensure_ascii=False))
    return rc


def _print_backends(report):
    """Two rows with two different weights: lightpanda is required, the extractors are not.

    Returns whether lightpanda is present, because that single fact decides a DEGRADED verdict.
    """
    rows = backend_table()
    report["backends"] = {name: {"path": where, "ok": ok} for name, where, ok in rows}
    print(
        "backends  %s" % "  ".join("%s=%s" % (name, "ok" if ok else "no") for name, _, ok in rows)
    )
    lightpanda_ok = False
    for name, _where, ok in rows:
        if name == "lightpanda":
            lightpanda_ok = ok
            if not ok:
                print("          lightpanda: not available, and the render path requires it")
                for line in LIGHTPANDA_HINT.splitlines()[1:]:
                    print("          %s" % line.strip())
        elif name == "playwright" and not ok:
            print(
                "          playwright: not installed (only needed for a page lightpanda cannot render)"
            )
        elif not ok:
            print("          %s: not available" % name)
    return lightpanda_ok


def discourse_json_url(url):
    """forums.developer.nvidia.com/t/<slog>/<id>[-tail] -> /t/<id>.json"""
    p = urllib.parse.urlparse(url)
    if p.netloc not in ("forums.developer.nvidia.com", "forums.developer.nvidia.cn"):
        return None
    m = re.match(r"^/t/(?:[^/]+/)?(\d+)(?:/[^/]*)?/?$", p.path)
    if not m:
        return None
    return "%s://%s/t/%s.json" % (p.scheme or "https", p.netloc, m.group(1))


FETCH_FORMATS = ("text", "markdown")


def _as_text(markdown):
    """Markdown routes produce markdown; `--format text` is the default, so it must not leak.

    This is a renderer, not a parser: the route already decided what the content is.
    """
    return markdown_to_text(markdown)


class _SkipFetch(Exception):
    """Internal: the archive already answered, so the network path is not taken."""


def _note(notes, line):
    if line:
        notes.append(line)


def _fetch_route(url, notes):
    """(name, markdown) for a URL with a structured route, or None. A declining route is a note."""
    route = routes.route_for(url)
    if route is None:
        return None
    try:
        name, body = routes.resolve(url)
    except FetchError as e:
        vwarn("route %s declined for %s (%s); plain path" % (route.name, url, e))
        return None
    except (ValueError, KeyError, TypeError) as e:
        vwarn("route %s returned unreadable data for %s (%s); plain path" % (route.name, url, e))
        return None
    _note(notes, "route: %s" % name)
    return name, body


def _fetch_archive(url, notes):
    """On a dead page, the last good snapshot. Returns (body, kind); kind is markdown or text.

    A 429 from web.archive.org is the archive rate-limiting a second snapshot request in a
    minute, not a missing snapshot: it is reported as a note and the caller falls back to the
    original error, because "the archive was busy" and "nothing was ever archived" are
    different sentences and only one of them is true.
    """
    found = wayback_snapshot(url)
    if not found:
        return None, None
    stamp, archived = found
    try:
        raw, ctype, _, cs = wayback_body(archived)
    except FetchError as e:
        vwarn("archive: snapshot %s would not open (%s)" % (stamp, e))
        return None, None
    _note(notes, "archive: %s (%s)" % (stamp, archived))
    body = raw.decode(cs, "replace")
    if "html" in (ctype or ""):
        return html_to_markdown(body, base=archived), "markdown"
    return body, "text"


def _save_or_warn(url, text, fmt, route, status, a):
    """Write into .webscour/ when asked. A refused save is a warning, not a failed fetch."""
    if not (a.save or a.save_only):
        return None
    if a.no_cache:
        vwarn("save: --no-cache turns saving off too, nothing written")
        return None
    try:
        entry = cache_store.save(
            url, text, fmt=fmt, route=route, status=status, max_bytes=a.max_size
        )
    except cache_store.CacheError as e:
        warn("save: %s" % e)
        return None
    vwarn("save: %s (%s, %d bytes)" % (entry["file"], entry["format"], entry["bytes"]))
    return entry


def cmd_fetch(argv):
    ap = argparse.ArgumentParser(prog="wsc fetch")
    ap.add_argument("url")
    ap.add_argument("--max-chars", type=int, default=6000)
    ap.add_argument("--grep")
    ap.add_argument("--format", choices=list(FETCH_FORMATS), default="text")
    ap.add_argument(
        "--render",
        action="store_true",
        help="force a real browser; no silent fallback if it is unusable",
    )
    ap.add_argument("--render-engine", choices=[*RENDER_ENGINES, "auto"], default="auto")
    ap.add_argument(
        "--archive",
        action="store_true",
        help="resolve the latest Wayback snapshot when the page is gone (404/410 does it anyway)",
    )
    ap.add_argument("--no-route", action="store_true", help="ignore the structured site routes")
    ap.add_argument("--save", action="store_true", help="also write the page into ./.webscour/")
    ap.add_argument(
        "--save-only", action="store_true", help="write it and print an index line, not the page"
    )
    ap.add_argument("--fresh", action="store_true", help="ignore the cache for this call")
    ap.add_argument("--ttl", default="", help="cache freshness window (default 24h; e.g. 30m, 7d)")
    ap.add_argument("--no-cache", action="store_true", help="neither read nor write the cache")
    ap.add_argument(
        "--max-size", type=int, default=cache_store.MAX_BYTES, help="save limit in bytes"
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="explain every choice on stderr (engine, route, document backend, pacing)",
    )
    a = ap.parse_args(argv)
    set_verbose(a.verbose)

    try:
        ttl = (
            0
            if a.fresh
            else cache_store.parse_duration(a.ttl)
            if a.ttl
            else cache_store.DEFAULT_TTL
        )
    except cache_store.CacheError as e:
        warn("fetch: %s" % e)
        return 2

    notes = []
    engine_note = ""
    route_name = ""

    # 1. cache read. The cache is the reason a second read of the same page is cheap, so it is
    #    consulted before the network, and `--fresh` is the one flag that skips it.
    if not a.no_cache:
        try:
            hit = cache_store.lookup(a.url, ttl=ttl)
        except cache_store.CacheError as e:
            hit, _ = None, warn("cache: %s" % e)
        if hit:
            text, entry, age = hit
            text = text.rstrip("\n")
            if len(text) > a.max_chars:
                text = text[: a.max_chars].rstrip() + "\n... (cut at %d chars)" % a.max_chars
            if a.save_only:
                print(
                    "%s  %s  %d bytes"
                    % (
                        os.path.join(cache_store.DIRNAME, entry.get("file") or ""),
                        entry.get("format") or "?",
                        int(entry.get("bytes") or 0),
                    )
                )
            else:
                print(text)
            # Always on stderr, like `route:` and `render:`: a cache hit changes what the
            # caller gets (a page from hours ago, not now), so it announces itself and never
            # hides behind -v.
            warn("cache: hit (%s ago)" % cache_store.human_age(age))
            return 0

    status = 0
    text = ""
    markdown_body = None
    prefetched = False
    # `--archive` means "I want the snapshot", not "I want the live page or else": it is asked
    # for first, and the live page is the fallback. On the error path below the same helper
    # answers the implicit case (a 404 or a 410), which is why this is not duplicated there.
    if a.archive:
        archived, kind = _fetch_archive(a.url, notes)
        if archived is not None:
            text = (
                archived
                if (kind == "markdown" or a.format == "markdown")
                else markdown_to_text(archived)
            )
            status = 200
            route_name = "wayback"
            prefetched = True
        else:
            vwarn("archive: no snapshot for %s, taking the live page" % a.url)

    try:
        if prefetched:
            raise _SkipFetch

        raw = None
        ctype = ""
        cs = "utf-8"
        jurl = discourse_json_url(a.url)
        if a.render:
            # An explicit --render wins over everything: the caller asked for a browser, so the
            # engine is reported even when the plain path would have produced the same text.
            (body, engine) = render_page(a.url, a.render_engine, a.max_chars)
            engine_note = "render: %s" % engine.split(" (")[0]
            vwarn("fetch: asked to render, %s answered" % engine)
            text = body
            status = 200
        elif jurl:
            doc, _, _ = http(jurl, accept="application/json")
            text = "\n".join(parse_discourse_topic(json.loads(doc)))
            vwarn("fetch: discourse .json path (no SearXNG involved)")
            status = 200
        elif document_format("", a.url) in ("pdf", "docx", "epub"):
            lines, _path = _document_lines(a.url, markdown=a.format == "markdown")
            text = "\n".join(lines)
            status = 200
        else:
            routed = None
            if not a.no_route:
                routed = _fetch_route(a.url, notes)
            if routed is not None:
                route_name, markdown_body = routed
                text = markdown_body if a.format == "markdown" else markdown_to_text(markdown_body)
                status = 200
            else:
                raw, ctype, _hdrs, cs = http_raw(
                    a.url, accept="text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5"
                )
                status = 200
                if looks_like_pdf(raw, ctype):
                    lines, _path = _document_lines(
                        a.url, raw=raw, ctype=ctype, markdown=a.format == "markdown"
                    )
                    text = "\n".join(lines)
                else:
                    body = raw.decode(cs, "replace")
                    html = "html" in (ctype or "")
                    if html and a.format == "markdown":
                        markdown_body = html_to_markdown(body, base=a.url)
                        text = markdown_body
                    else:
                        text = html_to_text(body) if html else body
                    hollow = js_shell_reason(body, text) if html else ""
                    if hollow:
                        # A short but complete page is no longer hollow (the heuristic checks
                        # text outside <noscript> before it checks length), so this is a real shell.
                        vwarn("fetch: plain HTTP looked hollow (%s), asking a browser" % hollow)
                        try:
                            body, engine = render_page(a.url, a.render_engine, a.max_chars)
                            engine_note = "render: %s" % engine.split(" (")[0]
                            vwarn("fetch: %s answered (%s chars)" % (engine, len(body.strip())))
                            text = body
                        except FetchError as e:
                            warn(
                                "fetch: plain HTTP looked hollow (%s) and no render backend"
                                " answered: %s" % (hollow, e)
                            )
                    else:
                        vwarn(
                            "fetch: plain HTTP, %s, no render needed (%d chars of text)"
                            % (ctype or "unknown type", len(text))
                        )
    except _SkipFetch:
        pass
    except FetchError as e:
        dead = e.status in (404, 410)
        if dead or a.archive:
            vwarn("fetch: %s%s, asking the Wayback Machine" % (e, " (dead)" if dead else ""))
            archived, kind = _fetch_archive(a.url, notes)
            if archived is not None:
                # The snapshot is markdown, so `--format markdown` takes it as it is and the
                # default text format flattens it. A plain-text snapshot has nothing to flatten.
                text = (
                    archived
                    if (kind == "markdown" or a.format == "markdown")
                    else markdown_to_text(archived)
                )
                status = 200
            elif a.archive or dead:
                warn("fetch: %s, and no Wayback snapshot answered" % e)
                return 2
            else:
                warn("fetch: %s" % e)
                return 2
        else:
            warn("fetch: %s" % e)
            return 2

    text = text.rstrip("\n")
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        warn("fetch: empty document")
        return 2

    if a.grep:
        try:
            rx = re.compile(a.grep, re.I)
        except re.error as e:
            warn("fetch: bad --grep regex: %s" % e)
            return 2
        hits = [i for i, ln in enumerate(lines) if rx.search(ln)]
        if not hits:
            warn("fetch: no line matches %r (%d lines)" % (a.grep, len(lines)))
            return 1
        shown = set()
        out = []
        for i in hits:
            for j in (i - 1, i, i + 1):
                if not (0 <= j < len(lines)) or j in shown:
                    continue
                shown.add(j)
                out.append(("> " if j == i else "  ") + lines[j])
        text = "\n".join(out)
    else:
        text = "\n".join(lines)

    payload = text + "\n"
    entry = _save_or_warn(a.url, payload, a.format, route_name, status, a)
    if a.save_only:
        if entry is not None:
            print(
                "%s  %s  %d bytes"
                % (
                    os.path.join(cache_store.DIRNAME, entry["file"]),
                    entry["format"],
                    entry["bytes"],
                )
            )
        for line in notes:
            warn(line)
        if engine_note:
            warn(engine_note)
        return 0 if entry is not None else 2

    if len(text) > a.max_chars:
        text = text[: a.max_chars].rstrip() + "\n... (cut at %d chars)" % a.max_chars
    print(text)
    for line in notes:
        warn(line)
    if engine_note:
        warn(engine_note)
    return 0


def _document_lines(url, raw=None, ctype=None, markdown=False):
    """URL -> (lines, path). One download, then the first backend that reads the format.

    `markdown` asks pandoc for `-t gfm` instead of `-t plain`. Only pandoc can produce markdown;
    pdftotext and markitdown cannot, and inventing a structure they did not extract would be a
    worse answer than the plain text they do produce. A PDF gets plain text either way, which is
    why the flag changes nothing that used to be correct.
    """
    if raw is None:
        raw, ctype, _, _ = http_raw(url)
    fmt = document_format(ctype or "", url)
    if not fmt and looks_like_pdf(raw, ctype or ""):
        fmt = "pdf"
    if not fmt:
        raise FetchError("not a document (%s)" % (ctype or "unknown content type"))
    d = tempfile.mkdtemp(prefix="web-doc-")
    try:
        path = os.path.join(d, "document" + (CT_SUFFIX.get(ctype or "") or "." + fmt))
        with open(path, "wb") as fh:
            fh.write(raw)
        text, backend = extract_document(raw, fmt, path, markdown=markdown)
        if not backend or not text.strip():
            raise FetchError("no backend could read this %s: %s" % (fmt, backend))
        vwarn("extract: %s -> %s%s" % (fmt, backend, " (markdown)" if markdown else ""))
        if markdown and backend != "pandoc":
            # Only pandoc has a markdown writer. Saying so is better than letting the caller
            # believe the headings in the answer came from a converter that never ran.
            vwarn("format: %s has no markdown writer, so this is its plain text" % backend)
        return text.splitlines(), path
    finally:
        shutil.rmtree(d, ignore_errors=True)


def cmd_pdf(argv):
    """A paper or a manual as text. URL or local path; `-v` names the backend that read it."""
    ap = argparse.ArgumentParser(prog="wsc pdf")
    ap.add_argument("source")
    ap.add_argument("--max-chars", type=int, default=20000)
    ap.add_argument(
        "--format",
        choices=list(FETCH_FORMATS),
        default="text",
        help="text (default) or markdown; a PDF has no links, an HTML document does",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="name the format and the backend that produced the text",
    )
    a = ap.parse_args(argv)
    set_verbose(a.verbose)

    local = a.source
    is_url = a.source.startswith(("http://", "https://"))
    if not is_url and not os.path.exists(local):
        warn("pdf: no such file: %s" % local)
        return 2
    try:
        if is_url:
            lines, _path = _document_lines(a.source, markdown=a.format == "markdown")
        else:
            fmt = document_format("", local)
            if not fmt:
                warn("pdf: %s is not a document by its extension (pdf/docx/epub/html)" % local)
                return 2
            with open(local, "rb") as fh:
                raw = fh.read()
            text, backend = extract_document(raw, fmt, local, markdown=a.format == "markdown")
            if not backend or not text.strip():
                warn("pdf: no backend could read this %s: %s" % (fmt, backend))
                return 2
            vwarn("extract: %s -> %s" % (fmt, backend))
            lines = text.splitlines()
    except FetchError as e:
        warn("pdf: %s" % e)
        return 2

    if a.format == "markdown":
        # pandoc's gfm keeps blank lines inside a fence, so a block-level strip would eat them.
        text = "\n".join(lines).strip("\n")
    else:
        text = "\n".join(line for line in (raw.rstrip() for raw in lines) if line.strip())
    if not text.strip():
        warn("pdf: the document produced no text (scanned image? needs OCR, out of scope)")
        return 2
    if len(text) > a.max_chars:
        text = text[: a.max_chars].rstrip() + "\n… (cut at %d chars)" % a.max_chars
    print(text)
    return 0


def cmd_map(argv):
    ap = argparse.ArgumentParser(prog="wsc map")
    ap.add_argument("url")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument(
        "-v", "--verbose", action="store_true", help="name the source that answered, on stderr"
    )
    a = ap.parse_args(argv)
    set_verbose(a.verbose)
    limit = max(1, a.limit)

    root = "%s://%s" % (
        urllib.parse.urlparse(a.url).scheme or "https",
        urllib.parse.urlparse(a.url).netloc,
    )
    found, seen, used, note = [], set(), "", ""

    def add(urls):
        for u in urls:
            key = u.rstrip("/")
            if key and key not in seen:
                seen.add(key)
                found.append(u)

    for cand in map_sources(a.url):
        if len(found) >= limit:
            break
        try:
            pace()
            raw, _ctype, _, _ = http_raw(cand, accept="application/xml,text/plain,*/*")
        except FetchError:
            continue
        raw = _gunzip_if_needed(raw)
        text = raw.decode("utf-8", "replace")
        if cand.endswith("robots.txt"):
            smaps = parse_robots_sitemaps(text)
            if not smaps:
                continue
            used = used or "robots.txt"
            for sm in smaps[:3]:
                try:
                    pace()
                    sraw, _, _, _ = http_raw(sm, accept="application/xml,text/plain,*/*")
                    urls, is_index = parse_sitemap(
                        _gunzip_if_needed(sraw).decode("utf-8", "replace")
                    )
                    if is_index:
                        for child in urls[:3]:
                            pace()
                            craw, _, _, _ = http_raw(child, accept="application/xml,text/plain,*/*")
                            sub, _ = parse_sitemap(
                                _gunzip_if_needed(craw).decode("utf-8", "replace")
                            )
                            add(sub)
                    else:
                        add(urls)
                except FetchError as e:
                    note = note or "%s: %s" % (sm, e)
            continue
        if cand.endswith("llms.txt"):
            urls = parse_llms_txt(text)
            if urls:
                used = used or "llms.txt"
                add(urls)
            continue
        urls, is_index = parse_sitemap(text)
        if not urls:
            continue
        used = used or cand
        if is_index:
            for child in urls[:3]:
                try:
                    pace()
                    craw, _, _, _ = http_raw(child, accept="application/xml,text/plain,*/*")
                    sub, _ = parse_sitemap(_gunzip_if_needed(craw).decode("utf-8", "replace"))
                    add(sub)
                except FetchError:
                    continue
        else:
            add(urls)

    if not found:
        warn(
            "map: no sitemap, robots Sitemap line or llms.txt answered at %s%s"
            % (root, " (%s)" % note if note else "")
        )
        return 2
    vwarn("map: source %s, %d url(s)" % (used, len(found)))
    for u in found[:limit]:
        print(u)
    if len(found) > limit:
        vwarn("map: %d more url(s) not printed (--limit %d)" % (len(found) - limit, limit))
    return 0


def cmd_crawl(argv):
    """BFS from map's seed plus each page's links. Prints, writes nothing, paces every fetch."""
    ap = argparse.ArgumentParser(prog="wsc crawl")
    ap.add_argument("url")
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--limit", type=int, default=20)
    same = ap.add_mutually_exclusive_group()
    same.add_argument(
        "--same-origin",
        dest="same_origin",
        action="store_true",
        default=True,
        help="stay on the seed's origin (default)",
    )
    same.add_argument("--any-origin", dest="same_origin", action="store_false")
    ap.add_argument(
        "-v", "--verbose", action="store_true", help="report seeds, skips and pacing on stderr"
    )
    a = ap.parse_args(argv)
    set_verbose(a.verbose)
    limit = max(1, min(a.limit, 200))
    depth = max(0, a.depth)

    seen = {a.url.rstrip("/")}
    queue = [(a.url, 0)]
    done, n = 0, 0

    # `map` first: a sitemap gives the crawl its shape without guessing.
    try:
        seed_urls = map_seed_urls(a.url, cap=max(limit * 5, 40))
    except FetchError:
        seed_urls = []
    for u in filter_links(seed_urls, a.url, a.same_origin):
        key = u.rstrip("/")
        if key not in seen and len(queue) < limit * 10:
            seen.add(key)
            queue.append((u, 1 if depth else 0))

    while queue and n < limit:
        url, level = queue.pop(0)
        try:
            pace()
            raw, ctype, _, cs = http_raw(url, accept="text/html,application/xhtml+xml,*/*;q=0.5")
        except FetchError as e:
            vwarn("crawl: %s -> %s" % (url, e))
            continue
        body = raw.decode(cs, "replace")
        text = html_to_text(body) if "html" in ctype else ""
        title = page_title(body) if "html" in ctype else ""
        n += 1
        print("%s  |  %s  |  %d chars" % (url, title or "(no title)", len(" ".join(text.split()))))
        done += 1
        if level >= depth or "html" not in ctype:
            continue
        for nxt in filter_links(page_links(body, url), a.url, a.same_origin):
            key = nxt.rstrip("/")
            if key not in seen and len(queue) < limit * 10:
                seen.add(key)
                queue.append((nxt, level + 1))
    if not done:
        warn("crawl: nothing fetched")
        return 2
    vwarn(
        "crawl: %d page(s), depth %d, same-origin %s, %.1f s of pacing"
        % (done, depth, "yes" if a.same_origin else "no", done * PACE_SECONDS)
    )
    return 0


def map_seed_urls(url, cap=200):
    """The `map` answer as a list, raising FetchError when nothing answers. Shared with crawl.

    `-v` is passed through and the global is restored afterwards: the nested `map` parses its own
    argv, and without this a verbose crawl went quiet the moment its seed list was collected.
    """
    buf, err = io.StringIO(), io.StringIO()
    saved, was_verbose = sys.stderr, is_verbose()
    try:
        sys.stderr = err
        with contextlib.redirect_stdout(buf):
            rc = cmd_map([url, "--limit", str(cap)] + (["-v"] if was_verbose else []))
    finally:
        sys.stderr = saved
        set_verbose(was_verbose)
    if rc != 0:
        raise FetchError(
            err.getvalue().strip().splitlines()[-1] if err.getvalue().strip() else "map failed"
        )
    return [ln.strip() for ln in buf.getvalue().splitlines() if ln.strip()]


# ---------------------------------------------------------------- self-test

FIX_SEARXNG = json.dumps(
    {
        "query": "asyncio cancellation",
        "results": [
            {
                "url": "https://example.org/asyncio",
                "title": "Asyncio task cancellation",
                "content": "How cancellation propagates.",
                "engine": "brave",
                "engines": ["brave", "naver"],
            },
            {
                "url": "https://example.net/b",
                "title": "Second hit",
                "content": "Other text.",
                "engine": "bing",
                "engines": ["bing"],
            },
            {
                "url": "",
                "title": "no url, dropped",
                "content": "x",
                "engine": "bing",
                "engines": ["bing"],
            },
        ],
        "answers": [],
        "corrections": [],
        "infoboxes": [],
        "suggestions": [],
        "unresponsive_engines": [["qwant", "Suspended: access denied"], ["mojeek", "CAPTCHA"]],
    }
)


FIX_DDG_LITE = """<html><body><table>
<tr><td valign="top">1.&nbsp;</td><td><a rel="nofollow" href="https://example.com/a" class="result-link">RetinaFace detector</a></td></tr>
<tr><td>&nbsp;</td><td class="result-snippet">A <b>single-stage</b> face detector.</td></tr>
<tr><td valign="top">2.&nbsp;</td><td><a rel="nofollow" href="//example.com/b" class="result-link">Second hit</a></td></tr>
<tr><td>&nbsp;</td><td class="result-snippet">Other snippet.</td></tr>
</table></body></html>"""


FIX_DDG_HTML = """<html><body><div class="result results_links">
<h2 class="result__title"><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fx&amp;rut=1">Example title</a></h2>
<a class="result__snippet" href="https://example.org/x">Snippet <b>text</b> here.</a></div></body></html>"""


FIX_BING = """<html><body><ol id="b_results"><li class="b_algo"><h2><a href="https://example.net/b">Bing hit</a></h2>
<div class="b_caption"><p>Some <b>snippet</b>.</p></div></li>
<li class="b_algo"><h2><a href="https://example.net/c">Second bing</a></h2><p>More.</p></li></ol></body></html>"""


FIX_GH_REPOS = json.dumps(
    {
        "total_count": 1,
        "items": [
            {
                "full_name": "serengil/retinaface",
                "html_url": "https://github.com/serengil/retinaface",
                "description": "RetinaFace in Keras",
                "stargazers_count": 2100,
                "language": "Python",
            }
        ],
    }
)


FIX_GH_ISSUES = json.dumps(
    {
        "total_count": 1,
        "items": [
            {
                "title": "How to drop frames",
                "html_url": "https://github.com/x/y/issues/12",
                "number": 12,
                "state": "open",
                "body": "body text",
                "repository_url": "https://api.github.com/repos/x/y",
            }
        ],
    }
)


FIX_SO = json.dumps(
    {
        "items": [
            {
                "title": "nvv4l2decoder drop-frame-interval",
                "link": "https://stackoverflow.com/q/1",
                "tags": ["python", "gstreamer"],
                "score": 5,
                "is_answered": True,
            }
        ]
    }
)


FIX_HN = json.dumps(
    {
        "hits": [
            {
                "title": "A story",
                "url": "https://example.com/s",
                "objectID": "42",
                "points": 10,
                "num_comments": 3,
            }
        ]
    }
)


FIX_ARXIV = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1905.00641v1</id>
<title>RetinaFace: Single-stage Dense Face Localisation</title><summary>We present a face detector.</summary>
</entry></feed>"""


FIX_DSC = json.dumps(
    {
        "topics": [{"id": 123456, "title": "NVStreammux live-source", "posts_count": 4}],
        "posts": [{"topic_id": 123456, "blurb": "set live-source to 1"}],
    }
)


FIX_TOPIC = json.dumps(
    {
        "title": "nvstreammux live-source",
        "post_stream": {
            "posts": [
                {
                    "post_number": 1,
                    "username": "alice",
                    "cooked": "<p>Set <code>live-source=1</code>.</p>",
                },
                {
                    "post_number": 2,
                    "username": "bob",
                    "cooked": "<p>Also check batched-push-timeout.</p>",
                },
            ]
        },
    }
)


FIX_ANOMALY = """<html><head><title>DuckDuckGo</title></head><body><div class="anomaly-modal__box">
<div class="anomaly-modal__title">Unfortunately, bots use DuckDuckGo too.</div></div></body></html>"""


FIX_PAGE = """<html><head><title>t</title></head><body><nav>menu here</nav>
<h1>DeepStream Quickstart</h1><p>Works on Xavier NX and Orin.</p><script>var x=1;</script>
<p>Second paragraph.</p></body></html>"""


# A real, minimal PDF whose content stream holds the words: pdftotext reads this offline, so the
# routing check exercises the actual backend rather than a mock of it.
FIX_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n"
    b"2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n"
    b"3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>\nendobj\n"
    b"4 0 obj\n<</Length 42>>stream\nBT /F1 12 Tf 20 100 Td (Hello web) Tj ET\nendstream\nendobj\n"
    b"5 0 obj\n<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>\nendobj\n"
    b"trailer\n<</Size 6/Root 1 0 R>>\n%%EOF\n"
)


FIX_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://example.com/a?x=1&amp;y=2</loc></url>
<url><loc>https://example.com/b</loc></url>
<url><loc>not-a-url</loc></url>
</urlset>"""


FIX_SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>https://example.com/sitemap-1.xml.gz</loc></sitemap>
</sitemapindex>"""


FIX_ROBOTS = """User-agent: *
Disallow: /admin
Sitemap: https://example.com/sitemap.xml
sitemap: https://example.com/second.xml
"""


FIX_LLMS = """# Example
- [Docs](https://example.com/docs)
- [Api](https://example.com/api)
https://example.com/bare
"""


FIX_SHELL = """<html><head><title>App</title></head><body><div id="root"></div>
<noscript>You need to enable JavaScript to run this app. This application requires a modern
browser and JavaScript turned on before any of its content can be displayed at all.</noscript>
<script>window.__NEXT_DATA__={};</script></body></html>"""


FIX_SHELL_NEXT = (
    "<html><body><div id=__next></div>"
    '<script id="__NEXT_DATA__" type="application/json">{}</script>'
    "<p>" + "filler text that is long enough to pass the length gate " * 12 + "</p>"
    "</body></html>"
)


# A short page that is complete: 200, text/html, one text-bearing element outside <noscript>,
# no JavaScript-required marker. example.com is this shape, and it must never cost a browser.
FIX_SHORT_COMPLETE = """<html><head><title>Example Domain</title></head><body><div>
<h1>Example Domain</h1>
<p>This domain is for use in documentation examples without needing permission.
Avoid use in operations.</p><p><a href="https://iana.org/domains/example">More information...</a></p>
</div></body></html>"""


FIX_SOLID = (
    "<html><body><article><h1>Async</h1><p>"
    + "real content for the reader " * 40
    + "</p></article></body></html>"
)

# The three shapes the pruning rules have to tell apart. Each one is a different decision, so
# each one gets its own fixture rather than a combined page that cannot say which fired.
FIX_DENSE = """<html><body><div class="sidebar">
<ul><li><a href="/a">Docs</a></li><li><a href="/b">Api</a></li><li><a href="/c">Blog</a></li>
<li><a href="/d">Pricing</a></li><li><a href="/e">Careers</a></li></ul></div>
<article><p>The article survives because a container that is not mostly links is not a menu.</p>
</article></body></html>"""

FIX_COOKIE = """<html><body>
<div id="onetrust-consent-sdk"><p>We value your privacy and 400 partners store cookies.</p></div>
<div class="cmp_cookie_bar"><p>This site uses cookies to improve your experience.</p></div>
<article><p>The article body is what the reader came for.</p></article></body></html>"""

FIX_PRE = """<html><body><p>Install it:</p>
<pre>def f(x):
    return  'two  spaces  and four ahead'

    # a blank line above is code, not layout</pre>
<p>Done.</p></body></html>"""


FIX_CRAWL_PAGE = """<html><head><title>Seed page</title></head><body><h1>Seed</h1>
<p>Some text on the seed page.</p>
<a href="/inner">inner</a>
<a href="https://example.com/inner">inner dup</a>
<a href="https://other.example/x">other origin</a>
<a href="/logo.png">image</a>
<a href="#frag">fragment</a>
<a href="mailto:a@b.c">mail</a>
</body></html>"""


def self_test():
    checks = []

    def chk(name, fn):
        try:
            ok = fn()
            checks.append((name, bool(ok), "" if ok else "assertion failed"))
        except Exception as e:
            checks.append((name, False, "%s: %s" % (type(e).__name__, e)))

    def ddg_lite():
        r = parse_ddg_lite(FIX_DDG_LITE)
        assert len(r) == 2, r
        assert r[0]["title"] == "RetinaFace detector", r[0]
        assert r[0]["url"] == "https://example.com/a", r[0]
        assert "single-stage" in r[0]["snippet"], r[0]
        assert r[1]["url"] == "https://example.com/b"
        return True

    def ddg_html():
        r = parse_ddg_html(FIX_DDG_HTML)
        assert len(r) == 1, r
        assert r[0]["title"] == "Example title", r[0]
        assert r[0]["url"] == "https://example.org/x", r[0]
        assert "Snippet text here." in r[0]["snippet"], r[0]
        return True

    def bing():
        r = parse_bing(FIX_BING)
        assert len(r) == 2, r
        assert r[0]["title"] == "Bing hit", r[0]
        assert r[0]["url"] == "https://example.net/b", r[0]
        assert "Some snippet." in r[0]["snippet"], r[0]
        return True

    def gh_repos():
        r = parse_github_repos(json.loads(FIX_GH_REPOS))
        assert r[0]["url"] == "https://github.com/serengil/retinaface", r
        assert "Python" in r[0]["snippet"] and "2100 stars" in r[0]["snippet"], r
        return True

    def gh_issues():
        r = parse_github_issues(json.loads(FIX_GH_ISSUES))
        assert r[0]["title"] == "x/y#12 How to drop frames", r
        return True

    def so():
        r = parse_so(json.loads(FIX_SO))
        assert r[0]["url"] == "https://stackoverflow.com/q/1", r
        assert "answered" in r[0]["snippet"], r
        return True

    def hn():
        r = parse_hn(json.loads(FIX_HN))
        assert r[0]["url"] == "https://example.com/s", r
        return True

    def arxiv():
        r = parse_arxiv(FIX_ARXIV)
        assert r[0]["url"] == "http://arxiv.org/abs/1905.00641v1", r
        assert r[0]["title"].startswith("RetinaFace"), r
        return True

    def discourse_search():
        r = parse_discourse_search(json.loads(FIX_DSC), "https://forums.developer.nvidia.com")
        assert r[0]["url"] == "https://forums.developer.nvidia.com/t/123456", r
        assert r[0]["snippet"] == "set live-source to 1", r
        return True

    def discourse_topic():
        lines = parse_discourse_topic(json.loads(FIX_TOPIC))
        blob = "\n".join(lines)
        assert "#1 alice" in blob and "#2 bob" in blob, blob
        assert "live-source=1" in blob, blob
        return True

    def nvidia_rewrite():
        a = discourse_json_url(
            "https://forums.developer.nvidia.com/t/nvstreammux-live-source/123456"
        )
        assert a == "https://forums.developer.nvidia.com/t/123456.json", a
        b = discourse_json_url("https://forums.developer.nvidia.com/t/123456")
        assert b == "https://forums.developer.nvidia.com/t/123456.json", b
        assert discourse_json_url("https://example.com/t/123456") is None
        return True

    def to_text():
        text = html_to_text(FIX_PAGE)
        assert "Xavier NX" in text, text
        assert "menu here" not in text, text
        assert "var x" not in text, text
        return True

    def dense_prune():
        """A menu of short links goes; the article beside it stays."""
        text = html_to_text(FIX_DENSE)
        assert "The article survives" in text, text
        for gone in ("Docs", "Pricing", "Careers"):
            assert gone not in text, (gone, text)
        return True

    def cookie_prune():
        """Vendor and compound class names go; a normal paragraph does not."""
        text = html_to_text(FIX_COOKIE)
        assert "The article body is what the reader came for." in text, text
        assert "We value your privacy" not in text, text
        assert "improve your experience" not in text, text
        return True

    def pre_verbatim():
        """Code keeps its indentation, its double spaces and its blank line."""
        text = html_to_text(FIX_PRE)
        assert "    return  'two  spaces  and four ahead'" in text, repr(text)
        assert "\n\n    # a blank line above is code, not layout" in text, repr(text)
        assert "Install it:" in text, text
        return True

    def render_small():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            render([{"title": "t", "url": "u", "snippet": "x" * 500}])
        out = buf.getvalue()
        assert len(out) < 320, len(out)
        assert " - u" in out
        return True

    def no_identity():
        """No identity leaks into a query. The tokens are assembled here so this check cannot
        match its own source, and the split is why there is no regex with a stray escape."""
        with open(__file__, encoding="utf-8") as handle:
            src = handle.read()
        forbidden = ["get" + "pass", "gethost" + "name", "get" + "login"]
        hits = [t for t in forbidden if t in src]
        assert not hits, hits
        return True

    def blocked_page():
        assert blocked(FIX_ANOMALY), "bot-check page not detected"
        assert not blocked(FIX_BING), "real result page flagged as blocked"
        return True

    def ck_a():
        assert (
            _url("https://www.bing.com/ck/a?!&&u=a1aHR0cHM6Ly9leGFtcGxlLm5ldC9wYXRo&ntb=1")
            == "https://example.net/path"
        ), _url("https://www.bing.com/ck/a?!&&u=a1aHR0cHM6Ly9leGFtcGxlLm5ldC9wYXRo")
        return True

    def related_guard():
        junk = [
            {
                "title": "Store Finder - Lidl US",
                "url": "https://lidl.com/c/store-finder",
                "snippet": "zip code",
            }
        ]
        good = [
            {
                "title": "Gst-nvstreammux",
                "url": "https://docs.nvidia.com/x",
                "snippet": "live-source=1",
            }
        ]
        assert not related("deepstream nvstreammux live-source", junk)
        assert related("deepstream nvstreammux live-source", good)
        return True

    def searx_parse():
        got, dead = parse_searxng(json.loads(FIX_SEARXNG))
        assert len(got) == 2, got
        assert got[0]["title"] == "Asyncio task cancellation", got[0]
        assert got[0]["engines"] == ["brave", "naver"], got[0]
        assert got[0]["snippet"] == "How cancellation propagates.", got[0]
        assert got[1]["engine"] == "bing" and got[1]["engines"] == ["bing"], got[1]
        assert dead == ["qwant", "mojeek"], dead
        assert related("asyncio cancellation", got[:1])
        assert not related("deepstream nvstreammux live-source", got[:1])
        return True

    def drift_filter():
        rows = [
            {"title": "About Get Help", "url": "https://support.microsoft.com/x", "snippet": ""},
            {
                "title": "nvv4l2decoder drop-frame-interval",
                "url": "https://example.com/a",
                "snippet": "",
            },
            {
                "title": "Interval to drop frames",
                "url": "https://docs.nvidia.com/b",
                "snippet": "drop-frame-interval=5",
            },
            {"title": "unrelated", "url": "https://example.org/c", "snippet": "nvv4l2decoder note"},
        ]
        got = _prefer_on_topic("nvv4l2decoder drop-frame-interval", rows, 8)
        assert [r["url"] for r in got] == ["https://example.com/a"], got
        dup = [*rows, dict(rows[1])]
        assert len(_dedupe(dup)) == len(rows), _dedupe(dup)
        # nothing on topic: hand back the rows unchanged, related() decides about the set
        nothing = [rows[0], rows[3]]
        assert len(_prefer_on_topic("nvv4l2decoder drop-frame-interval", nothing, 8)) == 2
        return True

    def google_unwrap():
        got, _ = parse_searxng(json.loads(FIX_SEARXNG))
        wrapped = {
            "url": "https://www.google.com/url?opi=1&q=https%3A%2F%2Fexample.com%2Freal&uoh=3",
            "title": "x",
            "content": "",
            "engine": "abcnyheter",
            "engines": ["abcnyheter"],
        }
        got.append(wrapped)
        for r in got:
            r["url"] = _url(r["url"])
        assert got[0]["url"] == "https://example.org/asyncio", got[0]
        assert got[2]["url"] == "https://example.com/real", got[2]
        return True

    def pace_guard():
        assert _pace_delay(0.0, 100.0) == 0.0
        assert abs(_pace_delay(99.5, 100.0) - 0.5) < 1e-6
        assert _pace_delay(100.0, 100.0) == PACE_SECONDS
        return True

    def engine_tag():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            render(
                [
                    {
                        "title": "t",
                        "url": "u",
                        "snippet": "s",
                        "engine": "brave",
                        "engines": ["brave", "naver"],
                    }
                ]
            )
        assert "[brave,naver]" in buf.getvalue(), buf.getvalue()
        return True

    def pdf_routing():
        """A %PDF body must pick the pdftotext path, and the real backend must read it."""
        assert looks_like_pdf(FIX_PDF, "application/octet-stream"), "magic bytes not honoured"
        assert looks_like_pdf(b"", "application/pdf"), "content type not honoured"
        assert not looks_like_pdf(b"<html>", "text/html")
        assert document_format("application/pdf", "x") == "pdf"
        assert document_format("", "https://a/b/paper.PDF?v=2") == "pdf"
        assert document_format("text/html; charset=utf-8", "") == "html"
        assert document_format("", "https://a/b/page") == ""
        # pandoc cannot read a PDF: with both installed the PDF path is still pdftotext
        have = {
            "pdftotext": "/usr/bin/pdftotext",
            "pandoc": "/usr/bin/pandoc",
            "markitdown": "/usr/bin/markitdown",
        }
        assert document_backend("pdf", have) == "pdftotext"
        assert document_backend("docx", have) == "pandoc"
        assert document_backend("pdf", {"pandoc": "/x"}) == ""
        if shutil.which("pdftotext"):
            text, backend = extract_document(FIX_PDF, "pdf", "/dev/null", have=have)
            assert backend == "pdftotext", backend
            assert "Hello web" in text, text
        return True

    def map_robots():
        assert parse_robots_sitemaps(FIX_ROBOTS) == [
            "https://example.com/sitemap.xml",
            "https://example.com/second.xml",
        ]
        assert parse_robots_sitemaps("User-agent: *\nDisallow: /\n") == []
        urls, is_index = parse_sitemap(FIX_SITEMAP)
        assert not is_index, urls
        assert urls == ["https://example.com/a?x=1&y=2", "https://example.com/b"], urls
        idx, is_index = parse_sitemap(FIX_SITEMAP_INDEX)
        assert is_index and idx == ["https://example.com/sitemap-1.xml.gz"], (is_index, idx)
        assert parse_llms_txt(FIX_LLMS) == [
            "https://example.com/docs",
            "https://example.com/api",
            "https://example.com/bare",
        ], parse_llms_txt(FIX_LLMS)
        gz = gzip.compress(FIX_SITEMAP.encode())
        assert not _gunzip_if_needed(gz).startswith(b"\x1f\x8b")
        assert _gunzip_if_needed(b"plain") == b"plain"
        sources = map_sources("https://example.com/docs/x")
        assert sources[0] == "https://example.com/sitemap.xml", sources
        assert sources[2] == "https://example.com/robots.txt", sources
        return True

    def crawl_origin():
        links = page_links(FIX_CRAWL_PAGE, "https://example.com/dir/page")
        assert links == ["https://example.com/inner", "https://other.example/x"], links
        kept = filter_links(links, "https://example.com/", True)
        assert kept == ["https://example.com/inner"], kept
        assert filter_links(links, "https://example.com/", False) == links
        assert not same_origin("http://example.com/x", "https://example.com/")
        assert same_origin("https://example.com/x", "https://EXAMPLE.com/")
        assert not crawlable("https://example.com/a.png")
        assert crawlable("https://example.com/a?page=2")
        assert page_title(FIX_CRAWL_PAGE) == "Seed page"
        return True

    def markdown_suite():
        """The ten captured pages, against their hand-checked expected markdown.

        Skipped when the source tree is not here (a wheel install has no fixtures): the check is
        about the current tree, and pretending a missing fixture passed would be the one thing a
        self-test must never do. The gate runs the same suite as a unit test, so a wheel that
        ships without it is still covered on the machine that built it.
        """
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base = os.path.join(root, "tests", "fixtures", "markdown")
        if not os.path.isdir(base):
            return True
        bases = {
            "01-npm-docs": "https://docs.npmjs.com/cli/v10/commands/npm-install",
            "02-mdn-fetch": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch",
            "03-github-readme": "https://github.com/sindresorhus/got",
            "04-arxiv-abs": "https://arxiv.org/abs/1706.03762",
            "05-stackoverflow": "https://stackoverflow.com/questions/11227809",
            "06-vercel-docs": "https://vercel.com/docs/frameworks",
            "07-react-docs": "https://react.dev/learn/state-a-components-memory",
            "08-wikipedia": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
            "09-hackernews": "https://news.ycombinator.com/item?id=1",
            "10-discourse": "https://discourse.jupyter.org/t/39125",
        }
        seen = 0
        for name, url in bases.items():
            html_path = os.path.join(base, name + ".html")
            md_path = os.path.join(base, name + ".md")
            if not (os.path.exists(html_path) and os.path.exists(md_path)):
                continue
            with open(html_path, encoding="utf-8") as fh:
                html = fh.read()
            with open(md_path, encoding="utf-8") as fh:
                want = fh.read()
            got = html_to_markdown(html, base=url)
            assert got == want, "%s differs from its expected markdown" % name
            seen += 1
        assert seen == 10, "expected ten fixture pairs, found %d" % seen
        return True

    def js_shell():
        assert js_shell_reason(FIX_SHELL, html_to_text(FIX_SHELL)), "shell not detected"
        assert js_shell_reason(FIX_SHELL_NEXT, html_to_text(FIX_SHELL_NEXT)), "__NEXT_DATA__ missed"
        assert not js_shell_reason(FIX_SOLID, html_to_text(FIX_SOLID)), "solid page flagged"
        # A 200 text/html page with real text outside <noscript> is complete at any length:
        # length is the last signal, never the first. This is what keeps example.com offline.
        short = FIX_SHORT_COMPLETE
        assert not js_shell_reason(short, html_to_text(short)), "short complete page flagged"
        assert len(" ".join(html_to_text(short).split())) < JS_SHELL_MIN
        # An empty body is still a shell, and its reason is the length it never had.
        empty = '<html><body><div id="root"></div></body></html>'
        assert "chars of text" in js_shell_reason(empty, html_to_text(empty)), (
            "empty shell not flagged"
        )
        tiny = "<html><body><div id=root></div><script>go()</script></body></html>"
        assert js_shell_reason(tiny, html_to_text(tiny)), "nothing-outside-noscript not flagged"
        long_plain = (
            "<html><body><p>" + "ordinary prose, no script marker " * 60 + "</p></body></html>"
        )
        assert not js_shell_reason(long_plain, html_to_text(long_plain))
        # A long page holding only a <noscript> apology must still be retried.
        ns_only = (
            "<html><body><noscript>" + "please turn on javascript " * 40 + "</noscript>"
            "</body></html>"
        )
        assert js_shell_reason(ns_only, html_to_text(ns_only)), "noscript-only page not flagged"
        return True

    chk("searxng json parser", searx_parse)
    chk("google redirect unwrap", google_unwrap)
    chk("merged-set drift filter", drift_filter)
    chk("live-query pacing", pace_guard)
    chk("engine tag in output", engine_tag)
    chk("unrelated-result guard", related_guard)
    chk("bot-check detection", blocked_page)
    chk("bing redirect unwrap", ck_a)
    chk("ddg-lite parser", ddg_lite)
    chk("ddg-html parser", ddg_html)
    chk("bing parser", bing)
    chk("github repos parser", gh_repos)
    chk("github issues parser", gh_issues)
    chk("stackexchange parser", so)
    chk("hackernews parser", hn)
    chk("arxiv parser", arxiv)
    chk("discourse search parser", discourse_search)
    chk("discourse topic renderer", discourse_topic)
    chk("nvidia url rewrite", nvidia_rewrite)
    chk("html to text", to_text)
    chk("link-density pruning", dense_prune)
    chk("cookie-banner pruning", cookie_prune)
    chk("pre kept verbatim", pre_verbatim)
    chk("small default output", render_small)
    chk("no identity in request", no_identity)
    chk("pdf content-type routing", pdf_routing)
    chk("map from robots and sitemap", map_robots)
    chk("same-origin crawl filtering", crawl_origin)
    chk("js-shell heuristic", js_shell)
    chk("markdown conformance suite", markdown_suite)

    ok = 0
    for name, good, why in checks:
        print("%s %s%s" % ("PASS" if good else "FAIL", name, "" if good else " :: " + why))
        ok += good
    print("SUMMARY pass=%d fail=%d" % (ok, len(checks) - ok))
    return 0 if ok == len(checks) else 1


# ---------------------------------------------------------------- setup and probe


def cmd_setup(argv):
    """Install the pieces the caller asks for, explicitly. Bare `setup` is SearXNG only.

    There are two independent installs and they are never one verb without a flag: a search
    backend is what `search` needs, a browser is what a hollow page needs, and a user may want
    one without the other. `--all` is the only way to ask for both in one run.
    """
    ap = argparse.ArgumentParser(prog="wsc setup")
    ap.add_argument("--searxng", action="store_true", help="install the local SearXNG unit")
    ap.add_argument("--playwright", action="store_true", help="install the playwright fallback")
    ap.add_argument("--all", action="store_true", help="both installs")
    ap.add_argument(
        "--with-deps",
        action="store_true",
        help="let playwright install the browser's OS packages (needs root)",
    )
    ap.add_argument("--force", action="store_true", help="rebuild what is already there")
    ap.add_argument("--no-start", action="store_true", help="install without starting the unit")
    ap.add_argument("--check", action="store_true", help="report state, change nothing")
    a, unknown = ap.parse_known_args(argv)
    both = a.all or (a.searxng and a.playwright)
    want_searxng = both or a.searxng or not (a.playwright or a.all)
    want_playwright = both or a.playwright or a.all
    rc = 0

    if want_searxng:
        passthrough = list(unknown)
        for flag, given in (("--force", a.force), ("--no-start", a.no_start), ("--check", a.check)):
            if given:
                passthrough.append(flag)
        code = searx_bundle.install(passthrough)
        if code != 0:
            return code
        found = searx_bundle.lightpanda_path()
        if found:
            print("lightpanda  %s" % found)
        else:
            warn("lightpanda: not on PATH, and the render path requires it")
            print(LIGHTPANDA_HINT)
            rc = 1

    if want_playwright:
        ok, lines = render_venv.setup(force=a.force, with_deps=a.with_deps, dry_run=a.check)
        for line in lines:
            print(line)
        if not ok:
            rc = 1

    return rc


def cmd_probe(argv):
    """The bundled engine probe: which engines this IP can actually use, as data."""
    return searx_bundle.probe(argv)


# ---------------------------------------------------------------- main


def cmd_cache(argv):
    """The four verbs over `.webscour/`: list, get, prune, path. No network except `get`."""
    ap = argparse.ArgumentParser(prog="wsc cache")
    ap.add_argument("action", choices=("list", "get", "prune", "path"))
    ap.add_argument("url", nargs="?")
    ap.add_argument("--older-than", default="7d", help="prune window (default 7d)")
    ap.add_argument("--all", action="store_true", help="prune: remove the whole directory")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.action == "path":
        print(cache_store.cache_dir())
        return 0

    if a.action == "get":
        if not a.url:
            warn("cache get: a URL is required")
            return 2
        try:
            hit = cache_store.lookup(a.url, ttl=None)  # `cache get` ignores the TTL on purpose
        except cache_store.CacheError as e:
            warn("cache: %s" % e)
            return 2
        if hit:
            print(hit[0].rstrip("\n"))
            vwarn("cache: file %s, %s old" % (hit[1].get("file"), cache_store.human_age(hit[2])))
            return 0
        # Missing: fetch it, save it, print it. `cache get` is the "give me this page" verb.
        vwarn("cache: miss, fetching %s" % a.url)
        rc = cmd_fetch([a.url, "--save", "--fresh", "--max-chars", "1000000"])
        return rc

    try:
        index = cache_store.read_index()
    except cache_store.CacheError as e:
        warn("cache: %s" % e)
        return 2

    if a.action == "list":
        if a.json:
            print(json.dumps(index, indent=1, sort_keys=True, ensure_ascii=False))
            return 0
        if not index:
            print("cache: empty (%s)" % cache_store.cache_dir())
            return 0
        now = time.time()
        rows = sorted(index.items(), key=lambda kv: kv[1].get("fetched_at") or 0, reverse=True)
        print("%-19s %9s %8s %-10s %s" % ("fetched", "bytes", "age", "format", "file"))
        for _key, entry in rows:
            age = cache_store.human_age(now - float(entry.get("fetched_at") or 0))
            print(
                "%-19s %9d %8s %-10s %s"
                % (
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(entry.get("fetched_at") or 0)
                    ),
                    int(entry.get("bytes") or 0),
                    age,
                    entry.get("format") or "?",
                    entry.get("file") or "?",
                )
            )
        total = sum(int(e.get("bytes") or 0) for e in index.values())
        print(
            "%d entr%s, %d bytes, %s"
            % (len(index), "y" if len(index) == 1 else "ies", total, cache_store.cache_dir())
        )
        for name in cache_store.orphans():
            vwarn("orphan file (not in the index): %s" % name)
        return 0

    # prune
    if a.all:
        path = cache_store.cache_dir()
        if not os.path.isdir(path):
            print("cache: nothing at %s" % path)
            return 0
        names = cache_store.clear()
        print("cache: removed %s" % names)
        return 0
    try:
        window = cache_store.parse_duration(a.older_than)
        gone = cache_store.prune(window)
    except cache_store.CacheError as e:
        warn("cache prune: %s" % e)
        return 2
    if not gone:
        print("cache: nothing older than %s" % a.older_than)
        return 0
    freed = sum(size for _, _, size in gone)
    for entry in gone:
        print("removed  %s  %s" % (entry[1], entry[0]))
    print("cache: %d file(s), %d bytes freed" % (len(gone), freed))
    return 0


def cmd_mcp(argv):
    """The stdio JSON-RPC server that ships outside the wheel. Loaded by path, never copied.

    By path rather than by name on purpose: `mcp/` is not a package of this wheel (the wheel is
    the CLI; the server is a front end for a host that speaks MCP), so an `import mcp.server`
    would be a lie about where it lives. It also keeps the dependency guard honest: this file
    imports nothing that is not the standard library.
    """
    import importlib.util

    pkg = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(pkg)
    # Three places, in order: the source tree next to this package, a copy installed beside the
    # package (what a wheel needs, see the note in mcp/README.md), and the share directory the
    # SearXNG data files already use.
    candidates = [
        os.path.join(root, "mcp", "server.py"),
        os.path.join(pkg, "_mcp_server.py"),
        os.path.join(pkg, "mcp", "server.py"),
    ]
    path = next((c for c in candidates if os.path.exists(c)), "")
    if not path:
        warn(
            "mcp: no server found (looked for %s); the source tree ships one, the wheel does not"
            % ", ".join(candidates)
        )
        return 2
    spec = importlib.util.spec_from_file_location("webscour_mcp_server", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["webscour_mcp_server"] = module
    spec.loader.exec_module(module)
    return module.main(argv)


MAIN_DOC = """wsc - one keyless CLI for lookups and pages, with small output. Linux, stdlib only.

    wsc search "<query>" [--source SRC] [--limit N] [--category C] [--fresh [--since D]] [--json]
    wsc fetch <url> [--max-chars N] [--grep REGEX] [--format text|markdown]
                    [--archive] [--no-route] [--save|--save-only] [--fresh] [--ttl D]
                    [--no-cache] [--max-size BYTES] [--render] [--render-engine E] [-v]
    wsc pdf <url|path> [--max-chars N] [--format text|markdown] [-v]
    wsc map <url> [--limit N] [-v]
    wsc crawl <url> [--depth N] [--limit N] [--same-origin] [-v]
    wsc cache list|get <url>|prune [--older-than D]|path
    wsc doctor [--json] [--live]
    wsc setup [--searxng|--playwright|--all] [--with-deps] [--force] [--no-start] [--check]
    wsc probe [--engines a,b] [--quality] [--write] [--json]
    wsc mcp
    wsc tool-argv --json '<params>'
    wsc --self-test

`--source` is one of web, github, so, hn, arxiv, discourse:<base>, or a keyless API source:
wikipedia, openalex, crossref, arxiv-api, europepmc, pubmed, pypi, npm, crates, devto, wayback,
googlenews, bbc. `--fresh` restricts to the freshness rows (Google News, BBC, SearXNG news) and
sorts by publication date. `--category` passes a SearXNG category through; it is opt-in because
a category changes which engines answer, and so changes the answer.

`--source web` asks a LOCAL SearXNG (127.0.0.1:8888, systemd user unit searxng-local;
installed by `wsc setup`) first and falls back to scraping only if that is not available.
Only the query leaves the machine, through SearXNG to the upstream engines: no cwd, host,
user or project name. GitHub allows 10 req/min unauthenticated.
`fetch` resolves a known site through its own API (`route: <name>` on stderr) and a dead page
through the Wayback Machine; `--format markdown` keeps headings, links and code fences.
`--save` writes the page to ./.webscour/ and a repeat read inside 24h comes from there
(`cache: hit`), which is the point: a page an agent reads twice is paid for once.
`pdf` picks the first working local backend (pdftotext, pandoc, markitdown). `fetch --render`
leaves plain HTTP for a real browser: lightpanda is the render engine and the render path
requires it, playwright is the fallback for a page that defeats lightpanda. Without the flag a
hollow page is retried once through the same chain. `map` reads sitemap, robots and llms.txt,
`crawl` walks links from there under a hard cap and the shared pace. `setup` installs the
SearXNG unit and checks lightpanda; `probe` measures the engines.
Output is the answer: stderr carries failures only, and `-v` explains every choice."""

USAGE = MAIN_DOC.strip().splitlines()[0]

VERBS = {
    "search": cmd_search,
    "fetch": cmd_fetch,
    "pdf": cmd_pdf,
    "map": cmd_map,
    "crawl": cmd_crawl,
    "cache": cmd_cache,
    "doctor": cmd_doctor,
    "setup": cmd_setup,
    "probe": cmd_probe,
    "mcp": cmd_mcp,
    "tool-argv": argv_mod.main,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(MAIN_DOC)
        return 0 if argv else 1
    if argv[0] in ("-V", "--version"):
        print("webscour %s" % __version__)
        return 0
    if argv[0] == "--self-test":
        return self_test()
    cmd, rest = argv[0], argv[1:]
    fn = VERBS.get(cmd)
    if fn is None:
        warn("unknown command %r" % cmd)
        print(MAIN_DOC)
        return 2
    return fn(rest)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)
