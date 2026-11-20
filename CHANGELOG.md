# Changelog

## Unreleased

## 0.2.1 - 2026-11-20

Search quality over the same contract: no flag, format or exit code changed.

### Changed

- The web draw is re-ranked by documentation evidence before truncation: a docs host is the
  strongest signal, a documentation path is a weak one, and a query term that begins a host
  label is a medium one. Engine counts are never a score; they were measured harmful.
- On comparison and opinion questions (13 whole-word markers, `vs` and `why` among them) the
  evidence score changes sign, so a one-sided page is counter-evidence and stops burying the
  pages that answer the question. Inert on every query without a marker.
- The two SearXNG draws are merged and deduped instead of the longer one discarding the other,
  so a rotating answer can no longer lose rows.
- Scraped draws are accepted row by row, the scraper fallback triggers on thin answers (fewer
  than three rows) and not only on empty ones, and the scraper path is paced like the rest.
- Hostless urls (a scraped relative link) are dropped.

### Dependencies

- `scraper` 0.29.

### Measured

- 40 queries, hit at 3, one session: 23 before, 33 and 35 after the first change, 32 and 34
  after the damp, no query falling to the change. Diagnostic and documentation queries probed
  live and unchanged.

## 0.2.0 - 2026-11-20

The crate is the project. `webscour` 0.2.0 is a keyless search CLI in one binary: a local SearXNG
first, three scraper fallbacks, and 19 structured sources, over four direct dependencies.

### Added

- `wsc search` with `--source`, `--limit`, `--category`, `--fresh`, `--since` and `--json`.
- The `web` chain: local SearXNG, then DDG lite, DDG html, Bing, with the fallback reported on
  stderr and one `[engine]` tag per row.
- Structured sources: `github`, `so`, `hn`, `arxiv`, `discourse:<base>`, `rss:<feed-url>`,
  `wikipedia`, `openalex`, `crossref`, `arxiv-api`, `europepmc`, `pubmed`, `pypi`, `npm`, `crates`,
  `devto`, `wayback`, `googlenews`, `bbc`.
- `--self-test`: 35 offline checks compiled into the binary, over the captured fixtures.
- `cargo install webscour` as the install path, plus a staged AUR PKGBUILD that builds the
  published crate.

### Changed

- The output shape is fixed: title, url, snippet, engines, published; `--json` uses one space of
  indent, insertion order, non-ASCII left as UTF-8.
- Exit codes are the contract: `0` answered, `1` help with no verb, `2` usage error or no answer.

### Removed

- The pre-0.2 tree: the earlier tool, its packaging, its docs, its tests and its CI. The repository
  now carries the crate, the AUR packaging and the license. Earlier notes are in git history.
