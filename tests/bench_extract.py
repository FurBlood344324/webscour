#!/usr/bin/env python3
"""Extraction benchmark: our reading text against trafilatura's, on the five reference pages.

A dev tool, not shipped in the wheel: `pyproject.toml` packages `webscour` only. It exists
because "the extraction got better" is a claim, and a claim needs a number with a date on it.

    python3 tests/bench_extract.py                 # offline, from tests/fixtures/bench/
    python3 tests/bench_extract.py --live          # re-fetch the pages first, then measure
    python3 tests/bench_extract.py --save-baseline tests/baselines/0.2.0.json
    python3 tests/bench_extract.py --tolerance 0.10

Three numbers per page:

  bytes   what the extractor produced, in UTF-8 bytes
  lines   how many lines those bytes are split into
  prec    bytes_out / bytes_of_visible_text. The denominator is a naive strip-all-tags text,
          so 1.00 means the extractor kept every visible character including every menu, and
          0.60 means it threw 40% away. It is a proxy, not a truth: it cannot tell boilerplate
          from content. That is why every page also carries PHRASES, a recall gate, and a run
          that loses one of those fails regardless of any byte count.

trafilatura is a reference measured through a throwaway venv at /tmp/tfvenv (`python3 -m venv
/tmp/tfvenv && /tmp/tfvenv/bin/pip install trafilatura`). It is never a dependency of anything
shipped; when the venv is absent the column reads n/a and only our own baseline decides.

Exit code: non-zero when a page lost a PHRASES string, or when our output regressed past
`--tolerance` against the newest file in tests/baselines/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "bench"
BASELINES = ROOT / "tests" / "baselines"
TFVENV = Path("/tmp/tfvenv/bin/python")
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# The pages the extraction design was measured against. `phrases` is the recall gate: the
# main content of each page, as a string a human would search for.
PAGES = [
    {
        "url": "https://en.wikipedia.org/wiki/Web_scraping",
        "fixture": "0dbff88b78.html",
        "phrases": ["Web scraping", "Screen scraping", "JumpStation"],
    },
    {
        "url": "https://arxiv.org/abs/1706.03762",
        "fixture": "32b9d4c781.html",
        "phrases": ["Attention Is All You Need", "dominant sequence transduction models"],
    },
    {
        "url": "https://news.ycombinator.com/item?id=1",
        "fixture": "cb7f1c1377.html",
        "phrases": ["Y Combinator", "Sandhill Road"],
    },
    {
        "url": "https://github.com/simonw/llm",
        "fixture": "6c7b15256e.html",
        "phrases": ["pip install llm", "Run prompts from the command-line"],
    },
    {
        "url": "https://react.dev/learn",
        "fixture": "3598bfc083.html",
        "phrases": ["Creating and nesting components", "Conditional rendering"],
    },
    # The page that is a table of links. Kept in the set because an earlier version of the
    # link-density rules emptied it completely: a rule that reads "mostly link text" is correct
    # for an article and catastrophic for a feed.
    {
        "url": "https://news.ycombinator.com/",
        "fixture": "hn-front.html",
        "phrases": ["Hacker News", "points by"],
    },
]

# Live-only: the page the hollow heuristic is about. Kept out of the offline set because its
# whole point is that it is short and complete.
EXTRA = [
    {"url": "https://example.com", "fixture": "example.html", "phrases": ["Example Domain"]},
]


class _Naive(HTMLParser):
    """Every visible character, no pruning. The denominator of the precision proxy."""

    SKIP = frozenset({"script", "style", "noscript", "template", "head", "title"})

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)


def visible_text(page):
    parser = _Naive()
    parser.feed(page or "")
    parser.close()
    return " ".join(" ".join(parser.parts).split())


def trafilatura_text(page):
    """(bytes, lines) from trafilatura, or None when the reference venv is not installed."""
    if not TFVENV.exists():
        return None
    code = (
        "import json, sys\n"
        "import trafilatura\n"
        "text = trafilatura.extract(sys.stdin.read(), include_comments=False,\n"
        "                           include_tables=True) or ''\n"
        "print(json.dumps([len(text.encode()), len(text.splitlines())]))\n"
    )
    try:
        done = subprocess.run(
            [str(TFVENV), "-c", code], input=page, capture_output=True, text=True, timeout=300
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0 or not done.stdout.strip():
        return None
    nbytes, nlines = json.loads(done.stdout.strip().splitlines()[-1])
    return nbytes, nlines


def fetch(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", "replace")


def pages(live):
    for page in PAGES + (EXTRA if live else []):
        path = FIXTURES / page["fixture"]
        if live or not path.exists():
            try:
                html = fetch(page["url"])
            except OSError as exc:
                yield page, None, str(exc)
                continue
            FIXTURES.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
            yield page, html, ""
        else:
            yield page, path.read_text(encoding="utf-8", errors="replace"), ""


def newest_baseline():
    files = sorted(BASELINES.glob("*.json")) if BASELINES.is_dir() else []
    if not files:
        return None
    try:
        return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def compare(rows, baseline, tolerance):
    path, data = baseline
    was = {row["url"]: row for row in data.get("pages", [])}
    out = []
    for row in rows:
        old = was.get(row["url"])
        if not old:
            continue
        if row["bytes"] > old["bytes"] * (1 + tolerance) + 64:
            out.append(
                "%s: %d bytes is over baseline %d by %d%% (%s)"
                % (
                    row["url"],
                    row["bytes"],
                    old["bytes"],
                    round(100 * (row["bytes"] / old["bytes"] - 1)),
                    path.name,
                )
            )
        if row["prec"] < old["prec"] - 0.05:
            out.append(
                "%s: kept %.2f of visible text, baseline %.2f (%s)"
                % (row["url"], row["prec"], old["prec"], path.name)
            )
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bench_extract", description=__doc__.splitlines()[0])
    ap.add_argument("--live", action="store_true", help="re-fetch the pages before measuring")
    ap.add_argument(
        "--tolerance",
        type=float,
        default=0.10,
        help="allowed regression over the baseline, relative (default 0.10)",
    )
    ap.add_argument("--save-baseline", metavar="PATH", help="write this run as a new baseline")
    ap.add_argument("--json", action="store_true", help="machine-readable rows")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(ROOT))
    from webscour.extract import html_to_text

    rows, failures = [], []
    for page, html, err in pages(args.live):
        if html is None:
            failures.append("%s: %s" % (page["url"], err))
            continue
        text = html_to_text(html)
        naive = visible_text(html)
        row = {
            "url": page["url"],
            "bytes": len(text.encode()),
            "lines": len(text.splitlines()),
            "visible": len(naive.encode()),
            "prec": round(len(text.encode()) / max(1, len(naive.encode())), 3),
        }
        ref = trafilatura_text(html)
        if ref:
            row["traf_bytes"], row["traf_lines"] = ref
            row["vs_traf"] = round(row["bytes"] / max(1, ref[0]), 3)
        low = text.lower()
        missing = [p for p in page["phrases"] if p.lower() not in low]
        if missing:
            failures.append("%s: lost %s" % (page["url"], ", ".join(repr(p) for p in missing)))
        rows.append(row)

    if args.json:
        print(json.dumps(rows, indent=1))
    else:
        head = "%-44s %8s %6s %8s %6s %8s" % ("URL", "bytes", "lines", "visible", "prec", "vs traf")
        print(head)
        print("-" * len(head))
        for row in rows:
            ratio = ("%.2fx" % row["vs_traf"]) if "vs_traf" in row else "n/a"
            print(
                "%-44s %8d %6d %8d %6.2f %8s"
                % (row["url"], row["bytes"], row["lines"], row["visible"], row["prec"], ratio)
            )
        measured = [row for row in rows if "traf_bytes" in row]
        if measured:
            ours = sum(row["bytes"] for row in measured)
            theirs = sum(row["traf_bytes"] for row in measured)
            print("-" * len(head))
            print(
                "%-44s %8d %6d %8d %6.2f %8.2fx"
                % (
                    "TOTAL",
                    ours,
                    sum(row["lines"] for row in measured),
                    sum(row["visible"] for row in measured),
                    ours / max(1, sum(row["visible"] for row in measured)),
                    ours / theirs,
                )
            )

    if args.save_baseline:
        target = Path(args.save_baseline)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps({"pages": rows}, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("baseline written: %s" % target, file=sys.stderr)
    elif not args.live:
        baseline = newest_baseline()
        if baseline:
            failures += compare(rows, baseline, args.tolerance)

    for failure in failures:
        print("FAIL " + failure, file=sys.stderr)
    print("SUMMARY pages=%d fail=%d" % (len(rows), len(failures)), file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
