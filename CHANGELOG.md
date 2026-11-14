# Changelog

## Unreleased

Newest first. Notes no commit message can carry go here.

## 0.1.0 - 2026-11-14

First published version. The tool ran for months inside one operator's vault as `web`; this release
packages it and then does the two jobs the packaging exposed: the extraction was noisy, and the
render fallback was borrowing someone else's environment.

### Added

- `wsc setup` and `wsc probe`: the bundled SearXNG installer and the engine probe, as verbs.
- `wsc setup --playwright`: the optional render fallback, installed into
  `~/.local/share/webscour/render-venv`, a directory this tool owns. `--all` does both installs;
  bare `setup` still means SearXNG. Idempotent, and never a post-install hook.
- `wsc doctor` reports the render venv: path, health, browser-build drift, and the one command per
  failure. lightpanda remains required; playwright is a note when absent.
- `-v` on `fetch`, `map` and `crawl`: diagnostics behind a flag, default output is the answer.
- `tests/bench_extract.py` and `tests/baselines/`: a six-page extraction benchmark against
  trafilatura, with a recall gate per page, committed as the number future versions must beat.
- `scripts/check.sh`, `scripts/release.sh`, `cliff.toml`, `docs/decisions/`: a local-first release
  gate, a local release, changelog rules for 0.x, and five decision records.

### Changed

- **Extraction is 16.9% smaller and much closer to trafilatura**, from 1.25x its byte count to
  1.04x over the benchmark set (github.com/simonw/llm: 10615 B to 4163 B, 2.67x to 1.05x). The tag
  list is trafilatura's `MANUALLY_CLEANED`; container pruning follows its link-density rules;
  cookie banners are matched by anchored compounds only; `<pre>` is now byte-exact.
- The render fallback no longer probes `~/.pyenv/versions/*/bin/python3`. That glob found a
  scratch environment on one machine and nothing on any other, and searching a user's environment
  manager is not something a CLI should do.
- `requires-python = ">=3.11"`, and the version is single-sourced from `webscour.__version__`.
- A page with 200, `text/html`, and text outside `<noscript>` is complete at any length, so a short
  complete page no longer pays for a browser launch. Length is now the last signal, not the first.
- A render fallback prints one line, `render: lightpanda` or `render: playwright`.

### Removed

- The GitHub-search snippet's star glyph prefix: it is a star count, and `2100 stars` reads in
  every terminal without depending on a font.
