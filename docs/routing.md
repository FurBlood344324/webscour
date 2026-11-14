# Routing: which source for which question

The measurement page. Every endpoint named here was measured on this machine (2026-11-14) with
`webscour/0.1`, no key, and the status in the table is what it returned. The same decisions, written
for a model in the middle of a task, are `skill/references/choosing-a-source.md` (routing),
`skill/references/anti-bot-and-failures.md` (the walls) and `skill/references/saving-output.md`
(`./.webscour/`). When the two disagree, this page is the evidence and the skill is the instruction:
fix the skill.

`wsc` is the whole interface: `wsc search`, `wsc fetch`, `wsc pdf`, `wsc map`, `wsc crawl`.

## 1. Decision table

| The question is | Run | Why this and not the general path |
|---|---|---|
| How do I use this library or function? | `wsc search "requests session retries" --source github` then `--source so` | Two index types: code in repos, answers in Q&A. Both beat a web search that returns blog posts from 2015. |
| What does this concept mean? | `wsc search "consistent hashing" --source wikipedia` | A definition, not a result page. One call, 0.5 KB, no scraping. |
| Find papers on a topic | `wsc search "<topic>" --source arxiv-api`, then `openalex`, then `crossref` | `arxiv-api` is full text and recent; `openalex` adds citation counts and venues; `crossref` is the DOI record of record. |
| Medical or biological | `wsc search "<topic>" --source pubmed`, then `europepmc` | PubMed is the index medicine cites; Europe PMC adds preprints and open-access status. |
| Is this package maintained, and what version? | `wsc search "<name>" --source pypi`, `npm`, `crates` | Exact registry JSON: version, release date, deprecation, download counts. Zero guesswork. |
| What happened today? | `wsc search "<subject>" --fresh --limit 10` | Google News RSS, BBC and SearXNG's news category, sorted by publication date. The general index is not freshness-ranked. |
| This link is dead | `wsc fetch "<url>" --archive` | The Wayback CDX API resolves the newest 200 snapshot; the plain path would just report 404. |
| What do practitioners say? | `wsc search "<topic>" --source devto`, then `hn` | dev.to is working code; Hacker News is discussion. `lobsters` is not a row: it answers 404 on `search.json` and 200 with an Anubis challenge on the page (see section 4). |
| General web | `wsc search "<query>"` | The local SearXNG, paced, with the scrapers as fallback. The default when no row above fits. |
| A page I will read twice | `wsc fetch "<url>" --save`, then `wsc cache get "<url>"` | Second read is a file, not a second download, and the index says when it was fetched. |
| A paper or manual as text | `wsc pdf "<url>"` | Routes through pdftotext/pandoc, not through HTML extraction that would eat the columns. |

Two flags change shape rather than source: `--format markdown` keeps headings, links and fences
(the right default for a page you will quote), and `--source discourse:<host>` reaches a forum
that the general index does not crawl.

## 2. Do not

- Do not `crawl` for a single page. `crawl` is for a section you have not enumerated; `fetch` is
  for a page you already have.
- Do not `search` for a URL you already hold. One `fetch` is cheaper than a query plus a click.
- Do not fetch the same page twice without `--save`. The second read is free; the second download
  is not, and neither is the second copy in the context.
- Do not run `--category` when the plain path answers. It measured 1.1 s to 6.1 s in one session
  against 1.2 s to 6.1 s plain, so the honest claim is "unpredictable, and no scraper fallback".
- Do not use a specialised source for a question it does not index: `pypi` is exact-match, not a
  search box, and `crossref` has no full text.
- Do not `--render` first. It costs a browser launch; it is the answer to a hollow page, not a
  default.

## 3. Cost table

Approximate, one query, 2 rows, measured on one machine over a residential link. Latency dominates
what a sequence of calls costs; payload dominates what an answer costs.

| Source | Latency | Payload | Note |
|---|---|---|---|
| Wikipedia API | 0.4-0.6 s | 0.5-2 KB | the whole answer in one call |
| npm registry | 0.3-0.4 s | 0.1-4 KB | `/<name>/latest` is small; `/<name>` is megabytes |
| dev.to | 0.3 s | 0.3-0.7 KB | tag-based, one word queries |
| BBC RSS | 0.3-0.4 s | 0.6 KB | one outlet's latest, newest first |
| PyPI | 0.4 s | 0.1-0.2 KB | exact package only |
| crates.io | 0.7-0.9 s | 0.2 KB | 403 without a contact User-Agent |
| Crossref | 0.5-0.7 s | 0.2 KB | DOI records, no abstracts |
| arxiv-api | 0.5-0.6 s | 0.6 KB | Atom XML, published dates included |
| OpenAlex | 0.7 s | 0.3 KB | citation counts; a free key lifts the daily budget |
| PubMed | 0.3-0.9 s | 0.4 KB | two calls: esearch then esummary |
| Google News RSS | 0.5-0.8 s | 0.8 KB | freshness rows, real dates |
| Wayback CDX | 1.0 s | 0.3 KB | plus one request for the snapshot body |
| Europe PMC | 0.7-11 s | 0.4 KB | the one slow endpoint; 11 s observed twice |
| SearXNG, plain | 1.2-6.1 s | 0.9-1.5 KB | every upstream at once; the 0.2 s figure was one lucky run |
| SearXNG, `--category` | 1.1-6.1 s | 1.3 KB | opt-in; measured both ends in one session |
| `fetch` HTML | 0.2-1 s | 1-60 KB | plus a browser launch if hollow |
| `fetch --render` | 1-10 s | 1-60 KB | lightpanda launch, then the network |

Cheapest first: a package registry, then Wikipedia, then a news feed, then a general search, then
a page fetch, then a render.

## 4. Evaluated and rejected

Same machine, same day, same User-Agent (`webscour/0.1`). Listed so nobody measures them again
this quarter. Status is what came back, not what a blog said it would.

| Source | Status | Why it cannot ship |
|---|---|---|
| Reddit (`reddit.com/search.json`) | 403 | Blocks the JSON API from a desktop client; the page is a login wall. |
| Semantic Scholar (`api.semanticscholar.org`) | 429 | Needs a key for a shared budget. `openalex` covers the same ground keyless. |
| GDELT (`api.gdeltproject.org`) | 429 | One request per five seconds, enforced by a plain-text 429. Not a per-call cost a tool may impose. |
| Mojeek (`mojeek.com/search`) | 200, bot wall | A 5 KB challenge page: "JavaScript is required". No results in it. |
| Marginalia (`search.marginalia.nu`) | 302 to `marginalia-search.com`; `old-search.marginalia.nu` answers 200 | The new host redirects, and the old page's text is fragmented into one token per segment; extracting it costs more than it returns. |
| Lobsters (`lobste.rs/search.json`) | 404 | There is no search endpoint; `lobste.rs/hottest.json` answers 200 with 12 KB, and it duplicates what `hn` already answers. |
| Openverse (`api.openverse.org`) | 200, no key needed | Works, but it is CC-licensed images only. A text tool has no row for it; revisit if `--category images` proves insufficient. |
| r.jina.ai and similar proxies | 200, CAPTCHA page | Returns the challenge, needs 20 requests/min of their budget, and would send the URL to a third party. Rejected on the privacy claim alone. |

Two notes for the next person: an arXiv `abs` page that has no `html` rendering is not a route
failure, it is an old paper; and `web.archive.org` refuses a browser-shaped User-Agent with 429
while answering the honest `webscour/0.1 (+...)` one, so the archive client sets its own.
