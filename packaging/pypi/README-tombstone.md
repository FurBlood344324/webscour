# webscour: this Python package is retired

webscour is now a Rust crate. The tool is the same idea, keyless search for agents, and it installs
from crates.io:

```bash
cargo install webscour      # puts the `wsc` binary on your PATH
wsc search "pyproject vs setup.py"
```

The crate is `webscour`, version `0.2.0`, and the command it installs is `wsc`. Building it needs a
Rust toolchain (`rust-version = "1.75"` or newer); nothing else at runtime, no Python, no virtualenv,
no `pip`, no `pipx`. `search --source web` uses a local SearXNG when one answers and falls back to
the DuckDuckGo and Bing scrapers when none does, so the crate is usable on a machine with no search
service installed. When the AUR account opens there will also be a `webscour` package on Arch, built
from the same `.crate` tarball, for machines that would rather not keep a toolchain around to install
one CLI.

What is in the crate today is the `search` verb: a local SearXNG first, then the DDG and Bing
scrapers, plus the keyless structured sources (github, stackoverflow, hn, arxiv, wikipedia, openalex,
crossref, europepmc, pubmed, pypi, npm, crates, devto, wayback, googlenews, bbc, discourse and
`rss:<url>`). `--render`, `pdf`, `map` and `crawl` were not ported: their replacement is Firecrawl
Local, which is a program of its own and always was the wrong job for a single binary that people
install from a package index.

## Why the Python path retired

The Python tool shipped with `dependencies = []`, and that decision was the problem. Every capability
past a plain HTTP fetch lived in a system binary the package could not own: lightpanda for rendering,
`pdftotext` or `pandoc` for documents, a playwright venv the tool managed by hand for the render
fallback, and a systemd user unit for the search backend, installed by `wsc setup`. So `pip install
webscour` installed a launcher rather than the tool: `search` worked, everything past it depended on
binaries pip cannot manage, and `wsc doctor` was the thing that told you which ones were still
missing. Keeping a second implementation byte-compatible with the Rust port, in a language nobody
here wanted to keep writing for a CLI that makes a handful of sequential HTTP calls, was the cost
that finally outweighed it. One Rust binary that carries its own HTTP client and its own HTML parser
removes that class of "it installed, but it does not work yet". The Python code stays in the git
history and in the repository, where it is the specification the port was diffed against; it is not
a supported install path any more.

## What is on PyPI, and in what state

Three Python releases exist. All three are yanked, do not install any of them:

| version | uploaded | state |
| --- | --- | --- |
| `0.1.1` | 2026-11-14 | yanked, do not install |
| `0.1.2` | 2026-11-14 | yanked, do not install |
| `0.1.3` | 2026-11-14 | yanked, do not install |

(When this file was written the three release files carried no yank flag yet: the checklist at the
bottom is what sets it. This wording is the state the page describes once that checklist has run, and
step 2 is the check that it did.)

Yanked means `pip install webscour` will not pick a version unless you pin it exactly
(`pip install webscour==0.1.3`), and even then it prints a warning that the release was yanked. Do
not pin it. Install the crate instead.

The versions stay published rather than deleted for one reason: deletion would free the name for
whoever registers `webscour` next, and a name someone else can take over is worse than a page that
says "retired". This file is that page.

## Operator checklist

Nothing here is automated and nothing here runs in CI. Do it by hand, in this order. Step 0 is a
gate: none of this runs until `cargo install webscour` actually works from crates.io, because this
text sends people there.

0. Check the crate is live and installable before anything sends traffic to it:
   `cargo search webscour --limit 5` must list the crate, and a clean
   `cargo install webscour --root /tmp/wsc-check` must finish and produce `/tmp/wsc-check/bin/wsc`.
   If either fails, stop here: the PyPI page must not point at a crate that is not there.

1. Yank `0.1.1`, then `0.1.2`, then `0.1.3`. PyPI has no command line yank: `twine` uploads and
   checks, it cannot yank, so use the web UI. For each version open
   `https://pypi.org/manage/project/webscour/release/<version>/` and use the yank control, giving the
   reason `Retired: webscour is a Rust crate now. Install with: cargo install webscour`. If the
   browser route ever fails, the same state can be set through the PyPI JSON API with an API token
   (`POST https://pypi.org/manage/project/webscour/release/<version>/yank/`), and that is the only
   other supported path. Never `twine upload` a Python release again, and never delete a version.
2. Confirm the yank landed, per version:
   `curl -s https://pypi.org/pypi/webscour/json | python3 -c "import json,sys; [print(v, all(f['yanked'] for f in fs)) for v,fs in sorted(json.load(sys.stdin)['releases'].items())]"`
   which must print `True` on the right of all three versions.
3. Put this text where the PyPI page reads it. Be clear about the constraint first: a PyPI page
   description is the README frozen into the uploaded metadata (`readme = "README.md"` in
   `pyproject.toml`), one per release, and yanking a release does not change it. The project page
   renders the newest release, so `https://pypi.org/project/webscour/` will keep showing the old
   `pipx` instructions until something newer is uploaded. Three routes, in the order to try them:
   - **In place, on the project settings page** at `https://pypi.org/manage/project/webscour/`.
     Look for an editable description field there and paste this text if it exists. This was not
     checked while writing this file, so check it first and take the shortcut if it is real.
   - **A tombstone release, `0.1.4`**, if the field does not exist. One release whose only change is
     this file, saved as `README.md` in the package metadata, so the project description becomes
     this page. **Do not yank `0.1.4`**: the page is the whole point and a yanked release is hidden
     behind a warning. This route is a new PyPI publish, which is exactly what the project decided
     against, so it needs the maintainer to say yes to that one exception. Nothing else may ride
     along in it: no code, no version bump beyond the metadata, no second Python release after it.
   - **Nothing, deliberately**, if both above are refused. The three yanked releases keep the name
     and the banner, and the yank reason carries the `cargo install webscour` line. The page stays
     stale and honest rather than stale and silent. If this is the choice, say so in the repository
     so the next person does not reopen the question.
4. Afterwards, whichever route was taken, `https://pypi.org/project/webscour/` must show one of:
   this text (`0.1.4` or the edited description), or the old README with the yanked banner on every
   release it links. What must not be there is a page that looks installable with no yank notice.
5. Leave the name registered. No `pip` release, no `twine upload`, no deletion, now or later. The
   project's real channel is crates.io, and this page exists only to point there.
