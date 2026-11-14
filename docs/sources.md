# Sources

`--source` decides who gets asked. Every source is keyless: no API token, no account and no
client id sits anywhere in this tool. Rate limits are the ones the upstream service publishes or
enforces, so they are properties of your IP, not of this tool.

## The three families

The source layer has three shapes, and the shape tells you what to expect.

- **The local meta-search**, `web`. One loopback call, several upstream engines merged, and each
  row tagged with the engines that produced it. This is the general case.
- **Direct service APIs**, `github`, `so`, `hn`, `arxiv` and `discourse:<base>`. One named
  service, its own ranking, its own rate limit.
- **Keyless single-purpose endpoints**, the fourteen below. One endpoint per kind of question,
  each with a pure parser that `--self-test` exercises offline.

`docs/routing.md` carries the decision table and the measured cost of each family.

## The table

| `--source` | what it queries | key | rate limit | output shape |
|---|---|---|---|---|
| `web` (default) | the local SearXNG on `http://127.0.0.1:8888`, which fans out to its enabled engines; then the DuckDuckGo lite page, the DuckDuckGo html page and Bing | none | SearXNG's engines pace themselves; the CLI spaces live queries to at most one per second across processes | rows tagged with their engines, `[naver,bing]` |
| `github` | `api.github.com/search/repositories` and `api.github.com/search/issues` | none | 10 requests per minute unauthenticated; one `github` search spends 2 of them | repo rows carry language and stars; issue rows carry state and body |
| `so` | `api.stackexchange.com/2.3/search/advanced` with `site=stackoverflow` | none | Stack Exchange's anonymous quota; the command reports a refusal, it does not retry | `title (score N)`, then `answered` or `open` plus tags |
| `hn` | `hn.algolia.com/api/v1/search` | none | Algolia's public search tier; no batch mode here | `title`, then points and comment count |
| `arxiv` | `export.arxiv.org/api/query`, the Atom feed | none | arXiv's request policy; one query per call | `title`, the `abs` URL, the abstract as the snippet |
| `discourse:<base>` | `<base>/search.json?q=<query>` | none | the forum's own anonymous limit | topic title, topic URL, blurb |
| `wikipedia` | `en.wikipedia.org/w/api.php`, list=search | none | none published; one request per call | article title and the article URL |
| `openalex` | `api.openalex.org/works` | none | none published; a polite email pool exists but this tool sends no identity | work title, DOI or landing URL, abstract |
| `crossref` | `api.crossref.org/works` | none | none published | work title, DOI URL, container and year |
| `arxiv-api` | the same Atom endpoint as `arxiv`, under the alias the tool-call schema uses | none | as `arxiv` | as `arxiv` |
| `europepmc` | `ebi.ac.uk/europepmc/webservices/rest/search` | none | none published | title, DOI, PubMed or Europe PMC URL |
| `pubmed` | `eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` | none | NCBI's policy; a keyless call gets the default pool | title, PubMed URL, journal and date |
| `pypi` | `pypi.org/pypi/<name>/json` | none | none published | project name, PyPI URL, version, summary, release date |
| `npm` | `registry.npmjs.org/<name>/latest` | none | none published | package name, npm URL, version, description |
| `crates` | `crates.io/api/v1/crates/<name>` | none | crates.io asks for a descriptive user agent, which the tool sends | crate name, crates.io URL, version, description |
| `devto` | `dev.to/api/articles?tag=<tag>` | none | dev.to's public limit | article title, URL, tags, reactions |
| `wayback` | `web.archive.org/cdx/search/cdx` | none | the archive rate-limits bursts; a 429 is reported as a note, not a failure | snapshot URL and timestamp |
| `googlenews` | `news.google.com/rss/search` | none | Google's RSS limits; no key involved | headline, source, publication date |
| `bbc` | `feeds.bbci.co.uk/news/rss.xml` | none | none published; one feed read per call | headline, article URL, date |

`<base>` is a full origin with a scheme, for example
`discourse:https://forums.developer.nvidia.com`. A `--source` value that matches none of those
shapes is a usage error: stderr lists every accepted value and the exit code is 2.

`--fresh` is not a source. It restricts the answer to the freshness rows (Google News, BBC and
SearXNG's news category), merges them, and sorts by publication date with the newest first.
`--since YYYY-MM-DD` sets the floor for that sort.

## What each source is good at

**`web`.** The default, and the right first attempt for a question about the world. The local
SearXNG merges several upstream engines, so one suspended engine does not empty the answer, and
each row tells you which engines produced it. When the local service is down the command falls
back to the three scrapers, one `backend <name>: <reason>` line per attempt on stderr. From a
residential IP those scrapers mostly answer a bot check, so the local backend is the one that
matters.

**`github`.** Code, not prose. Use it when the answer is a repository (a library that does X) or
an issue (someone already hit this error). It spends two API calls per query and prints the
remaining budget, so a loop is easy to stay under.

**`so`.** A symptom, an error text, a stack trace. Stack Overflow rows carry the score and
whether the question is answered, which is the cheapest signal about whether the page will help.
Prefer it over `web` when your query is an exception message rather than a concept.

**`hn`.** Opinion and experience: "has anyone run this in production", "what did people say about
this release". Story points and comment counts are the ranking you actually get, so a low-score
row is not worth opening.

**`arxiv`.** A paper, by topic rather than by citation. The snippet is the abstract, so one query
often decides whether you need the PDF; follow up with `wsc pdf` on the `abs` URL's `/pdf/` form.
Prefer it over `web` for anything where a blog summary would be second hand.

**`discourse:<base>`.** One forum's own search, which is the only way to reach posts that no
general engine indexes. The NVIDIA developer forum is the worked example; the same shape works
for any Discourse instance that leaves anonymous search on.

**The scholarly four** (`openalex`, `crossref`, `europepmc`, `pubmed`). Use them when you want a
record rather than prose: a DOI, a citation, a journal, a date. `pubmed` and `europepmc` overlap
by design and differ in what they index; `openalex` is the widest net and `crossref` is the
metadata of record for a DOI.

**The package four** (`pypi`, `npm`, `crates`, `devto`). These are exact lookups by name, not
searches. `wsc search requests --source pypi` either finds the project or does not; it is a check,
not a query.

**`wayback`, `googlenews`, `bbc`.** `wayback` answers "what did this URL say before it died", and
`fetch --archive` uses the same machinery. `googlenews` and `bbc` are the freshness pair: the
answer is a dated headline, and `--fresh` is how you get them sorted.

## Choosing a source

1. Is the answer a paper? Use `arxiv`, or `openalex` / `crossref` / `pubmed` if you want a DOI and
   a citation record rather than an abstract.
2. Is the answer a repository or an issue? Use `github`.
3. Is the query an error message or a stack trace? Use `so`.
4. Do you want experience rather than documentation? Use `hn`.
5. Do you want a package's current version? Use `pypi`, `npm` or `crates`.
6. Is the question specific to a product whose forum you know? Use `discourse:<base>`.
7. Do you need something published in the last day? Use `--fresh`, or `googlenews` / `bbc`
   directly.
8. Do you need a page that no longer exists? Use `wayback`, or `fetch --archive`.
9. Otherwise use `web`. It is the default because it is the general case, and its rows tell you
   which engine answered so a bad answer is diagnosable.

Two habits worth keeping:

- Run `web` first when you do not know which of the others applies. The rows name their engines,
  and a specialised source can be the second query rather than a guess.
- `github`, `so`, the package four and `discourse` are exact-match searches over a small corpus. A
  natural-language question does badly there; three or four distinctive words do well.

## Forums and documents

`fetch` rewrites a topic URL on `forums.developer.nvidia.com` to the thread's `.json` form and
prints `#post author` with plain text. That is the readable version of a forum page and it needs
no render.

`fetch` also resolves a known site through its own API when the plain page is measurably worse,
and announces it on stderr as `route: <name>`. `--no-route` turns that off. A route that declines
falls back to the plain path and says so only under `-v`; a route never turns a page that used to
work into a failure.

`pdf` and `fetch` share one document path: a URL whose content type or extension is a PDF, docx or
epub is downloaded once and handed to the first working local backend. Nothing is uploaded
anywhere to read it.
