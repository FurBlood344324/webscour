# 0003 - The extraction tag list is adapted from trafilatura's measured settings

**Status:** accepted, 2026-11-14.

## Context

Our extractor was a flat `HTMLParser` event stream: drop twelve tags, print text at block
boundaries. Measured against `trafilatura` 2.3.1 on five pages (a sixth, a feed page, joined
the set later) it produced 1.25x to 2.67x the bytes, and on `github.com/simonw/llm` kept whole
navigation trees (359 lines against 73). The choice was to invent a tag list, or read what a
project with a benchmark suite ships.

## Options

1. Invent a list of "obviously boilerplate" tags and iterate until the fixtures pass.
2. Adopt its measured tag list wholesale, reimplement its link-density decisions on our own tree,
   and note the source in the code.
3. Depend on trafilatura (refused: decision 0001).

## Choice

Option 2, with the provenance in a comment: `webscour/extract.py` names `settings.py`, version
2.3.1, and the date. Two of our own tags (`header`, `template`) are kept on top of it, each one
justified by a self-test fixture.

## Evidence

- `trafilatura/settings.py:341` holds `MANUALLY_CLEANED`, annotated in three groups (`important`,
  `other content`, `secondary`): the survivor list of a benchmark suite, not a guess.
- `trafilatura/htmlprocessing.py:173` holds `link_density_test`: 0.8 short-block ratio on 60/30
  and 300/100 length limits, `LINK_FARM_RATIO = 0.9` (`utils.py:140`), 100-char average link. Those
  are copied as constants with their reasons. `xpaths.py:286` holds the class/id vocabulary this
  tool does not copy wholesale.
- `trafilatura/settings.py:435` is `_COOKIE_CONSENT_RE`, and its comment records why bare
  `cookie`/`consent` substrings are wrong: up to 97% of a page lost on WordPress templates. Our
  `COOKIE_RE` is that anchored compound list.
- Measured after the change, same five pages plus the feed: 0.98x-1.11x of trafilatura's bytes,
  from 1.04x-2.67x, and the total fell 16.9%. `tests/baselines/0.1.0.json` is the record.

## Reversal condition

The benchmark set becomes mostly single-page applications, and a rule fires on real content twice.
