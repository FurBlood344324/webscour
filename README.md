<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/mark-dark.svg">
    <img src="assets/mark-light.svg" alt="webscour" width="112">
  </picture>
</p>

<p align="center">
  <b>webscour</b><br>
  A keyless web search CLI for agents.<br>
  One query in, numbered rows out. No API key. No account. No log.
</p>

<p align="center">
  <a href="https://crates.io/crates/webscour"><img src="https://img.shields.io/crates/v/webscour?color=black" alt="crates.io"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-black" alt="MIT"></a>
  <img src="https://img.shields.io/badge/rust-1.75%2B-black" alt="Rust 1.75+">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS-black" alt="Linux and macOS">
  <img src="https://img.shields.io/badge/dependencies-4-black" alt="Four dependencies">
</p>

`wsc` (the command the `webscour` crate installs) asks a local SearXNG first, falls back to the
DuckDuckGo and Bing scrapers, and carries one free API for each kind of question: a package, a
paper, a repository, a story, a feed. It is one binary, four crates deep, keyless, and it prints
text sized for a terminal instead of raw HTML.

## Install

```bash
cargo install webscour         # the crate is `webscour`, the binary is `wsc`
```

Rust 1.75 or newer. On Arch, a PKGBUILD that builds the published crate is staged in
`packaging/aur/`; it is updated by hand per release and is not submitted to the AUR yet.

SearXNG is optional. Without it the scrapers answer, which from a residential IP mostly means
CAPTCHA; for the meta-search results, run one on loopback at `127.0.0.1:8888` or point
`WEBSEARCH_SEARXNG` at the instance you have. No system binary is required: no render engine, no
document converter, no package manager.

`rust/README.md` has the flags, the source table and the behaviour in full.

## Check the install

```bash
wsc --version
wsc --self-test        # 35 offline checks, compiled into the binary
```

`--self-test` parses the bundled fixtures with the same code the live path uses, so a built binary
proves itself without a network call.

## Usage

```
wsc search "<query>" [--source SRC] [--limit N] [--category C] [--fresh [--since D]] [--json]
```

```bash
wsc search "ureq rust http client" --limit 3
```

```
1. Unsafe at Any Speed: Tradeoffs and values in the Rust ecosystem - https://bitbashing.io/rust-http.html  [rawweb]
2. GitHub - Olilin1/reqwest: An easy and powerful Rust HTTP Client - https://github.com/Olilin1/reqwest  [mwmbl]
3. Dragons' Den - Wikipedia - https://en.wikipedia.org/wiki/Dragons%27_Den  [bing]
```

Each row names the engines that produced it, so a result from one weak upstream is visible as such.
`--limit` clamps to 1..30, default 8. `--json` prints the same rows as objects, `indent=1`, keys in
insertion order.

`--fresh` restricts the answer to the freshness rows (Google News, BBC, SearXNG news), sorted by
publication date; it is its own source set, so `--source` beside it is a usage error. `--since
YYYY-MM-DD` is a floor for `--fresh`.

## Exit codes

`0` the question was answered. `1` `wsc` with no verb: the usage text, on stdout. `2` a usage error
(unknown flag or source, bad `--since`, a category outside `web`) or no answer. Output is the
answer: stderr carries failures only, and a non-zero exit is a real failure, never an empty result.

## Sources

| `--source` | Service | Notes |
|---|---|---|
| `web` (default) | local SearXNG, then DuckDuckGo lite, DuckDuckGo html, Bing | each row tagged `[naver,bing]`; a fallback prints one `backend <name>: <reason>` line |
| `github` | api.github.com repositories and issues | unauthenticated, 10 requests/min, remaining budget printed |
| `so` | Stack Exchange API, `site=stackoverflow` | answered/open, tags |
| `hn` | hn.algolia.com | story points, comment counts |
| `arxiv` | export.arxiv.org Atom | title, id URL, abstract |
| `discourse:<base>` | `<base>/search.json` | e.g. `discourse:https://forums.developer.nvidia.com` |
| `rss:<feed-url>` | any RSS or Atom feed | title, link, date |
| `wikipedia` | the MediaWiki API | plain text extract |
| `openalex`, `crossref`, `arxiv-api`, `europepmc`, `pubmed` | scholarly metadata | title, DOI or id, abstract |
| `pypi`, `npm`, `crates` | package registries | name, version, summary |
| `devto` | dev.to | tags, reactions |
| `wayback` | the Wayback Machine | the closest capture |
| `googlenews`, `bbc` | news feeds | publication date |

A source is a parser and one request in the same place. `--category` (`general`, `it`, `science`,
`news`, `images`, `files`, `social`) means `--source web` only, because a scraper cannot be asked
for a category.

## Privacy

Only the query leaves the machine, to whichever engine or API answers it. No key, no account, no
cookie, no telemetry, no log file: the tool writes nothing except its one-second pacing stamp in
`$XDG_CACHE_HOME/web/last-live`, so a shell loop cannot look like a scraper. Every live request
shares that stamp across processes.

This is not anonymity. Your IP talks to whichever upstream engines are enabled; a local proxy does
not change that. Send generic technical terms and keep private context out of a query.

## How it differs from firecrawl, and from an MCP server

firecrawl is a hosted service for turning sites into clean markdown at scale: crawl jobs, JS
rendering farms, structured extraction, and an API key. webscour is the opposite shape, a local tool
for one query, with no account, no credits and no state, and it tells you which engine answered
instead of hiding the plumbing. An MCP server is a transport: it puts a tool behind a protocol, and
then something still has to be installed, run and authenticated. `wsc` is a plain executable that an
agent, a shell script or a human calls the same way, so no server has to be running for it to work.
The page verbs (`fetch`, `pdf`, `map`, `crawl`) are not here; they live in Firecrawl Local.

## Limitations

- **The scrapers degrade on residential IPs.** Measured on 2026-11-13 with 30 generic queries, per
  engine; a meta-search needs coverage (how often an engine helps) and precision (share of its rows
  that are on topic), kept means coverage >= 10 % and precision >= 60 %:

| engine | cover | prec | rows | | engine | cover | prec | rows |
|---|---|---|---|---|---|---|---|---|
| naver | 90.0 % | 80.1 % | 403 | | wikibooks | 20.0 % | 93.8 % | 16 |
| abcnyheter | 70.0 % | 95.3 % | 214 | | wiby | 13.3 % | 42.9 % | 21 (dropped) |
| rawweb | 53.3 % | 98.8 % | 82 | | wikiversity, wikiquote | <=6.7 % | 100 % | 1-2 (dropped) |
| bing | 36.7 % | 60.0 % | 180 | | encyclosearch, wikisource | 3.3 % | 50 % | 2-14 (dropped) |
| yacy | 30.0 % | 96.7 % | 90 | | brave | 0 % this pass | n/a | kept by name |

  duckduckgo, google, mojeek, qwant, startpage, searchmysite and yandex answered CAPTCHA, "access
  denied" or a parsing error from a residential IP and are not in the set. Median merged query 5.0 s.
  Kept: naver, abcnyheter, rawweb, bing, yacy, wikibooks, brave. The table is one machine on one
  day, not a promise.
- **Snippets are quotes from a scraped page.** Open the URL before relying on a claim, and treat a
  row whose title and url lack every query term as drift, which the tool drops.
- **GitHub is unauthenticated**: 10 requests/min per IP, and `--source github` makes two calls.
- **A local SearXNG is the difference between a good `web` answer and a CAPTCHA.** The crate does
  not install one; `WEBSEARCH_SEARXNG` points it at any instance you already run.

## Development

```bash
cd rust
cargo test --release              # 57 tests: pure parsers plus the fixture suite, offline
cargo clippy --release --all-targets
./target/release/wsc --self-test  # 35 checks, compiled in
```

The eval is a release-time measurement, not a gate: 40 labelled queries, hit at 3, median latency.
`rust/REPORT.md` holds the evidence and the decisions behind the dependency choices.

## License

MIT. See [LICENSE](LICENSE).
