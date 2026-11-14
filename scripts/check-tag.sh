#!/usr/bin/env bash
# check-tag.sh <tag> - fail unless the tag is exactly `v` plus the package's own version.
#
# The release workflow's one piece of logic, kept here rather than in a YAML heredoc: a heredoc
# inside a `run:` block is indented, and an indented terminator is a shell error, so the "logic in
# a workflow" boundary was not only a style choice.
#
#   ./scripts/check-tag.sh v0.2.0     # exit 0 when webscour.__version__ is 0.2.0
#   ./scripts/check-tag.sh            # uses GITHUB_REF_NAME, then `git describe --exact-match`
#
# An absent tag is not a failure: this runs on a laptop too, and a laptop has no tag until the
# release script makes one.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
PY="${PYTHON:-python3}"

TAG="${1:-${GITHUB_REF_NAME:-}}"
if [ -z "$TAG" ]; then
  TAG="$(git describe --tags --exact-match 2>/dev/null || true)"
fi
if [ -z "$TAG" ]; then
  echo "check-tag: no tag given and HEAD is not tagged; nothing to compare"
  exit 0
fi

VERSION="$("$PY" -c 'import webscour; print(webscour.__version__)')"
if [ "$TAG" != "v$VERSION" ]; then
  echo "check-tag: tag $TAG does not match __version__ $VERSION (expected v$VERSION)" >&2
  exit 1
fi
echo "check-tag: $TAG == webscour.__version__ $VERSION"
