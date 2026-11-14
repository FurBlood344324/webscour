"""The fetch pipeline's cache contract, driven through `main()` with the network stubbed.

`test_cache.py` proves the store. This proves the flags a caller actually types: `--save`,
`--save-only`, `--fresh`, `--ttl`, `--no-cache`, `--max-size`, and the `cache` verbs on top. The
HTTP layer is replaced by a counter, so a cache hit is proved by the counter not moving.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webscour import backends, cache, cli

PAGE = (
    "<html><head><title>Example Domain</title></head><body><div>"
    "<h1>Example Domain</h1><p>This domain is for use in documentation examples.</p>"
    "</div></body></html>"
)


class Headers(dict):
    def get_content_type(self):
        return "text/html"

    def get_content_charset(self):
        return "utf-8"


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


class FetchCacheTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="webscour-fetch-")
        os.chdir(self.tmp)
        self.calls = []
        self._http_raw = backends.http_raw
        self._cli_raw = cli.http_raw

        def fake(url, *a, **k):
            self.calls.append(url)
            return PAGE.encode(), "text/html", Headers(), "utf-8"

        backends.http_raw = fake
        cli.http_raw = fake

    def tearDown(self):
        backends.http_raw = self._http_raw
        cli.http_raw = self._cli_raw
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_saving_prints_the_page_and_writes_the_file(self):
        rc, out, err = run(["fetch", "https://example.com/a", "--save"])
        self.assertEqual(rc, 0)
        self.assertIn("Example Domain", out)
        self.assertEqual(err, "", "saving is not a diagnostic, so stderr stays empty")
        index = cache.read_index()
        self.assertEqual(len(index), 1)

    def test_a_second_fetch_inside_the_ttl_is_a_hit(self):
        run(["fetch", "https://example.com/a", "--save"])
        rc, out, err = run(["fetch", "https://example.com/a"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.calls), 1, "the second read must not touch the network")
        self.assertIn("Example Domain", out)
        self.assertIn("cache: hit", err)

    def test_fresh_bypasses_the_cache(self):
        run(["fetch", "https://example.com/a", "--save"])
        rc, _out, _err = run(["fetch", "https://example.com/a", "--fresh"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.calls), 2, "--fresh must go to the network")

    def test_no_cache_neither_reads_nor_writes(self):
        run(["fetch", "https://example.com/a", "--no-cache", "--save"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(cache.read_index(), {}, "--no-cache must not write")
        run(["fetch", "https://example.com/a", "--no-cache"])
        self.assertEqual(len(self.calls), 2, "--no-cache must not read")

    def test_a_ttl_shorter_than_the_age_is_a_miss(self):
        run(["fetch", "https://example.com/a", "--save"])
        index = cache.read_index()
        key = cache.normalize("https://example.com/a")
        index[key]["fetched_at"] -= 7200
        cache.write_index(index)
        _rc, _out, _err = run(["fetch", "https://example.com/a", "--ttl", "1h"])
        self.assertEqual(len(self.calls), 2, "a two-hour-old entry is outside a one-hour TTL")

    def test_a_bad_ttl_is_a_usage_error(self):
        rc, _out, err = run(["fetch", "https://example.com/a", "--ttl", "soon"])
        self.assertEqual(rc, 2)
        self.assertIn("not a duration", err)

    def test_save_only_prints_one_index_line_and_not_the_page(self):
        rc, out, _err = run(["fetch", "https://example.com/a", "--save-only"])
        self.assertEqual(rc, 0)
        self.assertNotIn("Example Domain", out.splitlines()[0])
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertIn(".webscour/", out)
        self.assertIn("bytes", out)

    def test_a_refused_size_guard_warns_and_still_prints(self):
        rc, out, err = run(["fetch", "https://example.com/big", "--save", "--max-size", "10"])
        self.assertEqual(rc, 0, "a page too big to save is still a page to read")
        self.assertIn("Example Domain", out)
        self.assertIn("--max-size", err)
        self.assertEqual(cache.read_index(), {})

    def test_the_same_url_twice_writes_one_file(self):
        run(["fetch", "https://example.com/a", "--save", "--fresh", "--max-chars", "100"])
        run(["fetch", "https://example.com/a", "--save", "--fresh", "--max-chars", "100"])
        files = [n for n in os.listdir(cache.cache_dir()) if n.endswith(".md")]
        self.assertEqual(len(files), 1)
        self.assertEqual(len(cache.read_index()), 1)

    def test_dot_webscour_is_written_where_the_command_ran(self):
        run(["fetch", "https://example.com/a", "--save"])
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, ".webscour")))
        self.assertFalse(os.path.isdir(os.path.join(os.path.dirname(cli.__file__), ".webscour")))

    def test_a_dead_page_is_not_saved_and_the_error_is_reported(self):
        def gone(url, *a, **k):
            raise backends.FetchError("HTTP 404", status=404)

        backends.http_raw = gone
        cli.http_raw = gone
        saved_archive = cli.wayback_snapshot
        cli.wayback_snapshot = lambda url, **k: None
        try:
            rc, _out, err = run(["fetch", "https://example.com/gone", "--save"])
        finally:
            cli.wayback_snapshot = saved_archive
        self.assertEqual(rc, 2)
        self.assertIn("404", err)
        self.assertFalse(os.path.isdir(cache.cache_dir()), "a failed fetch writes nothing")


class CacheVerbsTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="webscour-verbs-")
        os.chdir(self.tmp)
        cache.save("https://example.com/a", "# A\n\nbody\n")
        cache.save("https://example.com/b", "# B\n\nbody\n")

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_path_prints_the_directory(self):
        rc, out, _err = run(["cache", "path"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), os.path.join(os.path.realpath(self.tmp), ".webscour"))

    def test_list_shows_one_row_per_entry(self):
        rc, out, _err = run(["cache", "list"])
        self.assertEqual(rc, 0)
        self.assertEqual(len([ln for ln in out.splitlines() if ".md" in ln]), 2, out)
        self.assertIn("2 entries", out)

    def test_list_json_is_the_index(self):
        rc, out, _err = run(["cache", "list", "--json"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(json.loads(out)), 2)

    def test_get_prints_the_saved_file_without_the_network(self):
        _rc, out, err = run(["cache", "get", "https://example.com/a"])
        self.assertIn("# A", out)
        self.assertEqual(err, "")

    def test_get_fetches_when_missing(self):
        saved = cli.cmd_fetch
        seen = []

        def fake(argv):
            seen.append(argv)
            print("fetched")
            return 0

        cli.cmd_fetch = fake
        cli.set_verbose(True)
        try:
            rc, out, err = run(["cache", "get", "https://example.com/missing"])
        finally:
            cli.cmd_fetch = saved
            cli.set_verbose(False)
        self.assertEqual(rc, 0)
        self.assertIn("fetched", out)
        self.assertIn("miss", err)
        self.assertIn("--save", seen[0])

    def test_prune_prints_what_it_removed(self):
        index = cache.read_index()
        for entry in index.values():
            entry["fetched_at"] -= 30 * 86400
        cache.write_index(index)
        rc, out, _err = run(["cache", "prune", "--older-than", "7d"])
        self.assertEqual(rc, 0)
        self.assertIn("removed", out)
        self.assertIn("2 file(s)", out)
        self.assertEqual(cache.read_index(), {})


class SearchFlagsTest(unittest.TestCase):
    def test_an_unknown_source_lists_every_known_one(self):
        rc, _out, err = run(["search", "x", "--source", "altavista"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown --source", err)
        self.assertIn("pubmed", err)
        self.assertIn("pypi", err)

    def test_a_category_without_the_web_source_is_refused(self):
        rc, _out, err = run(["search", "x", "--source", "hn", "--category", "it"])
        self.assertEqual(rc, 2)
        self.assertIn("only applies to --source web", err)

    def test_since_without_fresh_is_refused(self):
        rc, _out, err = run(["search", "x", "--since", "2026-01-01"])
        self.assertEqual(rc, 2)
        self.assertIn("--fresh", err)

    def test_a_malformed_since_is_refused(self):
        rc, _out, err = run(["search", "x", "--fresh", "--since", "last tuesday"])
        self.assertEqual(rc, 2)
        self.assertIn("YYYY-MM-DD", err)

    def test_fresh_with_a_source_is_refused(self):
        rc, _out, err = run(["search", "x", "--fresh", "--source", "hn"])
        self.assertEqual(rc, 2)
        self.assertIn("--fresh is its own source set", err)

    def test_json_carries_published_when_the_source_has_it(self):
        import webscour.sources as sources_mod

        saved = sources_mod.FETCHERS["googlenews"]
        sources_mod.FETCHERS["googlenews"] = lambda q, n: [
            {"title": "t", "url": "https://e/1", "snippet": "s", "published": "2026-11-14"}
        ]
        saved_bbc = sources_mod.FETCHERS["bbc"]
        sources_mod.FETCHERS["bbc"] = lambda q, n: []
        try:
            rc, out, _err = run(["search", "x", "--fresh", "--json"])
        finally:
            sources_mod.FETCHERS["googlenews"] = saved
            sources_mod.FETCHERS["bbc"] = saved_bbc
        self.assertEqual(rc, 0)
        rows = json.loads(out)
        self.assertEqual(rows[0]["published"], "2026-11-14")

    def test_a_source_row_without_a_date_has_no_published_key(self):
        import webscour.sources as sources_mod

        saved = sources_mod.FETCHERS["wikipedia"]
        sources_mod.FETCHERS["wikipedia"] = lambda q, n: [
            {"title": "t", "url": "https://e/1", "snippet": "s"}
        ]
        try:
            rc, out, _err = run(["search", "x", "--source", "wikipedia", "--json"])
        finally:
            sources_mod.FETCHERS["wikipedia"] = saved
        self.assertEqual(rc, 0)
        self.assertNotIn("published", json.loads(out)[0])


class MarkdownFormatTest(unittest.TestCase):
    """`--format markdown` keeps what the text path throws away, and `text` stays the default."""

    HTML = (
        "<html><head><title>Doc</title></head><body><article>"
        "<h1>Title</h1><p>See <a href='/guide'>the guide</a> and <code>run()</code>.</p>"
        "<pre><code class='language-bash'>  npm install\n  npm test</code></pre>"
        "<ul><li>one</li><li>two</li></ul>"
        "</article></body></html>"
    )

    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="webscour-md-")
        os.chdir(self.tmp)
        self._http_raw = backends.http_raw
        self._cli_raw = cli.http_raw

        def fake(url, *a, **k):
            return self.HTML.encode(), "text/html", Headers(), "utf-8"

        backends.http_raw = fake
        cli.http_raw = fake

    def tearDown(self):
        backends.http_raw = self._http_raw
        cli.http_raw = self._cli_raw
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_default_is_still_plain_text(self):
        _rc, out, _err = run(["fetch", "https://example.com/doc"])
        self.assertIn("the guide", out)
        self.assertNotIn("](", out)
        self.assertNotIn("**", out)

    def test_markdown_keeps_headings_links_fences_and_lists(self):
        _rc, out, _err = run(["fetch", "https://example.com/doc", "--format", "markdown"])
        self.assertIn("# Title", out)
        self.assertIn("[the guide](https://example.com/guide)", out)
        self.assertIn("`run()`", out)
        self.assertIn("```bash", out)
        self.assertIn("  npm install", out, "fence content keeps its indentation")
        self.assertIn("- one", out)

    def test_the_cached_copy_keeps_the_format_it_was_saved_in(self):
        run(["fetch", "https://example.com/doc", "--save", "--format", "markdown"])
        entry = next(iter(cache.read_index().values()))
        self.assertEqual(entry["format"], "markdown")
        _rc, out, err = run(["fetch", "https://example.com/doc", "--format", "markdown"])
        self.assertIn("cache: hit", err)
        self.assertIn("```bash", out)


class RouteThroughFetchTest(unittest.TestCase):
    """A route announces itself once; `--no-route` opts out; a declining route is silent."""

    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="webscour-route-")
        os.chdir(self.tmp)
        self._http_raw = backends.http_raw
        self._cli_raw = cli.http_raw
        self._resolve = getattr(cli.routes, "resolve", None)
        self._route_for = cli.routes.route_for

        def fake(url, *a, **k):
            return b"<html><body><p>plain page</p></body></html>", "text/html", Headers(), "utf-8"

        backends.http_raw = fake
        cli.http_raw = fake

    def tearDown(self):
        backends.http_raw = self._http_raw
        cli.http_raw = self._cli_raw
        cli.routes.route_for = self._route_for
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _stub_route(self):
        class R:
            name = "test-route"
            pattern = __import__("re").compile(".*")

            def resolve(self, m):
                # A resolver returns the body; routes.resolve() pairs it with the name.
                return "# Routed\n\nbody\n"

        cli.routes.route_for = lambda url: R()

    def test_a_route_prints_one_line(self):
        self._stub_route()
        rc, out, err = run(["fetch", "https://example.com/x", "--format", "markdown"])
        self.assertEqual(rc, 0)
        self.assertIn("# Routed", out)
        self.assertEqual(err, "route: test-route\n")

    def test_a_route_flattens_when_the_default_text_format_was_asked_for(self):
        self._stub_route()
        rc, out, _err = run(["fetch", "https://example.com/x"])
        self.assertEqual(rc, 0)
        self.assertIn("Routed", out)
        self.assertNotIn("# ", out, "text is the default, so no heading marker leaks")

    def test_no_route_takes_the_plain_path(self):
        self._stub_route()
        rc, out, err = run(["fetch", "https://example.com/x", "--no-route"])
        self.assertEqual(rc, 0)
        self.assertIn("plain page", out)
        self.assertNotIn("route:", err)


if __name__ == "__main__":
    unittest.main()
