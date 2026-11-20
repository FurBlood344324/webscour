# webscour - evidence report

Crate `webscour` 0.2.0, binary `wsc`, in `rust/`. The whole repository is this crate: one binary,
four direct dependencies, keyless search only. Nothing outside the worktree was touched; no push,
no publish.

## Files

| Path | What it is |
| --- | --- |
| `rust/Cargo.toml` | crate `webscour` **0.2.0**, bin `wsc` (path `src/main.rs`), 4 deps |
| `rust/Cargo.lock` | pinned |
| `rust/src/lib.rs` | module graph: row/util → net → html/search/sources → backends → selftest/main |
| `rust/src/row.rs` | `Row`; the two clipping styles (`...` at parse, `…` at render) |
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
| `rust/LICENSE` | MIT, copied into the crate so `cargo publish` ships the text |
| `rust/README.md` | usage, the row contract, one line per dependency choice |

## Steps (n, purpose)

1. worktree; read the search surface the crate must keep: the row shape, the clip lengths, the
   source names, the exit codes and the captured payloads.
2. `Cargo.toml` + first compile: ureq 3, serde_json, scraper 0.24, roxmltree 0.21.
3. `row`/`util`: the row shape, the two clippers, quoting, the drift filter, the shared pace file.
4. `net`: one request path, `FetchError` carrying the status, `append_text`, DDG/Bing/Google redirect unwrapping.
5. `html`: the three SERP parsers.
6. `backends`: SearXNG (start-and-retry, one retry below 5 rows), the DDG→DDG→Bing chain.
7. `search` + `sources`: every structured source, each parser pure and above its one request.
8. First live query answered: `wsc search "ureq rust http client" --limit 3` → 3 rows from SearXNG.
9. `selftest` + fixture suite; `cargo test` green.
10. `main`: argv, exit codes, `--fresh`, `--since`, the github rate-limit line.
11. Output pass: `--json` fixed to `indent=1`, insertion order, non-ASCII left as UTF-8; each of
    the 19 sources checked against its live endpoint.
12. eval: 40 labelled queries, first full run.
13. Fixes: DDG html snippet pairing, `--limit -3` → 1, category rejected for non-web, rate-limit
    note only when answered.
14. Second full run (the last one allowed) + this report.
15. Release checks on the tree with the retired tool removed: `cargo test --release` 41+5+11,
    clippy 0 warnings, `--self-test` 35/35, `cargo package --list` carries README and LICENSE.

## Evidence

### Tests

```
$ cargo test --release
test result: ok. 41 passed; 0 failed   (lib)
test result: ok.  5 passed; 0 failed   (bin)
test result: ok. 11 passed; 0 failed   (fixtures)
=> "test result: ok. 0 failed" on every target
```

### Self-test

```
$ ./target/release/wsc --self-test
SUMMARY pass=35 fail=0
all checks passed
```

### Live queries

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

### Eval

The eval is a release-time measurement, not a gate: 40 labelled queries, one expected domain each,
paced one query per second.

```
hit at 3   26/40    65 %
answered   40/40    100 %
median     1.02 s
```

That is one machine on one day, not a promise. The run was repeated after the pairing and limit
fixes; the numbers above are the second run, and the first was 22/40 before those fixes.

## Warnings

`cargo clippy --release --all-targets` is clean (0 warnings) after the pass in step 13.

## Not verified

- No crates.io / AUR publish and no `cargo package` run beyond `--list`: publishing is out of scope
  here. The crate builds from source and `Cargo.lock` is committed; whether the tarball is
  publishable is untested.
- The AUR PKGBUILD in `packaging/aur/` was not built here (it needs a clean chroot). The two facts it
  needs are set: `version = "0.2.0"` and `[[bin]] name = "wsc"`; the sha256 is filled in by hand at
  release time.
- `--fresh --since` is unit-tested (`merge_fresh`), not diffed live.
- `rss:<url>` was smoke-tested only (`feeds.bbci.co.uk`, 2 rows).
- A SearXNG that is stopped *and* startable was not exercised: the unit is running on this box, so
  only the "not answering, start failed" branch was hit.
- `arxiv-api` was checked as an alias (same function pointer) and live; it and `--source arxiv` are
  the same call.

## Decisions

| Decision | Why |
| --- | --- |
| `ureq` | Blocking. Every command is one request in front of a reader; a runtime is a second event loop for nothing, and `timeout_global` sets the 15 s timeout (20 for crates, 30 for the archive). |
| `scraper` | A real HTML5 tree so a `<b>` inside a snippet cannot break a row, and a selector says "the anchor in the heading" in one line. Used only by `src/html.rs`. |
| `serde_json` + `preserve_order` | Key order is visible in `--json`, so two runs must not differ on it. |
| `roxmltree` | Atom and RSS in one DOM walk, so `parse_rss` covers both feed shapes and arXiv's `<published>` needs no second parser. |
| Hand-rolled argv | One verb, six flags, and the exit codes are the contract (`0` answered, `2` usage/no answer, `1` help with no verb). |
| No tokio/reqwest | A runtime and a TLS stack for a CLI that makes a handful of sequential calls. |
| `--json` hand-written | `indent=1` and insertion order are part of the output; `to_string_pretty` gets neither. Verified by diff. |
| `fetcher()` split from `fetch()` | A table check that had to call the fetcher put 13 live requests in a test run, the scraper habit the tool exists to avoid. |
| DDG html scoped to `div.result` | Flat-list pairing hands a snippetless row its neighbour's snippet; the container is right, the flat pass is kept as a fallback shape. |
| `rss:<url>` added | One request, the same reader as the news sources; no other source covers an arbitrary feed. |
| Shape kept, not improved | Numbers, clip lengths, the `...` vs `…` split, the drift filter's "keep all if nothing is on topic", the pace file path, `(score N)` in SO titles. Changing one would move the output, not improve it. |
| Package list | `exclude = ["REPORT.md"]`: the evidence report belongs to the repo, not to the published crate. `tests` and its fixtures ship, because `cargo test` after install uses them. |

## Review round

Independent review (GLM 5.3, thinking max) returned approve-with-notes; the load-bearing findings
were verified first-hand and fixed directly, all small and localized:

1. should-fix - `strip_tags` no longer unescapes; only the rss path unescapes, so a wikipedia
   snippet keeps the entities the endpoint sent (`--source wikipedia "Bill & Ted"` diffs clean).
2. should-fix - the response body is read as bytes and decoded with replacement
   (`from_utf8_lossy`); a latin-1 mock title answers rc 0 with a replacement char instead of killing
   the whole backend with "stream did not contain valid UTF-8".
3. should-fix - `--category` is validated against the seven choices; invalid → usage error rc 2.
4. should-fix (release blocker) - LICENSE copied into `rust/` so `cargo publish` ships the text.
5. note - `--flag=value` accepted: `wsc search ureq --source=github` works.
6. note - wayback source timeout 30 s → 15 s, in line with the other sources.
7. note - an npm `repository` given as a bare string is ignored and the homepage is used.

Notes accepted as-is: `-v` accepted, `--version` reads 0.2.0.

After the round: `cargo test --release` 41+5+11 passing, clippy clean, `--self-test` all checks
passed.
