# webscour (Rust), binary `wsc`

Keyless search from the command line. One verb, `search`, and one source name per kind of question:
a local SearXNG first, then the scrapers, plus a free API for each shape of answer (a package, a
paper, a repository, a story, a feed). No API key, no account, no log. The crate is `webscour`,
version 0.2.0, the binary is `wsc`, and the direct dependency list is four crates.

`web` asks a **local** SearXNG (`127.0.0.1:8888`, `WEBSEARCH_SEARXNG` overrides) and falls back, in
order, to `lite.duckduckgo.com`, `html.duckduckgo.com` and Bing. The first backend that answers ends
the chain, and the fallback is reported on stderr rather than hidden. Everything else is a
structured API that answers JSON: `github`, `so`, `hn`, `arxiv`, `discourse:<base>`,
`rss:<feed-url>`, `wikipedia`, `openalex`, `crossref`, `arxiv-api`, `europepmc`, `pubmed`, `pypi`,
`npm`, `crates`, `devto`, `wayback`, `googlenews`, `bbc`.

This is a port of the keyless search half of the Python tool: the row shape, the clip lengths and
the `--json` bytes are the same on both sides, so the two can be diffed rather than merely coexist.
The page verbs (`fetch`, `pdf`, `map`, `crawl`) are not here; they live in Firecrawl Local.

## Install

```bash
cargo install webscour     # puts `wsc` in ~/.cargo/bin
```

Rust 1.75 or newer. From a checkout: `cargo build --release && ./target/release/wsc --version`.
SearXNG is optional. Without it the scrapers answer, which from a residential IP mostly means
CAPTCHA; for the meta-search results, run one on loopback at `127.0.0.1:8888` or point
`WEBSEARCH_SEARXNG` at the instance you have.

## Usage

```
wsc search "<query>" [--source SRC] [--limit N] [--category C] [--fresh [--since D]] [--json]
wsc --self-test
wsc --version
```

`--source` is one of the names above, default `web`. `--limit` is the rows to keep, clamped to
1..30, default 8. `--category` is `general`, `it`, `science`, `news`, `images`, `files` or `social`,
and it means `--source web` only, because a scraper cannot be asked for a category. `--fresh`
restricts the answer to the freshness rows (Google News, BBC, SearXNG news), sorted by publication
date; it is its own source set, so `--source` beside it is a usage error. `--since YYYY-MM-DD` is a
floor for `--fresh`. `--json` prints the same rows as objects, `indent=1`, keys in insertion order.

Two queries, and what they answered from this machine. SearXNG's own answer rotates between calls,
so the rows, their order and the engine tags are one run; the shapes are what stay.

```bash
wsc search "python pyproject packaging" --limit 3
```

```
1. Not Found - https://pycoders.com/python/pyproject  [mwmbl]
2. Welcome to Python.org - https://www.python.org/  [bing]
   Experienced programmers in any other language can pick up Python very quickly, and beginners find the clean syntax and …Read more
3. Packaging Python Projects - Python Packaging User Guide - https://packaging.python.org/en/latest/tutorials/packaging-projects/  [naver]
   This tutorial walks you through how to package a simple Python project. It will show you how to add the necessary files and structure to create the package, and how to build the package, and how to uploa…
```

```bash
wsc search --source github "ureq" --limit 3
```

```
1. algesten/ureq - https://github.com/algesten/ureq
   A simple, safe HTTP client · Rust · 2234 stars
2. solusipse/ureq - https://github.com/solusipse/ureq
   Micro C library for handling HTTP requests on low resource systems. · C · 656 stars
3. anodynos/uRequire - https://github.com/anodynos/uRequire
   The Ultimate JavaScript Module Builder & Automagical Task Runner. Convert AMD & CommonJS/NodeJS modules to UMD, AMD, CommonJS or bundle them as `combined.js` (rjs & almond, AMDclean soon) & automagic…
-- github rate limit remaining: 9
```

The rate-limit line is the unauthenticated GitHub budget, printed only when a call answered. Output
is the answer: stderr carries failures only.

## Exit codes

`0` the question was answered. `1` `wsc` with no verb: the usage text, on stdout. `2` a usage error
(unknown flag or source, bad `--since`, a category outside `web`) or no answer. A non-zero exit is a
real failure, never an empty result.

## Privacy

Only the query leaves the machine, to whichever engine or API answers it. No key, no account, no
cookie, no telemetry, no log file: the tool writes nothing except its one-second pacing stamp in
`$XDG_CACHE_HOME/web/last-live`, the same file the Python writes, so a shell loop mixing the two
still respects one live query per second. This is not anonymity: your IP talks to whichever upstream
engines are enabled, and a local proxy does not change that. Send generic technical terms and keep
private context out of a query.

## Behaviour that came from the Python on purpose

The Python implementation is the contract. Where a choice looks odd here, it is because the Python
does it and a diff should not be about the port's opinion.

- **`web` order.** SearXNG first; on failure or an empty answer, DDG lite, DDG html, then Bing.
- **One live query per second, across processes**, through the shared pace stamp above.
- **Drift filter.** After the merge, rows with no query term in their title or url are dropped as
  soon as one on-topic row exists. With none at all the rows come back unchanged.
- **`[engine]` provenance** per row on the text path, `engines` in the JSON.
- **Two clipping styles.** Keyless sources clip with `...`, the renderer with `…`. Same lengths,
  different mark, both in the output.
- **JSON** is `json.dumps(rows, ensure_ascii=False, indent=1)`, key for key and space for space.

## Choices, with the reason

`ureq` because every command is one blocking request in front of a reader, and a runtime would be a
second event loop for nothing. `scraper` because a result page is HTML and a real HTML5 tree keeps a
`<b>` inside a snippet from breaking a row. `serde_json` with `preserve_order` because key order is
visible in `--json`. `roxmltree` because Atom and RSS then share one DOM walk. Hand-rolled argv
because one verb and six flags do not justify a proc-macro compile, and the exit codes are part of
the contract. No `tokio`, no `reqwest`: a runtime and a TLS stack for a handful of sequential calls.

## Tests

```
cargo test              # 57 tests: pure parsers + the fixture suite (offline)
wsc --self-test         # 35 checks, compiled in, so a built binary proves itself
```

Fixtures live in `tests/fixtures/` and are the exact payload shapes the Python captured.
`src/selftest.rs` embeds them with `include_str!`; `tests/fixtures_test.rs` reads them from disk, so
a fixture cannot drift into passing only one of the two paths.

`eval/` runs 40 labelled queries through both implementations and prints hit@3, success rate and
median latency per side. In the two runs recorded there, both sides scored 26/40 on hit@3 (65 %),
agreement was 38/40 queries, and the median was 1.02 s against the Python's 1.64 s. That is one
machine on one day, not a promise.

## Not ported

`fetch`, `pdf`, `map`, `crawl`, `doctor`, `setup`, `probe`, `cache`, `mcp` and `tool-argv`. Those
verbs read pages rather than find them, and their destination is Firecrawl Local.

## License

MIT. See [LICENSE](LICENSE).
