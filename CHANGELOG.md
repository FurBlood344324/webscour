# Changelog

## Unreleased

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
