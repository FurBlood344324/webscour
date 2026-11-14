# Contributing

`webscour` is a small tool with a hard constraint, so most of this file is about that constraint.
Read the layout before writing code; the rest is procedure.

## Setup

```bash
git clone https://github.com/FurBlood344324/webscour && cd webscour
python3 -m venv .venv-dev && .venv-dev/bin/pip install ruff build twine
python3 -m unittest discover -s tests      # the unit tests, offline, a few seconds
./scripts/check.sh                         # the gate: lint, format, tests, self-test, build, guards
```

`check.sh` is the definition of releasable and the workflows only call it. `BENCH=1
./scripts/check.sh` adds the extraction benchmark, which needs the network and is therefore not
part of the default run. Python 3.11 is the floor.

## The layout

The import graph is one way: `extract` <- `backends` <- `searx` <- `cli`. Four modules carry the
promise; a few more hang off them.

- **`extract.py`** turns bytes into text: the tokenizer, the reading-tree pruning, the result
  parsers, the sitemap and robots readers, the document router. It must import no network module,
  and `tests/test_extract.py` enforces that by importing it with `socket`, `ssl` and `http`
  blocked. If your change needs to open a connection, it does not belong here.
- **`backends.py`** is everything that talks to the network: the HTTP client, SearXNG, the
  fallback scrapers, the render engines, and the pacing that keeps them polite.
- **`searx.py`** owns the search-backend lifecycle: install, measure, check. It shells out to the
  scripts in `searx/` rather than reimplementing them, because two implementations of "is SearXNG
  healthy" would drift and `wsc doctor` promises exactly one verdict.
- **`cli.py`** is the argv surface: verbs, flags, printing, exit codes. Nothing there opens a
  socket itself.

Around them: **`sources.py`** holds the keyless `--source` endpoints, parser and request together;
**`routes.py`** maps a URL to a structured endpoint the site already publishes; **`argv.py`** is
the single mapping from a JSON tool call to an argv, shared by the MCP server and the pi
extension; **`cache.py`** is the opt-in page store; **`render_venv.py`** owns one thing, the
optional playwright environment under `~/.local/share/webscour/render-venv`, created by
`wsc setup --playwright` and by nothing else.

## Adding a source

A source is a `--source` value that answers one query; its parser and its request live together in
`sources.py` on purpose. Five steps, in this order:

1. Write the parser: a decoded document (a `dict`, a `str`, or XML) in, rows of
   `title`/`url`/`snippet` out, plus `published` only when the source really carries a date. Pure,
   no I/O and no clock.
2. Write the one request beside it using `http` from `backends.py`, then add the name to
   `API_SOURCES` and `FETCHERS`. A source that reports a rate-limit number should hand it back so
   `cmd_search` can print it.
3. Document the name: a row in `docs/sources.md` and in the `README.md` source table.
4. Capture a real response, trimmed to two or three rows, into `tests/fixtures/`, and add a unit
   test beside it. A fixture typed by hand is not a fixture.
5. Add a `chk(...)` to `--self-test` so the parser is covered offline, then run the gate.

Keyless, unauthenticated sources are the default. A source that needs a key is a different
conversation: open a source request issue first, and read the rejection list below.

## Adding a site route

A route is a decision about a URL before any download, and there are two kinds. `routes.py` takes
a URL to an endpoint the site already publishes: add a `Route(...)` to `ROUTES` and a resolver
that returns markdown, never HTML. `extract.py` decides a document format (`document_format`), and
`cmd_fetch` branches on it, so a `.pdf` goes through the local document extractor while an `.html`
stays HTML and keeps the js-shell heuristic.

Two rules. A route that raises `FetchError` is a fallback, never a failure, and `-v` says which
route declined. A route that fires too eagerly is worse than no route: it takes a page away from
the generic extractor, which is usually right.

## Changing the extraction rules

Extraction is measured, not argued. Run the benchmark, read the table, and say what moved:

```bash
python3 tests/bench_extract.py                          # offline, against the captured pages
python3 tests/bench_extract.py --live                   # re-fetch the pages first
python3 tests/bench_extract.py --save-baseline tests/baselines/<next-version>.json
```

The numbers are bytes, lines and a precision proxy, plus a `phrases` recall gate per page that
must not lose a string whatever the byte count says. A pull request that changes a rule states the
per-page diff and updates the baseline in the same commit. Do not lower the bar quietly:
`--tolerance` defaults to 10 percent and raising it is a decision, not a fix.

## Decision records

A choice with real alternatives gets a file in `docs/decisions/`, numbered and not rewritten after
the fact: context, options considered, the choice, the evidence. `0001` through `0005` show the
shape. A change a future reader will ask "why on earth" about needs one; a typo does not.

## Commits

Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), because `cliff.toml` builds the
changelog from them. While the version is 0.x, `feat` bumps the minor and so does `!`: there is no
stable API to break yet, and a 0.x project that jumps to 1.0.0 has lied to every user who reads the
version as "safe to upgrade".

## What will be rejected

- A Python dependency. `dependencies = []` is the first promise, `0001` records why, and the gate
  fails the build for it.
- A paid API that is required rather than optional. Optional already happens (playwright lives in
  its own venv); required makes this a different tool.
- A change that breaks the honesty of the README's limitations section. Where the scrapers degrade
  on a residential IP, the README says so with a date and a number. Deleting the sentence is the
  one edit that is never merged.

Three prose rules the gate enforces: no em dash, no emoji, no absolute home path in a shipped
file. Say what was measured, and paste the output rather than describing it.

## Where to ask

Open an issue with the feature request form and say it is a question, including what you tried.
For anything that should not be public, write to `maintainer@wsc.ashina.live`. The release process
is in [docs/maintaining.md](docs/maintaining.md).
