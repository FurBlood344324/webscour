"""The site routes: which URL goes where, and what happens when a route declines.

`route_for` is pure, so the table needs no network. The resolvers are fed captured payloads with
`http`/`http_raw` stubbed, which is the only way to test "the API answered something unexpected"
without waiting for a site to break.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webscour import routes
from webscour.backends import FetchError


class RouteTableTest(unittest.TestCase):
    def test_the_measured_urls_each_pick_their_route(self):
        cases = {
            "https://stackoverflow.com/questions/11227809": "stackexchange",
            "https://github.com/psf/requests": "github-repo",
            "https://github.com/psf/requests/blob/main/README.md": "github-blob",
            "https://github.com/psf/requests/issues/6000": "github-issue",
            "https://arxiv.org/abs/1706.03762": "arxiv",
            "https://news.ycombinator.com/item?id=1": "hackernews",
            "https://en.wikipedia.org/wiki/Transformer_(deep_learning)": "wikipedia",
        }
        for url, name in cases.items():
            with self.subTest(url=url):
                route = routes.route_for(url)
                self.assertIsNotNone(route, "no route for %s" % url)
                self.assertEqual(route.name, name)

    def test_an_issue_url_is_not_taken_by_the_repo_route(self):
        # Order matters: `/issues/1` also matches a laxer repo pattern, and a README would be a
        # silently wrong answer for a bug report.
        self.assertEqual(routes.route_for("https://github.com/a/b/issues/1").name, "github-issue")
        self.assertEqual(
            routes.route_for("https://github.com/a/b/blob/main/x.md").name, "github-blob"
        )

    def test_an_unknown_host_has_no_route(self):
        self.assertIsNone(routes.route_for("https://example.com/anything"))

    def test_an_empty_url_has_no_route(self):
        self.assertIsNone(routes.route_for(""))

    def test_resolving_an_unrouted_url_raises_rather_than_guessing(self):
        with self.assertRaises(FetchError):
            routes.resolve("https://example.com/")


class Stub:
    """Replace `routes.http` for one test with a callable keyed by URL prefix."""

    def __init__(self, mapping):
        self.mapping = mapping
        self.seen = []

    def __call__(self, url, **kwargs):
        self.seen.append(url)
        for prefix, body in self.mapping.items():
            if url.startswith(prefix):
                return body, "text/html", {}
        raise FetchError("HTTP 404", status=404)


class StackExchangeTest(unittest.TestCase):
    def test_the_question_body_becomes_markdown_with_a_score_line(self):
        payload = json.dumps(
            {
                "items": [
                    {
                        "title": "Why is a sorted array faster?",
                        "body": "<p>Because of <strong>branch prediction</strong>.</p>",
                        "link": "https://stackoverflow.com/questions/1",
                        "score": 42,
                        "answer_count": 3,
                        "is_answered": True,
                    }
                ]
            }
        )
        saved = routes.http
        stub = Stub({"https://api.stackexchange.com/": payload})
        routes.http = stub
        try:
            name, body = routes.resolve("https://stackoverflow.com/questions/1")
        finally:
            routes.http = saved
        self.assertEqual(name, "stackexchange")
        self.assertIn("# Why is a sorted array faster?", body)
        self.assertIn("**branch prediction**", body)
        self.assertIn("score 42", body)
        self.assertIn("withbody", stub.seen[0], "the body is the reason this route exists")

    def test_an_empty_answer_declines(self):
        saved = routes.http
        routes.http = Stub({"https://api.stackexchange.com/": '{"items": []}'})
        try:
            with self.assertRaises(FetchError):
                routes.resolve("https://stackoverflow.com/questions/1")
        finally:
            routes.http = saved


class GithubTest(unittest.TestCase):
    def test_a_readme_is_not_double_titled(self):
        saved = routes.http
        routes.http = Stub({"https://api.github.com/": "<h1>Real Title</h1><p>body</p>"})
        try:
            _name, body = routes.resolve("https://github.com/a/b")
        finally:
            routes.http = saved
        self.assertTrue(body.startswith("# Real Title"), body[:40])
        self.assertEqual(body.count("# Real Title"), 1)

    def test_a_blob_without_a_markdown_extension_is_fenced(self):
        saved = routes.http
        routes.http = Stub({"https://raw.githubusercontent.com/": "print('hi')"})
        try:
            _name, body = routes.resolve("https://github.com/a/b/blob/main/script.py")
        finally:
            routes.http = saved
        self.assertEqual(body, "```\nprint('hi')\n```\n")

    def test_an_issue_carries_its_comments(self):
        issue = json.dumps(
            {
                "title": "It breaks",
                "body": "steps to reproduce",
                "state": "open",
                "comments": 1,
                "created_at": "2026-01-02T00:00:00Z",
                "html_url": "https://github.com/a/b/issues/7",
                "user": {"login": "someone"},
            }
        )
        comments = json.dumps(
            [
                {
                    "body": "same here",
                    "created_at": "2026-01-03T00:00:00Z",
                    "user": {"login": "other"},
                }
            ]
        )
        saved = routes.http
        stub = Stub(
            {
                "https://api.github.com/repos/a/b/issues/7/comments": comments,
                "https://api.github.com/repos/a/b/issues/7": issue,
            }
        )
        routes.http = stub
        try:
            _name, body = routes.resolve("https://github.com/a/b/issues/7")
        finally:
            routes.http = saved
        self.assertIn("# It breaks", body)
        self.assertIn("same here", body)
        self.assertIn("other", body)


class ArxivTest(unittest.TestCase):
    HTML = (
        "<html><body>"
        + "<h1>Attention Is All You Need</h1>"
        + "<p>"
        + "x " * 400
        + "</p></body></html>"
    )

    def test_the_banner_above_the_first_heading_is_dropped(self):
        saved = routes.http_raw
        routes.http_raw = lambda url, **k: (
            ("arXiv is now a nonprofit" + self.HTML).encode(),
            "text/html",
            {},
            "utf-8",
        )
        try:
            _name, body = routes.resolve("https://arxiv.org/abs/1706.03762")
        finally:
            routes.http_raw = saved
        self.assertTrue(body.startswith("# Attention Is All You Need"), body[:60])
        self.assertNotIn("nonprofit", body)

    def test_a_paper_without_html_declines(self):
        saved = routes.http_raw
        routes.http_raw = lambda url, **k: (
            b"<html><body>no full text</body></html>",
            "text/html",
            {},
            "utf-8",
        )
        try:
            with self.assertRaises(FetchError):
                routes.resolve("https://arxiv.org/abs/1234.5678")
        finally:
            routes.http_raw = saved


class HackerNewsTest(unittest.TestCase):
    def test_the_comment_tree_is_indented_by_depth(self):
        payload = json.dumps(
            {
                "id": 1,
                "title": "Y Combinator",
                "url": "http://ycombinator.com",
                "author": "pg",
                "created_at": "2006-10-09T00:00:00Z",
                "children": [
                    {
                        "id": 2,
                        "author": "sama",
                        "created_at": "2006-10-09T00:00:00Z",
                        "text": "a reply",
                        "children": [],
                    }
                ],
            }
        )
        saved = routes.http
        routes.http = Stub({"https://hn.algolia.com/": payload})
        try:
            _name, body = routes.resolve("https://news.ycombinator.com/item?id=1")
        finally:
            routes.http = saved
        self.assertIn("# Y Combinator", body)
        self.assertIn("- **sama**", body)
        self.assertIn("a reply", body)


class WikipediaTest(unittest.TestCase):
    def test_the_summary_leads_and_a_disambiguation_refuses(self):
        summary = json.dumps(
            {"title": "Transformer", "extract": "A family of models.", "type": "standard"}
        )
        saved = routes.http
        routes.http = Stub(
            {
                "https://en.wikipedia.org/api/rest_v1/page/summary/": summary,
                "https://en.wikipedia.org/api/rest_v1/page/html/": "<html><body><p>A family of models.</p></body></html>",
            }
        )
        try:
            _name, body = routes.resolve("https://en.wikipedia.org/wiki/Transformer")
        finally:
            routes.http = saved
        self.assertIn("# Transformer", body)
        self.assertIn("A family of models.", body)

    def test_a_disambiguation_page_falls_back_to_the_plain_path(self):
        saved = routes.http
        routes.http = Stub(
            {
                "https://en.wikipedia.org/api/rest_v1/page/summary/": json.dumps(
                    {"title": "Mercury", "type": "disambiguation"}
                )
            }
        )
        try:
            with self.assertRaises(FetchError):
                routes.resolve("https://en.wikipedia.org/wiki/Mercury")
        finally:
            routes.http = saved


if __name__ == "__main__":
    unittest.main()
