"""Markdown conformance: ten captured pages, one expected file each, compared byte for byte.

The fixtures are real captures and the expected markdown was read and corrected by hand: a test
that asserts whatever the code happened to print proves nothing. What each pair pins down:

    01-npm-docs        deep nested lists, Shiki `token-line` fences, angle brackets in prose
    02-mdn-fetch       fences with a language, inline code inside links, note blocks
    03-github-readme   badges (an image inside a link), tables, fenced examples
    04-arxiv-abs       headings, math left as text, a citation block
    05-stackoverflow   code blocks plus lists, the shape the API route returns
    06-vercel-docs     an SPA-shaped page that is server-rendered: nested nav must not win
    07-react-docs      nested headings, inline code in list items, em and strong
    08-wikipedia       references, nested lists, citation superscripts
    09-hackernews      a layout table (no header row), a flat comment tree
    10-discourse       a quoted block, a fence with a language, a nested thread

Regenerate with `python3 tests/markdown/regen.py <name>` after reading the diff: the expected file
is the specification, so changing it is a decision, not a refresh.

The captures live in `tests/fixtures/markdown/` rather than beside this file because the gate's
text-hygiene check exempts `tests/fixtures/` and scans everything else: a captured page contains
em dashes and emoji because the page contained them, and rewriting them to satisfy a style rule
about our own prose would corrupt the evidence.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIXTURES = os.path.join(ROOT, "tests", "fixtures", "markdown")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from webscour.extract import html_to_markdown  # noqa: E402

# The URL each capture came from, so relative links resolve the way they did on the site.
BASES = {
    "01-npm-docs": "https://docs.npmjs.com/cli/v10/commands/npm-install",
    "02-mdn-fetch": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch",
    "03-github-readme": "https://github.com/sindresorhus/got",
    "04-arxiv-abs": "https://arxiv.org/abs/1706.03762",
    "05-stackoverflow": "https://stackoverflow.com/questions/11227809",
    "06-vercel-docs": "https://vercel.com/docs/frameworks",
    "07-react-docs": "https://react.dev/learn/state-a-components-memory",
    "08-wikipedia": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
    "09-hackernews": "https://news.ycombinator.com/item?id=1",
    "10-discourse": "https://discourse.jupyter.org/t/39125",
}


def cases():
    """[(name, html, expected, base)] for every pair present on disk."""
    out = []
    for name in sorted(BASES):
        html_path = os.path.join(FIXTURES, name + ".html")
        md_path = os.path.join(FIXTURES, name + ".md")
        if not (os.path.exists(html_path) and os.path.exists(md_path)):
            continue
        with open(html_path, encoding="utf-8") as fh:
            html = fh.read()
        with open(md_path, encoding="utf-8") as fh:
            expected = fh.read()
        out.append((name, html, expected, BASES[name]))
    return out


def _first_diff(got, want):
    a, b = got.splitlines(), want.splitlines()
    for i in range(max(len(a), len(b))):
        left = a[i] if i < len(a) else "<end>"
        right = b[i] if i < len(b) else "<end>"
        if left != right:
            return i + 1, left, right
    return 0, "", ""


class ConformanceTest(unittest.TestCase):
    def test_ten_fixtures_exist(self):
        self.assertEqual(len(cases()), 10, "the suite is ten pairs; a missing pair is a gap")

    def test_every_pair_is_byte_equal(self):
        for name, html, expected, base in cases():
            with self.subTest(fixture=name):
                got = html_to_markdown(html, base=base)
                if got != expected:
                    line, left, right = _first_diff(got, expected)
                    self.fail(
                        "%s: markdown differs at line %d\n  got: %r\n  want: %r\n"
                        "read the diff, then regenerate with tests/markdown/regen.py %s"
                        % (name, line, left, right, name)
                    )

    def test_every_expected_file_ends_with_one_newline(self):
        for name, _html, expected, _base in cases():
            with self.subTest(fixture=name):
                self.assertTrue(expected.endswith("\n"), "%s must end with one newline" % name)
                self.assertFalse(expected.endswith("\n\n"), "%s ends with a blank line" % name)

    def test_no_expected_file_has_a_run_of_blank_lines(self):
        for name, _html, expected, _base in cases():
            with self.subTest(fixture=name):
                self.assertNotIn("\n\n\n", expected, "%s has a run of blank lines" % name)

    def test_fences_are_balanced(self):
        for name, _html, expected, _base in cases():
            with self.subTest(fixture=name):
                fences = [ln for ln in expected.splitlines() if ln.startswith("```")]
                self.assertEqual(len(fences) % 2, 0, "%s has an unclosed fence" % name)


if __name__ == "__main__":
    unittest.main()
