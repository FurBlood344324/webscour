# 0005 - The playwright fallback lives in a venv this tool owns

**Status:** accepted, 2026-11-14.

## Context

`playwright_python()` probed `sys.executable`, then `glob(~/.pyenv/versions/*/bin/python3)`, then
`which python3`. On the operator's machine exactly one of those scratch environments had
playwright, so the fallback worked by accident, and only here. A stranger's machine has no
`testmuh`, and scanning someone's environment manager for a package we did not install is both a
reliability bug and an intrusion.

## Options

1. Keep probing, add more candidates (conda, poetry, asdf).
2. Require an environment variable and do nothing else.
3. One directory the tool owns, created by an explicit verb, plus the running interpreter and PATH.

## Choice

Option 3. Resolution order is `WEBSCOUR_PLAYWRIGHT_PYTHON` (with `WEB_PLAYWRIGHT_PYTHON` accepted,
one deprecation note, once), then `~/.local/share/webscour/render-venv/bin/python`, then
`sys.executable`, then `python3`. `wsc setup --playwright` creates and fills that venv. Nothing is
installed by `pip install webscour`, ever: setup is a verb a person runs.

## Evidence

- Measured 2026-11-14 on this machine: `~/.pyenv/versions/*/bin/python3` matches five interpreters
  and exactly one of them (`testmuh`) imports playwright. That environment is a scratch venv
  someone made once; the shipped tool depended on it and no test could see that.
- The same day: the playwright package there wants chromium revision 1208 while
  `~/.cache/ms-playwright` held 1223, which is the drift `wsc doctor` now reports.
- `wsc setup --playwright` created the venv, installed playwright 1.65.2 and chromium 1255; a
  second run printed `ok render-venv` in 0.56 s and touched nothing. `wsc doctor` with the venv
  removed reports `render-venv absent`, playwright unavailable, lightpanda present.

## Reversal condition

Python packaging gains a standard per-user data directory for tool-owned environments and the
filesystem layout can be delegated to it.
