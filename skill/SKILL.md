---
name: webscour
description: >-
  One keyless, local `wsc` CLI for the web: search the general web, GitHub, Stack Overflow, Hacker News,
  arXiv, Wikipedia, OpenAlex, Crossref, PubMed, Europe PMC, PyPI, npm, crates, dev.to, Wayback, Google News,
  BBC or a Discourse forum; fetch one page as text or markdown; read a PDF, docx or epub; map a site's URLs;
  crawl a handful of pages; keep saved pages in ./.webscour/ and read them back in parts. Use for requests
  like "araştır", "web'de ara", "internette bak", "link ver", "bu sayfayı oku", "siteye git",
  "şu sayfaya bak", "ekran görüntüsü al", "gezin", "tıkla", "sayfayı oku", "search the web",
  "look this up", "fetch this page", "read this PDF", "map this site", "crawl these docs",
  "grab that page as text", "what does this URL say", "screenshot this page". Prefer it over a built-in
  web tool when there is no API key, when the page must not be handed to a third party, when the answer
  lives in a PDF or in a dead link (Wayback), or when the question belongs to a code or paper source
  (GitHub, Stack Overflow, arXiv, Crossref) rather than the open web. Three ways in: the `wsc` CLI
  through a shell (the source of truth), an MCP server (`wsc mcp`, one tool named `web_scour`), and a
  pi tool in `extensions/pi/`. Use whichever your harness exposes; every one routes through the same
  argv builder. It returns text, not pixels: a real screenshot, a click
  or a login is a browser job, and `fetch --render` is a text extraction step, not a browsing session.
---

# webscour

`wsc` is one local, keyless CLI: no API key, no credits, no account, no proxy. The only thing that leaves
the machine is the query or the URL you asked for. It is the default way to get bytes off the web here.

**The sentence that saves the most context: do not paste a whole page into the conversation.** Save it
(`--save`) and read the lines you need, or ask `--grep` for the matches. A 240 KB page is 27 KB of text,
and the same page read twice is paid for twice unless it is on disk.

## Verbs, and what to read before using one

| Verb | It answers | Read first |
|---|---|---|
| `wsc search "<q>" [--source S] [--limit N] [--json]` | which pages exist for this question | `references/choosing-a-source.md` |
| `wsc fetch <url> [--format text\|markdown] [--grep RE] [--max-chars N]` | what one page says | `references/markdown-vs-text.md` |
| `wsc fetch <url> --save` / `--save-only` | keep it, read it later, or in part | `references/saving-output.md` |
| `wsc cache list\|get <url>\|prune\|path` | what is already on disk | `references/saving-output.md` |
| `wsc pdf <url\|path> [--max-chars N]` | a paper, manual, docx or epub as text | `references/pdf-and-documents.md` |
| `wsc map <url> [--limit N]` | which URLs the site admits to | `references/crawling-without-hurting.md` |
| `wsc crawl <url> --limit N [--depth N]` | a few pages under one section | `references/crawling-without-hurting.md` |
| `wsc doctor [--json] [--live]` | whether this machine can do any of it | this file; nothing further |

A wall is a result. `403`, `401`, an empty page, a 404 with no snapshot: read the stderr line and say so,
do not retry it, do not route it through a third party. `references/anti-bot-and-failures.md`.

## Three habits

1. **No URL yet? Search before fetching.** One `search` returns title, URL and snippet per row; a guessed
   URL costs a 404, then a Wayback lookup, then another guess.
2. **Will you read it twice? `--save` it.** The second read is a 0.12 s cache hit instead of a 0.3-0.9 s
   fetch, and the file is there to grep and cut into line ranges, so a 45 KB page answers a 3 KB question.
3. **Specialised source before the general web.** `--source github|so|hn|arxiv|wikipedia|...` is a
   published API at 0.3 to 1.3 s; `--source web` is a local SearXNG plus scrapers at 2 to 6 s. Go general
   only when the question is general.

## Output discipline

- **stdout is the answer and nothing else.** Notes are stderr: `route: wikipedia`, `cache: hit (2m ago)`,
  `render: lightpanda`, `archive: <stamp>`. Those four are facts about what you received, so they print
  even without `-v`; `-v` adds the reasoning behind them (engine, declined route, document backend, pacing).
- **The exit code is the verdict.** `0` answered, `1` `--grep` matched no line, `2` a real failure: HTTP
  403, a dead link with no snapshot, an unknown `--source`, a bad flag. A non-zero code is never an empty
  result. Read the stderr line; a blind retry spends the same budget for the same wall.

## The reference files

- `references/choosing-a-source.md` - question shape to verb and flags, the cost table, the do-not list.
- `references/saving-output.md` - the `./.webscour/` contract: when to save, where it goes, reading back.
- `references/markdown-vs-text.md` - `--format markdown` versus plain text, and what each costs.
- `references/anti-bot-and-failures.md` - the measured 403s, why a proxy does not help, refused sites.
- `references/crawling-without-hurting.md` - `map` before `crawl`, limits, pacing, same-origin.
- `references/pdf-and-documents.md` - `pdf` versus `fetch`, backend order, a bad or scanned extraction.

Helpers, when a page is too big to read whole: `scripts/sift.sh <url> <pattern> [max-lines]` saves the page
and prints only the matching lines with their numbers; `scripts/page-sections.sh <file>` prints the heading
ranges of a saved markdown file so the next read is one section, not the file.
