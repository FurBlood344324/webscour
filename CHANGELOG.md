# Changelog

## Unreleased

Newest first. Notes no commit message can carry go here.

## 0.1.3 - 2026-11-15

The npm publish failed on 0.1.2 with a message no human should have needed to read: the workflow
asked for credentials that it deliberately does not have.

### Fixed

- The npm job now authenticates through OIDC trusted publishing: `id-token: write`, no
  `NODE_AUTH_TOKEN`, and `npm@11.5.1` installed first because the client bundled with Node 22
  predates trusted publishing and falls back to looking for a token. The trusted publisher was
  configured correctly on the package the whole time; the client was too old to use it.
- The tag for 0.1.2 pointed at a commit from before that fix, so re-running the workflow re-ran the
  old file. That is why 0.1.3 exists instead of a re-run: a workflow run executes the file as it
  was when the run was created, not as it is now.

## 0.1.2 - 2026-11-15

The project home page was showing the CI notes and the logo was a picture of the word "webscour"
drawn in a font-shaped path. Both are now what they should have been.

### Added

- The mark is a drawing rather than a letterform: a 4 by 4 page of cells with one cell per row
  replaced by a diagonal blade. The grid is the page, the four blades are what scrapes it.
- `scripts/build-llms-full.sh` rebuilds the concatenated docs file, so its recipe is a script and
  not a heredoc in prose.

### Changed

- `pi install npm:webscour` replaces the git URL everywhere. The npm package carries the skill and
  a shim; the tool stays Python and installs separately.
- `docs/quickstart.md` gains an agent-skill step, with the raw `SKILL.md` URL as the fallback for
  an agent that has no package manager.

### Fixed

- GitHub resolves a repository home page as `.github/README.md` before `README.md`, so the front
  page was an essay about CI wrappers while the real README sat one click away. The file moved to
  `.github/workflows/README.md`.
- Every drawing now ships as a light file and a dark file with the ink written in, chosen by
  `picture` and `prefers-color-scheme`. A media query inside the SVG cannot work: a file loaded
  through `img` is a separate document and the host page's theme never reaches it.

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
