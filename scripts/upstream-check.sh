#!/usr/bin/env bash
# upstream-check.sh - the live probe that upstream-check.yml runs, and that a human can run.
#
# It answers one question: is the web still shaped like the tool assumes? Not "does the code
# compile" (that is check.sh) and not "is the extraction good" (that is BENCH=1 check.sh). This
# is the one place where a third party's HTML can make us wrong without a single line changing.
#
# Writes .agent-out/upstream-check.txt and prints the same. Exit code is always 0: the report is
# the product. A failing line names what to look at.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

OUT_DIR="$ROOT/.agent-out"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/upstream-check.txt"
: > "$OUT"

say() { printf '%s\n' "$*" | tee -a "$OUT"; }

# Each row: label, command, and the substring that means "the answer is real, not chrome".
check() { # label, expected-substring, command...
  local label="$1" want="$2"
  shift 2
  local got rc=0
  got="$("$@" 2>&1)" || rc=$?
  if [ "$rc" -ne 0 ]; then
    say "FAIL $label :: exit $rc :: $(printf '%s' "$got" | head -1 | cut -c1-140)"
    return 0
  fi
  if printf '%s' "$got" | grep -qiF -- "$want"; then
    say "PASS $label ($(printf '%s' "$got" | wc -l) lines, $(printf '%s' "$got" | wc -c) bytes)"
  else
    say "FAIL $label :: answered without '$want' :: $(printf '%s' "$got" | head -2 | tr '\n' ' ' | cut -c1-140)"
  fi
}

PY="${PYTHON:-python3}"
WSC="$PY -m webscour"

say "# upstream check $(date -u +%Y-%m-%dT%H:%M:%SZ) python $($PY -c 'import sys;print(sys.version.split()[0])')"
say ""
say "## structured sources (a JSON API, so stable unless the API changes)"
check hn "$WSC search \"Y Combinator\" --source hn --limit 2" "news.ycombinator.com"
check arxiv "$WSC search \"attention is all you need\" --source arxiv --limit 2" "arxiv.org"
check github "$WSC search \"webscour\" --source github --limit 2" "github.com"
check stackexchange "$WSC search \"python bytes decode\" --source so --limit 2" "stackoverflow.com"

say ""
say "## scraped sources (HTML, so this is where a redesign bites)"
check ddg-lite "$WSC search \"python packaging\" --source web --limit 3" "http"

say ""
say "## page extraction (the part that has to keep working most)"
check example "$WSC fetch https://example.com" "domain"
check wikipedia "$WSC fetch https://en.wikipedia.org/wiki/Web_scraping --max-chars 2000" "scraping"
check github-readme "$WSC fetch https://github.com/simonw/llm --max-chars 4000" "pip install"
check react "$WSC fetch https://react.dev/learn --max-chars 4000" "component"

say ""
say "## the fallback chain is reachable"
check doctor-lightpanda "$WSC doctor" "lightpanda"

say ""
say "SUMMARY (exit code is always 0: read the FAIL lines)"
say "report: $OUT"
exit 0
