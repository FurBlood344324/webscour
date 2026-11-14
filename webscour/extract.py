"""Bytes to text. Nothing in this module touches the network.

The HTML tokenizer, the reading-tree pass that turns a page into its own text, the search-result
parsers, the sitemap and robots readers, the js-shell heuristic, the document router and the link
filter all live here. The four decisions a caller makes on the result (`js_shell_reason`,
`document_backend`, `filter_links`, `same_origin`) are pure functions on purpose, so the self-test
and the unit tests check them with no network, no SearXNG and no render backend installed.

One module boundary to keep in mind: `_run` shells out to a *local* binary (pdftotext, pandoc,
markitdown) and to nothing else. The render engines are in `backends.py`, because a browser is
a network client.

Extraction has two layers and they answer different questions. `Tokenizer`/`tokens()` is a flat
event stream, which is the right shape for reading anchors and blocks out of a search result page.
`html_to_text()` builds an element tree instead, because "is this div a menu" is a question about
a subtree, and a flat stream cannot answer it. Both are pure and neither is recursive in a way a
deep page can overflow.
"""

import gzip
import os
import re
import shutil
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# A snippet is cut at parse time, so every source yields rows of the same size.
SNIPPET = 200


# fmt: off
# Tags that end a line of reading text. Everything else is inline. The blocks below are tables
# and are read as tables, so the formatter is off for them: one tag per line hides the grouping.
BLOCK = {"p", "div", "br", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "section",
         "article", "table", "pre", "blockquote", "dt", "dd", "ul", "ol", "hr"}


# The tag list below is adopted wholesale, on 2026-11-14, from trafilatura 2.3.1's measured
# tag-removal settings (settings.py, line 341): the survivor of a benchmark suite rather than an
# opinion, and annotated there in three groups - `important`, `other content`, `secondary` - which
# are kept verbatim and in order here so a reader can check the provenance against the source. It
# is strictly larger than the twelve tags this tool dropped before, and the additions are exactly
# what a repository page is mostly made of: `button`, `dialog`, `figure`, `menu`, `object`, `time`,
# `use` and their neighbours. Two of ours sit on top of it, each justified by a fixture in
# `wsc --self-test`: `header` (site chrome, not a content heading) and `template` (never rendered).
DROP_TEXT = frozenset({
    # trafilatura, important
    "aside", "embed", "footer", "form", "head", "iframe", "menu", "object", "script",
    "fencedframe",
    # trafilatura, other content
    "applet", "audio", "canvas", "figure", "map", "picture", "svg", "video",
    # trafilatura, secondary
    "area", "blink", "button", "datalist", "dialog", "frame", "frameset", "fieldset", "label",
    "legend", "link", "input", "marquee", "math", "menuitem", "nav", "noindex", "noscript",
    "optgroup", "option", "output", "param", "progress", "rp", "rt", "rtc", "select", "source",
    "style", "track", "textarea", "time", "use",
    # ours
    "header", "template",
})


DROP_RESULTS = frozenset({"script", "style", "noscript", "template"})


# HTML void elements: opening them never pushes a scope.
VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


# Tags an author may leave unclosed without cheating the parser out of its tree.
AUTO_CLOSE = {
    "p": {"p"},
    "li": {"li"},
    "td": {"td", "th"},
    "th": {"td", "th"},
    "tr": {"tr"},
    "dt": {"dt", "dd"},
    "dd": {"dt", "dd"},
    "option": {"option"},
}


# Cookie and consent banners, matched against class and id. These are trafilatura's anchored
# compounds (xpaths.py, _COOKIE_CONSENT_RE), not bare `cookie`/`consent`: their benchmark found
# the bare substrings delete up to 97% of a WordPress page, because a template puts
# `cookies-not-set` on the body. A compound needs the vendor or the banner noun as well.
COOKIE_RE = re.compile(
    r"cookie[-_]?(?:banner|bar|consent|law|notice|policy|description)|notice[-_]{0,2}cookie"
    r"|consent[-_]?(?:banner|manager|sdk)|borlabs|cookiebot|cmplz|onetrust|moove[-_]?gdpr",
    re.I,
)


# Class fragments that mean "in the accessibility tree, not on the screen". Matched as
# substrings of the lowercased class list, not as exact tokens: every framework prefixes its
# utility classes (`sr-only`, `prc-src-InternalVisuallyHidden`, `tw-sr-only`) and the meaning is
# the same in all of them. `hidden`, `is-hidden` and `d-none` are matched as whole tokens, so a
# name like `not-hidden` cannot silently delete a paragraph.
HIDDEN_FRAGMENTS = ("sr-only", "visually-hidden", "visuallyhidden", "screen-reader-text",
                    "screenreader")
HIDDEN_TOKENS = frozenset({"hidden", "is-hidden", "d-none"})


# Containers whose link density says whether they are reading text or a menu. `p` and
# `blockquote` are here because a short paragraph that is one link is a caption, and trafilatura
# reaches the same conclusion from the same evidence.
DENSITY_TAGS = frozenset({"div", "section", "ul", "ol", "p", "blockquote"})


# The classic boilerplate heuristic, with trafilatura's numbers and its reasoning.
#
# A block is judged by what its links are, not only by how much of it they cover, because three
# different page shapes look identical to a single ratio: a caption (one long link), a menu (many
# words, all of them links) and a catalog ("every link alone in its own paragraph"). One ratio
# cannot separate them, and a rule that tries deletes the wrong one on a real page.
LONG_LINK = 100  # a lone link at least this long, holding 90% of the block, is a caption
SHORT_RATIO = 0.8  # a short block whose link text is this share of it is a menu
SHORT_LINK = 10  #   a link under this many characters is a menu item, not a sentence
FARM_LINKS = 4  #    "many links": a handful of long sentence-links is editorial, not a farm
FARM_RATIO = 0.9  #  above this share of link text a large block is a farm
FARM_AVG_LINK = 100  # unless the average link is this long: one link per card, a catalog


def _cls(attrs):
    return set((attrs.get("class") or "").split())


class Tokenizer(HTMLParser):
    """Flat event stream: start / end / text, each with its tag path and class sets."""

    def __init__(self, skip=DROP_RESULTS):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.stack = []
        self.events = []
        self.skip = frozenset(skip)

    def _skipping(self):
        return any(tag in self.skip for tag, _ in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append((tag, a))
        if not self._skipping():
            self.events.append(
                {
                    "kind": "start",
                    "tag": tag,
                    "attrs": a,
                    "depth": len(self.stack),
                    "tags": [t for t, _ in self.stack],
                    "classes": [_cls(x) for _, x in self.stack],
                }
            )

    def handle_startendtag(self, tag, attrs):
        a = dict(attrs)
        if not self._skipping():
            self.events.append(
                {"kind": "start", "tag": tag, "attrs": a, "depth": len(self.stack) + 1}
            )
            self.events.append({"kind": "end", "tag": tag, "depth": len(self.stack) + 1})

    def handle_endtag(self, tag):
        idx = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                idx = i
                break
        if idx is None:
            return
        was_skip = any(t in self.skip for t, _ in self.stack)
        del self.stack[idx:]
        if not was_skip:
            self.events.append({"kind": "end", "tag": tag, "depth": len(self.stack) + 1})

    def handle_data(self, data):
        if self._skipping():
            return
        text = " ".join(data.split())
        if not text:
            return
        self.events.append(
            {
                "kind": "text",
                "text": text,
                "depth": len(self.stack),
                "tags": [t for t, _ in self.stack],
                "classes": [_cls(a) for _, a in self.stack],
            }
        )


def tokens(page, skip=DROP_RESULTS):
    p = Tokenizer(skip)
    try:
        p.feed(page)
        p.close()
    except Exception:
        pass
    return p.events


def parse_items(page, is_title, is_snippet):
    """Title/snippet anchors -> [{title,url,snippet}]. Nested markup inside them is kept."""
    items = []
    mode = None  # ("title"|"snippet", open_depth, item)
    for ev in tokens(page):
        kind = ev["kind"]
        if kind == "start":
            if is_title(ev):
                item = {"title": "", "url": _url(ev["attrs"].get("href", "")), "snippet": ""}
                items.append(item)
                mode = ("title", ev["depth"], item)
            elif is_snippet(ev) and items:
                mode = ("snippet", ev["depth"], items[-1])
        elif kind == "end":
            if mode and ev["depth"] < mode[1]:
                mode = None
        elif kind == "text":
            if not mode:
                continue
            field, open_depth, item = mode
            if ev["depth"] < open_depth:
                mode = None
                continue
            item[field] = append_text(item[field], ev["text"])
    return [i for i in items if i["title"] and i["url"]]


def _url(href):
    """Unwrap the redirect shells DDG and Bing put in front of a result URL."""
    href = (href or "").strip()
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/" in href:
        real = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg")
        if real:
            href = real[0]
    elif "google.com/url" in href:
        real = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("q")
        if real and real[0].startswith(("http://", "https://")):
            href = real[0]
        else:
            return ""  # an opaque redirect shell: the target is not recoverable, do not print it
    elif "bing.com/ck/a" in href:
        u = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("u")
        if u and u[0].startswith("a1"):
            import base64

            raw = u[0][2:]
            try:
                href = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode(
                    "utf-8", "replace"
                )
            except Exception:
                pass
    return href


def _has(ev, word):
    """Only the element's own class attribute, never an ancestor's."""
    return word in (ev["attrs"].get("class") or "").split()


def append_text(have, add):
    """Join inline fragments without inventing spaces before punctuation."""
    if not have:
        return add
    if add[:1] in ",.;:!?)]}%":
        return have + add
    if have[-1:] in "([{/":
        return have + add
    return have + " " + add


def parse_ddg_lite(page):
    return parse_items(
        page,
        lambda ev: ev["tag"] == "a" and "result-link" in ev["attrs"].get("class", "").split(),
        lambda ev: ev["tag"] == "td" and "result-snippet" in ev["attrs"].get("class", "").split(),
    )


def parse_ddg_html(page):
    return parse_items(
        page,
        lambda ev: ev["tag"] == "a" and _has(ev, "result__a"),
        lambda ev: _has(ev, "result__snippet"),
    )


def _in(ev, token):
    return any(token in " ".join(c) for c in ev.get("classes", []))


def parse_bing(page):
    """Bing: <li class=b_algo><h2><a href>Title</a></h2><p>snippet</p>"""
    items = []
    mode = None
    for ev in tokens(page):
        if ev["kind"] == "start":
            if (
                ev["tag"] == "a"
                and "h2" in ev.get("tags", [])
                and ev["attrs"].get("href", "").startswith("http")
            ):
                item = {"title": "", "url": _url(ev["attrs"]["href"]), "snippet": ""}
                items.append(item)
                mode = ("title", ev["depth"], item)
            elif ev["tag"] == "p" and _in(ev, "b_algo") and items:
                mode = ("snippet", ev["depth"], items[-1])
        elif ev["kind"] == "end":
            if mode and ev["depth"] < mode[1]:
                mode = None
        elif ev["kind"] == "text" and mode:
            field, open_depth, item = mode
            if ev["depth"] < open_depth:
                mode = None
                continue
            item[field] = append_text(item[field], ev["text"])
    return [i for i in items if i["title"] and i["url"]]


def parse_github_repos(doc):
    out = []
    for it in doc.get("items", []):
        bits = [b for b in (it.get("language"), "%s stars" % it.get("stargazers_count")) if b]
        out.append(
            {
                "title": it.get("full_name") or "",
                "url": it.get("html_url") or "",
                "snippet": (it.get("description") or "")
                + (" · " + " · ".join(bits) if bits else ""),
            }
        )
    return out


def parse_github_issues(doc):
    out = []
    for it in doc.get("items", []):
        repo = (it.get("repository_url") or "").rsplit("/repos/", 1)[-1]
        out.append(
            {
                "title": "%s#%s %s" % (repo, it.get("number"), it.get("title") or ""),
                "url": it.get("html_url") or "",
                "snippet": "%s · %s" % (it.get("state") or "", (it.get("body") or "")[:SNIPPET]),
            }
        )
    return out


def parse_so(doc):
    out = []
    for it in doc.get("items", []):
        tags = ", ".join(it.get("tags") or [])
        out.append(
            {
                "title": "%s (score %s)" % (it.get("title") or "", it.get("score")),
                "url": it.get("link") or "",
                "snippet": ("answered" if it.get("is_answered") else "open")
                + (" · " + tags if tags else ""),
            }
        )
    return out


def parse_hn(doc):
    out = []
    for it in doc.get("hits", []):
        url = it.get("url") or "https://news.ycombinator.com/item?id=%s" % it.get("objectID")
        out.append(
            {
                "title": it.get("title") or it.get("story_title") or "",
                "url": url,
                "snippet": "%s points · %s comments" % (it.get("points"), it.get("num_comments")),
            }
        )
    return out


def parse_arxiv(xml_text):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    out = []
    for e in root.findall("a:entry", ns):
        title = " ".join((e.findtext("a:title", "", ns) or "").split())
        url = (e.findtext("a:id", "", ns) or "").strip()
        summ = " ".join((e.findtext("a:summary", "", ns) or "").split())
        out.append({"title": title, "url": url, "snippet": summ})
    return out


def parse_discourse_search(doc, base):
    out = []
    blurbs = {}
    for p in doc.get("posts") or []:
        if p.get("topic_id") and p.get("blurb"):
            blurbs.setdefault(p["topic_id"], p["blurb"])
    for t in doc.get("topics") or []:
        tid = t.get("id")
        out.append(
            {
                "title": t.get("title") or "",
                "url": "%s/t/%s" % (base.rstrip("/"), tid),
                "snippet": t.get("blurb") or blurbs.get(tid, ""),
            }
        )
    return out


def parse_discourse_topic(doc):
    lines = []
    title = doc.get("title") or ""
    if title:
        lines.append("# " + title)
    for post in (doc.get("post_stream") or {}).get("posts") or []:
        lines.append("")
        lines.append("#%s %s" % (post.get("post_number"), post.get("username") or "?"))
        lines.extend(html_to_text(post.get("cooked") or "").splitlines())
    return lines


class _El:
    """One element of the reading tree, with the numbers the prune pass needs."""

    __slots__ = (
        "attrs",
        "drop",
        "holds_pre",
        "kids",
        "linktext",
        "listing",
        "nlinks",
        "parent",
        "pre",
        "shortlinks",
        "tag",
        "text",
    )

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs
        self.kids = []
        self.parent = parent
        self.drop = False
        self.pre = tag == "pre"
        self.holds_pre = self.pre
        self.text = 0
        self.linktext = 0
        self.nlinks = 0
        self.shortlinks = 0  # links whose own text is under SHORT_LINK characters
        self.listing = False  # every link alone in its own <p>: a catalog, not a farm


class _Tree(HTMLParser):
    """HTML -> element tree, pruning as it goes and keeping <pre> verbatim.

    A tree is needed for the container rules, which are the part of extraction that a flat
    event stream cannot express: "is this div mostly a menu" is a question about the subtree.
    """

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = _El("", {}, None)
        self.stack = [self.root]
        self.skip = 0
        self.in_pre = 0
        self.base = ""  # <base href>, the one thing a relative link needs from <head>

    def handle_starttag(self, tag, attrs):
        if tag == "base" and not self.base:
            href = (dict(attrs).get("href") or "").strip()
            if href:
                self.base = href
        if self.skip:
            if tag not in VOID:
                self.skip += 1
            return
        a = dict(attrs)
        if tag in DROP_TEXT or _cookie_banner(a) or _hidden(a):
            if tag not in VOID:
                self.skip = 1
            return
        close = AUTO_CLOSE.get(tag)
        if close:
            while len(self.stack) > 1 and self.stack[-1].tag in close:
                self.stack.pop()
        el = _El(tag, a, self.stack[-1])
        self.stack[-1].kids.append(el)
        if tag == "pre":
            self.in_pre += 1
        if tag not in VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag, attrs):
        if self.skip or tag in DROP_TEXT:
            return
        self.stack[-1].kids.append(_El(tag, dict(attrs), self.stack[-1]))

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                if tag == "pre":
                    self.in_pre = max(0, self.in_pre - 1)
                del self.stack[i:]
                return

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_pre:
            self.stack[-1].kids.append(data)  # verbatim, newlines and indentation included
            return
        if not data.strip():
            # A whitespace-only node is the space between `</a>` and the next word. It is not
            # text to measure, but dropping it would glue two words together.
            self.stack[-1].kids.append(" ")
            return
        lead = " " if data[:1].isspace() else ""
        trail = " " if data[-1:].isspace() else ""
        self.stack[-1].kids.append(lead + " ".join(data.split()) + trail)


def _cookie_banner(attrs):
    for key in ("class", "id"):
        value = attrs.get(key)
        if value and COOKIE_RE.search(value):
            return True
    return False


def _hidden(attrs):
    """Off-screen or explicitly hidden. `display:none` is in trafilatura's discard expression;
    the screen-reader classes are the same idea under the names the big frameworks use."""
    if "hidden" in attrs or attrs.get("aria-hidden") == "true":
        return True
    style = (attrs.get("style") or "").replace(" ", "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True
    classes = _cls(attrs)
    if classes & HIDDEN_TOKENS:
        return True
    joined = " ".join(classes).lower()
    return any(fragment in joined for fragment in HIDDEN_FRAGMENTS)


def _elements(root):
    """Every element, pre-order, without recursion (a deep page overflows the C stack)."""
    out, stack = [], [root]
    while stack:
        el = stack.pop()
        out.append(el)
        stack.extend(k for k in reversed(el.kids) if isinstance(k, _El))
    return out


def _measure(root, order):
    """Bottom-up text and link statistics, in one pass per level.

    ``linktext`` is the total text under `<a>`; ``shortlinks`` counts the links whose own text is
    a few characters. ``listing`` is the paragraph-listing property trafilatura uses to tell a
    catalog ("every link alone in its own paragraph") from a link farm ("links running together"),
    carried up the tree so no rule needs a second walk.
    """
    for el in reversed(order):
        text = linktext = nlinks = shortlinks = 0
        holds_pre = el.pre
        all_paragraph = True        # every link below this element has a <p> parent
        for kid in el.kids:
            if isinstance(kid, str):
                text += len(kid.strip()) or 1
                continue
            if kid.drop:
                continue
            text += kid.text
            linktext += kid.text if kid.tag == "a" else kid.linktext
            nlinks += 1 if kid.tag == "a" else kid.nlinks
            shortlinks += (1 if 0 < kid.text < SHORT_LINK else 0) if kid.tag == "a" \
                else kid.shortlinks
            if kid.tag == "a":
                all_paragraph = all_paragraph and el.tag == "p"
            else:
                all_paragraph = all_paragraph and kid.listing
            holds_pre = holds_pre or kid.holds_pre
        if el.tag == "a":
            linktext, nlinks = text, 1
            shortlinks = 1 if 0 < text < SHORT_LINK else 0
            all_paragraph = el.parent is not None and el.parent.tag == "p"
        el.text, el.linktext = text, linktext
        el.nlinks, el.shortlinks = nlinks, shortlinks
        el.holds_pre = holds_pre
        el.listing = bool(all_paragraph and el.tag in ("p", "div", "section", "ul", "ol", "body",
                                                      "article", "main", "li", "table", "td"))


def _is_last(el):
    """Whether this is the last element child, which is how trafilatura decides whether a short
    block is a trailing caption (limit 60/300) or a mid-text one (limit 30/100)."""
    parent = el.parent
    if parent is None:
        return True
    kids = [k for k in parent.kids if isinstance(k, _El)]
    return bool(kids) and kids[-1] is el


def _limit(el):
    last = _is_last(el)
    if el.tag == "p":
        return 60 if last else 30
    return 300 if last else 100


def _drop(el):
    el.drop = True
    el.text = el.linktext = 0
    el.nlinks = el.shortlinks = 0
    el.listing = False


def _prune_density(root, order):
    """Container-level boilerplate removal. Three rules, each one a decision with a reason:

    1. one long link that is the whole block is a caption or a card title, not prose;
    2. a short block that is mostly link text, or mostly four-character links, is a menu --
       the second half is what catches a breadcrumb or a file tree, where the words are short;
    3. a large block that is a link farm is a "latest news" sidebar -- unless every link sits
       alone in its own paragraph, which is a catalog and worth keeping.

    A subtree that holds a `<pre>` is never dropped: on a repository page the code fences are the
    useful part, and the sidebar around them is caught by rule 2 instead.
    """
    for el in reversed(order):
        if el.drop or el.holds_pre or el.tag not in DENSITY_TAGS or not el.text or not el.nlinks:
            continue
        if el.nlinks == 1 and el.linktext > LONG_LINK and el.linktext > el.text * 0.9:
            _drop(el)
            continue
        if el.text < _limit(el):
            if el.linktext > el.text * SHORT_RATIO or (
                el.nlinks > 1 and el.shortlinks / el.nlinks > SHORT_RATIO
            ):
                _drop(el)
            continue
        if (
            el.nlinks > FARM_LINKS
            and el.linktext > el.text * FARM_RATIO
            and el.linktext < FARM_AVG_LINK * el.nlinks
            and not el.listing
        ):
            _drop(el)


def _pre_lines(el):
    """A <pre> block, verbatim: no whitespace collapsing, no per-line strip. Only the blank
    lines at the edges of the block go, because they are markup, not code.

    One piece of markup is content here: syntax highlighters (Shiki, Prism, Pygments, and the
    `token-line` divs the npm docs use) put every line of a fence in its own block element
    instead of a newline. Ignoring that joins a whole code block into one line, so a block
    element inside `<pre>` is a line break, and nothing else about it is interpreted. A `span`
    is not a break: highlighters wrap tokens in spans inside the line they belong to.
    """
    parts = []

    def at_line_start():
        return not parts or parts[-1].endswith("\n")

    def newline():
        if not at_line_start():
            parts.append("\n")

    def walk(node):
        for kid in node.kids:
            if isinstance(kid, str):
                parts.append(kid)
            elif not kid.drop:
                block = kid.tag in PRE_BREAK
                if block:
                    newline()
                walk(kid)
                if block:
                    newline()

    walk(el)
    raw = "".join(parts).replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _serialize(root):
    """Tree -> lines. A blank line survives inside `<pre>` and nowhere else."""
    out, cur = [], []

    def flush():
        if cur:
            line = " ".join("".join(cur).split())
            if line:
                out.append((line, False))
            del cur[:]

    def walk(el):
        for kid in el.kids:
            if isinstance(kid, str):
                cur.append(kid)
                continue
            if kid.drop:
                continue
            if kid.pre:
                flush()
                out.extend((line, True) for line in _pre_lines(kid))
                continue
            if kid.tag in BLOCK:
                flush()
                walk(kid)
                flush()
            else:
                walk(kid)

    walk(root)
    flush()
    return [line for line, keep_blank in out if keep_blank or line.strip()]


def _read(page):
    """Page -> the one reading tree both output formats are rendered from.

    Parse, measure, prune by link density, measure again. Deliberately total: a page the parser
    chokes on yields whatever was parsed before the exception, never an exception of ours.
    """
    tree = _Tree()
    try:
        tree.feed(page or "")
        tree.close()
    except Exception:
        pass
    order = _elements(tree.root)
    _measure(tree.root, order)
    _prune_density(tree.root, order)
    _measure(tree.root, order)
    return tree


def html_to_text(page):
    """Page HTML -> reading text, one block per line.

    Three passes and no XPath engine: parse into a tree while dropping the tags and the
    cookie banners, measure the subtree text once, then drop the containers whose link density
    says they are navigation. `<pre>` is emitted verbatim and its ancestors are exempt from
    pruning, so a README's fenced code is never a casualty of a clean-up rule.
    """
    return "\n".join(_serialize(_read(page).root))


# ---------------------------------------------------------------- markdown
#
# The tree keeps what the text renderer discards: the tag name of every node, its attributes
# (`href`, `src`, `alt`, `class`) and the order of its children. Rendering markdown is therefore a
# second walk over the same pruned tree, not a second parser: both formats see the same
# boilerplate removal, and the markdown path cannot drift from the text path on what a page
# contains. `_El` needed no new field for this; `attrs` was always there.

MD_HEADING = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
MD_STRONG = frozenset({"strong", "b"})
MD_EM = frozenset({"em", "i"})
MD_STRIKE = frozenset({"del", "s", "strike"})
MD_CONTAINER = frozenset(
    {
        "div",
        "section",
        "article",
        "main",
        "body",
        "html",
        "center",
        "dl",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
        "li",
        "span",
        "font",
        # A disclosure widget (react.dev's "Deep Dive") holds a heading and paragraphs of its
        # own; flattening it into one paragraph would merge the heading into the prose.
        "details",
        "summary",
    }
)
MD_BLOCK = frozenset(
    {"p", "pre", "blockquote", "table", "hr", "ul", "ol", "dl", "dt", "dd", "caption"}
) | frozenset(MD_HEADING)
MD_LINE_START = re.compile(r"^(#{1,6}\s|[-+*]\s|\d+[.)]\s|>)")
MD_TAG_START = re.compile(r"<(?=[A-Za-z/!?])")


class _Fence(str):
    """A fenced block: verbatim by contract, so the post-pass must not touch it."""


def _text_of(el):
    """Every string under `el`, concatenated, whitespace as the parser stored it."""
    out = []
    for kid in el.kids:
        if isinstance(kid, str):
            out.append(kid)
        elif not kid.drop:
            out.append("\n" if kid.tag == "br" else _text_of(kid))
    return "".join(out)


def _abs_url(href, base):
    """href -> absolute URL, or '' for a scheme a markdown reader must never execute."""
    href = (href or "").strip()
    if not href:
        return ""
    low = href.lower()
    if low.startswith(("javascript:", "data:", "vbscript:")):
        return ""
    if low.startswith(("http://", "https://", "mailto:")):
        return href
    if not base:
        return href
    try:
        return urllib.parse.urljoin(base, href)
    except ValueError:
        return href


def _md_url(url):
    """A URL inside `(...)`: spaces and parens would end the destination early."""
    return url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def _esc(text):
    """Escape the characters that would otherwise become markup. Not `*` or `_`: escaping those
    would turn every `snake_case` identifier in prose into `snake\_case`, which is a worse lie
    than the emphasis it prevents."""
    text = text.replace("\\", "\\\\")
    for ch in ("`", "[", "]"):
        text = text.replace(ch, "\\" + ch)
    return MD_TAG_START.sub(r"\\<", text)


def _code_span(code):
    """Inline code: one more backtick than the longest run inside it, spaces only when needed."""
    code = code.replace("\n", " ")
    runs = [len(r) for r in re.findall(r"`+", code)]
    fence = "`" * (max(runs) + 1 if runs else 1)
    pad = " " if code[:1] == "`" or code[-1:] == "`" else ""
    return fence + pad + code + pad + fence


def _tracking_pixel(attrs):
    """1x1 images, and the names the analytics vendors use. Alt text is the honest signal."""
    if (attrs.get("width") or "").strip() == "1" and (attrs.get("height") or "").strip() == "1":
        return True
    if (attrs.get("alt") or "").strip():
        return False
    src = (attrs.get("src") or "").lower()
    return any(mark in src for mark in ("1x1", "pixel.", "pixel.gif", "beacon", "/track"))


def _wrap(inner, marker):
    """Wrap the non-space core, and leave the boundary spaces outside the markers."""
    core = inner.strip()
    if not core:
        return inner
    lead = inner[: len(inner) - len(inner.lstrip())]
    trail = inner[len(inner.rstrip()) :]
    return lead + marker + core + marker + trail


def _inline(el, base):
    """Children of `el` -> one inline markdown string."""
    out = []
    for kid in el.kids:
        if isinstance(kid, str):
            out.append(_esc(kid))
            continue
        if kid.drop:
            continue
        tag = kid.tag
        if tag == "br":
            out.append("\n")
        elif tag in MD_STRONG:
            out.append(_wrap(_inline(kid, base), "**"))
        elif tag in MD_EM:
            out.append(_wrap(_inline(kid, base), "_"))
        elif tag in MD_STRIKE:
            out.append(_wrap(_inline(kid, base), "~~"))
        elif tag == "code":
            out.append(_code_span(_text_of(kid)))
        elif tag == "a":
            href = _abs_url(kid.attrs.get("href"), base)
            inner = _inline(kid, base).strip()
            if href and inner:
                out.append("[%s](%s)" % (inner, _md_url(href)))
            else:
                out.append(inner)
        elif tag == "img":
            if _tracking_pixel(kid.attrs):
                continue
            src = _abs_url(kid.attrs.get("src") or kid.attrs.get("data-src"), base)
            alt = " ".join((kid.attrs.get("alt") or "").split())
            if src:
                out.append("![%s](%s)" % (_esc(alt), _md_url(src)))
        elif tag == "pre":
            out.append(_fence_block(kid))
        else:
            out.append(_inline(kid, base))
    return "".join(out)


PRE_BREAK = frozenset({"div", "p", "li", "tr", "td", "th", "br", "table", "section"})


def _fence_lang(el):
    """`language-x` or `lang-x`, on the <pre> or on its <code> child.

    Three more spellings are read because the conformance fixtures use them and nothing else:
    MDN writes `class="brush: js notranslate"` (the old SyntaxHighlighter convention) and a
    Discourse fence writes `class="lang-JSON"`. A fence with no language anywhere stays bare,
    which is the honest output for a highlighter that never named one.
    """
    nodes = [el]
    nodes += [k for k in el.kids if not isinstance(k, str) and k.tag == "code"]
    for node in nodes:
        raw = node.attrs.get("class") or ""
        m = re.search(r"brush:\s*([A-Za-z0-9+#_.-]+)", raw)
        if m:
            return m.group(1)
        for token in raw.split():
            for prefix in ("language-", "lang-"):
                if token.startswith(prefix) and len(token) > len(prefix):
                    lang = token[len(prefix) :]
                    if all(c.isalnum() or c in "+#-_." for c in lang):
                        return lang
    return ""


def _fence_block(el):
    """A <pre> as a fenced block. Byte-exact content: `_pre_lines` already drops only the blank
    lines that are markup, and nothing here strips, joins or re-indents what is left."""
    lines = _pre_lines(el)
    if not lines:
        return ""
    body = "\n".join(lines)
    runs = [len(r) for r in re.findall(r"```+", body)]
    fence = "`" * (max(runs) + 1 if runs else 3)
    return _Fence(fence + _fence_lang(el) + "\n" + body + "\n" + fence)


def _md_lines(text, marker=""):
    """A paragraph as markdown lines: line starts that would become a list or a heading are
    escaped, and every line after the first is indented under its container."""
    lines = text.splitlines() or [""]
    out = [marker + MD_LINE_START.sub(r"\\\1", lines[0].strip())]
    pad = " " * len(marker)
    for line in lines[1:]:
        out.append(pad + MD_LINE_START.sub(r"\\\1", line.strip()))
    return out


def _cell(el, base):
    text = _inline(el, base)
    text = " ".join(text.split())
    return text.replace("|", "\\|")


def _md_table(el, base):
    """A data table as a pipe table; a layout table as the blocks it lays out."""
    rows = []

    def collect(node):
        for kid in node.kids:
            if isinstance(kid, str) or kid.drop:
                continue
            if kid.tag == "tr":
                rows.append(kid)
            elif kid.tag in ("thead", "tbody", "tfoot"):
                collect(kid)

    collect(el)
    grid, has_head = [], False
    for row in rows:
        cells = [
            k
            for k in row.kids
            if not isinstance(k, str) and not k.drop and k.tag in ("td", "th")
        ]
        if not cells:
            continue
        has_head = has_head or any(c.tag == "th" for c in cells)
        grid.append([_cell(c, base) for c in cells])
    if not grid:
        return []
    width = max(len(r) for r in grid)
    # A table without a header row is a data table only if its cells are cells: Hacker News, every
    # forum skin and most marketing pages use <table> for layout, and those arrive with empty
    # columns and cells that are nothing but a link. A pipe table there is a grid of blanks, so
    # the table is walked as the blocks it lays out instead.
    if not has_head:
        cells = [c for row in grid for c in row]
        empties = sum(1 for c in cells if not c.strip())
        linked = sum(len(c) for c in cells if "](" in c)
        total = sum(len(c) for c in cells) or 1
        layout = len(grid) < 2 or width < 2 or empties * 4 >= len(cells) or linked * 10 >= total * 6
        if layout:
            inner = []
            _md_children(el, inner, base)
            return inner
    head = grid[0] if has_head else [""] * width
    body_rows = grid[1:] if has_head else grid
    lines = [
        "| " + " | ".join(head + [""] * (width - len(head))) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in body_rows:
        lines.append("| " + " | ".join(row + [""] * (width - len(row))) + " |")
    return ["\n".join(lines)]


def _md_item(li, base):
    """One <li> -> (paragraph lines, [(nested list, ordered)]). Paragraphs inside one item are
    continuation lines, never a blank line: a list that grows a `<p>` must not become loose."""
    paras, nested, buf = [], [], []

    def flush():
        text = "".join(buf).strip()
        del buf[:]
        if text:
            paras.append(text)

    for kid in li.kids:
        if isinstance(kid, str):
            buf.append(_esc(kid))
            continue
        if kid.drop:
            continue
        if kid.tag in ("ul", "ol"):
            flush()
            nested.append((kid, kid.tag == "ol"))
        elif kid.tag in MD_BLOCK:
            flush()
            sub = []
            _md_children(kid, sub, base)
            paras.extend(str(x).strip() for x in sub if str(x).strip())
        else:
            buf.append(_inline(kid, base))
    flush()
    return paras, nested


def _md_list(el, base, depth, ordered):
    out, number = [], 1
    for kid in el.kids:
        if isinstance(kid, str) or kid.drop or kid.tag != "li":
            continue
        marker = "  " * depth + ("%d. " % number if ordered else "- ")
        number += 1
        paras, nested = _md_item(kid, base)
        lines = _md_lines(paras[0] if paras else "", marker)
        pad = " " * len(marker)
        for para in paras[1:]:
            for text_line in para.splitlines() or [""]:
                lines.append(pad + MD_LINE_START.sub(r"\\\1", text_line.strip()))
        for sub, sub_ordered in nested:
            lines.append(_md_list(sub, base, depth + 1, sub_ordered))
        out.append("\n".join(lines))
    return "\n".join(out)


MD_NESTED = frozenset({"pre", "table", "ul", "ol", "blockquote", "hr"}) | frozenset(MD_HEADING)


def _has_block(el):
    """True when a subtree holds a block a paragraph cannot contain.

    HTML forbids a <pre> inside a <p>, and browsers close the <p> for you; a server-rendered React
    page can still hand us the nesting through a serializer, and inlining a fence into a
    paragraph line would break every line after it. So the paragraph is walked as blocks.
    """
    for kid in el.kids:
        if isinstance(kid, str) or kid.drop:
            continue
        if kid.tag in MD_NESTED or _has_block(kid):
            return True
    return False


def _md_children(el, blocks, base):
    """Children of `el` -> markdown blocks (in order)."""
    buf = []

    def flush():
        text = "".join(buf).strip()
        del buf[:]
        if text:
            blocks.append("\n".join(_md_lines(text)))

    for kid in el.kids:
        if isinstance(kid, str):
            # A string here is data, but it can still hold a run of whitespace from an inline
            # element boundary (`<svg/>Deep Dive`), so it is flattened to single spaces. The
            # leading and trailing space are kept: they are the gap between `<a>` and the word
            # after it, and dropping them glues `past` to `|`.
            core = " ".join(kid.split())
            if not core:
                buf.append(" ")
                continue
            lead = " " if kid[:1].isspace() else ""
            trail = " " if kid[-1:].isspace() else ""
            buf.append(lead + _esc(core) + trail)
            continue
        if kid.drop:
            continue
        tag = kid.tag
        if tag in MD_HEADING:
            flush()
            text = " ".join(_inline(kid, base).split())
            if text:
                blocks.append("#" * MD_HEADING[tag] + " " + text)
        elif tag == "p" or tag in ("dt", "dd", "caption"):
            flush()
            if tag == "p" and _has_block(kid):
                _md_children(kid, blocks, base)
                continue
            text = _inline(kid, base).strip()
            if tag == "dt" and text:
                text = "**%s**" % text
            if text:
                blocks.append("\n".join(_md_lines(text)))
        elif tag == "pre":
            flush()
            fence = _fence_block(kid)
            if fence:
                blocks.append(fence)
        elif tag in ("ul", "ol"):
            flush()
            text = _md_list(kid, base, 0, tag == "ol")
            if text:
                blocks.append(text)
        elif tag == "table":
            flush()
            blocks.extend(_md_table(kid, base))
        elif tag == "blockquote":
            flush()
            inner = []
            _md_children(kid, inner, base)
            if inner:
                quoted = "\n".join(
                    "> " + line if line.strip() else ">"
                    for line in "\n\n".join(str(x) for x in inner).splitlines()
                )
                blocks.append(quoted)
        elif tag == "hr":
            flush()
            blocks.append("---")
        elif tag in MD_CONTAINER:
            flush()
            _md_children(kid, blocks, base)
        else:
            buf.append(_inline(kid, base))
    flush()


def html_to_markdown(page, base=""):
    """Page HTML -> markdown, from the same pruned tree `html_to_text` reads.

    `base` resolves relative links and images; when it is empty the page's own `<base href>` is
    used, and a relative URL with neither is left as written rather than guessed.
    """
    tree = _read(page)
    base = base or tree.base or ""
    blocks = []
    _md_children(tree.root, blocks, base)
    parts = []
    for block in blocks:
        text = str(block)
        if not text.strip():
            continue
        if isinstance(block, _Fence):
            parts.append(text)
        else:
            parts.append("\n".join(line.rstrip() for line in text.splitlines()))
    return "\n\n".join(parts).strip("\n") + "\n"


MD_INLINE_LINK = re.compile(r"!?\[([^\]]*)\]\([^)\s]*\)")


def markdown_to_text(markdown):
    """Our own markdown -> plain text, for a route that answers markdown when `--format text`
    was asked for. A small, total reader, not a CommonMark implementation: it strips the markers
    this module emits, and leaves anything it does not recognise alone rather than guessing."""
    out, in_fence = [], False
    for line in (markdown or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            out.append(line)
            continue
        if stripped.startswith(">"):
            line = stripped[1:].lstrip()
            stripped = line.strip()
        m = re.match(r"^#{1,6}\s+(.*)$", stripped)
        if m:
            out.append(m.group(1))
            continue
        m = re.match(r"^(?:[-+*]|\d+[.)])\s+(.*)$", stripped)
        if m:
            out.append(" " * (len(line) - len(line.lstrip())) + m.group(1))
            continue
        if stripped in ("---", "***", "___"):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip().replace("\\|", "|") for c in stripped.strip("|").split("|")]
            if all(re.match(r"^:?-{3,}:?$", c) for c in cells if c):
                continue
            out.append(" ".join(c for c in cells if c))
            continue
        line = MD_INLINE_LINK.sub(r"\1", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"(?<!\w)__(.+?)__(?!\w)", r"\1", line)
        line = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", line)
        line = re.sub(r"~~(.+?)~~", r"\1", line)
        line = re.sub(r"`+\s?(.*?)\s?`+", r"\1", line)
        line = re.sub(r"\\([\\`\[\]<>|])", r"\1", line)
        out.append(line.rstrip())
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n")


def parse_searxng(doc):
    """SearXNG JSON -> (results, unresponsive engine names). Pure, so --self-test can use it."""
    got = []
    for r in doc.get("results") or []:
        url = (r.get("url") or "").strip()
        if not url:
            continue
        primary = r.get("engine") or ""
        names = [e for e in (r.get("engines") or ([primary] if primary else [])) if e]
        if not names:
            names = [primary] if primary else []
        if url.startswith(("https://www.google.com/url", "http://www.google.com/url")):
            url = _url(url)
            if not url:
                continue  # an opaque redirect shell: drop the row rather than print junk
        got.append(
            {
                "title": (r.get("title") or "").strip() or url,
                "url": url,
                "snippet": (r.get("content") or "").strip(),
                "engine": primary,
                "engines": names,
            }
        )
    bad = [str(name) for name, _ in (doc.get("unresponsive_engines") or [])]
    return got, bad


# Suffix per content type: a temp file keeps the type, so a backend that sniffs by extension
# still knows what it was handed.
CT_SUFFIX = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/epub+zip": ".epub",
    "text/html": ".html",
}


DOC_FORMATS = ("pdf", "docx", "epub", "html")


BACKEND_BINS = ("pdftotext", "pandoc", "markitdown")


def have_backends(bins=BACKEND_BINS):
    """{name: path-or-None}. Injected by --self-test so routing can be checked without the binaries."""
    return {name: shutil.which(name) for name in bins}


def looks_like_pdf(raw, ctype=""):
    """Content type first, magic bytes second: some hosts serve a PDF as text/plain."""
    if (ctype or "").lower() == "application/pdf":
        return True
    return raw[:1024].lstrip()[:5] == b"%PDF-"


def document_format(ctype="", name=""):
    """Which kind of document this is, from the content type then the file name. '' = not one."""
    ctype = (ctype or "").split(";")[0].strip().lower()
    if ctype in CT_SUFFIX:
        fmt = CT_SUFFIX[ctype].lstrip(".")
        return "html" if fmt == "html" else fmt
    ext = os.path.splitext((name or "").split("?")[0].split("#")[0])[1].lower()
    return {".pdf": "pdf", ".docx": "docx", ".epub": "epub", ".html": "html", ".htm": "html"}.get(
        ext, ""
    )


def document_backend(fmt, have):
    """First backend that can read this format, in preference order. Pure, so the self-test
    can assert the choice without any binary or network."""
    # pandoc cannot read a PDF at all, so pdftotext leads there and closes the gap
    order = ["pdftotext", "markitdown"] if fmt == "pdf" else ["pandoc", "markitdown"]
    for name in order:
        if have.get(name):
            return name
    return ""


def _run(cmd, input_bytes=None, timeout=120):
    """(text or '', error text or ''). A backend that rejects a file is a fallback, not a crash."""
    try:
        p = subprocess.run(cmd, input=input_bytes, capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return "", "%s: %s" % (type(e).__name__, str(e)[:120])
    out = p.stdout.decode("utf-8", "replace")
    if p.returncode != 0 or not out.strip():
        return "", _last_error(
            p.stderr.decode("utf-8", "replace")
        ) or "exit %d, no output" % p.returncode
    return out, ""


def _last_error(stderr):
    """The line that says what went wrong. A Python traceback's first line is only
    'Traceback (most recent call last):', which tells a caller nothing."""
    lines = [ln.strip() for ln in (stderr or "").splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("Traceback") or ln.startswith('File "') or ln.startswith("^"):
            continue
        return ln[:200]
    return ""


def extract_document(raw, fmt, path, have=None, markdown=False):
    """Document bytes -> (text, backend name). Tries the preferred backend, then the rest.
    Returns ('', reason) when no backend could read it.

    `markdown` asks for pandoc's gfm writer, so a docx or an HTML file keeps its headings, links
    and fences instead of arriving as flat lines. The other two backends have no such writer:
    asking pdftotext for markdown would be a lie about what it extracted."""
    have = have or have_backends()
    tried = []
    order = [document_backend(fmt, have)] + [
        b
        for b in ("pdftotext", "pandoc", "markitdown")
        if have.get(b) and b != document_backend(fmt, have)
    ]
    for name in [b for b in order if b]:
        if name == "pdftotext":
            if fmt != "pdf":
                continue
            text, err = _run(["pdftotext", "-layout", "-", "-"], input_bytes=raw)
        elif name == "pandoc":
            src = ["-f", fmt] if fmt in ("docx", "epub", "html") else []
            text, err = _run(["pandoc", *src, "-t", "gfm" if markdown else "plain", path])
        else:
            text, err = _run(["markitdown", path])
        if text.strip():
            return text, name
        tried.append("%s: %s" % (name, err or "empty output"))
    if not tried:
        return "", "no document backend installed (need pdftotext, pandoc or markitdown)"
    return "", "; ".join(tried)


# Length is the last signal, not the first: a 200 text/html body that carries one text-bearing
# element outside <noscript> is complete whatever its size. example.com is 156 characters of
# real content, and launching a browser for it costs a process, a profile and a second.
JS_SHELL_MIN = 400  # kept as the message threshold for a page with nothing to read


SHELL_MARKS = ("enable javascript", "__next_data__", "__nuxt__", "you need to enable javascript")


NOSCRIPT_DOMINANCE = 0.5  # a noscript block holding most of the text is the page apologizing


def noscript_text(page):
    m = re.findall(r"(?is)<noscript[^>]*>(.*?)</noscript>", page or "")
    return " ".join(" ".join(html_to_text(x).split()) for x in m)


def text_outside_noscript(page):
    """The page's own text with every <noscript> block removed. Empty means nothing to read."""
    stripped = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", page or "")
    return " ".join(html_to_text(stripped).split())


def js_shell_reason(page, text):
    """'' when the page is its own content, else why it looks hollow. Pure: the self-test runs
    it on fixtures and `fetch` uses it to decide whether a browser launch is justified.

    Order is the whole point. A JavaScript-required marker, then a <noscript> that carries the
    page, then the absence of any text outside <noscript>. Length comes last and only describes
    a page that had nothing to read in the first place.
    """
    body = " ".join((text or "").split())
    low = (page or "").lower()
    for mark in SHELL_MARKS:
        if mark in low:
            return "page says %r" % mark
    ns = noscript_text(page or "")
    if ns and len(ns) >= NOSCRIPT_DOMINANCE * max(1, len(body)):
        return "a <noscript> block carries %d of %d chars" % (len(ns), len(body))
    if text_outside_noscript(page or ""):
        return ""
    if len(body) < JS_SHELL_MIN:
        return "only %d chars of text" % len(body)
    return "no text outside <noscript>"


SKIP_EXT = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".css",
    ".js",
    ".mjs",
    ".zip",
    ".gz",
    ".tar",
    ".mp4",
    ".mp3",
    ".webm",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".rss",
    ".atom",
    ".json",
)


def _loc_list(xml_text):
    """Every <loc> in a sitemap, whatever the namespace. Regex is enough and never raises on
    a slightly broken document, which a crawler forensics tool sees a lot of."""
    out = [" ".join(m.split()) for m in re.findall(r"(?is)<loc[^>]*>(.*?)</loc>", xml_text or "")]
    return [
        u.replace("&amp;", "&").strip()
        for u in out
        if u.strip().startswith(("http://", "https://"))
    ]


def parse_sitemap(xml_text):
    """(urls, is_index). An index lists other sitemaps; a plain sitemap lists pages."""
    low = (xml_text or "").lower()
    is_index = "<sitemapindex" in low
    urls = _loc_list(xml_text)
    if not urls and not is_index:
        # a plain-text sitemap: one url per line
        urls = [
            ln.strip()
            for ln in (xml_text or "").splitlines()
            if ln.strip().startswith(("http://", "https://"))
        ]
    return urls, is_index


def parse_robots_sitemaps(text):
    """Sitemap: lines from robots.txt, case-insensitive per RFC 9309."""
    out = []
    for line in (text or "").splitlines():
        m = re.match(r"(?i)^\s*sitemap\s*:\s*(\S+)", line)
        if m:
            out.append(m.group(1))
    return out


def parse_llms_txt(text):
    """Absolute urls out of an llms.txt link list, `[title](url)` or bare."""
    out = []
    for m in re.finditer(r"\(\s*(https?://[^)\s]+)\s*\)|^\s*(https?://\S+)", text or "", re.M):
        out.append((m.group(1) or m.group(2)).rstrip(".,;"))
    return out


def _gunzip_if_needed(raw):
    return gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw


def same_origin(url, base):
    a, b = urllib.parse.urlparse(url), urllib.parse.urlparse(base)
    return (
        a.scheme in ("http", "https")
        and a.scheme == b.scheme
        and a.netloc.lower() == b.netloc.lower()
    )


def crawlable(url):
    if not url or url.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return False
    path = urllib.parse.urlparse(url).path.lower()
    return not path.endswith(SKIP_EXT)


def page_links(page, base):
    """Absolute, fragment-free, de-duplicated links from one page, in document order."""
    out, seen = [], set()
    for ev in tokens(page, DROP_RESULTS):
        if ev["kind"] != "start" or ev["tag"] != "a":
            continue
        href = (ev["attrs"].get("href") or "").strip()
        if not href or href.startswith("#"):
            continue  # a pure fragment points at the page we are already on
        url = urllib.parse.urljoin(base, href).split("#")[0]
        if not url.startswith(("http://", "https://")) or not crawlable(url):
            continue
        key = url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(url)
    return out


def filter_links(links, base, origin_lock=True):
    return [u for u in links if crawlable(u) and (not origin_lock or same_origin(u, base))]


def page_title(page):
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", page or "")
    if m:
        return " ".join(m.group(1).split())[:120]
    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", page or "")
    return " ".join(html_to_text(m.group(1)).split())[:120] if m else ""


def map_sources(url):
    """Candidate sitemap documents for a site, cheapest and most likely first."""
    p = urllib.parse.urlparse(url)
    root = "%s://%s" % (p.scheme or "https", p.netloc)
    return [
        root + "/sitemap.xml",
        root + "/sitemap_index.xml",
        root + "/robots.txt",
        root + "/llms.txt",
    ]
