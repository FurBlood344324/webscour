# Contributing

This repository has one rule about scope: it is a small, dependency-free, Linux-first CLI. A
change that adds a runtime dependency, a network call in a pure module, or a daemon does not
belong here. Everything else is open.

## Repo layout

The Python package is small on purpose. Each module owns one question, and the boundary between
them is the design.

| module | what it owns |
|---|---|
| `webscour/extract.py` | bytes to text. The HTML tokenizer, the search-result parsers, the sitemap and robots readers, the js-shell heuristic, the document router and the link filter. It defines the four decisions a caller makes on a result (`js_shell_reason`, `document_backend`, `filter_links`, `same_origin`) as pure functions, so the self-test and the unit tests check them with no network and no browser |
| `webscour/backends.py` | everything that talks to the network, plus the pacing. HTTP, the SearXNG client and its start-if-stopped path, the scraper fallbacks, the API clients for GitHub, Stack Exchange, Hacker News, arXiv and Discourse, the bot-check detector, and the render engines behind lightpanda and playwright |
| `webscour/sources.py` | the keyless single-purpose endpoints and their parsers. Each source is a pure parser plus the one request that feeds it, in that order, so a parser is testable without a socket |
| `webscour/routes.py` | URL to a structured endpoint, when a site publishes one. A route returns markdown or text, never HTML, and a route that declines is a fallback rather than an error |
| `webscour/cache.py` | the on-disk cache under `./.webscour/`: one file per fetched URL, an index beside them, a TTL and a prune |
| `webscour/cli.py` | the argv surface: verbs, flags, printing, exit codes. Every command parses its arguments, calls into the modules above, and decides what the user sees. It opens no socket itself |
| `webscour/argv.py` | the one place a JSON tool call becomes a command line. The MCP server and the pi extension both call it, so a flag is added once |
| `webscour/searx.py` | the search-backend lifecycle: install it, measure it, check it. It shells out to the scripts in `searx/` rather than reimplementing them, because those scripts are the ones a user can read and run by hand |
| `webscour/render_venv.py` | the optional playwright fallback and the venv this tool owns. One place is allowed to install a Python package, and this is it |
| `searx/` | the bundled SearXNG installer, the engine probe and the query-redacting WSGI entrypoint. Data shipped for a human to read and run, not a package module: it is not installed, not imported, and deliberately not linted |
| `mcp/` and `extensions/pi/` | the two front ends. Both are thin and both route through `webscour/argv.py` |

`tests/` holds the unit tests, the markdown conformance suite and the extraction benchmark,
`scripts/` holds the release gate, `docs/decisions/` holds the reasoning, and `skill/` holds the
agent-facing instructions that ship as a pi package and a Claude Code plugin.

## The `extract.py` rule

**`webscour/extract.py` must import no network module.** Not `socket`, not `ssl`, not
`http.client`, not `urllib.request`. It may parse `urllib.parse`, because that is string handling,
and it may shell out to a *local* binary (`pdftotext`, `pandoc`, `markitdown`), because reading a
file you already have is not a network operation.

The rule is enforced, not documented and hoped for. `tests/test_extract.py` installs an import
hook that raises `ImportError` for `socket`, `ssl` and `http`, imports the module in a subprocess,
and fails if the import does not survive. If you break the rule, the test names the module you
added.

The reason is testability: the extraction rules are the part most likely to be wrong, and they are
the part that must be checkable with no network, no SearXNG and no render backend. A module that
cannot open a socket cannot accidentally become an integration test. `webscour/sources.py` follows
the same split for the same reason: a parser takes a dict or an XML string, and the request lives
in its own function.

## Run the tests

```bash
python3 -m unittest discover -s tests
```

The suite is offline by construction. The fetch tests inject a fake `http_raw` and a fake
`render_page`, so no test reaches the network. Run a single file or a single class the ordinary
way:

```bash
python3 -m unittest tests.test_extract
python3 -m unittest tests.test_cli.ExitCodeTest
```

The offline self-test is a second, shipping gate over the same pure functions:

```bash
python3 -m webscour --self-test
```

It prints one `PASS <name>` line per check and a `SUMMARY pass=N fail=N` line, and exits non-zero
if anything failed. It runs in an installed package too, which is why it exists next to the unit
tests rather than instead of them.

## Run the release gate

```bash
./scripts/check.sh
```

That is the only definition of "releasable". It prints one `PASS <name>` or `FAIL <name> :: <why>`
line per check and a summary, and stops at the first failure. In order: `ruff check .`,
`ruff format --check .`, the unit tests, `--self-test`, the entry point, the tag agreement, the
build, `twine check`, then a set of guards.

The guards are the interesting part, because each one is a fact that has been wrong before:

- one version, in one place: `webscour.__version__` is the source, and the tag and the pi manifest
  must agree with it.
- text hygiene: no em dash, no en dash and no emoji in the prose we wrote. Fenced blocks are
  exempt on purpose, because a real capture is evidence and transpiling it would be a lie.
- the licence is present and is MIT, and the metadata says so.
- zero runtime dependencies, and no import could smuggle one in. Every module is parsed and its
  imports are checked against `sys.stdlib_module_names`.
- no shipped file names a home directory.
- the wheel holds the package and the `searx/` data files, and nothing else.
- every config file parses.

The script needs `ruff`, `build` and `twine` importable. The documented way to provide them is a
throwaway venv the gate itself does not create:

```bash
python3 -m venv .venv-dev && .venv-dev/bin/pip install ruff build twine
./scripts/check.sh
```

`.github/workflows/` are thin wrappers that install the same three tools and run the same script.
No check exists only in CI: if a workflow learns something `check.sh` does not know, the knowledge
belongs in the script.

## The extraction benchmark

`scripts/check.sh` runs offline, so the benchmark is not part of it. Set `BENCH=1` to add it, or
run it directly:

```bash
python3 tests/bench_extract.py                   # offline, from the captured fixtures
python3 tests/bench_extract.py --live            # re-fetch the pages first, then measure
python3 tests/bench_extract.py --tolerance 0.10  # allowed regression over the baseline
python3 tests/bench_extract.py --save-baseline tests/baselines/0.2.0.json
```

It compares our reading text with trafilatura's on six reference pages, from captured fixtures in
`tests/fixtures/bench/`, and fails when a page regresses past `tests/baselines/` or loses one of
its required phrases. Three numbers per page: bytes produced, lines produced, and `prec`, the
ratio of bytes out to bytes of naive visible text. A tolerance of 0.10 is the default.

trafilatura is measured, never depended on. It lives in a throwaway venv:

```bash
python3 -m venv /tmp/tfvenv && /tmp/tfvenv/bin/pip install trafilatura
```

When that venv is absent the trafilatura column reads `n/a` and only our own baseline decides.
That is deliberate: a benchmark that cannot run must not block a release, but it must be visible
in the output that it did not run.

A baseline is a file, not a claim. When a change is meant to improve extraction, save a new
baseline in the same commit and say in the message what moved.

## Decision records

**Every design choice that cost someone an argument gets a record in `docs/decisions/`.** The
form is fixed, because a record that varies in shape is a record nobody rereads:

- a numbered file name and a title: `0006 - <the decision in one line>`
- `**Status:**` with the date, so a reversal is visible
- `## Context`, `## Options`, `## Choice`, `## Evidence`, `## Reversal condition`

`## Evidence` is the part that separates this from an opinion: a measurement, a date, and the
command that produced it. `## Reversal condition` is the part that keeps a record honest: the
observation that would make you choose differently. A record without both is a press release.

The five records that exist cover: no Python dependencies, lightpanda required with playwright as
a fallback, the extraction tag list adapted from trafilatura's measured settings, silent stderr
with `-v`, and the playwright venv owned by the tool. Read them before you change the thing they
describe; if you disagree, write `0006` rather than editing `0003`.

## Commits

Conventional Commits, one logical change per commit.

```text
feat: add a --format markdown pass to wsc pdf
fix: keep a lone <pre> block verbatim when trimming whitespace
docs: state the loopback bind in the self-hosting page
```

While the major version is 0 there is no stable API to break, so the bump rules are flat:

| commit | bump |
|---|---|
| `fix:` | patch, `0.1.0` to `0.1.1` |
| `feat:` | minor, `0.1.0` to `0.2.0` |
| `perf:`, `refactor:`, `chore:`, `ci:` | patch |
| anything with `!` | minor while the major is 0 |
| anything with `!` | major at `1.0.0` and after |

That last pair is the whole point of `cliff.toml`. A 0.x project that jumps to `1.0.0` because
someone marked a commit breaking has lied to every user who reads the version as "same major, safe
to upgrade". Breaking changes become `1.0.0` when the maintainers say so, not when a commit
message says so.

Grouping into the changelog follows the same file: `feat` goes to Added, `fix` to Fixed, `perf`,
`refactor`, `chore` and `ci` to Changed, `docs` to Documentation, and `test` and `style` are
skipped. A hand-written `## Unreleased` section at the top of `CHANGELOG.md` is for notes no commit
message can carry.

## Cutting a release

```bash
./scripts/release.sh 0.2.0 --dry-run   # show what would happen
./scripts/release.sh 0.2.0             # gate, stamp, changelog, tag, print the push commands
```

The script refuses a dirty tree and a version that does not increase, runs `check.sh`, writes the
version into `webscour/__init__.py` and the pi manifest, builds the changelog section from git
cliff, commits and tags. It never pushes and never publishes: it prints those two commands so the
person running them has read them first. A pushed tag is published to the world, and a published
release cannot be withdrawn. `docs/maintaining.md` is the fuller runbook.

## Style

`ruff` decides formatting and linting, with `target-version = "py311"`, `line-length = 100`, and
sorted imports. Prose is wrapped by hand at roughly 100 columns and the formatter is told to leave
docstrings alone. Two conventions that are not ruff's business:

- **Stdout is the answer, stderr is the diagnostic.** A new line that explains a choice goes
  through `vwarn` and therefore behind `-v`. A lost capability goes through `warn` and always
  prints. A fact about the answer (`render:`, `route:`, `cache: hit`) is its own short exception
  and is documented where the verb is.
- **Report what you cannot confirm.** A docstring or a doc line that states a number should say
  where the number came from, and a fact you did not verify belongs in the report, not in the
  prose.
