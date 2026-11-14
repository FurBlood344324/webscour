# Anti-bot and failures

A wall is a measurement, not a puzzle. Which walls are real, what gets through them, where this stops.

## What a failure looks like

| Exit | stderr says | Meaning |
|---|---|---|
| 2 | `fetch: HTTP 403`, `HTTP 401` | refused this client, or a paywall |
| 2 | `HTTP 404 (dead), asking the Wayback Machine` | gone; the second line says if a snapshot existed |
| 2 | `plain HTTP looked hollow ... no render backend answered` | a JS shell with nothing in it |
| 2 | `TimeoutError`, `URLError ... handshake` | slow, dropping, or TLS never completed |
| 2 | `map: no sitemap, robots Sitemap line or llms.txt answered` | no published URL list |
| 2 | `pdf: no backend could read this pdf: ...` | extraction failed, per backend |
| 1 | `no line matches '<re>' (N lines)` | the page loaded, `--grep` did not match |

Exit 1 is "asked and answered nothing"; exit 2 is "could not ask properly". Neither is an empty page,
and a 2 does not improve on a retry with the same flags.

## The measured walls

Measured 2026-11-14 from a residential IP, one attempt each.

| Site | Result |
|---|---|
| stackoverflow.com question HTML | 403, unless the route fires (it does) |
| npmjs.com package page | 403, Cloudflare "Just a moment" |
| theatlantic.com, economist.com, quora.com, glassdoor.com | 403 |
| wsj.com | 401, hard paywall |
| instagram.com post | hollow, renders to nothing |
| x.com post | 137 B of shell text, login wall |
| linkedin.com/pulse, /jobs | 1.9-2.0 KB of navigation, no content |
| amazon.com/dp/<asin>, /s?k= | 6 KB of chrome, no product description |
| discord.com/blog | TLS handshake timeout |
| washingtonpost.com | read timeout |

Not on the list: wikipedia, docs.python.org, github.com, news.ycombinator.com, pypi.org, arxiv.org,
bbc.com and dev.to answer directly in 0.3-1.1 s.

## A proxy does not help

Firecrawl's free `r.jina.ai` reader is the proxy everybody reaches for, so it was measured against
the walls above:

    wsc fetch https://r.jina.ai/https://www.npmjs.com/package/express

returns `Title: Just a moment...`, `Warning: Target URL returned error 403: Forbidden` and `Enable
JavaScript and cookies to continue`: 270 bytes of the same wall, 0.7 s later. Glassdoor returns the
same CAPTCHA warning. Medium does come back (5.6 KB in 5.4 s), because Medium serves it, not because
the proxy broke anything. A third-party reader is a proxy with the same IP reputation problem plus a
party now holding your URL. Not a bypass, not used here.

## What does work

Site protocols, not workarounds. `fetch` already tries these; `--no-route` disables them.
`stackexchange` uses `api.stackexchange.com/2.3/questions/<id>?filter=withbody`; `github-repo`,
`github-blob` and `github-issue` use `api.github.com` and `raw.githubusercontent.com`; `arxiv` reads
the paper's HTML at `arxiv.org/html/<id>` and declines below 500 chars; `hackernews` reads
`hn.algolia.com/api/v1/items/<id>`, the whole comment tree; `wikipedia` reads
`api/rest_v1/page/summary` plus `/html` as markdown.

A declined route says so under `-v` and the plain path runs. `route: <name>` prints without `-v`,
because it tells you what you got. Know the protocol yourself? Fetch the API URL: `wsc fetch
https://pypi.org/pypi/httpx/json` is the honest answer to "npm blocks the HTML", in 6 KB.

## Dead links

`fetch` asks the Wayback Machine on a 404 or 410, and `--archive` does it for any failure. A found
snapshot prints `archive: <stamp> (<url>)` on stderr. Wayback rate-limits too: `archive: rate
limited, retrying once in 3s`, then it gives up rather than looping. No snapshot is exit 2 and two
stderr lines; report "gone, no snapshot" and move on.

## Refused, and why

Not a technical limit: the content is private, behind a negotiated barrier, or the workaround is a lie
about what the page says. **LinkedIn** and **Instagram** are login walls: what comes back is
navigation, so an answer built on it is about the wrong text. **Amazon product pages** are a shell
with prices of unrelated listings, and a confident answer built on that is worse than "blocked".
**Paywalled news** (WSJ, FT, The Atlantic, The Economist) is a business model, and going around it is a
decision the user has not made.

The rule: **a wall is reported, not papered over.** Name it, offer the alternatives (the site's own
API, a search snippet, another source), and never assemble an answer out of chrome.

## Slow is not blocked

`--source web` at 2-6 s is SearXNG plus scrapers by design; `wsc map` at 3-4.5 s tries four candidate
documents in order; `wsc crawl` paces 1 s per page (`pace: waiting 0.8s` under `-v`). A single `fetch`
past 15 s is a timeout, not a slow page (`TIMEOUT` in `backends.py`).
