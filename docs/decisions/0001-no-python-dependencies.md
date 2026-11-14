# 0001 - No Python dependencies

**Status:** accepted, 2026-11-14.

## Context

`wsc` runs on machines where an agent has a shell and nothing else. It started as one file with
`import` lines that were all stdlib. Packaging it as a distribution meant deciding whether the
HTML extraction could lean on `lxml`, `trafilatura` or `readability-lxml`, all of which do the job
better than a hand-written parser does.

## Options

1. Depend on `lxml` and one extractor, and get a mature algorithm for free.
2. Standard library only, with the extraction rules written out.
3. Stdlib only by default, with an optional extra that upgrades extraction when present.

## Choice

Option 2. `dependencies = []` in `pyproject.toml`, and there is no extra that changes extraction.

## Evidence

- Measured 2026-11-14: a stdlib `HTMLParser` extraction pass over the benchmark pages takes
  0.05-0.06 s per page (350 KB of HTML), against 0.2-0.4 s for the whole network fetch. The parser
  is not the cost, so the dependency would buy nothing measurable in time.
- The reference implementation, `trafilatura` 2.3.1, is a useful measuring stick precisely because
  it is not installed: see `docs/decisions/0003-extraction-rules-from-trafilatura.md`.
- `pip install webscour` pulling in `lxml` means a C build on every machine without a wheel, which
  is the class of install that fails on the machine you actually needed the tool on.

## Reversal condition

A page whose content cannot be recovered without a real DOM engine, in the benchmark set, for
three releases running. Then the answer is an optional extra, not a hard dependency.
