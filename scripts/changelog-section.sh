#!/usr/bin/env bash
# changelog-section.sh <version> - print one release's section of CHANGELOG.md.
#
# Used by .github/workflows/release.yml as the body of the GitHub Release, so the release notes
# and the changelog cannot disagree: they are the same text. Prints nothing and exits 1 when the
# section is missing, because a release with an empty body is a release nobody will read.
#
#   ./scripts/changelog-section.sh 0.2.0
#   ./scripts/changelog-section.sh --list      # every version the changelog has

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

if [ "${1:-}" = "--list" ]; then
  grep -E '^## [0-9]+\.[0-9]+\.[0-9]+' CHANGELOG.md | sed 's/^## //; s/ - .*//'
  exit 0
fi

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  echo "usage: changelog-section.sh <version>|--list" >&2
  exit 2
fi
VERSION="${VERSION#v}"

out="$(awk -v want="$VERSION" '
  /^## / {
    if (found) exit
    if ($0 ~ ("^## " want "([ ]|$)")) { found = 1; next }
    next
  }
  found { print }
' CHANGELOG.md)"

if [ -z "$(printf '%s' "$out" | tr -d '[:space:]')" ]; then
  echo "changelog-section: no section for $VERSION in CHANGELOG.md" >&2
  exit 1
fi
printf '%s\n' "$out"
