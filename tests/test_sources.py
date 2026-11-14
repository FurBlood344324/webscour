"""The keyless sources, parsed from captured payloads: no network in any test here.

Each parser is fed the exact shape its endpoint returned when it was measured. The point is not
"does json.loads work" but "does a row carry the fact a caller would search for": a version, a
date, a citation count, a DOI. Where a field is absent the row must say so, not invent one.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webscour import sources
from webscour.extract import markdown_to_text


class WikipediaTest(unittest.TestCase):
    def test_highlight_markup_is_stripped_and_the_url_is_built(self):
        doc = {
            "query": {
                "search": [
                    {
                        "title": "Transformer (deep learning)",
                        "snippet": 'a family of <span class="searchmatch">transformer</span> models',
                    }
                ]
            }
        }
        rows = sources.parse_wikipedia(doc)
        self.assertEqual(
            rows[0]["url"], "https://en.wikipedia.org/wiki/Transformer_(deep_learning)"
        )
        self.assertNotIn("span", rows[0]["snippet"])
        self.assertNotIn("published", rows[0], "an article has no publication date to report")


class OpenAlexTest(unittest.TestCase):
    def test_year_venue_and_citations(self):
        doc = {
            "results": [
                {
                    "display_name": "The Heroes of CRISPR",
                    "doi": "https://doi.org/10.1016/j.cell.2015.12.041",
                    "publication_year": 2016,
                    "cited_by_count": 542,
                    "best_oa_location": {"source": {"display_name": "Cell"}},
                }
            ]
        }
        row = sources.parse_openalex(doc)[0]
        self.assertEqual(row["url"], "https://doi.org/10.1016/j.cell.2015.12.041")
        self.assertIn("542 citations", row["snippet"])
        self.assertIn("Cell", row["snippet"])
        # OpenAlex knows the year and nothing finer, and a year sorted against a full date is a
        # lie about precision, so `published` stays empty and the year lives in the snippet.
        self.assertNotIn("published", row)
        self.assertIn("2016", row["snippet"])


class CrossrefTest(unittest.TestCase):
    def test_doi_url_and_issued_date(self):
        doc = {
            "message": {
                "items": [
                    {
                        "title": ["A paper"],
                        "DOI": "10.1/x",
                        "URL": "https://doi.org/10.1/x",
                        "container-title": ["Journal of Tests"],
                        "is-referenced-by-count": 7,
                        "issued": {"date-parts": [[2020, 10, 1]]},
                    }
                ]
            }
        }
        row = sources.parse_crossref(doc)[0]
        self.assertEqual(row["title"], "A paper")
        self.assertEqual(row["published"], "2020-10-01")
        self.assertIn("Journal of Tests", row["snippet"])

    def test_an_item_without_a_title_is_dropped(self):
        self.assertEqual(sources.parse_crossref({"message": {"items": [{"DOI": "10.1/x"}]}}), [])


class ArxivTest(unittest.TestCase):
    ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All You Need</title>
    <summary> The dominant sequence transduction models are based on complex recurrent or
convolutional neural networks. </summary>
  </entry>
</feed>"""

    def test_published_is_carried_and_the_summary_is_flattened(self):
        row = sources.parse_arxiv_api(self.ATOM)[0]
        self.assertEqual(row["published"], "2017-06-12")
        self.assertNotIn("\n", row["snippet"])
        self.assertEqual(row["url"], "http://arxiv.org/abs/1706.03762v7")

    def test_the_old_parser_still_has_no_published_field(self):
        from webscour.extract import parse_arxiv

        self.assertNotIn("published", parse_arxiv(self.ATOM)[0])


class EuropePmcTest(unittest.TestCase):
    def test_doi_preferred_then_pmid(self):
        doc = {
            "resultList": {
                "result": [
                    {"title": "With DOI", "doi": "10.1/a", "journalTitle": "J"},
                    {"title": "No DOI", "pmid": "123", "journalTitle": "J"},
                ]
            }
        }
        rows = sources.parse_europepmc(doc)
        self.assertEqual(rows[0]["url"], "https://doi.org/10.1/a")
        self.assertEqual(rows[1]["url"], "https://pubmed.ncbi.nlm.nih.gov/123/")


class PubmedTest(unittest.TestCase):
    def test_uid_order_is_kept_and_the_date_is_parsed(self):
        doc = {
            "result": {
                "uids": ["2", "1"],
                "2": {"title": "Second.", "fulljournalname": "J Two", "pubdate": "2026 Nov 13"},
                "1": {"title": "First.", "source": "J One", "pubdate": "2026 Nov"},
            }
        }
        rows = sources.parse_pubmed(doc)
        self.assertEqual([r["title"] for r in rows], ["Second", "First"])
        self.assertEqual(rows[0]["published"], "2026-11-13")
        self.assertEqual(rows[1]["published"], "2026-11-01", "a month-only date is the first")

    def test_a_record_without_a_title_is_dropped(self):
        doc = {"result": {"uids": ["1"], "1": {"title": ""}}}
        self.assertEqual(sources.parse_pubmed(doc), [])


class PackageTest(unittest.TestCase):
    def test_pypi(self):
        doc = {
            "info": {
                "name": "requests",
                "version": "2.34.2",
                "summary": "Python HTTP for Humans.",
                "requires_python": ">=3.10",
                "project_url": "https://pypi.org/project/requests/",
            },
            "releases": {"2.34.2": [{"upload_time_iso_8601": "2026-05-14T19:25:26.443000Z"}]},
        }
        row = sources.parse_pypi(doc)[0]
        self.assertEqual(row["title"], "requests")
        self.assertIn("2.34.2", row["snippet"])
        self.assertEqual(row["published"], "2026-05-14")

    def test_npm_flags_a_deprecated_package(self):
        doc = {"name": "old-thing", "version": "1.0.0", "deprecated": "use new-thing"}
        row = sources.parse_npm(doc)[0]
        self.assertIn("DEPRECATED", row["snippet"])

    def test_crates_reports_recent_downloads_and_a_yanked_latest(self):
        doc = {
            "crate": {
                "name": "serde",
                "max_version": "1.0.229",
                "description": "A generic serialization framework",
                "recent_downloads": 434411314,
                "updated_at": "2026-07-18T23:05:13Z",
                "repository": "https://github.com/serde-rs/serde",
            },
            "versions": [{"num": "1.0.229", "yanked": True}],
        }
        row = sources.parse_crates(doc)[0]
        self.assertIn("downloads (90d)", row["snippet"])
        self.assertIn("yanked", row["snippet"])
        self.assertEqual(row["url"], "https://github.com/serde-rs/serde")


class DevtoTest(unittest.TestCase):
    def test_tags_and_reading_time(self):
        doc = [
            {
                "title": "Follow a live blockchain",
                "url": "https://dev.to/x/y",
                "published_at": "2026-11-12T21:50:21Z",
                "reading_time_minutes": 4,
                "tag_list": ["python", "asyncio"],
            }
        ]
        row = sources.parse_devto(doc)[0]
        self.assertEqual(row["published"], "2026-11-12")
        self.assertIn("python", row["snippet"])
        self.assertIn("4 min read", row["snippet"])


class WaybackTest(unittest.TestCase):
    def test_header_row_is_skipped_and_the_snapshot_url_uses_id(self):
        doc = [
            ["timestamp", "original", "statuscode"],
            ["20261113195909", "https://example.com/", "200"],
        ]
        row = sources.parse_wayback(doc)[0]
        self.assertIn("/20261113195909id_/", row["url"])
        self.assertEqual(row["published"], "2026-11-13")


class RssTest(unittest.TestCase):
    RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Story one - Outlet</title><link>https://ex.com/1</link>
<pubDate>Sat, 14 Nov 2026 19:43:32 GMT</pubDate>
<description>&lt;a&gt;Story one&lt;/a&gt; Outlet</description><source>Outlet</source></item>
<item><title>Old story</title><link>https://ex.com/2</link>
<pubDate>Mon, 02 Jan 2026 10:00:00 GMT</pubDate><description>text</description></item>
</channel></rss>"""

    def test_rfc822_dates_become_iso(self):
        rows = sources.parse_rss(self.RSS)
        self.assertEqual([r["published"] for r in rows], ["2026-11-14", "2026-01-02"])

    def test_the_outlet_is_not_repeated_three_times(self):
        row = sources.parse_rss(self.RSS)[0]
        self.assertEqual(row["title"], "Story one")
        self.assertEqual(row["snippet"], "Outlet", row["snippet"])
        self.assertEqual(row["snippet"].count("Outlet"), 1)

    def test_an_atom_feed_reads_the_same_way(self):
        atom = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom item</title><link href="https://ex.com/a"/><published>2026-03-04T00:00:00Z</published>
<summary>body</summary></entry></feed>"""
        row = sources.parse_rss(atom)[0]
        self.assertEqual(row["url"], "https://ex.com/a")
        self.assertEqual(row["published"], "2026-03-04")

    def test_broken_xml_is_an_empty_list_not_an_exception(self):
        self.assertEqual(sources.parse_rss("<rss><channel><item>"), [])


class FreshTest(unittest.TestCase):
    def _rows(self, *pairs):
        return lambda query, limit: [
            {"title": t, "url": u, "snippet": "", "published": p} for t, u, p in pairs
        ]

    def test_merge_sorts_by_date_and_labels_nothing_it_does_not_know(self):
        saved = sources.FETCHERS
        rows = {
            "googlenews": self._rows(("old", "https://a/1", "2026-11-01")),
            "bbc": self._rows(("new", "https://b/2", "2026-11-14")),
        }
        sources.FETCHERS = dict(saved, **rows)
        try:
            got = sources.fresh("q", 5)
        finally:
            sources.FETCHERS = saved
        self.assertEqual([r["title"] for r in got], ["new", "old"])

    def test_since_filters_and_undated_rows_are_dropped(self):
        saved = sources.FETCHERS
        sources.FETCHERS = dict(
            saved,
            googlenews=lambda q, n: [
                {"title": "dated", "url": "https://a/1", "snippet": "", "published": "2026-11-10"},
                {"title": "undated", "url": "https://a/2", "snippet": ""},
            ],
            bbc=lambda q, n: [],
        )
        try:
            self.assertEqual(
                [r["title"] for r in sources.fresh("q", 5, since="2026-11-01")], ["dated"]
            )
            self.assertEqual(sources.fresh("q", 5, since="2026-11-11"), [])
        finally:
            sources.FETCHERS = saved


class SourceTableTest(unittest.TestCase):
    def test_every_declared_source_has_a_fetcher(self):
        for name in sources.API_SOURCES:
            self.assertIn(name, sources.FETCHERS, name)

    def test_arxiv_api_is_the_same_callable_as_arxiv(self):
        self.assertIs(sources.FETCHERS["arxiv"], sources.FETCHERS["arxiv-api"])

    def test_the_help_string_names_every_source(self):
        for name in sources.API_SOURCES:
            if name == "arxiv-api":
                continue
            self.assertIn(name, sources.SOURCES_HELP)


class MarkdownToTextTest(unittest.TestCase):
    def test_links_and_emphasis_are_flattened(self):
        md = "# Title\n\nA [link](https://x/y) and **bold** and `code`.\n"
        self.assertEqual(markdown_to_text(md), "Title\n\nA link and bold and code.")

    def test_a_fence_is_kept_verbatim(self):
        md = "```bash\n  keep  spaces\n```\n"
        self.assertEqual(markdown_to_text(md), "  keep  spaces")

    def test_a_table_becomes_its_cells(self):
        md = "| a | b |\n| --- | --- |\n| 1 | 2 |\n"
        self.assertEqual(markdown_to_text(md), "a b\n1 2")


if __name__ == "__main__":
    unittest.main()
