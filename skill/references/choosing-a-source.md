# Choosing a source

One question, one verb. Read this when you have a question but not a URL, or a URL and a doubt about
which verb owns it.

## Question shape to command

| The question | Command | Why this one |
|---|---|---|
| something exists, source unknown | `wsc search "<q>" --limit 5` | rows are title, URL, 200-char snippet |
| code, a repo, an implementation | `wsc search "<q>" --source github` | GitHub API: repos and issues, 10 req/min |
| an error message, a "why does X do Y" | `wsc search "<q>" --source so` | Stack Exchange API, question bodies |
| what practitioners are saying | `wsc search "<q>" --source hn` | Hacker News, ranked by points |
| a paper on a topic | `wsc search "<q>" --source arxiv` | arXiv Atom API, title + abstract |
| a paper's full text | `wsc fetch https://arxiv.org/abs/<id>` | route `arxiv` reads the paper's HTML rendering; an older paper with no HTML falls back to the abs page |
| a paper that only exists as a PDF | `wsc pdf https://arxiv.org/pdf/<id>` | the PDF path, 20 000 chars by default |
| citation metadata, a DOI, a venue | `wsc search "<q>" --source crossref` | Crossref works |
| scholarly graph, citation counts | `wsc search "<q>" --source openalex` | OpenAlex works |
| biomedical, clinical | `wsc search "<q>" --source pubmed` | PubMed esummary |
| biomedical, preprints and open access | `wsc search "<q>" --source europepmc` | Europe PMC; the one endpoint that has timed out at 15 s |
| what a library's API looks like | `wsc search httpx --source pypi` | PyPI JSON: version, summary, project URLs |
| the same for JS or Rust | `wsc search <name> --source npm` / `--source crates` | registry metadata |
| today's news on X | `wsc search "<q>" --fresh` | Google News + BBC RSS + SearXNG news, date-sorted |
| a blog post feed | `wsc search "<q>" --source devto` | dev.to articles |
| what this URL used to say | `wsc search <url> --source wayback` | CDX list; the query must be a URL or a host |
| a vendor forum thread | `wsc search "<q>" --source discourse:<host>` | e.g. `discourse:https://forums.developer.nvidia.com` |
| a page I will read and quote | `wsc fetch <url> --format markdown` | headings, links and fences survive |
| a page I will grep | `wsc fetch <url> --grep <re>` | prints +/-1 line around each match |
| a page I will read twice | `wsc fetch <url> --save` | second read is a cache hit |
| a doc set, one section | `wsc map <url>` then `wsc crawl <url> --limit N` | see `crawling-without-hurting.md` |
| is this machine even able | `wsc doctor` | ends in one VERDICT line |

`search` caps `--limit` at 30. `--source web` is the only one that takes `--category`
(`general, it, science, news, images, files, social`), because a category is a SearXNG parameter and
no scraper can be asked for one. `search` takes no `-v`; it prints a fixed report. `--source` names are
checked against the FETCHERS table, so a typo is exit 2 with the valid list on stderr.

## What each route costs

Measured 2026-11-14 on this machine, one query of 5 rows, warm. Latency is wall clock including the
1 s shared pace; payload is stdout for that answer.

| Route | Latency | Payload |
|---|---|---|
| `--source arxiv` | 0.3 s | 1.6 KB |
| `--source devto` | 0.3 s | 1.4 KB |
| `--source pypi` | 0.4 s | 0.14 KB |
| `--source bbc` | 0.4 s | 1.5 KB |
| `--source so` | 0.45 s | 1.0 KB |
| `--source europepmc` | 0.5 s | 1.2 KB |
| `--source wikipedia` | 0.5 s | 1.1 KB |
| `--source npm` | 0.5 s | 0.13 KB |
| `--source hn` | 0.6 s | 0.64 KB |
| `--source googlenews` | 0.65 s | 2.1 KB |
| `--source openalex` | 0.8 s | 0.77 KB |
| `--source crossref` | 0.84 s | 0.74 KB |
| `--source crates` | 0.86 s | 0.17 KB |
| `--source pubmed` | 1.0 s | 1.1 KB |
| `--source github` | 1.3 s | 1.1 KB |
| `--source web` (local SearXNG) | 2-6 s | 0.9-1.5 KB |
| `--source web --category it` | 1-6 s, unpredictable | 1.3 KB |
| `wsc fetch <page>` | 0.3-0.9 s | 6 KB at the default cap |
| `wsc fetch --render` | +0.7 s | same |
| `wsc fetch` (cache hit) | 0.12 s | same |
| `wsc pdf <paper>` | 1.0 s | 20 KB at the default cap |
| `wsc map <site>` | 3-4.5 s | 0.2 KB for 20 URLs |
| `wsc crawl --limit 3` | 8 s | 0.3 KB of index lines |
| `wsc crawl --limit 12` | 12 s | 0.6 KB of index lines |

The pattern is the point: an API source is an order of magnitude cheaper than the general web, and
the general web is the only one that can answer a general question.

## Do not

- Do not `fetch` a URL you have not seen. A guessed URL costs a 404, a Wayback lookup, then a second
  guess; one `search` costs 0.4 s.
- Do not use `--source web` for a question a code or paper source owns. "What does `asyncio.timeout`
  raise" is `--source so`, not a search engine.
- Do not repeat a query with a slightly different phrasing. The engine set is the same; the rows will
  be the same. Change the source, not the wording.
- Do not `--category` by default. Latency swung 1.1 s to 6.1 s across runs, and it removes
  the scraper fallback: a category is a SearXNG-only parameter.
- Do not crawl to read one page. `map` is for a shape, `crawl` is for a section.
- Do not fetch a page you only need one line of. `--grep` returns that line and its neighbours.

If nothing answers, say which source you asked and what it said. `references/anti-bot-and-failures.md`
has the measured walls.
