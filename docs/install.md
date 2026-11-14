# Install

webscour is a Linux-only Python CLI. It is `wsc` on PATH, and it has no Python dependencies: the
standard library is the whole stack. What a machine needs is python 3.11 or newer, one way to
install a Python tool, and lightpanda.

## The one-liner

```bash
curl -LsSf https://wsc.ashina.live/install.sh | sh
```

`wsc.ashina.live` is GitHub Pages serving `install.sh` from the root of this repository, so the
script you run is the file in the repo, byte for byte. The workflow that publishes it also fails
when the domain stops returning that file, or returns anything other than the same bytes.

Pages chooses the content type from the file extension and does not let a project override it, so
this path is served as `application/x-sh`, not `text/plain`. Both are text and `curl | sh` does not
read the type; the only place it matters is a browser, which offers the script as a download
instead of printing it.

Pin one release instead of taking the latest:

```bash
WSC_VERSION=0.1.0 curl -LsSf https://wsc.ashina.live/install.sh | sh
```

See what it would do, without doing it:

```bash
curl -LsSf https://wsc.ashina.live/install.sh | sh -s -- --dry-run
```

## What it actually does

In this order, changing nothing if a step refuses:

1. Parses its flags (`--dry-run`, `--verbose`, `--allow-root`, `--help`) and validates
   `WSC_VERSION` if one is set. An unknown flag stops before anything is touched.
2. Refuses to run as root. `wsc setup` installs a systemd *user* unit, and as root that unit,
   its venv and its settings land in `/root`, where the person who will use the command cannot
   see them. `--allow-root` is the explicit override, for the case where root really is the user.
   `--dry-run` is exempt, because printing commands changes nothing.
3. Picks the first installer it finds: `uv`, then `pipx`, then `python3 -m pip --user`. For the
   pip path it also refuses a python that is missing pip, older than 3.11, inside a virtual
   environment, or marked `EXTERNALLY-MANAGED` by the distribution, because those cases would fail
   later with a worse message. If none of the three exists it prints what to install and exits 1.
4. Works out where the executable will land (`UV_TOOL_BIN_DIR` or `XDG_BIN_HOME` for uv,
   `PIPX_BIN_DIR` for pipx, `python3 -m site --user-base` for pip), then prints the three
   commands in order: the install, `command -v wsc`, `wsc --version`. Under `--dry-run` it also
   prints the PATH hint and the next steps at this point, and stops without running anything.
5. Runs the install command. On failure it says which command failed and stops.
6. Verifies `command -v wsc`, then `wsc --version`. A missing binary or a failed version check is
   an error with the path it looked at, not a warning. A pinned `WSC_VERSION` must match what
   `wsc --version` prints, so an older copy winning on PATH is caught here.
7. If the install directory is not on PATH, prints the `export PATH=...` line and the profile it
   belongs in. It does not append it. Editing a shell profile changes every future session, so
   that stays the user's decision.
8. Prints the next steps and stops. It does not run `wsc setup`.

It never uses `sudo`, never downloads anything except the package index the chosen installer
uses, and never edits a file outside the installer's own directories.

Colour is used only when the stream is a terminal, and never when `NO_COLOR` is set or `TERM=dumb`.
stdout and stderr are gated separately, so redirecting one of them to a log does not leave escape
codes in the file.

## Environment variables

| variable | effect |
| --- | --- |
| `WSC_VERSION` | install this exact release (`0.1.0`); a mismatch at the version check is a hard error |
| `NO_COLOR` | any value turns colour off, even on a terminal |
| `TERM=dumb` | also turns colour off |
| `SHELL` | only used to name the profile file in the PATH hint (`bash` -> `~/.bashrc`, `zsh` -> `~/.zshrc`, `fish` -> `fish_add_path`) |
| `UV_TOOL_BIN_DIR` | where `uv` puts tool executables, and therefore the directory the installer checks for PATH membership |
| `XDG_BIN_HOME` | fallback for the same directory when `UV_TOOL_BIN_DIR` is unset |
| `PIPX_BIN_DIR` | where `pipx` puts executables |

## Manual alternatives

The one-liner is a convenience wrapper around these. Any one of them produces the same `wsc`.

| method | command | installs into | remove with |
| --- | --- | --- | --- |
| uv tool | `uv tool install webscour` | `~/.local/share/uv/tools/webscour`, binaries in `~/.local/bin` | `uv tool uninstall webscour` |
| pipx | `pipx install webscour` | `~/.local/share/pipx/venvs/webscour` (older pipx: `~/.local/pipx`), binaries in `~/.local/bin` | `pipx uninstall webscour` |
| uvx, no install | `uvx webscour search "query"` | a cache that uv manages | `uv cache clean webscour` |
| pip user | `python3 -m pip install --user webscour` | the user site-packages of that interpreter | `python3 -m pip uninstall webscour` |
| from source | `git clone https://github.com/FurBlood344324/webscour && cd webscour && python3 -m webscour.cli search "query"` | nothing; runs in place | delete the checkout |

Use one of them. Two methods on PATH means one of them keeps winning and the other keeps looking
broken; `wsc doctor` cannot tell you which one you are running. The installer enforces the same
rule: when it finds `wsc` resolving somewhere other than the directory it installed into, it
warns and names the path that won.

`uvx webscour` is the no-install path: it resolves and runs the package on every invocation, so it
is slower to start and never leaves a `wsc` on PATH.

## After install

```bash
wsc setup                 # installs the local SearXNG systemd user unit, then checks lightpanda
wsc doctor                # unit, listener, engines, backends, one verdict line
wsc search "python packaging pyproject" --limit 3
```

`wsc setup` is a separate, deliberate step and it is the only part of the tool that touches
systemd. It creates a venv under `~/.local/share/searxng`, settings under `~/.config/searxng`, and
one user unit on `127.0.0.1:8888`. It does not use `sudo`, and it does not install lightpanda.

Optional: `wsc setup --playwright` builds a render fallback in `~/.local/share/webscour/render-venv`
and downloads chromium. Only needed for a page lightpanda cannot render.

A healthy report looks like this (counts vary by machine and by what the upstream engines are
doing today):

```
unit      active (enabled at boot)
listen    127.0.0.1:8888
engines   10 loaded
blocked   abcnyheter, brave, quark, yacy
answered  bing, mwmbl, naver, rawweb, seznam, yacy
silent    abcnyheter, brave, quark, wikibooks
backends  lightpanda=ok  playwright=ok  pdftotext=ok  pandoc=ok  markitdown=ok
VERDICT OK (6/10 engines answering, 4 blocked)
```

Read the last line first. `VERDICT OK` is the only good one:

- `VERDICT DOWN`: nothing is listening on the port. Run `wsc setup`, then `wsc doctor` again.
- `VERDICT DEGRADED: lightpanda is missing`: the render engine is absent. Plain HTTP still works;
  JS-heavy pages do not. Install lightpanda (below), then re-run `wsc doctor`.
- `VERDICT DEGRADED: not loopback only`: the service is reachable from outside this machine. Fix
  the unit before using it.
- `VERDICT DEGRADED: N/M engines blocked`: most upstreams are failing. Usually transient, or this
  IP is being rate-limited.

## Uninstall

Remove the command first, with the method you installed it with:

```bash
uv tool uninstall webscour        # or: pipx uninstall webscour
python3 -m pip uninstall webscour # the pip --user method
```

Then remove the state, if you also ran `wsc setup`:

```bash
# 1. stop and disable the unit, and delete it
systemctl --user disable --now searxng-local.service
rm -f ~/.config/systemd/user/searxng-local.service
systemctl --user daemon-reload

# 2. its data: the SearXNG venv, source checkout, engine list, settings and secret key
rm -rf ~/.local/share/searxng
rm -rf ~/.config/searxng

# 3. the optional playwright fallback and the chromium builds it downloaded
rm -rf ~/.local/share/webscour
rm -rf ~/.cache/ms-playwright

# 4. the pacing stamp is a single file inside the web cache
rm -f ~/.cache/web/last-live
rmdir ~/.cache/web 2>/dev/null || true
```

Nothing else is written outside the install method's own directory. There is no config file in
`/etc`, no system-wide unit, and no `sudo` step to undo.

## Troubleshooting

**`no usable installer: ...`**
The installer found nothing it could install with, and changed nothing. The line names the reason:
no uv, no pipx, a python3 without pip, a python3 older than 3.11, or a python3 that is a virtual
environment or is distro-managed. Install uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`), or
pipx (`python3 -m pip install --user pipx && python3 -m pipx ensurepath`), then re-run.

**`externally-managed-environment` from pip**
Debian, Ubuntu, Fedora and Arch mark the system interpreter with PEP 668, and pip then refuses
`install --user` outright, even into your own home. The installer checks for the marker before it
chooses the pip path, so it usually refuses earlier with a clearer line. If you hit this from a
manual command, do not reach for `--break-system-packages`: use uv or pipx instead. Both create an
isolated environment and touch nothing owned by the distribution.

```bash
uv tool install webscour     # or
pipx install webscour
```

**`wsc: command not found` right after a successful install**
The install directory is not on PATH in this shell. The installer prints the exact line; add it to
the profile your shell reads (`~/.bashrc`, `~/.zshrc`, `~/.profile`) and open a new shell, or for
this session only:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

`uv tool update-shell` and `pipx ensurepath` do the same edit for you if you would rather they
owned it.

**`wsc --version` prints a version you did not ask for**
An older copy is earlier on PATH, or two methods are installed. `type -a wsc` lists every copy in
bash, zsh and fish; in a POSIX `sh` use `which -a wsc` where it exists. Remove the copies you did
not just install.

**`systemctl --user` says "Failed to connect to bus"**
There is no user session bus: a container, a bare SSH session without lingering, or WSL without
systemd. `wsc setup` cannot install the unit there. Either enable lingering
(`loginctl enable-linger "$USER"`), or use `wsc search` without the SearXNG backend, which falls
back to scrapers and JSON APIs.

**`wsc doctor` says `VERDICT DEGRADED: lightpanda is missing`**
lightpanda is the render engine and the tool never installs it for you:

```bash
yay -S lightpanda-bin                       # Arch / AUR
curl -fsSL https://pkg.lightpanda.io/install.sh | bash -s "<version>"   # any Linux; needs curl, jq, sha256sum
# Debian/Ubuntu: the .deb attached to a tagged lightpanda release
brew install lightpanda-io/browser/lightpanda
```

Then `wsc doctor` again. Without it, `search`, `fetch` and `crawl` still work on plain HTML, and
`--render` and the hollow-page retry do not.

**A pip install as root, or an install into `/usr`**
Not supported. The unit and the search settings belong to one user. Uninstall it, then run the
installer as that user.

## Install with an agent

Paste the block below into your agent. It is written for an agent that has a shell and no further
context, and it names the checks, the fallbacks, and the one step it must not take without
permission.

```
Install the webscour CLI (command name: wsc) on this machine, then verify it. Linux only,
python 3.11 or newer.

Method, first choice:
  curl -LsSf https://wsc.ashina.live/install.sh | sh

That script is GitHub Pages serving install.sh from the repository root. It picks the best
available installer itself (uv tool, then pipx, then python3 -m pip --user) and refuses to run as
root. Use exactly one method; do not follow it with a second install.

If curl is unavailable, or the network blocks that domain, use the first of these that works,
and stop there:
  1. wget -qO- https://wsc.ashina.live/install.sh | sh
  2. uv tool install webscour
  3. pipx install webscour
  4. python3 -m pip install --user webscour    (not on Debian/Ubuntu: PEP 668 refuses this;
     use uv or pipx instead, and never --break-system-packages)

Verify, in this order:
  1. command -v wsc        must print a path under ~/.local/bin or a tool directory
  2. wsc --version         must print "webscour <version>"
  3. wsc doctor            exits non-zero on anything but OK, so read the line, not the code:
       "VERDICT OK"        installed and working
       "VERDICT DOWN"      no SearXNG yet; expected before wsc setup, not a failed install
       "VERDICT DEGRADED: lightpanda is missing"
                           the render engine is absent; tell the user, do not install a browser
                           engine on your own

A good report reads: unit active, listen 127.0.0.1:8888, more engines answering than blocked,
backends lightpanda=ok, and VERDICT OK on the last line. Anything else is one of the three
DEGRADED cases or DOWN, and the line names which.

If wsc is not on PATH after a successful install, do not edit a shell profile: report the
export line the installer printed and let the user add it.

Do not run `wsc setup` unattended. It installs a systemd *user* unit for SearXNG and starts a
service. Ask the user first, and say what it will create (~/.local/share/searxng,
~/.config/searxng, searxng-local.service on 127.0.0.1:8888). The same applies to
`wsc setup --playwright`, which downloads chromium.

Only one install method. If a previous copy of wsc exists, remove it before installing again,
so that one method owns the command.
```

A good run ends with three facts you can quote: the path from `command -v wsc`, the version from
`wsc --version`, and the single `VERDICT` line from `wsc doctor`. If any of them is missing, the
install is not done, whatever the earlier steps printed.
