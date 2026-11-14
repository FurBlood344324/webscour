"""URL -> a structured endpoint, when the site publishes one.

A scrape of a Stack Overflow question is a Cloudflare 403 today; the Stack Exchange API answers
the same question with the post bodies in JSON. A GitHub README rendered by the site is markup
and a session cookie; `api.github.com/.../readme` is the same file without either. These routes
exist because the plain path is measurably worse on these sites, not because an API is tidier.

Two rules the shape enforces:

* a route returns markdown or text, never HTML, so `fetch` has nothing left to guess about; and
* a route that raises `FetchError` is a *fallback*, never an error: the caller gets the plain
  path and a `-v` note saying which route declined. Nothing here may turn a page that used to
  work into a failure.

No route needs a credential, and none proxies through a third party.
"""

import html
import json
import re
import urllib.parse

from .backends import FetchError, http, http_raw
from .extract import html_to_markdown

JSON_ACCEPT = "application/json"
GITHUB_ACCEPT = "application/vnd.github+json"


class Route:
    """One rule: a compiled pattern, a name for the stderr line, and the resolver."""

    __slots__ = ("name", "pattern", "resolve")

    def __init__(self, name, pattern, resolve):
        self.name = name
        self.pattern = re.compile(pattern)
        self.resolve = resolve


def _so_question(m):
    """Stack Exchange `filter=withbody` returns the question body as HTML in the same call."""
    site, qid = m.group(1), m.group(2)
    url = "https://api.stackexchange.com/2.3/questions/%s?site=%s&filter=withbody" % (qid, site)
    doc, _, _ = http(url, accept=JSON_ACCEPT)
    data = json.loads(doc)
    items = data.get("items") or []
    if not items:
        raise FetchError("stackexchange: no item for %s" % qid)
    q = items[0]
    parts = ["# %s" % html_to_markdown(q.get("title") or "", base=q.get("link") or "").strip()]
    body = q.get("body") or q.get("body_markdown") or ""
    if "</" in body:
        parts.append(html_to_markdown(body, base=q.get("link") or "").strip())
    else:
        parts.append(body.strip())
    score = q.get("score")
    parts.append(
        "---\n%s | score %s | %s answers | %s"
        % (
            q.get("link") or "",
            score,
            q.get("answer_count"),
            "answered" if q.get("is_answered") else "unanswered",
        )
    )
    return "\n\n".join(p for p in parts if p) + "\n"


def _github_readme(m):
    owner, repo = m.group(1), m.group(2)
    doc, _, _ = http(
        "https://api.github.com/repos/%s/%s/readme" % (owner, repo),
        accept="application/vnd.github.html+json",
    )
    body = html_to_markdown(doc, base="https://github.com/%s/%s/blob/HEAD/" % (owner, repo))
    if not body.strip():
        raise FetchError("github readme: empty")
    # The README usually opens with its own h1; a second one above it would read as two titles.
    if body.lstrip().startswith("# "):
        return body if body.endswith("\n") else body + "\n"
    return "# %s/%s\n\n%s" % (owner, repo, body)


def _github_blob(m):
    owner, repo, ref, path = m.group(1), m.group(2), m.group(3), m.group(4)
    url = "https://raw.githubusercontent.com/%s/%s/%s/%s" % (owner, repo, ref, path)
    doc, ctype, _ = http(url)
    if "markdown" in ctype or path.endswith((".md", ".markdown")):
        return doc if doc.endswith("\n") else doc + "\n"
    return "```\n%s\n```\n" % doc.rstrip("\n")


def _github_issue(m):
    owner, repo, number = m.group(1), m.group(2), m.group(3)
    doc, _, _ = http(
        "https://api.github.com/repos/%s/%s/issues/%s" % (owner, repo, number),
        accept=GITHUB_ACCEPT,
    )
    issue = json.loads(doc)
    parts = [
        "# %s" % (issue.get("title") or ""),
        "**%s** opened %s, state %s, %s comments\n\n%s"
        % (
            (issue.get("user") or {}).get("login") or "unknown",
            (issue.get("created_at") or "")[:10],
            issue.get("state"),
            issue.get("comments"),
            issue.get("html_url") or "",
        ),
        (issue.get("body") or "").strip() or "(no body)",
    ]
    if issue.get("comments"):
        doc, _, _ = http(
            "https://api.github.com/repos/%s/%s/issues/%s/comments?per_page=50"
            % (owner, repo, number),
            accept=GITHUB_ACCEPT,
        )
        for c in json.loads(doc):
            parts.append(
                "### %s, %s\n\n%s"
                % (
                    (c.get("user") or {}).get("login") or "unknown",
                    (c.get("created_at") or "")[:10],
                    (c.get("body") or "").strip() or "(empty)",
                )
            )
    return "\n\n".join(parts) + "\n"


def _arxiv_abs(m):
    """Full text from arxiv's own HTML rendering; an older paper has none, so it says so."""
    ident = m.group(1)
    try:
        raw, _ctype, _hdrs, cs = http_raw(
            "https://arxiv.org/html/%s" % ident, accept="text/html,*/*;q=0.5"
        )
    except FetchError as e:
        raise FetchError("arxiv html: %s" % e) from e
    body = html_to_markdown(raw.decode(cs, "replace"), base="https://arxiv.org/html/%s" % ident)
    if len(body.strip()) < 500:
        raise FetchError("arxiv html: no full text for %s" % ident)
    # The rendering opens with arxiv's own banner and license note. The paper starts at the
    # first h1, and everything above it is chrome the reader did not ask for.
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# ") and i < 60:
            return "\n".join(lines[i:]).strip() + "\n"
    return body


def _hn_item(m):
    doc, _, _ = http("https://hn.algolia.com/api/v1/items/%s" % m.group(1), accept=JSON_ACCEPT)
    item = json.loads(doc)
    if not item or "id" not in item:
        raise FetchError("hn item: not found")
    lines = []

    def walk(node, depth):
        text = (node.get("text") or "") or ""
        if "</" in text:
            text = html_to_markdown(text).strip()
        title = node.get("title")
        if title:
            lines.append("# %s" % title)
            if node.get("url"):
                lines.append(node["url"])
        who = html.unescape(node.get("author") or "unknown")
        when = (node.get("created_at") or "")[:10]
        lead = "  " * depth + ("- " if depth else "")
        body = " ".join(html.unescape(text).split())
        if body:
            lines.append("%s**%s** (%s): %s" % (lead, who, when, body))
        elif not title:
            lines.append("%s**%s** (%s)" % (lead, who, when))
        for kid in node.get("children") or []:
            walk(kid, depth + 1)

    walk(item, 0)
    return "\n".join(lines).strip() + "\n"


def _wikipedia(m):
    """REST summary first (the definition), then the article HTML as the body."""
    lang, title = m.group(1) or "en", urllib.parse.unquote(m.group(2))
    slug = urllib.parse.quote(title.replace(" ", "_"), safe="()_,-!:''")
    api = "https://%s.wikipedia.org/api/rest_v1/page" % lang
    summary, _, _ = http("%s/summary/%s" % (api, slug), accept=JSON_ACCEPT)
    meta = json.loads(summary)
    if meta.get("type") == "disambiguation":
        raise FetchError("wikipedia: disambiguation page, use the plain path")
    body, _, _ = http("%s/html/%s" % (api, slug), accept="text/html,*/*;q=0.5")
    text = html_to_markdown(body, base="https://%s.wikipedia.org/wiki/%s" % (lang, slug))
    # The article HTML starts with a <title>-ish heading of its own; the summary is the lead
    # paragraph and the definition, so it goes above whatever the article begins with.
    parts = [text.strip()]
    extract = (meta.get("extract") or "").strip()
    if extract and not text.lstrip().startswith("# "):
        parts.insert(0, "# %s\n\n%s" % (meta.get("title") or title, extract))
    return "\n\n".join(p for p in parts if p) + "\n"


ROUTES = (
    Route(
        "stackexchange",
        r"^https?://(stackoverflow|superuser|serverfault|askubuntu|mathoverflow)\.com/questions/(\d+)",
        _so_question,
    ),
    Route(
        "github-issue",
        r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/issues/(\d+)",
        _github_issue,
    ),
    Route(
        "github-blob",
        r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$",
        _github_blob,
    ),
    Route("github-repo", r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/?$", _github_readme),
    Route("arxiv", r"^https?://(?:www\.)?arxiv\.org/abs/([^?#]+)", _arxiv_abs),
    Route("hackernews", r"^https?://news\.ycombinator\.com/item\?id=(\d+)", _hn_item),
    Route("wikipedia", r"^https?://([a-z]{2})\.wikipedia\.org/wiki/([^?#]+)", _wikipedia),
)


def route_for(url):
    """The first route whose pattern matches, or None. Pure, so a test can ask without a request."""
    for route in ROUTES:
        if route.pattern.match(url or ""):
            return route
    return None


def resolve(url):
    """(name, markdown) for a routed URL. Raises FetchError when the route declines."""
    route = route_for(url)
    if route is None:
        raise FetchError("no route for %s" % url)
    return route.name, route.resolve(route.pattern.match(url))
