# Crawling without hurting anything

`crawl` fetches pages. Every page it fetches is a request to somebody's server, so the default has to
be conservative and the caller has to spend a limit deliberately.

## The order of operations

1. **`map` first.** It asks the site what it publishes: `sitemap.xml`, `sitemap_index.xml`, the
   `Sitemap:` lines in `robots.txt`, then `llms.txt`. One request per candidate, 3-4.5 s total, and
   you get the shape of the site without touching a single content page.

        wsc map https://docs.example.com --limit 50 -v

   `-v` names which one answered (`map: source https://.../sitemap.xml, 4645 url(s)`).
   The default `--limit` is 200 URLs; `map` is the one verb that does not clamp it further.

2. **Pick a section, not a site.** The URL you pass to `crawl` should be the section root, not the
   homepage. `https://docs.python.org/3/library/` is a section; `https://docs.python.org/` is a site.

3. **Always a limit, and smaller than you think.** `--limit 20` is the default and it is already a lot
   of pages. For reading one manual, 5 to 10 with `--depth 0` is usually what the task needs.

        wsc crawl https://docs.python.org/3/library/ --limit 8 --depth 0

   `--depth 0` means the seed URLs from `map` only. `--depth 1` follows one link level further out.
   Depth 2 is almost never what you want: it multiplies the surface without improving the answer.

## What the tool already does for you

- **1 s pacing, shared across processes.** `backends.pace()` writes a timestamp file, so two `wsc`
  runs in the same second do not both hit a server. `-v` prints `pace: waiting 0.8s`.
- **Same-origin by default.** Links to another host are dropped; `--any-origin` opts out and is
  almost always wrong.
- **Binary extensions are filtered out** (`.png`, `.zip`, `.json`, `.rss`, ...) before any request.
  A link that is not HTML still prints a row with `0 chars`, because the crawl reports what it
  fetched rather than hiding it: those rows are your signal that the site publishes a `.md` twin.
- **It prints an index, not content:** `URL  |  title  |  N chars` per page. The crawl does not put
  page bodies in your context; fetch the one you want afterwards.
- **A hard stop on nothing fetched:** exit 2 and `crawl: nothing fetched` rather than an empty report.
- **`--limit` is clamped to 200** for this verb, so the worst case is bounded.

## The pacing rule

One request per second per site is the ceiling this tool enforces. It is not a target. If the crawl is
reading a docs section you also need to read, stop at ten pages; if the target is a small forum, five
is plenty. `robots.txt` is read for `Sitemap:` lines but a `Disallow:` is not currently enforced, so
the caller has to be the one who does not crawl where they are not wanted.

## When a crawl is the wrong verb

| You want | Use |
|---|---|
| one page | `wsc fetch` |
| one page, in a 40 KB document | `wsc fetch --grep` or `--save` then a line range |
| the URL list only | `wsc map` (no page is fetched) |
| everything on a site | nothing here; this is a job for a crawler with a politeness policy |
| a whole manual as files | `map` the section, then a script that loops `fetch --save` at 2 s intervals |

## A crawl you can defend

    wsc map https://docs.example.com/docs --limit 40         # what exists
    wsc crawl https://docs.example.com/docs/getting-started \
        --depth 0 --limit 6 -v                              # what I actually read
    wsc fetch https://docs.example.com/docs/getting-started/install --save

The crawl prints its own line: `crawl: 6 page(s), depth 0, same-origin yes, 6.0 s of pacing`. Quote
that when you report what you touched.

## Cost

| Call | Wall clock | stdout |
|---|---|---|
| `map --limit 20` (sitemap answers) | 4.4 s | 0.2 KB |
| `map` (nothing published) | 3.3 s, exit 2 | 0 |
| `crawl --limit 3 --depth 0` | 8.3 s | 0.3 KB |
| `crawl --limit 6 --depth 1` | 10.4 s | 0.5 KB |
| `crawl --limit 20 --depth 0` on `react.dev/learn` | 23.5 s | 1.5 KB |
| `crawl --limit 200` (computed from the 1 s pace) | ~4 min | ~12 KB |

`react.dev/learn` is the cautionary number: half its sitemap entries are `.md` twins that carry no
HTML, so the crawl spends a second each on a row that says `0 chars`. Depth 1 is worse: on
`arxiv.org/abs/<id>` it walks into `/login` and `/submit`. Read the index before trusting it, and
pick the section root, not the homepage.
