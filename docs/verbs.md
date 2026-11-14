# Verbs

`wsc` has eleven verbs and one self-test. This page gives each its purpose, its exact flags with
defaults and types, one example, and its exit codes. Every flag below is read from the parser in
`webscour/cli.py`.

Before the verbs, the two rules that apply to all of them.

**stdout is the answer.** Search rows, page text, URL lists, crawl lines and the doctor table all
go to stdout. You can redirect stdout to a file and still have a usable page.

**stderr is silent by default.** It carries only what you need when the exit code is not 0, plus
three exceptions, which are facts about the answer rather than explanations: `render: <engine>`
when a browser produced the text, `cache: hit (<age>)` when the text came from the on-disk cache
instead of the network, and `route: <name>` when a site's own API answered. `-v` (or `--verbose`)
turns on the reasoning: which backend answered, why a page looked hollow, how long the pace slept,
which sitemap answered, which backend read a document. `search`, `setup`, `probe`, `cache` and
`pdf` take no `-v`; `fetch`, `map`, `crawl` and `doctor` do.

Exit codes in general: `0` success, `1` a verdict or a gate failed, `2` a usage error or a
backend that could not answer. argparse exits 2 on a missing positional, an unknown flag or an
invalid choice.

## search

One query, one page of results. `--source` selects the backend; `web` asks the local SearXNG
first and falls back to the DuckDuckGo lite page, the DuckDuckGo html page and Bing, in that
order. Rows print as `N. title - url  [engine,engine]` with the snippet indented below and cut to
200 characters.

| flag | type | default | meaning |
|---|---|---|---|
| `query` | positional, required | none | the search terms |
| `--source` | string | `web` | `web`, `github`, `so`, `hn`, `arxiv`, `discourse:<base>`, or a keyless API source |
| `--limit` | int | `8` | rows wanted; clamped to the range 1 to 30 |
| `--category` | choice | empty | a SearXNG category: `general`, `it`, `science`, `news`, `images`, `files`, `social`. Opt-in because a category changes which engines answer, so it changes the answer |
| `--fresh` | flag | off | the freshness rows only (Google News, BBC), sorted by publication date, newest first |
| `--since` | string, `YYYY-MM-DD` | empty | a date floor for `--fresh` |
| `--json` | flag | off | print an array of objects: `title`, `url`, `snippet`, `engines` |

`--source` also accepts the keyless endpoints `wikipedia`, `openalex`, `crossref`, `arxiv-api`,
`europepmc`, `pubmed`, `pypi`, `npm`, `crates`, `devto`, `wayback`, `googlenews` and `bbc`. See
[sources](sources.md).

```console
$ wsc search "sqlite wal mode concurrent readers" --limit 2
1. SQLite WAL Mode, and How LiteFS Replicates It · The Fly Blog - https://fly.io/blog/wal-mode-in-litefs/  [mwmbl,seznam]
   WAL Mode in LiteFS LiteFS is a distributed file system that magically replicates your SQLite databases. Make an update on one server and, voilà, your cha…
2. SQLite Forum: How does SQLite maintains state? - https://sqlite.org/forum/forumpost/f007a66e693f3c24?raw  [mwmbl]
   I was going through SQLite WAL mode and found the below statement in the docs >**3.1. Automatic Checkpoint** >By default, SQLite will automatically checkp…
```

With `--source github` the command makes two unauthenticated calls, repositories then issues, and
prints one extra stdout line at the end: `-- github rate limit remaining: <n>`.

Exit codes: `0` at least one row printed. `2` for an unknown `--source`, for zero results, and for
a usage error. A failed backend prints `backend <name>: <reason>` on stderr and the command moves
on to the next one; it exits 2 only when every backend failed or returned nothing.

## fetch

One URL as reading text. Plain HTTP by default: one request, HTML tokenized, navigation and
boilerplate dropped, blank lines removed. A page that is a JavaScript shell is retried once
through a render engine, and that retry is what prints `render: <engine>`.

| flag | type | default | meaning |
|---|---|---|---|
| `url` | positional, required | none | `http://` or `https://` |
| `--max-chars` | int | `6000` | cut the text here; a `... (cut at N chars)` line is appended |
| `--grep` | string, a regex | none | keep only matching lines, with one line of context and `>` on the match |
| `--format` | choice | `text` | `text` or `markdown`; markdown keeps headings, links and code fences |
| `--render` | flag | off | force a browser; no silent fallback if none is usable |
| `--render-engine` | choice | `auto` | `lightpanda`, `playwright` or `auto`, which tries lightpanda first |
| `--archive` | flag | off | force the Wayback Machine snapshot; a live page that answers 404 or 410 already does this |
| `--no-route` | flag | off | ignore the structured per-site routes and always take the plain path |
| `--save` | flag | off | also write the page into `./.webscour/` |
| `--save-only` | flag | off | write it and print one index line instead of the page |
| `--fresh` | flag | off | ignore the cache for this call; the network is read |
| `--ttl` | string duration | empty (24h) | cache freshness window, for example `30m` or `7d` |
| `--no-cache` | flag | off | neither read nor write the cache |
| `--max-size` | int | `5242880` | the largest page, in bytes, that `--save` will write |
| `-v`, `--verbose` | flag | off | explain every choice on stderr |

```console
$ wsc fetch https://example.com --max-chars 120 --no-cache
This domain is for use in documentation examples without needing permission. This is not a service; avoid relying on it
... (cut at 120 chars)
```

```console
$ wsc fetch https://example.com --grep "documentation" --no-cache
> This domain is for use in documentation examples without needing permission. This is not a service; avoid relying on it for testing and monitoring purposes.
```

A PDF or docx URL is routed through the same local extractors `pdf` uses. A forum topic URL on
`forums.developer.nvidia.com` is read through its `.json` form, which needs no render.

Exit codes: `0` text printed. `1` `--grep` was given and no line matched; the text was not
printed. `2` the fetch failed (HTTP error, DNS failure, empty document), the text was empty, or
`--grep` was not a valid regex. `--render` with no usable engine exits 2 and names every engine it
tried.

## pdf

A paper or a manual as text, from a URL or a local file. The first working local backend reads it:
`pdftotext` then `markitdown` for a PDF, `pandoc` then `markitdown` for docx and epub. Nothing is
uploaded and no service is involved.

| flag | type | default | meaning |
|---|---|---|---|
| `source` | positional, required | none | an `http(s)` URL or a path on disk |
| `--max-chars` | int | `20000` | cut the text here, with the same cut marker as `fetch` |
| `--format` | choice | `text` | `text` or `markdown`; only pandoc can produce markdown, so a PDF stays plain either way |
| `-v`, `--verbose` | flag | off | name the format and the backend that produced the text |

```console
$ wsc pdf https://arxiv.org/pdf/1706.03762 --max-chars 200
                                            Provided proper attribution is provided, Google hereby grants permission to
                                            reproduce the tables and figures in
… (cut at 200 chars)
```

Exit codes: `0` text printed. `2` the path does not exist, the URL is not a document, no backend
could read the format, or the document has no text layer (a scan). The last case says so on
stderr and stops; OCR is out of scope.

## map

The URL list for a site. It asks four candidate documents in order, the cheapest first:
`/sitemap.xml`, `/sitemap_index.xml`, the `Sitemap:` line in `/robots.txt`, then `/llms.txt`. It
prints the first one that answers.

| flag | type | default | meaning |
|---|---|---|---|
| `url` | positional, required | none | any URL on the site; only scheme and host are used |
| `--limit` | int | `200` | stop after this many URLs; below 1 is raised to 1 |
| `-v`, `--verbose` | flag | off | name the document that answered and how many URLs were withheld |

```console
$ wsc map https://docs.python.org --limit 4
https://docs.python.org/3.11/
https://docs.python.org/3.12/
https://docs.python.org/3.13/
https://docs.python.org/3.14/
```

Exit codes: `0` at least one URL printed. `2` none of the four candidates answered, with
`map: no sitemap, robots Sitemap line or llms.txt answered at <origin>` on stderr.

## crawl

A short polite crawl. It seeds from `map`, then follows same-origin links breadth first, and
prints one line per page: `url  |  title  |  N chars`. It writes nothing to disk.

| flag | type | default | meaning |
|---|---|---|---|
| `url` | positional, required | none | the seed URL |
| `--depth` | int | `1` | link depth; below 0 is raised to 0, and 0 fetches the seed only |
| `--limit` | int | `20` | maximum pages fetched; clamped to the range 1 to 200 |
| `--same-origin` | flag | on | stay on the seed origin; this is the default |
| `--any-origin` | flag | off | leave the origin; mutually exclusive with `--same-origin` |
| `-v`, `--verbose` | flag | off | report the page count, the depth, the origin rule and the pacing |

```console
$ wsc crawl https://example.com --limit 3
https://example.com  |  Example Domain  |  156 chars
```

Every request in a crawl waits so that two live fetches stay at least one second apart, and the
stamp is shared across processes. A crawl of N pages therefore takes at least N seconds.

Exit codes: `0` at least one page printed. `2` nothing was fetched.

## cache

Four verbs over the on-disk cache, which is `<cwd>/.webscour/`: one markdown file per fetched URL
and an index beside them. Reading is on by default with a 24 hour window; writing only happens
when `fetch` was given `--save`, `--save-only`, or when `cache get` misses.

| flag | type | default | meaning |
|---|---|---|---|
| `action` | positional, required | none | `list`, `get <url>`, `prune`, or `path` |
| `url` | positional, optional | none | required by `get` |
| `--older-than` | string duration | `7d` | the prune window |
| `--all` | flag | off | `prune` only: remove the whole directory |
| `--json` | flag | off | print the index as one JSON object |

```console
$ wsc cache list
fetched                 bytes      age format     file
2026-11-15 00:08:34       157       2s markdown   0f115db0-example-com.md
1 entry, 157 bytes, /home/<user>/.webscour
```

`cache get <url>` returns the cached text, and on a miss it fetches the page, saves it and prints
it. It ignores the TTL on purpose: asking for a specific URL means you want that file. `cache path`
prints the directory. `cache prune` reports every file it removed and the bytes freed.

Exit codes: `0` for `list`, `path`, a successful `prune`, and a `get` that answered. `2` for a
`get` with no URL, a bad action (argparse), an unreadable index, or a `get` whose fetch failed.

## doctor

The health check. It reports the systemd user unit, the listener, the loaded engine count, which
engines are blocked in SearXNG's own error table, which engines answered one live probe query,
which engines are silent, the render and document backends, the render venv, the keyless sources,
and one verdict line. It changes nothing.

| flag | type | default | meaning |
|---|---|---|---|
| `--json` | flag | off | print the same report as one JSON object after the table |
| `--live` | flag | off | probe every keyless endpoint once; a dozen requests, so it is not the default |
| `-v`, `--verbose` | flag | off | name which source failed and why, on stderr |

```console
$ wsc doctor
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

The verdict has three forms. `VERDICT DOWN` when nothing is listening or no engine answered.
`VERDICT DEGRADED: <reason>` when lightpanda is missing, when the listener is not loopback only,
or when more than half of the loaded engines are blocked. `VERDICT OK (<n>/<m> engines answering,
<k> blocked)` otherwise.

Exit codes: `0` for `OK`. `1` for `DOWN` and for `DEGRADED`. A script can gate on the exit code
alone and read nothing.

## setup

The installer. Bare `wsc setup` means "install the local SearXNG"; the render fallback is a
separate install and needs its own flag, because a search backend and a browser are two different
capabilities. It is idempotent: a second run reports `unchanged` and restarts nothing.

| flag | type | default | meaning |
|---|---|---|---|
| `--searxng` | flag | off | install the local SearXNG user unit; bare `setup` does this too |
| `--playwright` | flag | off | install the render fallback into `~/.local/share/webscour/render-venv` |
| `--all` | flag | off | both installs in one run |
| `--with-deps` | flag | off | let playwright install chromium's OS packages; needs root |
| `--force` | flag | off | rebuild what is already there |
| `--no-start` | flag | off | install without starting the unit |
| `--check` | flag | off | report state and change nothing |

```console
$ wsc setup --check
src            de722ab
venv           present
settings       1938
state          present
unit           enabled / active
listen         127.0.0.1:8888
lightpanda  /usr/bin/lightpanda
```

Exit codes: `0` everything asked for is in place. `1` lightpanda is not on `PATH` after a SearXNG
install, or the playwright install failed; both print the exact fix. The SearXNG step returns the
bundled installer's own exit code, which is `2` for an unknown option and `1` for a failed
preflight.

## probe

The engine measurement. It asks the local SearXNG a fixed query set and reports, per engine, the
success rate, the median latency, whether the page was a bot check and its category. `--quality`
is the wider measurement that decides which engines are worth keeping.

| flag | type | default | meaning |
|---|---|---|---|
| `--engines` | string, comma separated | all candidates | measure only these engines |
| `--quality` | flag | off | the 30-query coverage and precision measurement |
| `--write` | flag | off | with `--quality`, write the survivors to the engine state file |
| `--json` | flag | off | print the rows as JSON |

```console
$ wsc probe --engines naver,bing
 1/2 naver          100.0%  median 0.83s  blocked 0  general web
 2/2 bing            40.0%  median 0.18s  blocked 0  general web

keep (>=70% success, no block, web category): naver
```

`--write` only stores a set the measurement kept: an empty result is refused and the settings are
left untouched. The file it writes is not live until the installer renders it again, and the
command prints that reminder.

Exit codes: `0` the measurement ran. `1` the local SearXNG did not answer, or `--write` had an
empty set to store. `2` an unknown option reached the bundled script.

## mcp

A stdio JSON-RPC server that exposes one tool, `web_scour`, over the standard library only. It is
a front end, not a second implementation: it builds an argv with `webscour/argv.py` and runs the
same commands you would type.

| flag | type | default | meaning |
|---|---|---|---|
| none | | | it speaks JSON-RPC on stdin and stdout |

```console
$ wsc mcp
```

Exit codes: `0` the client closed the stream. `2` no server file was found, which happens in a
wheel that does not ship one; the message names the three paths it looked in.

## tool-argv

The mapping itself, for a front end that is not Python. It takes one JSON object of tool
parameters and prints the argv, the error if there was one, and the command line as you would
type it.

| flag | type | default | meaning |
|---|---|---|---|
| `--json` | string, JSON | none; stdin is read when absent | one tool call: `{"action": ..., "query" or "url": ..., ...}` |

```console
$ wsc tool-argv --json '{"action":"fetch","url":"https://example.com","max_chars":500}'
{"argv": ["fetch", "https://example.com", "--max-chars", "500"], "error": "", "command": "wsc fetch https://example.com --max-chars 500"}
```

The action is one of `search`, `fetch`, `pdf`, `map` or `crawl`. `build` never raises: an
unusable call comes back with a non-empty `error` and an empty `argv`, which is why a front end
does not need a try/except to stay quiet.

Exit codes: `0` a usable argv. `2` invalid JSON, or a call the mapping refused.

## The entry points

`wsc` is a console script that calls one function, `webscour.cli:main`. Four spellings reach that
function and the same exit code.

- `wsc <verb>` is the console script, installed by pipx, uv or pip.
- `python3 -m webscour` and `python3 -m webscour.cli` run `main()` in process. Use these from a
  checkout with no build step, and in a test that must not depend on `PATH`. The module entry
  point also maps `Ctrl-C` to exit 130 and a closed stdout pipe to exit 0.
- `web` is the name the tool had before it was published. Where a local wrapper for it exists it
  `exec`s `wsc` rather than reimplementing anything, so an old habit or an old script reaches the
  same code. That wrapper lives outside this repository and is not installed by the package.

## `--self-test`

```console
$ wsc --self-test
PASS ddg lite parser
...
SUMMARY pass=30 fail=0
```

Thirty checks of the pure parts: the result parsers, the source parsers, the extraction rules, the
markdown conformance suite, the document router, the sitemap reader, the origin filter, the
js-shell heuristic and the no-identity check. It runs offline with no SearXNG and no render
backend, which is why `scripts/check.sh` uses it as a gate. Exit code `0` when every check passed,
`1` otherwise.

## Global flags

| flag | meaning |
|---|---|
| `-h`, `--help` | print the usage block and exit 0 |
| `-V`, `--version` | print `webscour <version>` and exit 0 |
| `--self-test` | run the offline checks |

`wsc` with no arguments prints the same usage block and exits `1`, so an empty invocation is not
mistaken for success. An unknown verb prints `unknown command '<name>'` on stderr, the usage block
on stdout, and exits `2`.
