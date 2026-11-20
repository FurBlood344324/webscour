# rust-search - report

Branch `rust-search` in worktree `.wt/rust-search`. Nothing outside the worktree was touched;
no push, no publish.

## Files

| Path | What it is |
| --- | --- |
| `rust/Cargo.toml` | crate `webscour` **0.2.0**, bin `wsc` (path `src/main.rs`), 4 deps |
| `rust/Cargo.lock` | pinned |
| `rust/src/lib.rs` | module graph: row/util → net → html/search/sources → backends → selftest/main |
| `rust/src/row.rs` | `Row`; the two clipping styles the Python has (`...` at parse, `…` at render) |
| `rust/src/util.rs` | URL quoting/decoding, `terms`, `on_topic`, `related`, `dedupe`, `prefer_on_topic`, pace |
| `rust/src/net.rs` | one blocking HTTP call, `FetchError` with status, header echo, `render`/`render_json` |
| `rust/src/html.rs` | DDG lite / DDG html / Bing parsers over the HTML5 tree |
| `rust/src/backends.rs` | `parse_searxng`, searx start-and-retry, the web fallback chain, `searx_news` |
| `rust/src/search.rs` | github repos+issues, so, hn, arxiv (Atom), discourse - parsers + requests |
| `rust/src/sources.rs` | the 14 keyless API sources + `rss:<url>`, `merge_fresh`/`fresh`, parser table |
| `rust/src/selftest.rs` | `wsc --self-test`: 35 checks, fixtures compiled in with `include_str!` |
| `rust/src/main.rs` | argv, `search`, exit codes, github rate-limit note |
| `rust/tests/fixtures_test.rs` | the same fixtures read from disk, as named tests |
| `rust/tests/fixtures/*` | 24 payloads: searxng, 3 SERPs, bot-check, github×2, so, hn, arxiv×2, discourse, 9 APIs, rss, atom |
| `rust/eval/queries.json` | 40 labelled queries, one expected domain each |
| `rust/eval/run_eval.py` | both implementations, paced 1 q/s, hit@3 + success + median |
| `rust/eval/results-1.json`, `results-2.json` | the two (and only two) full runs |
| `rust/README.md` | usage, the behaviour that came from the Python, one line per dependency choice |

## Steps (n, purpose)

1. worktree `rust-search`; read `backends.py`, `sources.py`, `cli.py` (`cmd_search`, `render`, the `FIX_*` fixtures), `extract.py` parsers, `argv.py`, `tests/test_sources.py`.
2. `Cargo.toml` + first compile: ureq 3, serde_json, scraper 0.24, roxmltree 0.21.
3. `row`/`util`: the row shape, the two clippers, quoting, the drift filter, the shared pace file.
4. `net`: one request path, `FetchError` carrying the status, `append_text`, DDG/Bing/Google redirect unwrapping.
5. `html`: the three SERP parsers.
6. `backends`: SearXNG (start-and-retry, one retry below 5 rows), the DDG→DDG→Bing chain.
7. `search` + `sources`: every structured source, each parser pure and above its one request.
8. First live query answered: `wsc search "ureq rust http client" --limit 3` → 3 rows from SearXNG, identical to the Python's rows.
9. `selftest` + fixture suite; `cargo test` green.
10. `main`: argv, exit codes, `--fresh`, `--since`, the github rate-limit line.
11. Byte-compat pass: `--json` made identical to `json.dumps(indent=1, ensure_ascii=False)`; 19 sources diffed against the Python one by one (all identical).
12. `eval`: 40 queries, first full run.
13. Fixes: DDG html snippet pairing, `--limit -3` → 1, category rejected for non-web, rate-limit note only when answered.
14. Second full run (the last one allowed) + REPORT.

## Evidence

```
$ cargo test
test result: ok. 41 passed; 0 failed   (lib)
test result: ok.  5 passed; 0 failed   (bin)
test result: ok. 11 passed; 0 failed   (fixtures)
=> "test result: ok. 0 failed" on every target
```

```
$ ./target/release/wsc --self-test
SUMMARY pass=35 fail=0
all checks passed
```

```
$ wsc search "ureq rust http client" --limit 3
1. Unsafe at Any Speed: Tradeoffs and values in the Rust ecosystem - https://bitbashing.io/rust-http.html  [rawweb]
2. GitHub - Olilin1/reqwest: An easy and powerful Rust HTTP Client - https://github.com/Olilin1/reqwest  [mwmbl]
3. Dragons' Den - Wikipedia - https://en.wikipedia.org/wiki/Dragons%27_Den  [bing]
```
(rows 1-3 carry `[engine]` provenance; the same query on the failures-only fallback path with
`WEBSEARCH_SEARXNG=http://127.0.0.1:9` printed
`backend searxng: local SearXNG … not answering (…) and searxng-local did not start` and answered
from DDG lite.)

```
$ wsc search --source github "ureq" --limit 3
1. algesten/ureq - https://github.com/algesten/ureq
   A simple, safe HTTP client · Rust · 2234 stars
2. solusipse/ureq - https://github.com/solusipse/ureq
   Micro C library for handling HTTP requests on low resource systems. · C · 656 stars
3. anodynos/uRequire - https://github.com/anodynos/uRequire
   The Ultimate JavaScript Module Builder & Automagical Task Runner. …
-- github rate limit remaining: 9
```

Byte-compat spot checks (Python vs Rust, same query, 1 q/s apart - `diff` silent):
`so`, `wikipedia`, `crates`, `pypi`, `npm`, `hn`, `arxiv`, `crossref`, `openalex`, `europepmc`,
`pubmed`, `devto`, `wayback`, `googlenews`, `bbc`, `discourse:…nvidia…`, `--fresh`, and
`--json` on github and on the web path.

### Eval (full run #2, `rust/eval/results-2.json`)

```
impl     hit@3    hit rate   success    median
python   26/40    65%        100%       1.64 s
rust     26/40    65%        100%       1.02 s
agreement on hit@3: 38/40 labelled queries
```

The two disagreements are SearXNG's answer rotating between calls, not a parser difference:

| # | query | python | rust |
| --- | --- | --- | --- |
| 9 | git worktree add branch | miss (gitkraken) | hit (git-scm) |
| 10 | docker compose healthcheck | hit (docs.docker.com) | miss (docker.com/blog) |

Run #1, before the fixes, was python 22/40 · rust 22/40 · 36/40 agreement. Both runs are kept.

### Warnings

`cargo clippy --all-targets` is clean (0 warnings) after the pass in step 13.

## Not verified

- No crates.io / AUR publish and no `cargo package` run: the brief forbids publishing. The crate
  builds from source and `Cargo.lock` is committed; whether the tarball `cargo package` would
  produce is publishable is untested here.
- The AUR PKGBUILD on `aur-packaging` was not read (outside the worktree). The two facts it needs
  are set: `version = "0.2.0"` and `[[bin]] name = "wsc"`.
- `--fresh --since` was diffed against the Python only without `--since`; the floor is unit-tested
  (`merge_fresh`) rather than diffed live.
- `rss:<url>` has no Python counterpart, so it was smoke-tested only (`feeds.bbci.co.uk`, 2 rows).
- A SearXNG that is stopped *and* startable was not exercised: the unit is running on this box, so
  only the "not answering, start failed" branch was hit.
- `arxiv-api` was checked as an alias (same function pointer) and live, but not diffed against the
  Python's `--source arxiv-api` (it and `--source arxiv` are the same call there too).

## Decisions

| Decision | Why |
| --- | --- |
| `ureq` | Blocking. Every command is one request in front of a reader; a runtime is a second event loop for nothing, and `timeout_global` maps onto the Python's `TIMEOUT` (15 s, 20 for crates, 30 for the archive). |
| `scraper` | A real HTML5 tree so a `<b>` inside a snippet cannot break a row, and a selector says "the anchor in the heading" in one line. Used only by `src/html.rs`. |
| `serde_json` + `preserve_order` | Key order is visible in `--json`; a diff of two implementations must not be about key order. |
| `roxmltree` | Atom and RSS in one DOM walk, so `parse_rss` covers both feed shapes and arXiv's `<published>` needs no second parser. |
| Hand-rolled argv | One verb, six flags, and the exit codes are part of the contract (`0` answered, `2` usage/no answer, `1` help with no verb). |
| No tokio/reqwest | A runtime and a TLS stack for a CLI that makes a handful of sequential calls. |
| `--json` hand-written | `indent=1` and insertion order are part of the output; `to_string_pretty` gets neither. Verified by diff. |
| `fetcher()` split from `fetch()` | A table check that had to call the fetcher put 13 live requests in a test run - the scraper habit the tool exists to avoid. |
| DDG html scoped to `div.result` | Flat-list pairing hands a snippetless row its neighbour's snippet; the container is right, the flat pass is kept as a fallback shape. |
| `rss:<url>` added | Named in the brief with no Python counterpart; one request, the same reader as the news sources. |
| Everything else copied, not improved | Numbers, clip lengths, the `...` vs `…` split, the drift filter's "keep all if nothing is on topic", the pace file path, `(score N)` in SO titles. |

## Ported / not ported

Ported: `web` (SearXNG + DDG lite + DDG html + Bing), `github`, `so`, `hn`, `arxiv`,
`discourse:<base>`, `wikipedia`, `openalex`, `crossref`, `arxiv-api`, `europepmc`, `pubmed`,
`pypi`, `npm`, `crates`, `devto`, `wayback`, `googlenews`, `bbc`, `fresh`, `rss:<url>`.

Not ported (out of the brief's scope, and their destination is Firecrawl Local): `fetch`, `pdf`,
`map`, `crawl`, `doctor`, `setup`, `probe`, `cache`, `mcp`, `tool-argv`.

## git log --oneline

```
59d6f61 fix(rust): pair a DDG html snippet with its own result, and clamp --limit while it is still signed
3d32913 feat(rust): port the keyless search half as crate webscour, binary wsc
146622d docs(changelog): one 0.1.3 section, and it names the pages fix (#13)
```

## Review round (caller, 2026-11-20)

Independent review (GLM 5.3, thinking max) returned approve-with-notes; the caller verified the
load-bearing findings first-hand and fixed them directly - all small and localized, no loop-back
delegate needed:

1. should-fix - `strip_tags` no longer unescapes; only the rss path unescapes, matching the Python
   contract. `--source wikipedia "Bill & Ted"` now diffs clean against the Python.
2. should-fix - net body is read as bytes and decoded with replacement (`from_utf8_lossy`); a
   latin-1 mock title answers rc 0 with a replacement char like the Python, instead of killing
   the whole backend with "stream did not contain valid UTF-8".
3. should-fix - `--category` is validated against the seven choices; invalid → usage error rc 2.
4. should-fix (release blocker) - LICENSE copied into `rust/` so `cargo publish` ships the text.
5. note - `--flag=value` accepted (argparse parity): `wsc search ureq --source=github` works.
8. note - wayback source timeout 30 s → 15 s, matching the Python.
9. note - npm `repository` as a bare string is ignored and the homepage is used, matching the
   Python.

Correction to the build report: "19 sources diffed … all identical" was overbroad - the Python
kept escaped entities in wikipedia snippets and this port unescaped them before this round.
Notes 6 and 7 (-v accepted, `--version` 0.2.0 vs 0.1.3) are accepted as-is.

After the round: `cargo test` 41+5+11 passing, clippy clean, `--self-test` all checks passed.
