#!/bin/sh
# sift.sh - save a page once, then show only the lines that matter.
#
#   sift.sh <url> <pattern> [max-lines]
#
# Fetches the URL with `wsc fetch --save-only` (the page lands in ./.webscour/), then prints the
# saved path and the first max-lines lines matching pattern, with line numbers. Default max-lines
# is 20. The point is that a 45 KB page costs a few hundred bytes of context to inspect.
#
# pattern is an extended regular expression (grep -E), case-sensitive.
# Exit: 0 matches printed, 1 fetched but no match, 2 usage or the fetch failed.

set -u

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "usage: sift.sh <url> <pattern> [max-lines]" >&2
    exit 2
fi

url=$1
pattern=$2
max=${3:-20}

case $max in
    ''|*[!0-9]*) echo "sift: max-lines must be a number, got '$max'" >&2; exit 2 ;;
esac
if [ "$max" -lt 1 ]; then
    echo "sift: max-lines must be at least 1" >&2
    exit 2
fi

# Resolve the CLI: PATH first, then an importable source checkout.
wsc_run() {
    if command -v wsc >/dev/null 2>&1; then
        wsc "$@"
    elif python3 -c 'import webscour.cli' >/dev/null 2>&1; then
        python3 -m webscour.cli "$@"
    else
        return 127
    fi
}

if ! wsc_run --version >/dev/null 2>&1; then
    echo "sift: the webscour CLI was not found here (no executable, no package)" >&2
    echo "sift: run from the webscour checkout, or install it (pipx install webscour)" >&2
    exit 2
fi

saved=$(wsc_run fetch "$url" --save-only 2>/dev/null) || {
    echo "sift: fetch failed for $url (run 'wsc fetch $url -v' to see why)" >&2
    exit 2
}

path=$(printf '%s\n' "$saved" | sed -n '1p' | awk '{print $1}')
if [ -z "$path" ] || [ ! -f "$path" ]; then
    echo "sift: no file was written (got: $saved)" >&2
    exit 2
fi

total=$(wc -l <"$path" | tr -d ' ')
hits=$(grep -c -E -- "$pattern" "$path" 2>/dev/null)
rc=$?
if [ "$rc" -gt 1 ]; then
    echo "sift: '$pattern' is not a valid extended regex (grep -E)" >&2
    exit 2
fi
hits=${hits:-0}

printf '%s\n' "$path"
printf '%s\n' "$total lines, $hits match(es) for /$pattern/"

if [ "$hits" -eq 0 ]; then
    echo "sift: no line matches, the page was still saved; try a broader pattern" >&2
    exit 1
fi

grep -n -E -m "$max" -- "$pattern" "$path"
if [ "$hits" -gt "$max" ]; then
    printf '%s\n' "... $((hits - max)) more match(es) not shown (raise max-lines, or grep the file)"
fi
