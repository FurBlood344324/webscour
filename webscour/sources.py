"""The keyless sources: one free endpoint per kind of question.

Each source is two things, deliberately in one place: a pure parser (dict/XML in, rows out) and
the one request that feeds it. The parsers are pure so `--self-test` and the unit tests exercise
them with no network, which is the same rule `extract.py` follows for the HTML parsers.

Every endpoint here was measured before it was added: no key, no login, a 200 and a body with
the fact in it. The sources that failed that test (Reddit 403, Semantic Scholar 429 without a
key, GDELT 429, Openverse 403, Mojeek 403, Marginalia's bot wall) are listed in
`docs/routing.md` so nobody spends an afternoon rediscovering them.

Row shape is the same everywhere: `title`, `url`, `snippet`, plus `published` (ISO date) when the
source really carries a publication date. Nothing invents one: a Wikipedia article has no
publication date, and pretending its last-edit timestamp is one would corrupt `--fresh`.
"""

import html
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET

from .backends import FetchError, _q, http
from .extract import SNIPPET

JSON_ACCEPT = "application/json"

# The names `search --source` accepts. `arxiv` is the API route already (export.arxiv.org), so
# `arxiv-api` is an alias for it rather than a second implementation: there is one arXiv source
# and the alias exists so a caller who reads the endpoint table finds the name they expect.
API_SOURCES = (
    "wikipedia",
    "openalex",
    "crossref",
    "arxiv",
    "arxiv-api",
    "europepmc",
    "pubmed",
    "pypi",
    "npm",
    "crates",
    "devto",
    "wayback",
    "googlenews",
    "bbc",
)

FRESH_SOURCES = ("googlenews", "bbc")

# The SearXNG categories passed through as `--category`. Opt-in and never a default: a category
# changes which engines answer, so it changes the answer, and a caller who did not ask for that
# should not get it. Latency on this box ranged from about 1 s to about 6 s for both shapes on the
# same afternoon (the plain path waiting out the server's 6 s cap when an engine hangs), so a
# category is not reliably cheaper or dearer than the plain path; see `docs/routing.md`.
CATEGORIES = ("general", "it", "science", "news", "images", "files", "social")

# Every name `--source` accepts, in one string: the error message and the help text are the same
# list, so a name can never be accepted by the parser and missing from the message that lists it.
SOURCES_HELP = "web|github|so|hn|discourse:<base>|" + "|".join(
    s for s in API_SOURCES if s != "arxiv-api"
)


def _clip(text, n=SNIPPET):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "..."


def _row(title, url, snippet, published=""):
    row = {"title": _clip(title, 300), "url": url, "snippet": _clip(snippet)}
    if published:
        row["published"] = published
    return row


def _full_date(value):
    """True only for a value that carries a month and a day, not just a year."""
    return bool(re.match(r"^\d{4}[-/]\d{2}", str(value or "")))


def _iso(value):
    """The many ways these APIs spell a date, to YYYY-MM-DD. Empty when it cannot be read."""
    value = (value or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.match(r"^(\d{4})/(\d{2})/(\d{2})", value)
    if m:
        return "%s-%s-%s" % m.groups()
    return ""


# ---------------------------------------------------------------- pure parsers


def parse_wikipedia(doc):
    """MediaWiki list=search. The snippet carries <span class="searchmatch"> highlight markup."""
    out = []
    for it in (doc.get("query") or {}).get("search") or []:
        title = it.get("title") or ""
        snippet = re.sub(r"<[^>]+>", "", it.get("snippet") or "")
        slug = urllib.parse.quote((title or "").replace(" ", "_"), safe="()_,-")
        out.append(_row(title, "https://en.wikipedia.org/wiki/" + slug, snippet))
    return out


def parse_openalex(doc):
    out = []
    for w in doc.get("results") or []:
        year = w.get("publication_year")
        venue = ""
        loc = w.get("best_oa_location") or {}
        if isinstance(loc, dict):
            venue = (
                loc.get("source", {}).get("display_name")
                if isinstance(loc.get("source"), dict)
                else ""
            )
        title = w.get("display_name") or w.get("title") or ""
        bits = [str(year)] if year else []
        if venue:
            bits.append(venue)
        bits.append("%s citations" % (w.get("cited_by_count") or 0))
        url = w.get("doi") or w.get("id") or ""
        if url.startswith("https://doi.org/https://"):
            url = url[8:]
        # A year is not a publication date: `2016` cannot order against `2026-11-14` in a
        # sorted list, so it goes into the snippet where a reader can use it and `published`
        # stays empty. Only a full date earns the field.
        out.append(
            _row(title, url, " · ".join(bits), _iso(str(year or "")) if _full_date(year) else "")
        )
    return out


def parse_crossref(doc):
    out = []
    for it in (doc.get("message") or {}).get("items") or []:
        title = (it.get("title") or [""])[0]
        if not title:
            continue
        parts = it.get("issued", {}).get("date-parts") or [[]]
        date = parts[0] if parts and isinstance(parts[0], list) else []
        published = "-".join("%02d" % p for p in date[:3]) if len(date) >= 3 else ""
        venue = (it.get("container-title") or [""])[0]
        bits = [venue] if venue else []
        if it.get("is-referenced-by-count"):
            bits.append("%s citations" % it["is-referenced-by-count"])
        url = it.get("URL") or ("https://doi.org/" + it["DOI"] if it.get("DOI") else "")
        out.append(_row(title, url, " · ".join(bits), published))
    return out


def parse_arxiv_api(xml_text):
    """Atom, with the one field `parse_arxiv` drops: <published>."""
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in ET.fromstring(xml_text).findall("a:entry", ns):
        out.append(
            _row(
                e.findtext("a:title", "", ns),
                (e.findtext("a:id", "", ns) or "").strip(),
                e.findtext("a:summary", "", ns),
                _iso(e.findtext("a:published", "", ns)),
            )
        )
    return out


def parse_europepmc(doc):
    out = []
    for it in (doc.get("resultList") or {}).get("result") or []:
        title = it.get("title") or ""
        if it.get("source") == "PPR" and not title:
            continue
        if it.get("doi"):
            url = "https://doi.org/" + it["doi"]
        elif it.get("pmid"):
            url = "https://pubmed.ncbi.nlm.nih.gov/%s/" % it["pmid"]
        else:
            url = "https://europepmc.org/article/%s/%s" % (it.get("source"), it.get("id"))
        bits = [it.get("journalTitle") or "", it.get("authorString") or ""]
        out.append(
            _row(
                title,
                url,
                " · ".join(b for b in bits if b),
                _iso(it.get("firstPublicationDate") or it.get("pubYear") or ""),
            )
        )
    return out


def parse_pubmed(doc):
    """esummary.fcgi: `result.uids` is the order, the same keys also hold the records."""
    result = doc.get("result") or {}
    out = []
    for uid in result.get("uids") or []:
        it = result.get(uid) or {}
        title = (it.get("title") or "").rstrip(".")
        if not title:
            continue
        bits = [it.get("fulljournalname") or it.get("source") or ""]
        out.append(
            _row(
                title,
                "https://pubmed.ncbi.nlm.nih.gov/%s/" % uid,
                " · ".join(b for b in bits if b),
                _pubmed_date(it),
            )
        )
    return out


def _pubmed_date(record):
    """`2026 Nov 13` and `2026 Nov` are the two shapes esummary uses."""
    m = re.match(
        r"^(\d{4})\s+([A-Z][a-z]{2})(?:\s+(\d{1,2}))?", (record.get("pubdate") or "").strip()
    )
    if not m:
        return ""
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    month = months.index(m.group(2)) + 1 if m.group(2) in months else 1
    return "%s-%02d-%02d" % (m.group(1), month, int(m.group(3) or 1))


def parse_pypi(doc):
    info = doc.get("info") or {}
    files = (doc.get("releases") or {}).get(info.get("version") or "") or []
    uploaded = ""
    if files:
        uploaded = (files[0].get("upload_time_iso_8601") or files[0].get("upload_time") or "")[:10]
    bits = [info.get("version") or "?", info.get("summary") or ""]
    if info.get("requires_python"):
        bits.append("python " + info["requires_python"])
    if uploaded:
        bits.append("released " + uploaded)
    return [
        _row(
            info.get("name") or "",
            info.get("project_url") or info.get("package_url") or "",
            " · ".join(b for b in bits if b),
            uploaded,
        )
    ]


def parse_npm(doc):
    bits = [doc.get("version") or "?", doc.get("description") or ""]
    if doc.get("license"):
        bits.append(doc["license"] if isinstance(doc["license"], str) else "see license")
    if (doc.get("engines") or {}).get("node"):
        bits.append("node " + doc["engines"]["node"])
    if doc.get("deprecated"):
        bits.append("DEPRECATED: " + str(doc["deprecated"]))
    repo = doc.get("repository") or {}
    url = repo.get("url") if isinstance(repo, dict) else ""
    url = (url or doc.get("homepage") or "").replace("git+", "").replace(".git", "")
    return [_row(doc.get("name") or "", url, " · ".join(b for b in bits if b))]


def parse_crates(doc):
    crate = doc.get("crate") or {}
    versions = doc.get("versions") or []
    bits = [crate.get("max_version") or "?", crate.get("description") or ""]
    if crate.get("recent_downloads"):
        bits.append("%s downloads (90d)" % crate["recent_downloads"])
    updated = (crate.get("updated_at") or "")[:10]
    if updated:
        bits.append("updated " + updated)
    if versions and versions[0].get("yanked"):
        bits.append("latest yanked")
    return [
        _row(
            crate.get("name") or "",
            crate.get("repository") or crate.get("homepage") or "",
            " · ".join(b for b in bits if b),
            updated,
        )
    ]


def parse_devto(doc):
    out = []
    for it in doc if isinstance(doc, list) else []:
        bits = []
        if it.get("reading_time_minutes"):
            bits.append("%d min read" % it["reading_time_minutes"])
        if it.get("positive_reactions_count"):
            bits.append("%d reactions" % it["positive_reactions_count"])
        tags = [t for t in (it.get("tag_list") or []) if isinstance(t, str)]
        if tags:
            bits.append(", ".join(tags[:5]))
        out.append(
            _row(
                it.get("title") or "",
                it.get("url") or "",
                " · ".join(bits),
                _iso(it.get("published_at") or ""),
            )
        )
    return out


def parse_wayback(doc, url=""):
    """CDX JSON: [[timestamp, original, statuscode], ...] with a header row."""
    rows = doc if isinstance(doc, list) else []
    out = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 2:
            continue
        stamp, original = row[0], row[1]
        if stamp in ("timestamp", "urlkey"):
            continue
        out.append(
            _row(
                "%s (%s)" % (original, stamp[:8]),
                "https://web.archive.org/web/%sid_/%s" % (stamp, original),
                "archived %s-%s-%s, status %s"
                % (stamp[:4], stamp[4:6], stamp[6:8], row[2] if len(row) > 2 else "?"),
                _iso("%s-%s-%s" % (stamp[:4], stamp[4:6], stamp[6:8])),
            )
        )
    return out


def parse_rss(xml_text):
    """RSS 2.0 and Atom, the two shapes a news feed uses. Returns rows with a real date."""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    for item in root.iter():
        tag = item.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        fields = {child.tag.split("}")[-1]: (child.text or "") for child in item}
        title = html.unescape(fields.get("title") or "")
        link = fields.get("link") or ""
        if not link:
            for child in item:
                if child.tag.split("}")[-1] == "link" and child.get("href"):
                    link = child.get("href")
                    break
        published = _iso(
            fields.get("pubDate") or fields.get("published") or fields.get("updated") or ""
        )
        if not published:
            published = _rfc822_date(fields.get("pubDate") or "")
        source = html.unescape(fields.get("source") or "")
        if source and title.endswith(" - " + source):
            title = title[: -(len(source) + 3)].rstrip()
        snippet = re.sub(r"<[^>]+>", " ", fields.get("description") or fields.get("summary") or "")
        snippet = html.unescape(snippet).replace("\xa0", " ")
        snippet = " ".join(snippet.split())
        # Google News repeats the headline and then the outlet inside <description>. Left alone
        # that prints the title three times per row and reads as a bug in the output.
        if title and snippet.lower().startswith(title.lower()):
            snippet = snippet[len(title) :].lstrip(" -|:")
        for repeat in (title, source):
            if repeat and snippet.lower().endswith(repeat.lower()):
                snippet = snippet[: -len(repeat)].rstrip(" -|:")
        snippet = " ".join(snippet.split())
        if source:
            snippet = "%s · %s" % (source, snippet) if snippet else source
        out.append(_row(title, link, snippet, published))
    return out


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _rfc822_date(text):
    """`Sat, 14 Nov 2026 19:43:32 GMT` -> 2026-11-14. Empty when it is not that shape."""
    m = re.search(r"(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{4})", text or "")
    if not m or m.group(2) not in _MONTHS:
        return ""
    return "%s-%02d-%02d" % (m.group(3), _MONTHS.index(m.group(2)) + 1, int(m.group(1)))


# ---------------------------------------------------------------- the requests


def wikipedia(query, limit):
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json"
        "&srlimit=%d&srsearch=%s" % (limit, _q(query))
    )
    return parse_wikipedia(json.loads(http(url, accept=JSON_ACCEPT)[0]))[:limit]


def openalex(query, limit):
    url = "https://api.openalex.org/works?per-page=%d&search=%s" % (limit, _q(query))
    return parse_openalex(json.loads(http(url, accept=JSON_ACCEPT)[0]))[:limit]


def crossref(query, limit):
    url = "https://api.crossref.org/works?rows=%d&query=%s" % (limit, _q(query))
    return parse_crossref(json.loads(http(url, accept=JSON_ACCEPT)[0]))[:limit]


def arxiv_api(query, limit):
    url = "https://export.arxiv.org/api/query?max_results=%d&search_query=%s" % (
        limit,
        urllib.parse.quote("all:" + query),
    )
    return parse_arxiv_api(http(url)[0])[:limit]


def europepmc(query, limit):
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=%d&query=%s"
        % (
            limit,
            _q(query),
        )
    )
    return parse_europepmc(json.loads(http(url, accept=JSON_ACCEPT)[0]))[:limit]


def pubmed(query, limit):
    """Two calls, because esearch returns ids and esummary returns the facts."""
    ids = json.loads(
        http(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"
            "&retmode=json&retmax=%d&term=%s" % (limit, _q(query)),
            accept=JSON_ACCEPT,
        )[0]
    )
    found = ((ids.get("esearchresult") or {}).get("idlist") or [])[:limit]
    if not found:
        return []
    summary = json.loads(
        http(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed"
            "&retmode=json&id=%s" % ",".join(found),
            accept=JSON_ACCEPT,
        )[0]
    )
    return parse_pubmed(summary)[:limit]


def pypi(query, limit):
    name = urllib.parse.quote(query.strip().split()[0].lower(), safe="")
    return parse_pypi(
        json.loads(http("https://pypi.org/pypi/%s/json" % name, accept=JSON_ACCEPT)[0])
    )


def npm(query, limit):
    name = urllib.parse.quote(query.strip().split()[0].lower(), safe="")
    return parse_npm(
        json.loads(http("https://registry.npmjs.org/%s/latest" % name, accept=JSON_ACCEPT)[0])
    )


def crates(query, limit):
    name = urllib.parse.quote(query.strip().split()[0].lower(), safe="")
    return parse_crates(
        json.loads(
            http(
                "https://crates.io/api/v1/crates/%s" % name,
                accept=JSON_ACCEPT,
                # crates.io answers 403 to a client with no contact story in its UA
                timeout=20,
            )[0]
        )
    )


def devto(query, limit):
    """dev.to has tags, not full text: the query becomes one tag (`python`, `asyncio`)."""
    tag = re.sub(r"[^a-z0-9]", "", query.strip().lower().split()[0]) or "webdev"
    url = "https://dev.to/api/articles?per_page=%d&tag=%s" % (limit, urllib.parse.quote(tag))
    return parse_devto(json.loads(http(url, accept=JSON_ACCEPT)[0]))[:limit]


def wayback(query, limit):
    """The query is a URL or a host: CDX lists snapshots, newest last."""
    target = urllib.parse.quote(query.strip(), safe="")
    url = (
        "https://web.archive.org/cdx/search/cdx?url=%s&output=json&limit=-%d"
        "&fl=timestamp,original,statuscode&filter=statuscode:200" % (target, limit)
    )
    body = http(url, accept=JSON_ACCEPT)[0].strip() or "[]"
    return parse_wayback(json.loads(body) if body else [])[:limit]


def googlenews(query, limit):
    url = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q=%s" % _q(query)
    return parse_rss(http(url)[0])[:limit]


def bbc(query, limit):
    """One outlet, no query facility: the query filters its latest feed, newest first.

    A query with no match in the feed returns the newest items rather than nothing, because
    "what happened today" is the question this source answers and the filter is a convenience.
    """
    rows = parse_rss(http("https://feeds.bbci.co.uk/news/rss.xml")[0])
    rows.sort(key=lambda r: r.get("published") or "", reverse=True)
    terms = [t.lower() for t in re.findall(r"[a-z0-9]{3,}", query.lower())]
    if terms:
        hit = [
            r for r in rows if any(t in (r["title"] + " " + r["snippet"]).lower() for t in terms)
        ]
        if hit:
            rows = hit
    return rows[:limit]


FETCHERS = {
    "wikipedia": wikipedia,
    "openalex": openalex,
    "crossref": crossref,
    "arxiv": arxiv_api,
    "arxiv-api": arxiv_api,
    "europepmc": europepmc,
    "pubmed": pubmed,
    "pypi": pypi,
    "npm": npm,
    "crates": crates,
    "devto": devto,
    "wayback": wayback,
    "googlenews": googlenews,
    "bbc": bbc,
}


def fresh(query, limit, since="", searx=None):
    """The freshness sources, merged and sorted by publication date, newest first.

    `searx` is a callable(query, limit) that answers the SearXNG `news` category, injected so this
    module does not import the search backend and the caller can leave it out on a box without it.
    """
    rows = []
    for name in FRESH_SOURCES:
        try:
            rows.extend(FETCHERS[name](query, limit))
        except (FetchError, ValueError, ET.ParseError) as e:
            from .backends import vwarn

            vwarn("fresh: %s: %s" % (name, e))
    if searx is not None:
        try:
            rows.extend(searx(query, limit))
        except FetchError as e:
            from .backends import vwarn

            vwarn("fresh: searxng news: %s" % e)
    seen, merged = set(), []
    for row in rows:
        if not row.get("published"):
            continue
        if since and row["published"] < since:
            continue
        key = row["url"].split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        merged.append(row)
    merged.sort(key=lambda r: r["published"], reverse=True)
    return merged[:limit]
