# webscour

`webscour` is a Linux-first, dependency-free Python CLI that fetches the web for agents. The
executable is `wsc`. It searches the web through a local SearXNG first and falls back to
scrapers, queries GitHub, Stack Overflow, Hacker News, arXiv, Discourse and fourteen keyless API
endpoints directly, fetches a page as text or markdown, reads a PDF, maps a site from its
sitemap, and crawls a few pages politely. It renders with lightpanda, and playwright is the
fallback for a page that defeats lightpanda. It installs no Python package, needs no key and
opens no account.

It is not fast, and it does not claim to be. It is local, keyless, logless and terminal first:
one executable, text on stdout, failures on stderr, and an answer sized for an agent's context
instead of a browser tab.

**No key. No account. No log.**

```bash
wsc search "sqlite wal mode concurrent readers" --limit 5
wsc fetch https://example.com --max-chars 2000
wsc doctor
```

## Three ways in

The CLI is the source of truth. Two front ends call it rather than reimplementing it, and both
route their arguments through one mapping in `webscour/argv.py`, so a flag is added once and all
three stay in step.

| front end | how you reach it | what it is |
|---|---|---|
| CLI | `wsc <verb>` | the tool itself, documented on these pages |
| MCP server | `wsc mcp` | a stdio JSON-RPC server exposing one tool, `web_scour`, over the standard library only |
| pi tool | `extensions/pi/` | a pi extension that shells out to `wsc tool-argv` and runs the command it gets back |

`wsc tool-argv --json '{"action":"fetch","url":"https://example.com","max_chars":500}'` prints the
exact command line the other two front ends would run, which is the cheapest way to see what the
mapping does.

## The documentation

| page | read it for |
|---|---|
| [quickstart](quickstart.md) | install, run `wsc setup`, see real commands with their output, read what `wsc doctor` reports |
| [verbs](verbs.md) | every verb, its exact flags with defaults and types, an example, and the exit codes |
| [sources](sources.md) | the `--source` table, what each source queries, its rate limit, and how to choose one |
| [privacy](privacy.md) | exactly what leaves the machine, what never does, and how to verify the logging claim |
| [self-hosting](self-hosting.md) | what `wsc setup` writes, a different port, a remote SearXNG, clean removal |
| [contributing](contributing.md) | the module layout, the test command, the benchmark, the commit convention |

[routing.md](routing.md) is the cost and decision table for the source layer, [install.md](install.md)
covers the installer and the uninstall, and [maintaining.md](maintaining.md) is the release runbook.
The reasoning behind the five structural choices is in [decisions/](decisions/).

## Requirements, in one line each

Python 3.11 or newer. Linux, because `wsc setup` installs a systemd user unit. lightpanda on
`PATH` is required for rendering; `pdftotext`, `pandoc` and `markitdown` are optional and only
`wsc pdf` uses them. `wsc doctor` reports which of those it can see and ends in one verdict line.

Licence: MIT.
