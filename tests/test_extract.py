"""Offline tests for the byte-to-text layer: no network, no SearXNG, no render backend."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webscour.extract import (
    JS_SHELL_MIN,
    document_backend,
    document_format,
    filter_links,
    html_to_text,
    js_shell_reason,
    looks_like_pdf,
    parse_llms_txt,
    parse_robots_sitemaps,
    parse_sitemap,
    same_origin,
)

PAGE = """<html><head><title>Quickstart</title><style>body{color:#000}</style></head>
<body><nav>home | docs | blog</nav>
<h1>DeepStream quickstart</h1>
<p>Works on Xavier NX and Orin.</p>
<script>var x = 1;</script>
<p>Second paragraph, with   extra    spaces.</p>
<footer>copyright</footer></body></html>"""

SHORT_COMPLETE = """<html><head><title>Example Domain</title></head><body><div>
<h1>Example Domain</h1>
<p>This domain is for use in documentation examples without needing permission.
Avoid use in operations.</p>
</div></body></html>"""

APP_SHELL = """<html><head><title>App</title></head><body><div id="root"></div>
<noscript>You need to enable JavaScript to run this app. This application requires a modern
browser and JavaScript turned on before any of its content can be displayed at all.</noscript>
<script>window.__NEXT_DATA__={};</script></body></html>"""

MARKER_ONLY = (
    "<html><body><div id=__next></div>"
    '<script id="__NEXT_DATA__" type="application/json">{}</script></body></html>'
)

SOLID = (
    "<html><body><article><h1>Async</h1><p>"
    + "real content for the reader " * 40
    + "</p></article></body></html>"
)

PDF_BODY = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n"
    b"2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n"
    b"3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>\nendobj\n"
    b"4 0 obj\n<</Length 42>>stream\nBT /F1 12 Tf 20 100 Td (Hello web) Tj ET\nendstream\nendobj\n"
    b"5 0 obj\n<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>\nendobj\n"
    b"trailer\n<</Size 6/Root 1 0 R>>\n%%EOF\n"
)

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://example.com/a?x=1&amp;y=2</loc></url>
<url><loc>https://example.com/b</loc></url>
<url><loc>not-a-url</loc></url>
</urlset>"""

ROBOTS = """User-agent: *
Disallow: /admin
Sitemap: https://example.com/sitemap.xml
sitemap: https://example.com/second.xml
"""

LLMS = """# Example
- [Docs](https://example.com/docs)
- [Api](https://example.com/api)
https://example.com/bare
"""

LINKS_PAGE = """<html><head><title>Seed page</title></head><body><h1>Seed</h1>
<a href="/inner">inner</a>
<a href="https://example.com/inner">inner duplicate</a>
<a href="https://other.example/x">other origin</a>
<a href="/logo.png">image</a>
<a href="#frag">fragment</a>
<a href="mailto:a@b.c">mail</a>
</body></html>"""

# A repository-shaped page: a file tree and a breadcrumb around a README that carries a code
# fence. The whole point of the pruning rules is to keep the second half and drop the first.
REPO_PAGE = """<html><head><title>simonw/llm</title></head><body>
<div class="file-tree"><ul>
<li><a href="/a">.github</a></li><li><a href="/b">docs</a></li>
<li><a href="/c">llm</a></li><li><a href="/d">tests</a></li>
<li><a href="/e">.gitignore</a></li><li><a href="/f">AGENTS.md</a></li>
<li><a href="/g">Justfile</a></li><li><a href="/h">LICENSE</a></li>
</ul></div>
<div class="breadcrumbs"><a href="/x">simonw</a> / <a href="/y">llm</a></div>
<div class="star-bar"><a href="/stars">1,354</a> <a href="/forks">112</a> <a href="/watch">88</a></div>
<article><h1>LLM</h1>
<p>A CLI tool for running prompts against large language models from the command line,
with plugins, embeddings and a SQLite log of every response you have ever received.</p>
<h2>Installation</h2>
<pre><code>pip install llm
llm "ten names for a pet pelican"</code></pre>
<p>Then run <code>llm --help</code> for the full command surface.</p>
</article>
<footer><a href="/terms">Terms</a> <a href="/privacy">Privacy</a></footer>
</body></html>"""

COOKIE_PAGE = """<html><head><title>Article</title></head><body>
<div id="onetrust-consent-sdk"><p>We value your privacy and 400 partners store cookies.</p></div>
<div class="cookie-banner"><p>Accept all cookies to continue reading this publication.</p></div>
<div class="newsletter-signup"><p>Get the weekly digest in your inbox every Thursday morning.</p></div>
<article><p>The article body is the only part of this page a reader came for, and it survives.</p>
</article></body></html>"""

# A page that is ABOUT cookies. The bare substrings must not fire: trafilatura measured up to
# 97% of a WordPress page lost that way, which is why the vocabulary is anchored compounds.
COOKIE_TOPIC = """<html><head><title>Cookie policy</title></head><body>
<article><h1>Cookies</h1><p class="cookies-not-set">A cookie is a small text file that a site
stores in your browser. The consent notice you saw is one example of its use.</p></article>
</body></html>"""

PRE_PAGE = """<html><body><p>Install it:</p>
<pre>def f(x):
    if x:
        return  'two  spaces  kept'

    return None</pre>
<p>That is all.</p></body></html>"""


class HtmlToTextTest(unittest.TestCase):
    def test_keeps_prose_and_drops_chrome_and_script(self):
        text = html_to_text(PAGE)
        self.assertIn("Xavier NX and Orin.", text)
        self.assertNotIn("home | docs", text, "nav must be dropped")
        self.assertNotIn("copyright", text, "footer must be dropped")
        self.assertNotIn("var x", text, "script must be dropped")
        self.assertNotIn("color:#000", text, "style must be dropped")

    def test_whitespace_is_collapsed_per_line(self):
        text = html_to_text(PAGE)
        self.assertIn("Second paragraph, with extra spaces.", text)
        self.assertNotIn("   ", text)

    def test_blocks_become_separate_lines(self):
        lines = html_to_text(PAGE).splitlines()
        self.assertIn("DeepStream quickstart", lines)
        self.assertIn("Works on Xavier NX and Orin.", lines)


class JsShellTest(unittest.TestCase):
    def test_short_complete_page_is_not_hollow(self):
        text = html_to_text(SHORT_COMPLETE)
        self.assertLess(
            len(" ".join(text.split())),
            JS_SHELL_MIN,
            "the fixture must stay below the length threshold to be a regression test",
        )
        self.assertEqual(
            js_shell_reason(SHORT_COMPLETE, text),
            "",
            "a complete short page must not cost a browser launch",
        )

    def test_app_shell_is_hollow(self):
        self.assertTrue(js_shell_reason(APP_SHELL, html_to_text(APP_SHELL)))
        self.assertIn("enable javascript", js_shell_reason(APP_SHELL, html_to_text(APP_SHELL)))

    def test_framework_marker_beats_length(self):
        self.assertIn("__next_data__", js_shell_reason(MARKER_ONLY, html_to_text(MARKER_ONLY)))

    def test_long_solid_page_is_not_hollow(self):
        self.assertEqual(js_shell_reason(SOLID, html_to_text(SOLID)), "")

    def test_empty_body_is_hollow_by_length(self):
        empty = '<html><body><div id="root"></div></body></html>'
        self.assertIn("chars of text", js_shell_reason(empty, html_to_text(empty)))


class NoNetworkTest(unittest.TestCase):
    """The module boundary is a promise: extract.py must import with no network module at all."""

    def test_extract_imports_with_socket_blocked(self):
        import subprocess

        code = (
            "import sys\n"
            "class Block:\n"
            "    def find_module(self, name, path=None):\n"
            "        if name.split('.')[0] in ('socket', 'ssl', 'http'):\n"
            "            return self\n"
            "    def load_module(self, name):\n"
            "        raise ImportError('network module blocked: ' + name)\n"
            "sys.meta_path.insert(0, Block())\n"
            "import webscour.extract\n"
            "print('ok')\n"
        )
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=root)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        self.assertIn("ok", out.stdout)


class DocumentRoutingTest(unittest.TestCase):
    def test_content_type_wins_over_missing_name(self):
        self.assertEqual(document_format("application/pdf", ""), "pdf")
        self.assertEqual(document_format("application/pdf; charset=binary", "page"), "pdf")

    def test_name_used_when_content_type_is_generic(self):
        self.assertEqual(document_format("", "https://example.com/paper.pdf?x=1"), "pdf")
        self.assertEqual(
            document_format("text/html", "whatever.pdf"),
            "html",
            "an explicit text/html is an HTML page, not a document to extract",
        )

    def test_extension_is_not_a_document(self):
        self.assertEqual(document_format("", "https://example.com/notes.txt"), "")

    def test_pdf_magic_bytes_are_enough(self):
        self.assertTrue(looks_like_pdf(PDF_BODY, "application/octet-stream"))
        self.assertTrue(looks_like_pdf(b"", "application/pdf"))
        self.assertFalse(looks_like_pdf(b"<html>", "text/html"))

    def test_backend_choice_is_pure_and_format_aware(self):
        have = {"pdftotext": "/usr/bin/pdftotext", "pandoc": "/usr/bin/pandoc", "markitdown": ""}
        self.assertEqual(document_backend("pdf", have), "pdftotext")
        self.assertEqual(
            document_backend("docx", have),
            "pandoc",
            "pandoc cannot read a PDF, so it is never the PDF choice",
        )
        self.assertEqual(document_backend("pdf", {}), "")

    def test_pdf_body_routes_to_the_pdf_backend(self):
        """No network: the body is bytes, and the router decides before any download exists."""
        self.assertEqual(document_format("application/pdf", "download"), "pdf")
        self.assertTrue(looks_like_pdf(PDF_BODY, "application/pdf"))
        self.assertEqual(document_backend("pdf", {"pdftotext": "/usr/bin/pdftotext"}), "pdftotext")


class SiteWalkTest(unittest.TestCase):
    def test_filter_links_keeps_one_origin_by_default(self):
        from webscour.extract import page_links

        kept = filter_links(
            page_links(LINKS_PAGE, "https://example.com/seed"), "https://example.com/seed"
        )
        self.assertEqual(
            kept,
            ["https://example.com/inner"],
            "the duplicate, the other origin, the image, the fragment and the mailto all go",
        )

    def test_any_origin_is_opt_in(self):
        from webscour.extract import page_links

        kept = filter_links(
            page_links(LINKS_PAGE, "https://example.com/seed"),
            "https://example.com/seed",
            origin_lock=False,
        )
        self.assertIn("https://other.example/x", kept)

    def test_origin_is_scheme_plus_host_plus_port(self):
        self.assertTrue(same_origin("https://example.com/a", "https://example.com"))
        self.assertFalse(same_origin("http://example.com/a", "https://example.com"))
        self.assertFalse(same_origin("https://example.com:8443/a", "https://example.com"))

    def test_sitemap_parsing_unescapes_and_skips_junk(self):
        urls, is_index = parse_sitemap(SITEMAP)
        self.assertFalse(is_index)
        self.assertEqual(urls, ["https://example.com/a?x=1&y=2", "https://example.com/b"])

    def test_robots_and_llms_txt_sources(self):
        self.assertEqual(
            parse_robots_sitemaps(ROBOTS),
            ["https://example.com/sitemap.xml", "https://example.com/second.xml"],
        )
        self.assertEqual(
            parse_llms_txt(LLMS),
            ["https://example.com/docs", "https://example.com/api", "https://example.com/bare"],
        )


if __name__ == "__main__":
    unittest.main()


class LinkDensityTest(unittest.TestCase):
    """Container pruning: navigation is dropped, the README next to it is kept."""

    def test_repository_chrome_is_dropped_and_readme_kept(self):
        text = html_to_text(REPO_PAGE)
        self.assertIn("A CLI tool for running prompts", text, text)
        self.assertIn("pip install llm", text, text)
        self.assertNotIn(".gitignore", text, "a file tree is navigation, not content")
        self.assertNotIn("simonw / llm", text, "breadcrumbs are navigation")
        self.assertNotIn("1,354", text, "star and fork counters are chrome")
        self.assertNotIn("Privacy", text, "the footer links are chrome")

    def test_a_dense_section_does_not_take_its_neighbour_with_it(self):
        # The README sits inside <article>; the tree above it must go and nothing else.
        lines = html_to_text(REPO_PAGE).splitlines()
        self.assertEqual(lines[0], "LLM", lines[:3])
        self.assertIn("Installation", lines)


class CookieBannerTest(unittest.TestCase):
    def test_vendor_banner_is_dropped_by_class(self):
        text = html_to_text(COOKIE_PAGE)
        self.assertIn("The article body is the only part", text)
        self.assertNotIn("We value your privacy", text, "OneTrust is in the vendor list")
        self.assertNotIn("Accept all cookies", text, "cookie-banner is an anchored compound")

    def test_a_page_about_cookies_is_not_a_cookie_banner(self):
        # The bare substrings `cookie`/`consent` are what trafilatura measured losing 97% of a
        # page on; the vocabulary here is compounds only, so topical classes survive.
        text = html_to_text(COOKIE_TOPIC)
        self.assertIn("A cookie is a small text file", text, text)
        self.assertIn("consent notice", text)


class PreTest(unittest.TestCase):
    def test_code_block_is_byte_exact(self):
        text = html_to_text(PRE_PAGE)
        self.assertIn(
            "        return  'two  spaces  kept'",
            text,
            "indentation and the double space inside the string are the code",
        )
        self.assertIn("\n\n    return None", text, "the blank line inside the block is code too")
        self.assertNotIn(
            "return 'two spaces kept'", text, "whitespace inside <pre> is never collapsed"
        )

    def test_a_container_holding_code_is_never_pruned(self):
        # An <article> of one word plus a code fence is mostly link text in some themes; the
        # fence is the reason the page exists.
        page = '<html><body><div><a href="/x">back</a><pre>make test</pre></div></body></html>'
        self.assertIn("make test", html_to_text(page))


class TableIsContentTest(unittest.TestCase):
    """A table of links can be the page. This is the regression the rules were tuned against.

    An earlier pass pruned every table whose text was mostly link text. On Hacker News the whole
    front page is one such table, so the extractor returned nothing at all: the page's content
    *is* a list of links, and a rule copied from article extraction cannot tell the two apart.
    """

    PAGE = """<html><body><table>
<tr><td><a href="/s1">Lovable apps expose passport details and 200K private messages</a>
<td><a href="/s2">A Family Tree of Software Job Titles</a>
<tr><td><a href="/s3">A look at the new Go 1.26 features</a>
<td><a href="/s4">Show HN: DeepSeek V3 in 200 lines of pure lisp</a>
</table></body></html>"""

    def test_a_page_that_is_a_table_of_links_keeps_its_links(self):
        text = html_to_text(self.PAGE)
        self.assertIn("Lovable apps expose passport details", text)
        self.assertIn("A Family Tree of Software Job Titles", text)
        self.assertIn("Show HN: DeepSeek", text)
