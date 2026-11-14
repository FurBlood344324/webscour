#!/usr/bin/env python3
"""Measure which SearXNG engines actually answer from this IP, and write the result as data.

    probe-engines.py [--engines a,b,c] [--json]   one engine at a time (the isolation experiment)
    probe-engines.py --quality [--write] [--json] coverage/precision per engine; --write selects
    probe-engines.py --doctor                     the CLI's doctor, never a second opinion

Why isolation is not the criterion: a single upstream is either rate-limited or spammy from a
residential IP, so a per-engine "70 % success" bar selects nothing -- and a bar that selects
nothing is not a measurement. What a meta-search needs is engines whose rows are on topic and
that arrive often. `--quality` measures coverage and precision in one merged pass and `--write`
stores the survivors in ~/.local/share/searxng/engines.json, which install.sh renders into the
`engines:` block of settings.yml.

A row is relevant when a title/url word of the query appears in it, the same guard the CLI uses.
CAPTCHA, access denied, suspension, timeout and parse errors count as blocks regardless of the
result count. Queries are generic technical terms: no project, company, device, camera, person,
path or credential name is ever sent.
"""
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8888"
STATE = os.path.expanduser("~/.local/share/searxng/engines.json")
UNIT = "searxng-local"
CANDIDATES = ["duckduckgo", "brave", "mojeek", "startpage", "qwant", "bing", "google",
              "wikipedia", "github", "stackoverflow", "arxiv", "hackernews", "yandex",
              "marginalia", "searchmysite"]
# Kept by name, not by score: the one engine that answers well from a residential IP
# whenever it is not rate-limited, so the set improves by itself when its suspension lapses.
BONUS_ENGINES = ["brave"]
PROBE_QUERIES = [  # 4 English technical, 3 Turkish, 3 niche-but-public
    "python asyncio task cancellation timeout",
    "postgres index bloat vacuum full",
    "nginx proxy_pass websocket upgrade headers",
    "rust borrow checker lifetime elision",
    "python sanal ortam oluşturma",
    "linux disk kullanımını görüntüleme",
    "git commit geçmişini düzenleme",
    "nvv4l2decoder drop-frame-interval",
    "patchcore memory bank coreset sampling",
    "granian wsgi workers backpressure",
]
# The measured set from the README table: 10 mixed + 10 more + 10 more, all generic.
QUALITY_QUERIES = PROBE_QUERIES + [
    "pytorch dataloader num_workers hangs",
    "docker build multi-stage alpine reduces size",
    "sqlite wal mode concurrent readers",
    "ffmpeg h264 crf preset comparison",
    "pandas dataframe sütun seçme",
    "türkçe karakter encoding sorunu",
    "nginx worker_connections ulimit too many open files",
    "git rebase interactive squash commits",
    "gstreamer appsink drop property latency",
    "opencv imread unicode path windows",
    "c++ std::optional monadic operations",
    "kubernetes readiness probe httpGet",
    "redis eviction policy allkeys-lru",
    "webassembly wasm simd support browser",
    "pandas groupby agg multiple columns",
    "django select_related prefetch_related difference",
    "türkçe metin benzerlik ölçümü",
    "makine öğrenmesi veri ön işleme eksik değer",
    "görüntü işleme kenar tespiti algoritmaları",
    "opencv gaussian blur kernel size",
]
BLOCK_WORDS = ("captcha", "access denied", "too many requests", "timeout", "error",
               "exception", "forbidden", "unexpected", "suspended", "crash")
PACE = 1.05  # at most one live web query per second: this is not a scraper


def get_json(url, timeout=40):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def search(query, engines=None, timeout=40):
    params = {"q": query, "format": "json", "safesearch": "0"}
    if engines:
        params["engines"] = engines
    return get_json("%s/search?%s" % (BASE, urllib.parse.urlencode(params)), timeout)


def terms(query):
    return [t.lower() for t in re.findall(r"[0-9a-zA-Z_+-]{4,}", query)]


def is_relevant(query, row):
    """Same guard as webscour.backends.related: an unrelated cached page is not a success."""
    words = terms(query)
    if not words:
        return True
    blob = " ".join(str(row.get(k) or "") for k in ("title", "url", "content")).lower()
    return any(w in blob for w in words)


def blocked_msg(data, engine):
    for name, msg in data.get("unresponsive_engines") or []:
        if name == engine:
            low = msg.lower()
            if any(w in low for w in BLOCK_WORDS):
                return msg
    return None


def engine_config():
    return {e["name"]: e for e in get_json(BASE + "/config", timeout=15).get("engines", [])}


# ---------------------------------------------------------------- per engine

def per_engine(only=None):
    loaded = engine_config()
    want = [n for n in (only or CANDIDATES) if n in loaded]
    missing = [n for n in (only or CANDIDATES) if n not in loaded]
    if missing:
        print("probe: not loaded by this instance, skipped: " + ", ".join(missing))
    rows = []
    for i, name in enumerate(want, 1):
        hits, lat, blocks, why = 0, [], 0, {}
        for q in PROBE_QUERIES:
            t0 = time.time()
            try:
                data = search(q, name)
            except (urllib.error.URLError, ValueError, OSError):
                lat.append(time.time() - t0)
                blocks += 1
                why["request failed"] = why.get("request failed", 0) + 1
                time.sleep(PACE)
                continue
            lat.append(time.time() - t0)
            mine = [r for r in data.get("results", []) if r.get("engine") == name]
            bad = blocked_msg(data, name)
            if bad:
                blocks += 1
                why[bad] = why.get(bad, 0) + 1
            elif mine and any(is_relevant(q, r) for r in mine):
                hits += 1
            else:
                why["no relevant result"] = why.get("no relevant result", 0) + 1
            time.sleep(PACE)
        n = len(PROBE_QUERIES)
        median = statistics.median(lat) if lat else 0.0
        row = {"name": name, "categories": loaded[name].get("categories", []),
               "success_pct": round(100.0 * hits / n, 1), "median_latency": round(median, 2),
               "blocked": blocks, "reasons": why,
               # a slow engine must not hold the whole search; 4 s floor, 2x median, 9 s cap
               "timeout": round(min(9.0, max(4.0, median * 2.0)), 1)}
        rows.append(row)
        print("%2d/%d %-14s %5.1f%%  median %4.2fs  blocked %d  %s"
              % (i, len(want), name, row["success_pct"], row["median_latency"],
                 row["blocked"], " ".join(row["categories"])), flush=True)
    return rows


# ---------------------------------------------------------------- quality

def quality(as_json=False, do_write=False):
    """Per engine, measured on ONE merged pass: coverage (queries it helps on) and precision.

    Coverage is what a meta-search needs from an engine; precision is what keeps the
    output readable. Both come from the engine's own results inside a merged response,
    so this costs one query per case instead of one query per engine per case.
    """
    try:
        loaded = engine_config()
    except (urllib.error.URLError, ValueError, OSError) as e:
        print("quality: SearXNG is not answering on %s (%s)" % (BASE, str(e)[:60]))
        return 1
    stat = {n: {"queries": 0, "was_up": 0, "rows": 0, "relevant": 0,
                "same_as_others": 0} for n in loaded}
    lat, done = [], 0
    for q in QUALITY_QUERIES:
        t0 = time.time()
        try:
            data = search(q)
        except (urllib.error.URLError, ValueError, OSError):
            time.sleep(PACE)
            continue
        lat.append(time.time() - t0)
        done += 1
        dead = {n for n, _ in (data.get("unresponsive_engines") or [])}
        per_url_engines = {}
        for r in data.get("results", []):
            url = (r.get("url") or "").split("#")[0]
            if url:
                per_url_engines.setdefault(url, set()).update(r.get("engines") or [])
        for r in data.get("results", []):
            url = (r.get("url") or "").split("#")[0]
            rel = is_relevant(q, r)
            for eng in (r.get("engines") or ([r.get("engine")] if r.get("engine") else [])):
                if eng not in stat:
                    continue
                stat[eng]["rows"] += 1
                stat[eng]["relevant"] += bool(rel)
                if rel and len(per_url_engines.get(url, ())) > 1:
                    stat[eng]["same_as_others"] += 1
        seen = set()
        for r in data.get("results", []):
            for eng in (r.get("engines") or []):
                if eng not in seen and eng in stat:
                    seen.add(eng)
                    stat[eng]["queries"] += 1
                    stat[eng]["was_up"] += bool(is_relevant(q, r))
        print("  q=%-46s results=%-3d dead=%-2d %.1fs" % (q[:46], len(data.get("results", [])),
                                                          len(dead), lat[-1]), flush=True)
        time.sleep(PACE)

    rows = []
    for name, s in stat.items():
        if not s["queries"]:
            continue
        rows.append({"name": name,
                     "coverage_pct": round(100.0 * s["was_up"] / max(1, done), 1),
                     "precision_pct": round(100.0 * s["relevant"] / max(1, s["rows"]), 1),
                     "rows": s["rows"], "shared": s["same_as_others"],
                     "median_latency": round(statistics.median(lat), 2) if lat else 0.0})
    rows.sort(key=lambda r: (r["coverage_pct"], r["precision_pct"]), reverse=True)
    print("\n%-14s %8s %9s %6s %7s" % ("engine", "coverage", "precision", "rows", "shared"))
    for r in rows:
        print("%-14s %7.1f%% %8.1f%% %6d %7d"
              % (r["name"], r["coverage_pct"], r["precision_pct"], r["rows"], r["shared"]))

    # The bar: an engine is kept when it helps on enough queries AND its rows are mostly
    # relevant. Coverage alone would keep a spam funnel; precision alone would keep a
    # once-a-month wiki. BONUS engines are kept by name for a different reason, written
    # down so the choice is auditable rather than a feeling.
    MIN_COVERAGE, MIN_PRECISION = 10.0, 60.0
    keep = [r for r in rows if r["coverage_pct"] >= MIN_COVERAGE
            and r["precision_pct"] >= MIN_PRECISION]
    bonus = [n for n in BONUS_ENGINES if n in loaded and n not in {r["name"] for r in keep}]
    dead = [r["name"] for r in rows if r["coverage_pct"] < MIN_COVERAGE
            and r["precision_pct"] < MIN_PRECISION]
    print("\nkeep %d: %s" % (len(keep), ", ".join(r["name"] for r in keep) or "none"))
    if bonus:
        print("keep (bonus): " + ", ".join(bonus))
    print("drop %d (weak on both axes): %s" % (len(dead), ", ".join(dead) or "none"))
    bar = sum(1 for _ in rows) and len(keep) + len(bonus)
    print("selected %d engines; bar coverage>=%.0f%% and precision>=%.0f%%"
          % (bar, MIN_COVERAGE, MIN_PRECISION))

    if do_write:
        if not keep and not bonus:
            print("probe: refusing to write an empty engine set; settings left untouched")
            return 1
        # Per-engine latency is not separable from a merged pass, so the per-engine timeout
        # is a fixed 5 s: below outgoing.max_request_timeout (6 s) in settings.yml, so one
        # slow upstream can never hold the whole response past the six-second budget.
        chosen = [{"name": r["name"], "timeout": 5.0,
                   "coverage_pct": r["coverage_pct"], "precision_pct": r["precision_pct"]}
                  for r in keep]
        chosen += [{"name": n, "timeout": 5.0, "coverage_pct": None, "precision_pct": None}
                   for n in bonus]
        out = {"searxng": BASE, "measured": time.strftime("%Y-%m-%dT%H:%M:%S"), "queries": done,
               "criterion": "coverage >= %.0f%% and precision >= %.0f%%" % (MIN_COVERAGE, MIN_PRECISION),
               "engines": chosen}
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print("probe: wrote %s (%d engines) -- run install.sh to render it"
              % (STATE, len(chosen)))
    if as_json:
        print(json.dumps({"queries": done, "engines": rows,
                          "keep": [r["name"] for r in keep] + bonus}, indent=1, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- doctor

def doctor(as_json=False):
    """One verdict, one implementation: the CLI's. Duplicating the rule here produced a second,
    stricter verdict (any blocked engine -> DEGRADED) that contradicted `wsc doctor`.

    Inside an installed package there is no sibling CLI to exec, so `wsc probe` passes the
    command line in WSC_DOCTOR_CMD. A standalone checkout still finds `../web`, which the
    brain-side shim execs into the same code.
    """
    cmd = shlex.split(os.environ.get("WSC_DOCTOR_CMD") or "") or [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"), "doctor"]
    if as_json:
        cmd.append("--json")
    try:
        return subprocess.run(cmd, timeout=90, check=False).returncode
    except (OSError, subprocess.SubprocessError) as e:
        print("doctor: cannot run `wsc doctor` (%s)" % e)
        return 1


def main(argv):
    if "--doctor" in argv:
        return doctor("--json" in argv)
    if "--quality" in argv:
        return quality("--json" in argv, "--write" in argv)
    only = None
    if "--engines" in argv:
        only = argv[argv.index("--engines") + 1].split(",")
    try:
        rows = per_engine(only)
    except (urllib.error.URLError, ValueError, OSError) as e:
        print("probe: SearXNG is not answering on %s (%s)" % (BASE, str(e)[:80]))
        print("probe: start it with   systemctl --user start %s" % UNIT)
        return 1
    keep = [r for r in rows if r["success_pct"] >= 70.0 and not r["blocked"]
            and set(r["categories"]) & {"general", "web"}]
    print("\nkeep (>=70%% success, no block, web category): %s"
          % (", ".join(r["name"] for r in keep) or "none"))
    if "--json" in argv:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
