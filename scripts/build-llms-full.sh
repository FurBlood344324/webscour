#!/usr/bin/env bash
# Rebuild llms-full.txt from docs/. The header ends at the `<!-- pages -->` marker and everything
# after it is generated, so a rerun is byte-identical unless a page changed.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
tmp="$(mktemp)"
sed -n '1,/^<!-- pages -->$/p' llms-full.txt > "$tmp"
for p in index quickstart verbs sources privacy self-hosting contributing; do
  printf '\n---\n\n# docs/%s.md\n\n' "$p" >> "$tmp"
  cat "docs/$p.md" >> "$tmp"
done
mv "$tmp" llms-full.txt
echo "llms-full.txt rebuilt"
