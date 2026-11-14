#!/bin/sh
# page-sections.sh - the heading map of a saved markdown file.
#
#   page-sections.sh <file>
#
# Prints one line per ATX heading (`#` to `######` at the start of a line) as
#   <line>  <indent><heading text>
# so the next step can be `sed -n '<line>,<next-line>p' <file>` instead of reading the whole file.
# A heading inside a fenced code block (``` or ~~~) is not a heading and is skipped, which matters
# for a saved documentation page: its examples are full of `# comment` lines.
#
# This expects MARKDOWN. A plain-text capture (the default `--format text`) has no fences, so a
# Python comment or a shell line that starts with `#` is reported as a heading. Fetch with
# `--format markdown` before using this.
#
# Exit: 0 printed at least one heading, 1 none found, 2 usage or unreadable file.

set -u

if [ "$#" -ne 1 ]; then
    echo "usage: page-sections.sh <file>" >&2
    exit 2
fi

file=$1
if [ ! -f "$file" ]; then
    echo "page-sections: no such file: $file" >&2
    exit 2
fi
if [ ! -r "$file" ]; then
    echo "page-sections: not readable: $file" >&2
    exit 2
fi

awk '
    BEGIN { fence = 0; found = 0 }
    {
        line = $0
        # a fence line toggles and is never a heading
        if (line ~ /^[ ]{0,3}(```|~~~)/) { fence = !fence; next }
        if (fence) next
        if (line ~ /^[ ]{0,3}#{1,6}[ ]/) {
            if (!found) { print "# line  heading"; found = 1 }
            rest = line
            sub(/^[ ]{0,3}/, "", rest)          # drop the allowed indent
            level = 0
            while (substr(rest, level + 1, 1) == "#") level++   # the 1 to 6 hashes
            pad = ""
            for (i = 1; i < level; i++) pad = pad "  "
            printf "%6d  %s%s\n", FNR, pad, rest
        }
    }
    END { if (!found) exit 1 }
' "$file"

rc=$?
if [ "$rc" -eq 1 ]; then
    echo "page-sections: no markdown headings in $file" >&2
    echo "page-sections: a plain-text capture has none; refetch with --format markdown" >&2
    exit 1
fi
exit "$rc"
