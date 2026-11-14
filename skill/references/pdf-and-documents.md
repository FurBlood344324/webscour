# PDF and documents

`fetch` and `pdf` both accept a document URL, and one of them is usually easier to predict. The
difference is the cap and the error message, not the parser.

## Which verb

| You have | Use | Why |
|---|---|---|
| an `arxiv.org/abs/<id>` page | `wsc fetch <abs url>` | route `arxiv` reads the paper's HTML rendering, 0.5 s; an older paper has no HTML and the abs page comes back |
| an `arxiv.org/pdf/<id>` | `wsc pdf <url>` | cap is 20 000 chars, not 6 000 |
| a PDF or docx on disk | `wsc pdf <path>` | the extension picks the format, no network |
| an HTML manual page | `wsc fetch` | `pdf` would route it through pandoc for no gain |
| a scanned PDF | neither | an image has no text to extract; see below |
| a docx or epub | `wsc pdf <url\|path> --format markdown` | pandoc writes gfm and keeps headings and links |

`fetch` on a PDF URL does work: it sees `%PDF` magic bytes or an `application/pdf` content type,
routes through the same extractor, and applies its 6 000-char default. On a 15-page paper that is a
frustrating 6 KB. Use `--max-chars 20000`, or `pdf`, which defaults to exactly that.

## Which backend it picks

The order is fixed and printed by `-v` as `extract: <fmt> -> <backend>`:

| Format | Order |
|---|---|
| `pdf` | `pdftotext` first, then `markitdown` (pandoc cannot read PDF at all) |
| `docx`, `epub`, `html` | `pandoc` first, then `markitdown` |

A backend that returns nothing, errors, or produces whitespace is a fallback, not a failure: the next
one is tried and the error text from each is kept. With none installed:

    pdf: no backend could read this pdf: no document backend installed (need pdftotext, pandoc or markitdown)

`wsc doctor` names which of the three it can see.

`pdftotext` runs with `-layout`, so columns and tables keep their geometry. That is good for a
two-column paper and ugly for a table with wrapped cells; it is still better than the alternative,
which is no table.

## When the extraction is bad

- **It is flat and columns are interleaved.** That is the PDF's own layout. Try another backend:
  `wsc pdf` prefers `pdftotext`; if the file is a PDF, `markitdown` is the fallback, and on a
  multi-column paper it sometimes reads the flow better.
- **You only need one section.** Do not raise `--max-chars` and read all 60 KB. Keep it and grep it:
  `wsc pdf <url> --max-chars 200000 > p.md` then `grep -n -A3 attention p.md`. `pdf` has no `--save`
  yet, so the shell redirect is the save.
- **The page range matters.** There is no `--page` flag. Ask for a bigger `--max-chars` and cut with
  `sed -n 'a,bp'`, or find the section by grep first.
- **`--format markdown` changed nothing.** Expected on a PDF: only pandoc writes markdown, and pandoc
  cannot read PDF. On docx or epub it works and is worth asking for.
- **The output starts with a footer or a license line.** The extractor did not model the page; the
  text is still in document order, so grep rather than read from the top.

## A scanned PDF comes back empty, not wrong

There is no OCR here, by design: OCR is a dependency, a model download, and a very large claim about
accuracy. A PDF that is a photograph of a page produces **no text operators**, so every backend
returns empty and the tool says so:

    pdf: no backend could read this pdf: pdftotext: exit 0, no output; pandoc: Pandoc can convert
    to PDF, but not from PDF.; markitdown: exit 0, no output

Exit 2. That is the correct answer. Do not tell the user the paper says something when the extraction
returned nothing; say the PDF is image-only and offer the HTML version (`arxiv.org/html/<id>`) or the
abstract page instead. Many papers now have an HTML rendering that reads fine:

    wsc fetch https://arxiv.org/html/1706.03762v7 --max-chars 4000

## Cost

| Call | Wall clock | stdout |
|---|---|---|
| `pdf` on an arXiv paper (15 pages) | 1.0 s | 20 KB at the default cap, 59 KB at 100 000 |
| `fetch` on the same PDF URL | 0.9 s | 6 KB at the default cap |
| `pdf` on a local docx | 0.34 s | the document |
| `fetch` on `arxiv.org/abs/1706.03762` (route) | 0.49 s | 6 KB of the paper's HTML rendering |
| `fetch` on an old abs page with no HTML rendering | 0.4 s | 3.5 KB of the abs page |

The abs URL is the cheap first move, not only for the abstract: for a recent paper it is the full
text at a third of the PDF's cap. Fetch the PDF when the route says `arxiv html: no full text` on
stderr under `-v`.
