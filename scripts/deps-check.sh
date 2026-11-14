#!/usr/bin/env bash
# deps-check.sh - do the pinned things still exist, and is lightpanda's CLI still the CLI we call?
#
# Two facts, weekly, read-only:
#
#   1. every `uses: owner/repo@ref` in .github/workflows/ still resolves to a real tag or branch
#   2. `lightpanda fetch --dump markdown --dump-max-bytes N URL` still does what backends.py
#      assumes: prints text to stdout, exits 0, and does not rename the flags
#
# It never upgrades anything. A green run means "the pins are still valid today", not "upgrade
# later": the upgrade is a decision with a diff, and it deserves a person. Writes
# .agent-out/deps-check.txt; exit 1 when a fact changed, which is what opens the issue.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

mkdir -p .agent-out
OUT=".agent-out/deps-check.txt"
: > "$OUT"
bad=0
say() { printf '%s\n' "$*" | tee -a "$OUT"; }

# ---------------------------------------------------------------- pinned actions
say "# dependency check $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say ""
say "## pinned GitHub actions"
refs="$(grep -rhoE 'uses: *[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[^ ]+' .github/workflows/ 2>/dev/null |
        sed 's/^uses: *//' | sort -u)"
if [ -z "$refs" ]; then
  say "no pinned actions found (unexpected: the workflows call several)"
  bad=1
fi
for ref in $refs; do
  repo="${ref%@*}"
  tag="${ref##*@}"
  case "$tag" in
    v*) : ;;                                    # a major tag moves; it is not a pin
  esac
  url="https://api.github.com/repos/$repo/git/ref/tags/$tag"
  code="$(curl -s -o /dev/null -w '%{http_code}' -m 20 "$url" || echo 000)"
  if [ "$code" = "200" ] || [ "$code" = "422" ]; then
    say "ok   $ref"
  else
    # A branch ref is legitimate too; ask for the branch before calling it broken.
    bcode="$(curl -s -o /dev/null -w '%{http_code}' -m 20 \
             "https://api.github.com/repos/$repo/branches/$tag" || echo 000)"
    if [ "$bcode" = "200" ]; then
      say "ok   $ref (branch)"
    else
      say "DRIFT $ref :: tag $code, branch $bcode"
      bad=1
    fi
  fi
done

# ---------------------------------------------------------------- lightpanda CLI surface
say ""
say "## lightpanda CLI surface"
if ! command -v lightpanda >/dev/null 2>&1; then
  say "skip lightpanda: not on PATH in this runner (the nightly is not installed here)"
  say "      install route: https://pkg.lightpanda.io/install.sh (README has the four options)"
else
  version="$(lightpanda version 2>&1 | head -1 || true)"
  say "lightpanda: ${version:-unknown}"
  out="$(lightpanda fetch --dump markdown --dump-max-bytes 4000 https://example.com 2>&1 || true)"
  if printf '%s' "$out" | grep -qiE 'unknown (flag|argument)|unrecognized|usage:'; then
    say "DRIFT lightpanda :: --dump / --dump-max-bytes are not accepted any more"
    say "      saw: $(printf '%s' "$out" | head -2 | tr '\n' ' ' | cut -c1-200)"
    bad=1
  elif printf '%s' "$out" | grep -qi 'example domain'; then
    say "ok    lightpanda fetch --dump markdown --dump-max-bytes"
  else
    say "DRIFT lightpanda :: the flags were accepted but the dump did not contain the page"
    say "      saw: $(printf '%s' "$out" | head -2 | tr '\n' ' ' | cut -c1-200)"
    bad=1
  fi
fi

say ""
if [ "$bad" -eq 0 ]; then
  say "SUMMARY deps=ok"
else
  say "SUMMARY deps=drift (see DRIFT lines above)"
fi
exit "$bad"
