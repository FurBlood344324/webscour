# webscour (Rust) — `wsc`

A port of the keyless search half of [webscour](../../README.md): the verb is `search`, the
sources are the same ones, and the output is byte-compatible with the Python so the two can be
compared rather than merely coexist. `fetch`, `pdf`, `map` and `crawl` are not here; they moved
to Firecrawl Local and are not part of this crate.

    wsc search "<query>" [--source SRC] [--limit N] [--category C] [--fresh [--since D]] [--json]
    wsc --self-test
    wsc --version

`--source` is `web`, `github`, `so`, `hn`, `arxiv`, `discourse:<base>`, `rss:<feed-url>`, or one
of the keyless APIs: `wikipedia`, `openalex`, `crossref`, `arxiv-api`, `europepmc`, `pubmed`,
`pypi`, `npm`, `crates`, `devto`, `wayback`, `googlenews`, `bbc`.

## Behaviour that came from the Python on purpose

The Python implementation is the contract. Where a choice looks odd here, it is because the
Python does it and a diff should not be about the port's opinion:

- **`web` order.** Local SearXNG (`127.0.0.1:8888`, `WEBSEARCH_SEARXNG` overrides) first; on
  failure or an empty answer, `lite.duckduckgo.com`, then `html.duckduckgo.com`, then Bing. The
  first backend that answers ends the chain.
- **One live query per second, across processes.** The stamp is `$XDG_CACHE_HOME/web/last-live`,
  the same file the Python writes, so a shell loop mixing the two still respects one budget.
- **Drift filter.** After the merge, rows with no query term in their title or url are dropped as
  soon as one on-topic row exists. With none at all the rows come back unchanged and the
  `related()` check decides about the set.
- **`[engine]` provenance** per row on the text path, `engines` in the JSON.
- **Two clipping styles.** Keyless sources clip with `...` (`sources._clip`), the renderer with
  `…` (`cli.cut`). Same lengths, different mark, and both are in the output.
- **JSON** is `json.dumps(rows, ensure_ascii=False, indent=1)`, key for key and space for space.
- **Exit codes.** `0` answered, `2` usage error or no answer, `1` help with no verb.

## Choices, with the reason

| Choice | Why |
| --- | --- |
| `ureq` | Blocking HTTP. Every command is one request in front of a reader; a runtime would be a second event loop for nothing, and the crate's `timeout_global` maps onto the Python's `TIMEOUT` exactly. |
| `scraper` | The result pages are HTML. A real HTML5 tree keeps a `<b>` inside a snippet from breaking a row, and a selector says "the anchor in the heading" in one line. `src/html.rs` is the only consumer. |
| `serde_json` with `preserve_order` | Key order is visible in `--json`, and a diff of two implementations must not be about key order. |
| `roxmltree` | Atom and RSS in one DOM walk, so `parse_rss` handles both shapes and arXiv's date field needs no second parser. |
| Hand-rolled argv | One verb, six flags. A parser crate would be a proc-macro compile for a `match` loop, and the exit codes are part of the contract, so they stay literal. |
| No `tokio`, no `reqwest` | Both would be a runtime and a TLS stack for a CLI that makes at most a handful of sequential calls. |

## Tests

    cargo test              # 57 tests: pure parsers + the fixture suite (offline)
    wsc --self-test         # the same checks, compiled in, so a built binary proves itself

Fixtures live in `tests/fixtures/` and are the exact payload shapes the Python captured.
`src/selftest.rs` embeds them with `include_str!`; `tests/fixtures_test.rs` reads them from disk.
Two paths, one payload, so a fixture cannot drift into passing only one of them.

## Eval

`eval/` runs 40 labelled queries through both implementations and prints hit@3, success rate and
median latency per side. A label is the domain a correct hit must carry.

    cargo build --release
    python3 eval/run_eval.py --limit 3            # hit@3 needs 3 rows
    python3 eval/run_eval.py --only 0,1,2         # a smoke test
    python3 eval/run_eval.py --json eval/results.json

Both sides are paced at one live query per second, the same rule the tool itself follows.

## Not ported

The four page verbs (`fetch`, `pdf`, `map`, `crawl`), `doctor`, `setup`, `probe`, `cache`, `mcp`
and `tool-argv`. The brief covers the search half; those verbs read pages rather than find them
and their destination is Firecrawl Local, not this crate.
