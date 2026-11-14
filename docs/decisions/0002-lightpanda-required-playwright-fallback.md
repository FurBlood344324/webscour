# 0002 - lightpanda is required, playwright is a fallback

**Status:** accepted, 2026-11-14.

## Context

Two render backends were treated as interchangeable. They are not: lightpanda is a single static
binary, playwright is a Python package plus a ~170 MB browser plus (on Linux) system libraries.
The tool is honest about needing *something* to render a JavaScript page; the question is which
thing the documentation makes mandatory.

## Options

1. Both optional, degrade quietly to plain HTTP.
2. lightpanda required, playwright an optional fallback.
3. playwright required, lightpanda optional.

## Choice

Option 2. `wsc doctor` fails when lightpanda is missing and prints a note when playwright is not
installed. `wsc setup --playwright` installs the fallback into a venv this tool owns.

## Evidence

- On this machine on 2026-11-14: `react.dev/learn` renders through lightpanda in 0.76 s wall clock
  with `render: lightpanda` on stderr. The same page through playwright needs an interpreter that
  imports it, which was the reason for the second backend in the first place.
- A single binary is what an agent host can install without a package manager negotiation; if the
  required path were the Python one, `pip install webscour` would depend on a 170 MB download to
  be useful, and that is not a decision to make silently.
- No render backend can be installed by `pip` alone, which the README states rather than hides.

## Reversal condition

lightpanda stops shipping for Linux, or a page in the benchmark set needs a real Chrome and
lightpanda cannot do it in two consecutive releases.
