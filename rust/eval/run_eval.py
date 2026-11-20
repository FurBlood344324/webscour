#!/usr/bin/env python3
"""Compare the Python `wsc search` with the Rust port, query for query.

The point is not a benchmark of the two languages. It is one number per implementation: does
the port answer the same question as the code it was ported from? A faster port that finds a
different page is a different tool, and this table is what makes that visible.

    python3 rust/eval/run_eval.py                 # all 40 labelled queries
    python3 rust/eval/run_eval.py --limit 3       # a smoke test
    python3 rust/eval/run_eval.py --only 0,1,2    # specific indices

Each query runs through both implementations with the same `--limit`, at most one live query
per second (the shared pace both implementations honour). A run is a hit when any of the first
three rows carries the expected domain; a failure is recorded with the urls it did return, so a
median with no evidence under it cannot pass as a result.

Rows are printed as they land, then one summary table. Exit status is 0 when both columns were
measured, 1 when one implementation could not be run at all — a missing binary is not a miss.
"""

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
QUERIES = os.path.join(HERE, "queries.json")
PACE = 1.0
TIMEOUT = 90


def load_queries():
    with open(QUERIES, encoding="utf-8") as fh:
        return json.load(fh)["queries"]


def rust_binary():
    for candidate in (
        os.path.join(ROOT, "rust", "target", "release", "wsc"),
        os.path.join(ROOT, "rust", "target", "debug", "wsc"),
        shutil.which("wsc"),
    ):
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


def run(argv, cwd, timeout=TIMEOUT):
    """(rows, seconds, exit code). Rows are the urls in the numbered output, in order."""
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return [], timeout, 124
    elapsed = time.monotonic() - started
    # The numbered row is `N. title - url  [engine,engine]`, and both halves can contain " - ",
    # so the url is what is left after the last separator, with the tag cut off first.
    urls = []
    for line in proc.stdout.splitlines():
        if not re.match(r"^\d+\.\s", line):
            continue
        rest = line.split("  [", 1)[0]
        tail = rest.rsplit(" - ", 1)[-1].strip()
        if tail.startswith(("http://", "https://")):
            urls.append(tail)
    return urls, elapsed, proc.returncode


def hit(urls, expect, k=3):
    return any(expect in u for u in urls[:k])


def beep_pace(last):
    """Never start two live queries closer than PACE seconds apart."""
    delay = PACE - (time.monotonic() - last)
    if delay > 0:
        time.sleep(delay)
    return time.monotonic()


def main():
    ap = argparse.ArgumentParser(description="python vs rust search eval")
    ap.add_argument("--limit", type=int, default=3, help="rows per query (hit@3 needs 3)")
    ap.add_argument("--only", default="", help="comma-separated query indices")
    ap.add_argument("--json", default="", help="write the raw results here")
    a = ap.parse_args()

    queries = load_queries()
    if a.only:
        keep = {int(x) for x in a.only.split(",") if x.strip()}
        queries = [q for i, q in enumerate(queries) if i in keep]

    rust = rust_binary()
    if not rust:
        print("eval: no rust binary (cargo build --release in rust/)", file=sys.stderr)
        return 1

    python_cmd = [sys.executable, "-m", "webscour.cli"]
    results = []
    print("%-3s %-46s %-28s %-6s %-6s" % ("#", "query", "expect", "py", "rs"))
    print("-" * 96)
    stamp = time.monotonic() - PACE
    for i, item in enumerate(queries):
        q, expect = item["q"], item["expect"]
        stamp = beep_pace(stamp)
        py_urls, py_s, py_rc = run(python_cmd + ["search", q, "--limit", str(a.limit)], ROOT)
        stamp = beep_pace(stamp)
        rs_urls, rs_s, rs_rc = run(
            [rust, "search", q, "--limit", str(a.limit)], os.path.join(ROOT, "rust")
        )
        py_ok, rs_ok = hit(py_urls, expect), hit(rs_urls, expect)
        results.append(
            {
                "query": q,
                "expect": expect,
                "python": {"urls": py_urls, "seconds": py_s, "rc": py_rc, "hit": py_ok},
                "rust": {"urls": rs_urls, "seconds": rs_s, "rc": rs_rc, "hit": rs_ok},
            }
        )
        print(
            "%-3d %-46s %-28s %-6s %-6s"
            % (i, q[:46], expect[:28], "hit" if py_ok else "miss", "hit" if rs_ok else "miss")
        )
        # A miss prints the evidence immediately: a summary alone would hide which side drifted.
        for name, got in (("py", py_urls), ("rs", rs_urls)):
            if not hit(got, expect):
                print("      %s: %s" % (name, "; ".join(got[:3]) or "(no rows)"))

    def median(values):
        return statistics.median(values) if values else 0.0

    summary = []
    for name, key in (("python", "python"), ("rust", "rust")):
        col = [r[key] for r in results]
        hits = sum(1 for c in col if c["hit"])
        answered = sum(1 for c in col if c["rc"] == 0 and c["urls"])
        summary.append(
            {
                "impl": name,
                "hit@3": hits,
                "queries": len(results),
                "hit_rate": hits / len(results) if results else 0.0,
                "success_rate": answered / len(results) if results else 0.0,
                "median_seconds": median([c["seconds"] for c in col]),
            }
        )

    print()
    print("%-8s %-8s %-10s %-8s %-10s" % ("impl", "hit@3", "hit rate", "success", "median s"))
    print("-" * 54)
    for row in summary:
        print(
            "%-8s %-8s %-10s %-8s %-10.2f"
            % (
                row["impl"],
                "%d/%d" % (row["hit@3"], row["queries"]),
                "%.0f%%" % (100 * row["hit_rate"]),
                "%.0f%%" % (100 * row["success_rate"]),
                row["median_seconds"],
            )
        )

    agree = sum(1 for r in results if r["python"]["hit"] == r["rust"]["hit"])
    print()
    print("agreement on hit@3: %d/%d labelled queries" % (agree, len(results)))

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"results": results, "summary": summary}, fh, indent=1)
        print("raw results: %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
