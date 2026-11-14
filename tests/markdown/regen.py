"""Regenerate one fixture pair (or all) from the captured HTML.

    python3 tests/markdown/regen.py 01-npm-docs
    python3 tests/markdown/regen.py --all

The expected file is the specification, so this script is a convenience for the case where the
renderer changed on purpose. Look at `git diff -- tests/fixtures/markdown/` before committing the
result: every line it writes is a line the test will now demand.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tests.markdown.test_conformance import BASES, FIXTURES  # noqa: E402
from webscour.extract import html_to_markdown  # noqa: E402


def regenerate(name):
    html_path = os.path.join(FIXTURES, name + ".html")
    if not os.path.exists(html_path):
        raise SystemExit("no capture at %s" % html_path)
    with open(html_path, encoding="utf-8") as fh:
        html = fh.read()
    markdown = html_to_markdown(html, base=BASES[name])
    with open(os.path.join(FIXTURES, name + ".md"), "w", encoding="utf-8") as fh:
        fh.write(markdown)
    print("%-20s %8d bytes" % (name, len(markdown)))


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    names = sorted(BASES) if argv[0] == "--all" else argv
    for name in names:
        if name not in BASES:
            raise SystemExit("unknown fixture %r (known: %s)" % (name, ", ".join(sorted(BASES))))
        regenerate(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
