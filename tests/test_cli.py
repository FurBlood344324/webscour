"""Offline tests for the argv surface: exit codes, and where the diagnostics go.

Every test here runs with no network. The two fetch tests inject a fake `http_raw`/`render_page`
so the output discipline (silent default, one line for a real fallback) is measured rather than
read from the source.
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webscour import backends, cli

SHORT_COMPLETE = """<html><head><title>Example Domain</title></head><body><div>
<h1>Example Domain</h1>
<p>This domain is for use in documentation examples without needing permission.
Avoid use in operations.</p>
</div></body></html>"""

SHELL_PAGE = """<html><head><title>App</title></head><body><div id="root"><p>Loading...</p></div>
<noscript>You need to enable JavaScript to run this app, and this page has nothing else in it
to read at all, which is exactly what the shell heuristic is looking for. This apology is the
whole document: every other element is empty until the bundle runs.</noscript>
<script>window.__NEXT_DATA__={};</script></body></html>"""


def run(argv):
    """Run main() and return (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


class ExitCodeTest(unittest.TestCase):
    def test_unknown_verb_returns_2(self):
        rc, out, err = run(["frobnicate"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown command", err)
        self.assertIn("wsc search", out, "the usage text is the help a wrong verb deserves")

    def test_no_argv_returns_1_and_prints_usage(self):
        rc, out, _ = run([])
        self.assertEqual(rc, 1)
        self.assertIn("wsc", out)

    def test_help_returns_0(self):
        rc, out, _ = run(["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("wsc fetch", out)

    def test_version(self):
        rc, out, _ = run(["--version"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("webscour "))

    def test_unknown_source_returns_2(self):
        rc, _, err = run(["search", "x", "--source", "altavista"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown --source", err)

    def test_every_verb_is_registered(self):
        for verb in ("search", "fetch", "pdf", "map", "crawl", "doctor", "setup", "probe"):
            self.assertIn(verb, cli.VERBS)


class FetchOutputDisciplineTest(unittest.TestCase):
    """Default stderr is empty. A fallback earns exactly one `render: <engine>` line."""

    def setUp(self):
        # The cache is on by default, and a page this class fetches is also a URL a previous test
        # may have saved. An isolated cwd keeps these tests about output, not about the cache.
        self._cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="webscour-cli-")
        os.chdir(self._tmp)
        self._http_raw = backends.http_raw
        self._render_page = backends.render_page
        self._saved_modules = (cli.http_raw, cli.render_page)

    def tearDown(self):
        backends.http_raw = self._http_raw
        backends.render_page = self._render_page
        cli.http_raw, cli.render_page = self._saved_modules
        os.chdir(self._cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _patch(self, body, render):
        class Headers(dict):
            def get_content_type(self):
                return "text/html"

            def get_content_charset(self):
                return "utf-8"

        backends.http_raw = lambda *a, **k: (body.encode(), "text/html", Headers(), "utf-8")
        backends.render_page = render
        cli.http_raw = backends.http_raw
        cli.render_page = backends.render_page

    def test_complete_short_page_prints_nothing_on_stderr(self):
        calls = []

        def render(*a, **k):
            calls.append(a)
            return "should not be used", "lightpanda"

        self._patch(SHORT_COMPLETE, render)
        rc, out, err = run(["fetch", "https://example.com"])
        self.assertEqual(rc, 0)
        self.assertIn("Example Domain", out)
        self.assertEqual(err, "", "a complete page must leave stderr empty")
        self.assertEqual(calls, [], "a complete page must not launch a browser")

    def test_hollow_page_prints_exactly_one_render_line(self):
        self._patch(SHELL_PAGE, lambda *a, **k: ("rendered body text", "lightpanda"))
        rc, out, err = run(["fetch", "https://app.example.com"])
        self.assertEqual(rc, 0)
        self.assertIn("rendered body text", out)
        self.assertEqual(err, "render: lightpanda\n")

    def test_verbose_explains_the_same_run(self):
        self._patch(SHELL_PAGE, lambda *a, **k: ("rendered body text", "lightpanda"))
        rc, _, err = run(["fetch", "https://app.example.com", "-v"])
        self.assertEqual(rc, 0)
        lines = err.strip().splitlines()
        self.assertGreater(len(lines), 2, "verbose must say why the browser was opened")
        self.assertTrue(any("looked hollow" in ln for ln in lines))
        self.assertEqual(lines[-1], "render: lightpanda")

    def test_explicit_render_reports_the_engine_even_for_a_plain_page(self):
        self._patch(
            SHORT_COMPLETE, lambda *a, **k: ("forced render text", "playwright (render-venv)")
        )
        rc, out, err = run(["fetch", "https://example.com", "--render"])
        self.assertEqual(rc, 0)
        self.assertIn("forced render text", out)
        self.assertEqual(err, "render: playwright\n")

    def test_failed_render_falls_back_to_plain_text_with_a_reason(self):
        def render(*a, **k):
            raise backends.FetchError("no render backend worked: lightpanda not on PATH")

        self._patch(SHELL_PAGE, render)
        rc, _, err = run(["fetch", "https://app.example.com"])
        self.assertEqual(rc, 0)
        self.assertIn("no render backend answered", err)

    def test_pdf_url_routes_to_the_document_backend_and_stays_silent(self):
        class Headers(dict):
            def get_content_type(self):
                return "application/pdf"

            def get_content_charset(self):
                return "utf-8"

        backends.http_raw = lambda *a, **k: (b"%PDF-1.4\n", "application/pdf", Headers(), "utf-8")
        cli.http_raw = backends.http_raw
        extracted = []

        def fake_extract(raw, fmt, path, have=None, markdown=False):
            extracted.append(fmt)
            return "line one\nline two", "pdftotext"

        saved = cli.extract_document
        cli.extract_document = fake_extract
        try:
            rc, out, err = run(["fetch", "https://example.com/paper.pdf"])
        finally:
            cli.extract_document = saved
        self.assertEqual(rc, 0)
        self.assertEqual(extracted, ["pdf"], "the content type must pick the pdf branch")
        self.assertIn("line two", out)
        self.assertEqual(err, "", "asking for a pdf is not news the caller needs on stderr")

    def test_pdf_verb_names_the_backend_under_verbose(self):
        saved = cli.searx_bundle
        calls = []

        class FakeBundle:
            @staticmethod
            def install(argv):
                calls.append(list(argv))
                return 0

            @staticmethod
            def lightpanda_path():
                return "/usr/bin/lightpanda"

        cli.searx_bundle = FakeBundle
        try:
            rc, out, err = run(["setup", "--check"])
        finally:
            cli.searx_bundle = saved
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [["--check"]], "setup must pass its flags through to install.sh")
        self.assertIn("lightpanda", out)
        self.assertEqual(err, "")

    def test_setup_fails_when_lightpanda_is_missing(self):
        saved = cli.searx_bundle

        class FakeBundle:
            @staticmethod
            def install(argv):
                return 0

            @staticmethod
            def lightpanda_path():
                return ""

        cli.searx_bundle = FakeBundle
        try:
            rc, out, err = run(["setup"])
        finally:
            cli.searx_bundle = saved
        self.assertEqual(
            rc, 1, "lightpanda is required, so setup must not report success without it"
        )
        self.assertIn("requires it", err)
        self.assertIn("yay -S lightpanda-bin", out, "the hint must name the real install route")

    def test_pdf_verbose_names_the_backend(self):
        saved = cli._document_lines

        def fake_lines(url, raw=None, ctype=None, markdown=False):
            backends.vwarn("extract: pdf -> pdftotext")
            return ["line one"], "path"

        cli._document_lines = fake_lines
        try:
            rc, _out, err = run(["fetch", "https://example.com/paper.pdf", "-v"])
        finally:
            cli._document_lines = saved
        self.assertEqual(rc, 0)
        self.assertEqual(err, "extract: pdf -> pdftotext\n")


class VerbosePassthroughTest(unittest.TestCase):
    """A nested command parses its own argv: a verbose crawl must stay verbose after its seeds."""

    def test_map_seed_urls_restores_the_verbose_flag(self):
        saved_map, saved_flag = cli.cmd_map, backends.VERBOSE
        argv_seen = []

        def fake_map(argv):
            argv_seen.append(list(argv))
            cli.set_verbose("-v" in argv)
            print("https://example.com/a")
            return 0

        cli.cmd_map = fake_map
        try:
            cli.set_verbose(True)
            urls = cli.map_seed_urls("https://example.com", cap=5)
            self.assertEqual(urls, ["https://example.com/a"])
            self.assertIn("-v", argv_seen[0], "verbose must be passed through to the nested map")
            self.assertTrue(backends.VERBOSE, "the flag must come back as it was")
        finally:
            cli.cmd_map = saved_map
            cli.set_verbose(saved_flag)


class DoctorTest(unittest.TestCase):
    """The render rows have two different weights, and doctor says so."""

    def test_render_rows_distinguish_required_from_fallback(self):
        rows = cli.backend_table()
        names = [name for name, _, _ in rows]
        self.assertEqual(
            names[:2],
            ["lightpanda", "playwright"],
            "lightpanda is the engine under test first, playwright is the fallback",
        )

    def test_missing_lightpanda_makes_doctor_degrade(self):
        saved = cli.shutil.which

        def which(name, *a, **k):
            return "" if name == "lightpanda" else saved(name, *a, **k)

        cli.shutil.which = which
        try:
            report = {}
            with contextlib.redirect_stdout(io.StringIO()):
                ok = cli._print_backends(report)
        finally:
            cli.shutil.which = saved
        self.assertFalse(ok)
        self.assertIn("lightpanda", report["backends"])
        self.assertFalse(report["backends"]["lightpanda"]["ok"])


if __name__ == "__main__":
    unittest.main()


class RenderVenvTest(unittest.TestCase):
    """The fallback's resolution order, without installing anything.

    The bug this class exists for: the old `playwright_python()` globbed
    `~/.pyenv/versions/*/bin/python3`, so the shipped tool worked by borrowing a scratch
    environment on one machine. Every assertion below is about *not* doing that.
    """

    def setUp(self):
        from webscour import render_venv

        self.rv = render_venv
        self.saved_env = {
            k: os.environ.get(k) for k in (render_venv.ENV_VAR, render_venv.DEPRECATED_ENV_VAR)
        }
        for key in self.saved_env:
            os.environ.pop(key, None)
        self.saved_python = render_venv._imports_playwright

    def tearDown(self):
        for key, value in self.saved_env.items():
            os.environ.pop(key, None)
            if value is not None:
                os.environ[key] = value
        self.rv._imports_playwright = self.saved_python

    def test_candidates_never_leave_the_documented_set(self):
        root = "/tmp/wsc-render-venv-test"
        names = self.rv.candidates(root)
        self.assertIn(os.path.join(root, "bin", "python"), names)
        self.assertIn(sys.executable, names)
        # `sys.executable` may itself live under an environment manager, and that is fine: it is
        # the interpreter the caller chose by running us. What must never happen is a *search* for
        # one, so every candidate is one of the four documented sources, in order.
        expected = {
            os.path.join(root, "bin", "python"),
            sys.executable,
            shutil.which("python3") or "",
        }
        for path in names:
            self.assertIn(
                path, expected, "candidate %r is not one of the documented sources" % path
            )
        self.assertEqual(names[0], os.path.join(root, "bin", "python"))

    def test_env_var_wins_and_is_first(self):
        os.environ[self.rv.ENV_VAR] = "/opt/playwright/bin/python"
        names = self.rv.candidates("/tmp/x")
        self.assertEqual(names[0], "/opt/playwright/bin/python")

    def test_deprecated_env_var_still_works_and_says_so_once(self):
        os.environ[self.rv.DEPRECATED_ENV_VAR] = "/opt/old/bin/python"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            names = self.rv.candidates("/tmp/x")
            self.assertIn("/opt/old/bin/python", names)
            self.rv.candidates("/tmp/x")
        note = err.getvalue()
        self.assertEqual(note.count("deprecated"), 1, note)
        self.assertIn(self.rv.ENV_VAR, note)

    def test_find_returns_the_first_interpreter_that_imports_playwright(self):
        seen = []

        def fake(python):
            seen.append(python)
            return python.endswith("good")

        self.rv._imports_playwright = fake
        os.environ[self.rv.ENV_VAR] = "/a/good"
        self.assertEqual(self.rv.find("/tmp/root"), "/a/good")

    def test_find_returns_empty_when_nothing_has_it(self):
        self.rv._imports_playwright = lambda python: False
        self.assertEqual(self.rv.find("/tmp/root"), "")

    def test_healthy_probes_the_venv_python_and_nothing_else(self):
        # A global install is not this venv's health: `healthy()` answers about the directory the
        # tool owns, and `find()` is the one that accepts a globally installed playwright.
        root = "/tmp/wsc/render-venv"
        probed = []

        def fake(python):
            probed.append(python)
            return python == self.rv.venv_python(root)

        self.rv._imports_playwright = fake
        self.assertTrue(self.rv.healthy(root))
        self.assertEqual(probed, [os.path.join(root, "bin", "python")])

    def test_status_names_the_one_command_that_fixes_it(self):
        self.rv._imports_playwright = lambda python: False
        state = self.rv.status("/tmp/does-not-exist")
        self.assertFalse(state["exists"])
        self.assertEqual(state["fix"], "wsc setup --playwright")

    def test_setup_against_a_healthy_venv_touches_nothing(self):
        calls = []
        self.rv._imports_playwright = lambda python: True
        self.rv._run = lambda cmd, timeout=0: calls.append(cmd) or (True, "")
        self.rv.drift = lambda root=None: ([], [], False)
        ok, lines = self.rv.setup("/tmp/root")
        self.assertTrue(ok)
        self.assertEqual(lines, ["ok render-venv"])
        self.assertEqual(calls, [], "a healthy venv must not be reinstalled")

    def test_browser_drift_is_reported_not_fatal(self):
        self.rv._imports_playwright = lambda python: True
        self.rv.drift = lambda root=None: (["1208"], ["1223"], False)
        ok, lines = self.rv.setup("/tmp/root")
        self.assertTrue(ok)
        self.assertTrue(any("drift" in line for line in lines), lines)
        self.assertEqual(lines[-1], "ok render-venv")


class SetupVerbTest(unittest.TestCase):
    """Bare `setup` is SearXNG; the fallback is a flag, never an implied install."""

    def test_bare_setup_does_not_touch_the_render_venv(self):
        from webscour import render_venv

        saved_bundle, saved_setup = cli.searx_bundle, render_venv.setup
        touched = []

        class FakeBundle:
            @staticmethod
            def install(argv):
                return 0

            @staticmethod
            def lightpanda_path():
                return "/usr/bin/lightpanda"

        cli.searx_bundle = FakeBundle
        render_venv.setup = lambda **kwargs: touched.append(kwargs) or (True, [])
        try:
            rc, out, _err = run(["setup"])
        finally:
            cli.searx_bundle = saved_bundle
            render_venv.setup = saved_setup
        self.assertEqual(rc, 0)
        self.assertEqual(touched, [], "bare setup must not install playwright")
        self.assertIn("lightpanda", out)

    def test_setup_playwright_skips_searxng(self):
        from webscour import render_venv

        saved_bundle, saved_setup = cli.searx_bundle, render_venv.setup
        called = []

        class FakeBundle:
            @staticmethod
            def install(argv):
                called.append(argv)
                return 0

            @staticmethod
            def lightpanda_path():
                return "/usr/bin/lightpanda"

        cli.searx_bundle = FakeBundle
        render_venv.setup = lambda **kwargs: (True, ["ok render-venv"])
        try:
            rc, out, _err = run(["setup", "--playwright"])
        finally:
            cli.searx_bundle = saved_bundle
            render_venv.setup = saved_setup
        self.assertEqual(rc, 0)
        self.assertEqual(called, [], "the two installs are separate verbs, not one")
        self.assertIn("ok render-venv", out)

    def test_setup_all_does_both(self):
        from webscour import render_venv

        saved_bundle, saved_setup = cli.searx_bundle, render_venv.setup
        called = []

        class FakeBundle:
            @staticmethod
            def install(argv):
                called.append(list(argv))
                return 0

            @staticmethod
            def lightpanda_path():
                return "/usr/bin/lightpanda"

        cli.searx_bundle = FakeBundle
        render_venv.setup = lambda **kwargs: (True, ["ok render-venv"])
        try:
            rc, _out, _err = run(["setup", "--all"])
        finally:
            cli.searx_bundle = saved_bundle
            render_venv.setup = saved_setup
        self.assertEqual(rc, 0)
        self.assertEqual(len(called), 1, "SearXNG install must run once")


class DoctorRenderVenvTest(unittest.TestCase):
    def test_doctor_reports_the_venv_and_still_degrades_on_missing_lightpanda(self):
        from webscour import render_venv

        saved_bundle, saved_venv = cli.searx_bundle, render_venv.status
        cli.searx_bundle = type("B", (), {"SEARX_BASE": "http://127.0.0.1:1"})()
        render_venv.status = lambda: {
            "path": "/tmp/absent/bin/python",
            "exists": False,
            "ok": False,
            "wanted": [],
            "present": [],
            "browser_ok": False,
            "fix": "wsc setup --playwright",
        }
        try:
            _rc, out, _err = run(["doctor"])
        finally:
            cli.searx_bundle = saved_bundle
            render_venv.status = saved_venv
        self.assertIn("render-venv", out)
        self.assertIn("wsc setup --playwright", out)
