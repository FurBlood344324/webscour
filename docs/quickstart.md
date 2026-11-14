# Quickstart

You need Python 3.11 or newer and Linux. The render path needs lightpanda on `PATH`; everything
else is optional.

## 1. Install

```bash
pipx install webscour                        # recommended: isolated venv, `wsc` on PATH
uvx webscour search "sqlite wal mode"        # no install at all, one run
uv tool install webscour                     # uv's managed tool environment
pip install --user webscour                  # plain pip, user prefix
```

From a checkout, with no build step:

```bash
cd webscour
python3 -m webscour.cli search "sqlite wal mode"
```

None of those install a Python dependency, because there are none. lightpanda is a system binary
and pip does not and should not manage it. Install it before you run anything that renders:

```bash
yay -S lightpanda-bin                                                        # Arch / AUR
curl -fsSL https://pkg.lightpanda.io/install.sh | bash -s "<version>"        # any Linux
brew install lightpanda-io/browser/lightpanda                                # Homebrew
```

`docs/install.md` has the full installer page, including the uninstall and the troubleshooting
checklist.

## 1b. Install the agent skill, if your agent reads one

The skill is what tells a model when to reach for `wsc` and which source to pick. It installs
separately from the tool, because a skill is read by the agent and the CLI is run by the shell:

```bash
pi install npm:webscour                       # pi, shortest form
npx skills add webscour                       # the open skills CLI
claude plugin marketplace add FurBlood344324/webscour   # Claude Code, then /plugin install webscour
```

With none of those, hand the agent the raw file:
`https://raw.githubusercontent.com/FurBlood344324/webscour/main/skill/SKILL.md`.

## 2. Install the search backend

```bash
wsc setup
```

That installs the bundled SearXNG: a shallow clone at a pinned commit, a venv, a generated
settings file, and one systemd user unit bound to `127.0.0.1:8888`. It also verifies that
lightpanda is on `PATH` and prints the install hint when it is not. The command is idempotent, so
a second run reports `unchanged` and restarts nothing.

`wsc setup` is a command you run, never a post-install hook. See [self-hosting](self-hosting.md)
for the paths it writes and how to remove them.

## 3. Check the machine

```bash
wsc doctor
```

`wsc doctor` reports in this order, and ends in one verdict line:

- `unit` is `active` and `enabled at boot`, because the systemd user unit is running.
- `listen` is `127.0.0.1:8888`, and nothing else. A non-loopback address is reported as
  `NOT loopback only` and degrades the verdict.
- `engines` is the number of engines the local instance loaded; `answered` is the subset that
  returned a row for one live probe query; `blocked` is SearXNG's own error table. Some engines
  are blocked from a residential IP, which is expected, not a fault.
- `backends` names lightpanda, playwright, pdftotext, pandoc and markitdown with `ok` or `no`.
- `render-venv` is either `absent` with the fix line, or the venv path with its health.
- `sources` lists the keyless endpoints and whether each is configured. `--live` probes them, at
  the cost of about a dozen requests, which is why it is not the default.

The verdict is one of `VERDICT OK`, `VERDICT DEGRADED: <reason>` or `VERDICT DOWN`. `OK` exits 0;
the other two exit 1, so a script can gate on it. Add `--json` for the same report as data.

```text
unit      active (enabled at boot)
listen    127.0.0.1:8888
engines   10 loaded
blocked   abcnyheter, brave, quark, yacy
answered  bing, mwmbl, naver, rawweb, seznam
silent    abcnyheter, brave, quark, wikibooks, yacy
backends  lightpanda=ok  playwright=no  pdftotext=ok  pandoc=ok  markitdown=ok
          playwright: not installed (only needed for a page lightpanda cannot render)
render-venv  absent (/home/<user>/.local/share/webscour/render-venv/bin/python)
             fallback only: wsc setup --playwright
sources   14 keyless endpoint(s)
          wikipedia    configured
          ...
VERDICT OK (5/10 engines answering, 4 blocked)
```

A blocked count above half of the loaded engines is `DEGRADED`, not `OK`. That threshold is
deliberate: a meta-search is expected to lose upstreams, a majority is not.

## 4. Three real commands

Search. Rows are numbered, the snippet is cut to 200 characters, and the bracket tag names the
upstream engines that produced the row:

```console
$ wsc search "sqlite wal mode concurrent readers" --limit 3
1. SQLite WAL Mode, and How LiteFS Replicates It · The Fly Blog - https://fly.io/blog/wal-mode-in-litefs/  [mwmbl,seznam]
   WAL Mode in LiteFS LiteFS is a distributed file system that magically replicates your SQLite databases. Make an update on one server and, voilà, your cha…
2. Introduce Sqlite WAL journal mode by lainedfles · Pull Request #… - https://github.com/evilsocket/opensnitch/pull/1011  [mwmbl]
   Saved searches Use saved searches to filter your results more quickly You signed in with another tab or window. Reload to refresh your session.You signed…
3. Write-Ahead Logging - https://www.sqlite.org/wal.html  [seznam]
   By default, SQLite does a checkpoint automatically when the WAL file reaches a threshold size of 1000 pages. (The Sqlite_Default_WAL_Autocheckpoint compile-time option can be used to specify a differ…
```

Fetch. Plain HTTP, no browser, and a cut marker when the text is longer than `--max-chars`:

```console
$ wsc fetch https://example.com --max-chars 120 --no-cache
This domain is for use in documentation examples without needing permission. This is not a service; avoid relying on it
... (cut at 120 chars)
```

Map. One URL per line, from the site's sitemap, a `Sitemap:` line in robots.txt, or llms.txt:

```console
$ wsc map https://docs.python.org --limit 4
https://docs.python.org/3.11/
https://docs.python.org/3.12/
https://docs.python.org/3.13/
https://docs.python.org/3.14/
```

Each of those writes its answer to stdout. When a render was unavoidable, stderr carries exactly
one extra line, `render: lightpanda` or `render: playwright`; a cache hit and a structured route
announce themselves the same way. Add `-v` to see why the tool chose what it chose.

## 5. If you are an agent

Two more entry points reach the same code without a shell in between:

```bash
wsc mcp         # a stdio JSON-RPC server with one tool, web_scour
wsc tool-argv --json '{"action":"fetch","url":"https://example.com"}'
```

The second prints the command line the MCP server and the pi extension both build, so what a
front end runs is inspectable. `--source web` is the default for all of them.

## 6. Where to go next

- [verbs](verbs.md) for every flag, its default and its type.
- [sources](sources.md) to query GitHub, Stack Overflow, Hacker News, arXiv, a Discourse forum or
  one of the keyless paper and package endpoints instead of the general web.
- [privacy](privacy.md) for what leaves the machine.
