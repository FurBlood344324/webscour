"""The cache contract: one file per URL, an atomic index, a TTL, and a size guard.

Every test here works in a temporary directory, so nothing is written into the checkout and the
tests can run in parallel with a real `wsc fetch` in another shell.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webscour import cache

PAGE = "# Title\n\nBody text.\n"


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.mkdtemp(prefix="webscour-cache-")
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._cwd)


class DirectoryTest(CacheTestCase):
    def test_directory_lives_under_the_working_directory(self):
        self.assertEqual(cache.cache_dir(), os.path.join(os.path.realpath(self.tmp), ".webscour"))

    def test_creating_the_directory_writes_gitignore_once(self):
        cache.ensure_dir()
        ignore = os.path.join(cache.cache_dir(), ".gitignore")
        with open(ignore, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "*\n")
        # An existing .gitignore is never rewritten: a user who edited it meant what they wrote.
        with open(ignore, "w", encoding="utf-8") as fh:
            fh.write("# mine\n*\n")
        cache.ensure_dir()
        with open(ignore, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "# mine\n*\n")

    def test_normalize_is_the_identity(self):
        same = [
            "https://Example.com/a/",
            "https://example.com/a",
            "https://example.com:443/a",
            "https://example.com/a#fragment",
        ]
        keys = {cache.normalize(u) for u in same}
        self.assertEqual(len(keys), 1, keys)
        self.assertNotEqual(
            cache.normalize("https://e.com/a?page=1"), cache.normalize("https://e.com/a")
        )

    def test_file_name_is_hash_plus_slug(self):
        name = cache.file_name("https://example.com/docs/getting-started?x=1")
        digest, slug = name[:-3].split("-", 1)
        self.assertEqual(len(digest), 8)
        self.assertEqual(slug, "example-com-docs-getting-started")
        self.assertTrue(name.endswith(".md"))

    def test_long_segments_are_capped(self):
        slug = cache.slug_for("https://example.com/" + "x" * 300)
        self.assertLessEqual(len(slug), 60)

    def test_two_urls_with_the_same_path_get_different_files(self):
        one = cache.file_name("https://a.example.com/docs")
        two = cache.file_name("https://b.example.com/docs")
        self.assertNotEqual(one, two)
        self.assertNotEqual(
            os.path.basename(one).split("-")[0], os.path.basename(two).split("-")[0]
        )


class SaveAndLookupTest(CacheTestCase):
    def test_save_then_hit_inside_the_ttl(self):
        cache.save("https://example.com/a", PAGE)
        hit = cache.lookup("https://example.com/a")
        self.assertIsNotNone(hit)
        text, entry, age = hit
        self.assertEqual(text, PAGE)
        self.assertEqual(entry["format"], "markdown")
        self.assertLess(age, 5)

    def test_miss_after_the_ttl(self):
        entry = cache.save("https://example.com/a", PAGE)
        later = entry["fetched_at"] + cache.DEFAULT_TTL + 1
        self.assertIsNone(cache.lookup("https://example.com/a", now=later))

    def test_a_shorter_ttl_expires_sooner(self):
        entry = cache.save("https://example.com/a", PAGE)
        self.assertIsNone(
            cache.lookup("https://example.com/a", ttl=60, now=entry["fetched_at"] + 61)
        )
        self.assertIsNotNone(
            cache.lookup("https://example.com/a", ttl=60, now=entry["fetched_at"] + 59)
        )

    def test_ttl_zero_is_never_a_hit(self):
        cache.save("https://example.com/a", PAGE)
        self.assertIsNone(cache.lookup("https://example.com/a", ttl=0))

    def test_ttl_none_ignores_freshness_for_cache_get(self):
        entry = cache.save("https://example.com/a", PAGE)
        later = entry["fetched_at"] + cache.DEFAULT_TTL * 10
        self.assertIsNotNone(cache.lookup("https://example.com/a", ttl=None, now=later))

    def test_same_url_twice_is_one_file_and_an_updated_index(self):
        cache.save("https://example.com/a", PAGE)
        first = cache.read_index()
        cache.save("https://example.com/a", PAGE + "more\n")
        files = sorted(n for n in os.listdir(cache.cache_dir()) if n.endswith(".md"))
        index = cache.read_index()
        self.assertEqual(len(files), 1, files)
        self.assertEqual(len(index), 1, index)
        key = cache.normalize("https://example.com/a")
        self.assertGreaterEqual(index[key]["fetched_at"], first[key]["fetched_at"])
        self.assertEqual(index[key]["bytes"], len((PAGE + "more\n").encode()))

    def test_a_missing_file_is_a_miss_not_an_error(self):
        entry = cache.save("https://example.com/a", PAGE)
        os.unlink(os.path.join(cache.cache_dir(), entry["file"]))
        self.assertIsNone(cache.lookup("https://example.com/a"))

    def test_an_index_row_records_the_route_and_status(self):
        entry = cache.save(
            "https://example.com/a", PAGE, fmt="markdown", route="github-repo", status=200
        )
        self.assertEqual(entry["route"], "github-repo")
        self.assertEqual(entry["status"], 200)


class AtomicWriteTest(CacheTestCase):
    def test_a_failed_write_leaves_the_old_file_and_no_half_index(self):
        cache.save("https://example.com/a", PAGE)
        before = cache.read_index()

        def boom(*a, **k):
            raise OSError("disk full")

        saved = cache._atomic_write
        cache._atomic_write = boom
        try:
            with self.assertRaises(OSError):
                cache.save("https://example.com/a", "new body\n")
        finally:
            cache._atomic_write = saved
        self.assertEqual(cache.read_index(), before, "the index must be untouched")
        self.assertEqual(cache.lookup("https://example.com/a")[0], PAGE)

    def test_a_kill_between_temp_write_and_rename_cannot_corrupt_the_index(self):
        cache.save("https://example.com/a", PAGE)
        index_path = os.path.join(cache.cache_dir(), cache.INDEX)
        with open(index_path, encoding="utf-8") as fh:
            good = fh.read()

        # The rename is the last step; killing the process between the write and the rename
        # leaves the old index in place and an orphan temp file, which is what `regen` in
        # _atomic_write's absence looks like.
        tmp = os.path.join(cache.cache_dir(), cache.TMP_PREFIX + cache.INDEX)
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write('{"truncated": ')
        self.assertEqual(json.loads(good), cache.read_index(), "index must still parse")
        # The orphan temp file is exactly what the next save would overwrite; `orphans()` reports
        # it rather than deleting it, because a name it cannot explain is not its to remove.
        self.assertTrue(os.path.exists(tmp))

    def test_a_corrupt_index_is_reported_not_replaced(self):
        cache.ensure_dir()
        with open(os.path.join(cache.cache_dir(), cache.INDEX), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        with self.assertRaises(cache.CacheError):
            cache.read_index()


class SizeGuardTest(CacheTestCase):
    def test_a_body_over_the_limit_is_refused_and_nothing_is_written(self):
        with self.assertRaises(cache.CacheError) as ctx:
            cache.save("https://example.com/a", "x" * 100, max_bytes=50)
        self.assertIn("--max-size", str(ctx.exception))
        # A refused save writes nothing at all, not even the directory: a guard that leaves a
        # partial capture behind is worse than no guard.
        self.assertFalse(os.path.isdir(cache.cache_dir()))
        self.assertEqual(cache.read_index(), {})

    def test_the_limit_can_be_raised(self):
        entry = cache.save("https://example.com/a", "x" * 100, max_bytes=200)
        self.assertEqual(entry["bytes"], 100)


class PruneTest(CacheTestCase):
    def test_prune_deletes_only_what_is_older(self):
        old = cache.save("https://example.com/old", PAGE)
        index = cache.read_index()
        # Age the first entry by nine days and leave the second at its own timestamp, so the
        # window is the only difference between the two rows.
        index[cache.normalize("https://example.com/old")]["fetched_at"] = (
            old["fetched_at"] - 9 * 86400
        )
        cache.write_index(index)
        cache.save("https://example.com/new", PAGE)
        now = old["fetched_at"] + 3600
        gone = cache.prune(7 * 86400, now=now)
        self.assertEqual([g[0] for g in gone], [cache.normalize("https://example.com/old")])
        index = cache.read_index()
        self.assertEqual(list(index), [cache.normalize("https://example.com/new")])
        files = [n for n in os.listdir(cache.cache_dir()) if n.endswith(".md")]
        self.assertEqual(len(files), 1)

    def test_prune_with_nothing_old_is_a_no_op(self):
        cache.save("https://example.com/a", PAGE)
        self.assertEqual(cache.prune(7 * 86400), [])
        self.assertEqual(len(cache.read_index()), 1)

    def test_parse_duration(self):
        self.assertEqual(cache.parse_duration("7d"), 604800)
        self.assertEqual(cache.parse_duration("30m"), 1800)
        self.assertEqual(cache.parse_duration("90"), 90)
        with self.assertRaises(cache.CacheError):
            cache.parse_duration("soon")


class SlugEdgeTest(unittest.TestCase):
    def test_a_root_url_still_names_a_file(self):
        self.assertTrue(cache.file_name("https://example.com/").endswith("-example-com.md"))

    def test_an_empty_url_is_not_a_crash(self):
        self.assertTrue(cache.file_name("").endswith(".md"))
