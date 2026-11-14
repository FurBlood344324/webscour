# Markdown or plain text

`--format` exists on `fetch` and `pdf`, and the default is `text`. Pick `markdown` only when the shape
of the page is part of the answer.

## Ask for markdown when

- You will quote it. A heading becomes `## History` instead of a bare line, so the quotation carries
  where it came from.
- It has code. A fenced block survives as a fence, and an indented block stays indented.
- You need the structure: a table, a list of steps, a parameter table where the row label matters.
- You will save it and read a section later. Markdown headings are what
  `scripts/page-sections.sh` reads to give you line ranges.
- You need the link targets, not just the link text. Markdown keeps `[text](url)`.

## Ask for text when

- You are grepping. `--grep` works on both, but text has one line per block and fewer of them.
- You want the smallest context for the same information.
- The page is a feed or a changelog: markdown adds a marker to every line and no meaning.
- You are going to feed it to something that does not render markdown.

## What each costs

Measured 2026-11-14, whole page, no `--max-chars` cut, `--fresh`:

| Page | `text` | `markdown` | Ratio |
|---|---|---|---|
| en.wikipedia.org/wiki/Web_scraping | 37.8 KB | 45.5 KB | 1.20 |
| docs.python.org/3/library/asyncio-task.html | 44.6 KB | 61.9 KB | 1.39 |
| github.com/simonw/llm | 4.4 KB | 6.7 KB | 1.52 |
| news.ycombinator.com/item?id=1 | 232 B | 240 B | 1.03 |

Markdown costs 20 to 50 percent more bytes, and the extra is link URLs and heading markers. On a
documentation page that is a third more context for the same words. It buys navigability, so it is
worth it exactly when you will navigate.

The conversion itself is free: both formats come from the same parsed tree, and rendering markdown
takes 0.07 s against 0.08 s for text on a 239 KB page. There is no speed argument either way.

## Two facts that surprise people

- **A route always returns markdown.** GitHub, Stack Overflow, arXiv, Hacker News and Wikipedia are
  answered by their own API (`route: wikipedia` on stderr), which produces markdown. With the default
  `--format text` that markdown is rendered down to plain text for you, so the default is honest and
  you never see a stray `##`. Asking for `--format markdown` on a routed URL keeps it as-is.
- **`pdf --format markdown` is aspirational.** Only pandoc can write markdown, and pandoc cannot read
  a PDF. So `wsc pdf <pdf> --format markdown` goes through `pdftotext` and gives you the same flat
  text as without the flag; `-v` prints `extract: pdf -> pdftotext (markdown)` and that `(markdown)`
  is the request, not the result. For a docx, epub or HTML document pandoc does write gfm and the
  flag does what it says.

## Reading a saved markdown file by section

    wsc fetch "<url>" --format markdown --save-only --fresh
    scripts/page-sections.sh .webscour/<file>.md        # from the skill directory
    sed -n '<start>,<end>p' .webscour/<file>.md

`--fresh` matters here: a cached text capture answers first and ignores the new `--format`, so without
it you convert a plain-text file and get nothing. The heading map costs a few hundred bytes; reading
the wrong half of a 62 KB file costs 30 KB, so check the map before you read.

`page-sections.sh` reads markdown. A plain-text capture has no fences, so a Python comment starting
with `#` looks exactly like a heading to it and lands in the map.
