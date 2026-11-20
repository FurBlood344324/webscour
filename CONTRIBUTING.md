# Contributing

`webscour` is one Rust crate with a hard constraint: one binary, four direct dependencies, keyless
search only. Read the layout before writing code; the rest is procedure.

## Setup

```bash
git clone https://github.com/FurBlood344324/webscour && cd webscour/rust
cargo test --release                       # the unit tests and the fixture suite, offline
cargo clippy --release --all-targets       # must be 0 warnings
./target/release/wsc --self-test           # 35 checks, compiled in
```

Rust 1.75 is the floor. `cargo test` is offline; nothing in the suite opens a socket, because the
fixtures are captured payloads read from disk.

## The layout

The module graph is one way: `row` and `util` ← `net` ← `html`, `search`, `sources` ← `backends` ←
`selftest`, `main`.

- **`row.rs`** is the output: `Row`, the two clipping styles (`...` at parse, `…` at render) and
  the text renderer. The keys are title, url, snippet, engines, published, in that order.
- **`util.rs`** is the pure helpers: URL quoting and decoding, `terms`, `on_topic`, `related`,
  `dedupe`, `prefer_on_topic`, and the shared pace file that keeps one live query per second across
  processes.
- **`net.rs`** is everything that talks to the network: one blocking HTTP call, `FetchError`
  carrying the status, header echo, and the JSON helpers. `html.rs`, `search.rs`, `sources.rs` and
  `backends.rs` call into it.
- **`html.rs`** holds the three SERP parsers over the HTML5 tree, one pass per field.
- **`search.rs`** holds the sources that answer a search endpoint: github repositories and issues,
  Stack Exchange, HN, arXiv, Discourse.
- **`sources.rs`** holds the keyless `--source` values, each as a pure parser plus its one request,
  and the parser table the router uses.
- **`backends.rs`** owns the `web` chain: SearXNG first, then DDG lite, DDG html, Bing.
- **`main.rs`** is the argv surface: one verb, the flags, printing, exit codes. Nothing there opens
  a socket itself.
- **`selftest.rs`** compiles the fixtures in with `include_str!`, so a built binary proves itself.

## Adding a source

A source is a `--source` value that answers one query; its parser and its request live together in
`sources.rs` on purpose. Five steps, in this order:

1. Write the parser: a decoded document (JSON, XML, or a string) in, rows of
   `title`/`url`/`snippet` out, plus `published` only when the source really carries a date. Pure,
   no I/O and no clock.
2. Write the one request beside it, register the name in the parser table, and let a source that
   reports a rate-limit number hand it back so `main.rs` can print it.
3. Document the name: a row in the source table in `README.md` and in `rust/README.md`.
4. Capture a real response, trimmed to two or three rows, into `tests/fixtures/`, and add a unit
   test beside it. A fixture typed by hand is not a fixture.
5. Add a check to `--self-test` so the parser is covered offline, then run the gate.

Keyless, unauthenticated sources are the default. A source that needs a key is a different
conversation: open a source request issue first.

## Tests

`cargo test --release` runs three targets: the lib tests (pure parsers, `row`, `util`, `search`,
`backends`), the bin tests (argv and limits) and `tests/fixtures_test.rs`, which reads the same
fixtures from disk that `selftest.rs` embeds. A fixture must pass both paths, so a change that only
one of them sees is a bug.

`wsc --self-test` runs the same parsers against the captured payloads with no network. It is what a
user runs to prove an installed binary, and it must stay at 35 checks or more.

## Decision records

A choice with real alternatives goes in the commit message, and when it changes the row shape or
the output bytes it also goes into the Decisions table in `rust/REPORT.md`: context, the
alternatives, the choice, the evidence. A change a future reader will ask "why on earth" about needs
one; a typo does not.

## Commits

Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), because `cliff.toml` builds the
changelog from them. While the version is 0.x, `feat` bumps the minor and so does `!`: there is no
stable API to break yet, and a 0.x project that jumps to 1.0.0 has lied to every user who reads the
version as "safe to upgrade".

## What will be rejected

- A dependency that is not justified in the Decisions table. Four crates is the promise; a fifth is
  a conversation, not a patch, and a runtime or a second TLS stack is the shortest way to lose it.
- A paid API that is required rather than optional. A keyless source is the default; a required key
  makes this a different tool.
- A change that breaks the honesty of the README's limitations section. Where the scrapers degrade
  on a residential IP, the README says so with a date and a number. Deleting the sentence is the
  one edit that is never merged.

Three prose rules the repository enforces: no em dash, no emoji, no absolute home path in a shipped
file. Say what was measured, and paste the output rather than describing it.

## Where to ask

Open an issue with the feature request form and say it is a question, including what you tried. For
anything that should not be public, write to `maintainer@wsc.ashina.live`.
