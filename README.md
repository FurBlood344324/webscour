<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/mark-dark.svg">
    <img src="assets/mark-light.svg" alt="webscour" width="112">
  </picture>
</p>

<p align="center">
  <b>webscour</b><br>
  A keyless web CLI for agents.<br>
  Search, page text, PDFs, sitemaps and a polite crawl. No API key. No account. No log.
</p>

<p align="center">
  <a href="https://pypi.org/project/webscour/"><img src="https://img.shields.io/pypi/v/webscour?color=black" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-black" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-black" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/platform-linux-black" alt="Linux">
  <img src="https://img.shields.io/badge/dependencies-none-black" alt="No dependencies">
</p>

`wsc` (the command webscour installs) asks a local SearXNG first, falls back to scrapers and
structured APIs, and prints text sized for a terminal instead of raw HTML. The standard library is the
whole stack; the only system binaries are the ones you choose to install for rendering and documents.

## Install

The Rust crate is the way in now: it is keyless search only, one binary, no Python and no system
binaries to audit.

```bash
cargo install webscour         # the crate is `webscour`, the binary is `wsc`
```

Rust 1.75 or newer. SearXNG stays optional and is still what makes `--source web` answer well; if
you have the unit from the Python tool it keeps working, and `WEBSEARCH_SEARXNG` points the crate
at any instance. `rust/README.md` has the sources, the flags and the evidence.

### The Python install (retired)

The `pipx`, `uvx`, `uv tool` and `pip` lines below still install the Python tool, and that tool
still answers, but it is retired: the port is where the work goes and the Python entry point is
being wound down. Use `cargo install webscour` instead. The tombstone note for the Python install
(what it did, why it goes, what replaced it) lands with the removal, not before it, so this page is
the whole story until that commit.

```bash
pipx install webscour          # retired: installs the Python tool, not the crate
uvx webscour search "pyproject vs setup.py"   # retired for the same reason
uv tool install webscour
pip install --user webscour
```

Or, on Linux, the installer that also sets up the search backend:

```bash
curl -LsSf https://wsc.ashina.live/install.sh | sh
wsc setup                      # installs SearXNG as a systemd user unit
wsc doctor                     # one line: OK, DEGRADED or DOWN
```

### Install with an agent

Paste this into Claude Code, pi, dsh, or any agent that can run a shell:

```text
Install webscour, a keyless web CLI. Run:
  curl -LsSf https://wsc.ashina.live/install.sh | sh
Then run `wsc doctor`. A good report says lightpanda present and the SearXNG unit active, with
one VERDICT line ending in OK. If the installer is unavailable, fall back in this order:
`uv tool install webscour`, then `pipx install webscour`, then `python3 -m pip install --user
webscour` (skip the last one on Debian or Ubuntu if it refuses with externally-managed-environment).

Ask the user before running `wsc setup`, because it installs a systemd user unit on their machine.
Use exactly one install method. The skill file, if your agent supports skills, is at
https://raw.githubusercontent.com/FurBlood344324/webscour/main/skill/SKILL.md
```

From a checkout, the same thing without a build step:

```bash
cd webscour
python3 -m webscour.cli search "pyproject vs setup.py"
```

**System requirements: python 3.11+, lightpanda, linux.** No Python dependencies are installed, by design:
`dependencies = []` in `pyproject.toml` is a decision, not an omission. Everything else is a system binary,
which pip cannot manage and should not pretend to.

- **lightpanda** is required. It is the render engine, and `wsc doctor` fails when it is missing.
- Linux only because `wsc setup` installs a systemd **user** unit for SearXNG. The crawler itself runs on
  macOS, and lightpanda ships for it too; the limit is the service, not the scraper.
- Optional: `pdftotext` (poppler) for PDF, `pandoc` for docx/epub, `markitdown` as a last resort, and
  playwright as a render fallback.

Install lightpanda from one of these, in the order that usually applies:

```bash
yay -S lightpanda-bin                       # Arch / AUR; nightly variant: lightpanda-nightly-bin
curl -fsSL https://pkg.lightpanda.io/install.sh | bash -s "<version>"   # any Linux; needs curl, jq, sha256sum
# Debian/Ubuntu: the .deb published with each tagged release
brew install lightpanda-io/browser/lightpanda                          # Homebrew
```

The one-liner installs to `~/.local/bin/lightpanda`; `LIGHTPANDA_DIR` overrides the directory. `wsc setup`
verifies lightpanda on PATH and never installs it, because a package install that downloads and runs a
binary is something a user has to audit rather than trust.

### What is required, and what is optional

| piece | needed for | installed by |
|---|---|---|
| python 3.11+ | everything | you |
| SearXNG | `search --source web` | `wsc setup` (SearXNG only) |
| lightpanda | `--render`, and the retry of a hollow page | you, from the list above |
| playwright | the render fallback, only for a page lightpanda defeats | `wsc setup --playwright` |
| pdftotext / pandoc / markitdown | `wsc pdf`, and docx/epub | you, optional |

playwright is the one Python package this project can use, and the tool installs it into a directory
it owns rather than into your environment:

```bash
wsc setup --playwright              # ~/.local/share/webscour/render-venv, then chromium
wsc setup --playwright --with-deps  # also let playwright install chromium's OS libraries (needs root)
```

`pip install webscour` never does this: setup is a command you run, not a post-install hook. The lookup
order for the fallback is `WEBSCOUR_PLAYWRIGHT_PYTHON`, that venv, the running interpreter, then
`python3`; it never searches your environment manager. `wsc doctor` reports the venv, its health, and
whether its chromium build still matches the installed playwright package. A missing playwright is a
note. A missing lightpanda is a failure.

`wsc setup` alone still means "install SearXNG"; `--all` does both installs in one run.

### Claude Code, through MCP

The tool is also an MCP server, so a client that speaks MCP can register it once and stop shelling out.
Standard library only: there is no `mcp` package to install, and the server is a second door onto the same
executable, not a second implementation.

```bash
claude mcp add webscour -- wsc mcp
```

That is the whole configuration: one tool named `web_scour` with `action`, `query`, `url`, `source`,
`category`, `max_chars`, `grep`, `fresh` and `archive`. Every call runs the same argv builder the CLI uses,
so a flag cannot mean one thing on the command line and another through the protocol.

Fetched page text is returned inside explicit delimiters with a warning above it. A page can contain a
prompt injection and the wrapper says so; a cooperating model treats the block as data. It is a signpost,
not a sandbox, and `mcp/README.md` says exactly that.

`mcp/README.md` also covers running it by hand, the pi route and the reason `wsc mcp` exists rather than
`python3 -m mcp.server`.

### Agent skill

The repo is also a pi package and a Claude Code marketplace.

```bash
pi install npm:webscour    # adds skill/SKILL.md as a skill, no path to remember
```

The npm package is the skill and a small `wsc` shim; the tool itself is Python and is installed
separately (`pipx install webscour`). `package.json` at the repo root declares the skill, so a git
source works too; `pi/package.json` declares the same skill when `pi/` is the source.

Claude Code, two steps and no owner name to remember (2.1.275 or later):

```bash
claude plugin marketplace add https://wsc.ashina.live/marketplace.json
claude plugin install webscour
```

The marketplace file is served from the same domain as the installer, so the line carries no
account name; only that file mentions where the repository lives. From a checkout, the local form
is `claude plugin marketplace add ./.claude-plugin/marketplace.json`.

`.claude-plugin/marketplace.json` lists one plugin whose `source` is `./skill`, with `skills: ["."]` because
that directory is the skill itself rather than a folder of `<name>/SKILL.md` subdirectories.

## First run

```bash
wsc setup      # installs the local SearXNG unit, then checks lightpanda
wsc doctor
```

```
unit      active (enabled at boot)
listen    127.0.0.1:8888
engines   10 loaded
blocked   abcnyheter, brave, quark, yacy
answered  bing, mwmbl, naver, rawweb, seznam, yacy
silent    abcnyheter, brave, quark, wikibooks
backends  lightpanda=ok  playwright=ok  pdftotext=ok  pandoc=ok  markitdown=ok
VERDICT OK (6/10 engines answering, 4 blocked)
```

`wsc setup` is idempotent: a venv under `~/.local/share/searxng`, settings under `~/.config/searxng`, one
systemd user unit on loopback, no docker and no sudo. `--check` reports state without touching anything,
`--force` rebuilds the venv, `--no-start` installs without starting.

Then:

```bash
wsc search "python packaging pyproject" --limit 3
```

```
1. Packaging Python Projects - Python Packaging User Guide - https://packaging.python.org/en/latest/tutorials/packaging-projects/  [naver,seznam]
   This tutorial walks you through how to package a simple Python project. It will show you how to add the necessary files and structure to create the package, how to build the package, and how to uploa…
2. PEP 609 – Python Packaging Authority (PyPA) Governance | peps.py… - https://www.python.org/dev/peps/pep-0609  [mwmbl]
   This document describes a governance model for the Python Packaging Authority (PyPA). The model is closely based on existing informal practices and the …
```

Each row names the engines that produced it, so a result from one weak upstream is visible as such.
`--json` prints the same rows as objects. Exit codes: 0 answered, 2 nothing answered or a bad verb.

## Verbs

| Verb | What it does |
|---|---|
| `wsc search "<q>"` | one query, at most 30 rows, engine tags, optional `--json`, `--source` selects the backend |
| `wsc fetch <url>` | a page as text; `--max-chars`, `--grep` (context lines around a match), `--render`, `--render-engine`, `-v` |
| `wsc pdf <url\|path>` | a paper or manual as text, through pdftotext, pandoc or markitdown; `-v` names the backend |
| `wsc map <url>` | the URL list from sitemap, robots, llms.txt; `--limit` (default 200); `-v` names the source |
| `wsc crawl <url>` | links from that seed, same origin by default, `--depth`, `--limit`, `--any-origin`, `-v` |
| `wsc setup` | installs SearXNG and verifies lightpanda; `--playwright` installs the render fallback into its own venv, `--all` does both, `--check` reports without changing anything |
| `wsc doctor` | unit, listener, engine health, render backends, the render venv, one `VERDICT OK\|DEGRADED\|DOWN` line, `--json` |
| `wsc probe` | measures which engines this IP can use; `--quality --write` stores the survivors |
| `wsc cache list\|get\|prune\|path` | the on-disk captures under `./.webscour/`; `--save` writes one, `--fresh` bypasses a hit |
| `wsc mcp` | the same tool over stdio as a JSON-RPC MCP server, one tool named `web_scour` |
| `wsc tool-argv --json '<params>'` | the argv builder the MCP server and the pi extension both call, so neither owns a flag string |
| `wsc --self-test` | 29 offline checks of the parsers, the extraction rules, the router and the shell heuristic |

Output is the answer. By default stderr carries failures only, so `wsc fetch url > page.txt` leaves it
empty; `-v` explains every choice. When a page really is a JavaScript shell, plain HTTP comes back hollow
and one render is attempted; that fallback prints exactly one line, `render: lightpanda` or
`render: playwright`. A short page with real text is complete at any length, so `example.com` costs no
browser launch.

Two more stderr lines a caller can rely on: `route: <name>` when a known site is read through its own API
rather than scraped, and `cache: hit (2h ago)` when a capture is replayed instead of fetched again.

Exit codes: `0` the question was answered, `1` a usable answer was not produced and the reason is on
stderr (a 404, a block, an empty document), `2` the command line was wrong. A non-zero exit is a real
failure, never an empty result.

## Sources

| `--source` | Service | Notes |
|---|---|---|
| `web` (default) | local SearXNG, then DuckDuckGo lite, DuckDuckGo html, Bing | each row tagged `[naver,bing]`; a fallback prints one `backend <name>: <reason>` line |
| `github` | api.github.com repositories and issues | unauthenticated, 10 requests/min, remaining budget printed |
| `so` | Stack Exchange API, `site=stackoverflow` | answered/open, tags |
| `hn` | hn.algolia.com | story points, comment counts |
| `arxiv` | export.arxiv.org Atom | title, id URL, abstract |
| `discourse:<base>` | `<base>/search.json` | e.g. `discourse:https://forums.developer.nvidia.com` |

A `fetch` on a forum topic URL (`forums.developer.nvidia.com/t/...`) reads the topic's `.json` form and
prints `#post author` with plain text, which is far cleaner than the HTML and needs no render.

## Privacy

Only the query leaves the machine, through the local SearXNG to the upstream engines. No cwd, no host, no
user, no project name, no identifiers, no telemetry, and no log file: the tool writes nothing except its
one-second pacing stamp in `~/.cache/web/last-live`.

The SearXNG unit drops the query from its own logs. Access log off, level WARNING, autocomplete off (no
keystroke leaves the box), and the bundled `serve.py` filters every log record so that any URL query
string becomes `?<query withheld>`. The journal keeps engine errors and none of the terms. That is a
feature, and the reason the unit runs a wrapper instead of stock SearXNG.

This is not anonymity. Your IP talks to whichever upstream engines are enabled; a local proxy does not
change that. Send generic technical terms and keep private context out of a query.

`map` and `crawl` send only a URL to the target site, never a query, and every live request is paced to one
per second across processes, so a shell loop cannot look like a scraper.

## How it differs from firecrawl, and from an MCP server

firecrawl is a hosted pipeline for turning sites into clean markdown at scale: crawl jobs, JS rendering
farms, structured extraction, and an API key. webscour is the opposite shape, a local tool for one page or
one query, with no account, no credits and no state, and it tells you which engine or backend answered
instead of hiding the plumbing. An MCP server is a transport: it puts the same kind of tool behind a
protocol so a chat client can call it, and then something still has to be installed, run and authenticated.
`wsc` is a plain executable that an agent, a shell script or a human calls the same way, so no server has to
be running for it to work. When a client only speaks MCP, `wsc mcp` exposes the same tool over stdio: one
tool, standard library only, no `mcp` package to install. The CLI is the base representation; the server is
a second door onto it, not a second implementation.

## Limitations

- **Linux only**, because of the systemd user unit. Without the unit the scrapers answer from a residential
  IP, and mostly they answer CAPTCHA.
- **The scrapers degrade on residential IPs.** Measured on 2026-11-13 with 30 generic queries, per engine;
  a meta-search needs coverage (how often an engine helps) and precision (share of its rows that are on
  topic), kept means coverage >= 10 % and precision >= 60 %:

| engine | cover | prec | rows | | engine | cover | prec | rows |
|---|---|---|---|---|---|---|---|---|
| naver | 90.0 % | 80.1 % | 403 | | wikibooks | 20.0 % | 93.8 % | 16 |
| abcnyheter | 70.0 % | 95.3 % | 214 | | wiby | 13.3 % | 42.9 % | 21 (dropped) |
| rawweb | 53.3 % | 98.8 % | 82 | | wikiversity, wikiquote | <=6.7 % | 100 % | 1-2 (dropped) |
| bing | 36.7 % | 60.0 % | 180 | | encyclosearch, wikisource | 3.3 % | 50 % | 2-14 (dropped) |
| yacy | 30.0 % | 96.7 % | 90 | | brave | 0 % this pass | n/a | kept by name |

  duckduckgo, google, mojeek, qwant, startpage, searchmysite and yandex answered CAPTCHA, "access denied"
  or a parsing error from a residential IP and are not in the set. Median merged query 5.0 s. Kept:
  naver, abcnyheter, rawweb, bing, yacy, wikibooks, brave. `wsc probe --quality --write` repeats the
  measurement on your own IP; the table above is one machine on one day, not a promise.
- **No render backend is installed by pip.** lightpanda is the one to install, and playwright is the
  fallback for a page that defeats it. `wsc doctor` says which is present.
- **Scanned PDFs have no text layer.** `wsc pdf` says so and stops; OCR is out of scope.
- **Snippets are quotes from a scraped page.** Open the URL before relying on a claim, and treat a row whose
  title and url lack every query term as drift, which the tool drops.
- **GitHub is unauthenticated**: 10 requests/min per IP, and `--source github` makes two calls.

## Development

Everything a release needs runs on this machine, offline:

```bash
python3 -m venv .venv-dev && .venv-dev/bin/pip install ruff build twine
./scripts/check.sh          # lint, format, tests, --self-test, build, twine, guards
BENCH=1 ./scripts/check.sh  # also the extraction benchmark (needs the network)
./scripts/release.sh 0.2.0  # local: gate, stamp, changelog, tag. Never pushes or publishes
```

`scripts/check.sh` is the only definition of "releasable": it prints one `PASS <name>` line per
check and a summary, and the workflows in `.github/workflows/` are thin wrappers that call it. It
runs with no network, no SearXNG and `LIGHTPANDA=0`.

The extraction benchmark compares our reading text with trafilatura's on six pages, from captured
fixtures in `tests/fixtures/bench/`, and fails when a page regresses past `tests/baselines/`. The
reference extractor is a throwaway venv, never a dependency:

```bash
python3 -m venv /tmp/tfvenv && /tmp/tfvenv/bin/pip install trafilatura
python3 tests/bench_extract.py                    # table, and a check against the baseline
python3 tests/bench_extract.py --live             # re-fetch the pages first
python3 tests/bench_extract.py --save-baseline tests/baselines/0.2.0.json
```

Design decisions live in `docs/decisions/`, one short record each, with the evidence and the
condition that would reverse it.

## License

MIT. See [LICENSE](LICENSE).
