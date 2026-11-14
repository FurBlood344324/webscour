# Changelog

## Unreleased

Newest first. Notes no commit message can carry go here.

## 0.1.1 - 2026-11-15

A patch release with no change to what the tool does. Every commit here fixes something that made
the project harder to trust: two of them were gate failures that only appeared on a clean machine,
and one was a README that opened without its own name.

### Fixed

- `check-tag.sh` read `GITHUB_REF_NAME` unconditionally, so a pull-request run (`1/merge`) was
  reported as a version mismatch. It now reads the name only when `GITHUB_REF_TYPE` is `tag`.
- The build probe in `check.sh` ran from the repository root, where a leftover `./build` directory
  is a namespace package and replaced the `build` tool with an empty namespace. It runs from `/`.
- The same probe tested `[ -x python3 ]`, which is false: `-x` tests a path and `python3` is a
  command name. The interpreter is now resolved with `command -v` first.
- The release gate builds with `--no-isolation`, and pyproject declares `setuptools>=77` as the
  backend. Python 3.12 and later ship without setuptools, so two of the three matrix entries
  failed with a message naming neither the interpreter nor the fix. CI installs it, and the gate
  checks the version before building and says what to install.

### Documentation

- The README opens with the wordmark, the name, the one-line promise and the badges, then gives the
  `curl` installer and a paste-ready agent prompt before the manual install routes.

## 0.1.0 - 2026-11-14

First published version. The tool ran for months inside one operator's vault as `web`; this release
packages it and then does the two jobs the packaging exposed: the extraction was noisy, and the
render fallback was borrowing someone else's environment.
