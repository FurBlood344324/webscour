# 0004 - Silent stderr by default, `-v` for reasoning

**Status:** accepted, 2026-11-14.

## Context

Every command printed why it did what it did: "plain HTTP looked hollow (only 156 chars of text),
lightpanda won". That is useful when diagnosing and noise when an agent runs the tool in a loop
and captures stderr as an error channel.

## Options

1. Always print the reasoning.
2. Print nothing but failures; a flag explains the rest.
3. Print one line per fallback, in both directions.

## Choice

Option 2, with one exception that is not reasoning but a fact the caller must know: when a render
engine actually produced the text, stderr carries exactly one line, `render: lightpanda` or
`render: playwright`. `-v` turns on everything else.

## Evidence

- Measured 2026-11-14, after the hollow heuristic was fixed: `wsc fetch https://example.com
  >/dev/null` produces 0 bytes on stderr, because a short page with text outside `<noscript>` is
  complete. The old behaviour printed a sentence and launched a browser for it.
- `wsc fetch https://react.dev/learn >/dev/null` produces exactly `render: lightpanda`, one line.
- The distinction the code makes is capability versus choice: `warn()` is a lost capability and
  always prints, `vwarn()` is an explanation and is behind `-v`.

## Reversal condition

An agent consumer asks for machine-readable diagnostics on stdout, at which point `--json` grows a
diagnostics field and stderr stays quiet.
