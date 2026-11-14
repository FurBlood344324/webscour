# Self-hosting the search backend

`wsc setup` installs one thing: a SearXNG instance that belongs to your user, listens on
loopback, and exists so that `wsc search --source web` has somewhere local to ask. This page says
exactly what that install touches, how to move it to another port, how to use a remote instance
instead, and how to remove it so nothing is left behind.

You can read the installer instead of trusting this page: it is `searx/install.sh`, 267 lines,
and it is the only thing `wsc setup` runs. `wsc setup` shells out to it rather than reimplementing
it, so there is one definition of "installed".

## What `wsc setup` writes

Everything below is under your home directory, and all of it is yours. No sudo is used and no
system-wide path is touched. The installer refuses to run as root for exactly that reason.

| path | what it is |
|---|---|
| `~/.local/share/searxng/src` | a shallow git clone of SearXNG, checked out detached at a pinned commit (`de722ab1bc95`, SearXNG 1.0.0). A commit, not a tag, because a tag can move |
| `~/.local/share/searxng/venv` | a Python venv made with `python3.11` (override with `SEARX_PYTHON`), with `requirements.txt` and `requirements-server.txt` installed. It provides `granian`, the WSGI server the unit runs |
| `~/.local/share/searxng/venv/.searx-install` | a marker holding the commit and a hash of the requirements. When it matches, pip is skipped, which is what makes a second install fast |
| `~/.local/share/searxng/engines.json` | the engine state. Absent means every candidate is enabled. `wsc probe --quality --write` writes it, and the next install renders it into the settings |
| `~/.local/share/searxng/serve.py` | a copy of `searx/serve.py`, the WSGI entrypoint with the query-redacting log filter. It is copied here so the unit never reads a repository |
| `~/.config/searxng/secret_key` | 48 bytes of `secrets.token_urlsafe`, mode 600, generated once and kept across rebuilds so the settings do not churn |
| `~/.config/searxng/settings.yml` | the generated settings, mode 600. Never hand-edit it: the installer rewrites it from `engines.json` on the next run |
| `~/.config/systemd/user/searxng-local.service` | the systemd **user** unit, mode 644 |

The unit runs as your user, in your user session, and is enabled so it starts at login. Its
service section is deliberately narrow. It sets `SEARXNG_SETTINGS_PATH`, `GRANIAN_INTERFACE=wsgi`,
`GRANIAN_HOST=127.0.0.1`, `GRANIAN_PORT=8888`, `GRANIAN_LOG_LEVEL=warning`,
`GRANIAN_LOG_ACCESS_ENABLED=false` and `ExecStart=<venv>/bin/granian serve:app`, plus
`NoNewPrivileges=yes`, `PrivateTmp=yes`, `ProtectSystem=strict`, `ProtectHome=read-only` and
`ReadWritePaths` limited to `~/.local/share/searxng`.

The generated settings pin the parts that matter: `server.bind_address: 127.0.0.1`,
`limiter: false`, `public_instance: false`, `image_proxy: false`, `autocomplete: ""`,
`query_in_title: false`, `enable_metrics: true`, `outgoing.request_timeout: 4.0` and
`outgoing.max_request_timeout: 6.0`. Appended to that are the engine list and a per-engine
timeout.

After writing, the installer enables the unit, restarts it when anything changed, and waits for
the port to answer. A second run with nothing changed prints `unchanged` through its steps and
leaves the running service alone.

## Check it, without changing anything

```console
$ wsc setup --check
src            de722ab
venv           present
settings       1938
state          present
unit           enabled / active
listen         127.0.0.1:8888
lightpanda  /usr/bin/lightpanda
```

`src` is the short commit, `settings` is the file size in bytes, `state` says whether an engine
selection exists, and `lightpanda` is the path the render path will use or a warning that it is
not on `PATH`. `--check` exits 0 without writing anything.

For the operational view, which includes engine health and one verdict line:

```bash
wsc doctor
wsc doctor --json
```

## Run it on a different port

There is no `--port` flag. The port is written in two places, and both are generated, so the
honest procedure is to change both and then not re-run the installer until you mean to (the
installer rewrites them from its own hardcoded `8888`).

1. Stop the unit:

   ```bash
   systemctl --user stop searxng-local
   ```

2. Change the port in the settings file, in the `server:` section:

   ```yaml
   server:
     bind_address: "127.0.0.1"
     port: 8899
   ```

3. Change the port the unit passes to granian, with a drop-in rather than an edit:

   ```bash
   systemctl --user edit searxng-local
   ```

   In the override:

   ```ini
   [Service]
   Environment=GRANIAN_PORT=8899
   ```

   A drop-in is the right tool here precisely because `install.sh` rewrites the unit file itself;
   an override survives that rewrite.

4. Reload, start, and confirm:

   ```bash
   systemctl --user daemon-reload
   systemctl --user start searxng-local
   ss -ltn | grep 8899
   ```

5. Point the CLI at it. The backend address comes from one environment variable:

   ```bash
   export WEBSEARCH_SEARXNG="http://127.0.0.1:8899"
   wsc search "sqlite wal mode" --limit 3
   ```

   Put that export in your shell profile if the port is permanent. `wsc doctor` reads the same
   variable, so it checks the port you actually use.

`wsc setup --check` keeps checking `8888`, because that is the bundled installer's own view of the
world. Use `wsc doctor` for the truth about a moved instance.

## Use a remote SearXNG instead

If you already run a SearXNG elsewhere, or you trust an instance someone else runs, do not install
the bundled one. Set the same variable:

```bash
export WEBSEARCH_SEARXNG="https://searx.example.net"
wsc search "postgres index bloat" --limit 5
```

The variable is read once, at import time, and trailing slashes are stripped. Everything that
talks to the search backend uses it: `search --source web`, `doctor`, and the start-if-stopped
attempt. Against a remote instance the start attempt is harmless: it only tries
`systemctl --user start searxng-local` when the port refuses, and moves on when that fails.

Read [privacy](privacy.md) before you do this. A remote instance changes who sees your query, and
the log redaction this project installs applies only to the unit it installs.

## Remove it cleanly

There is no `wsc uninstall`. The pieces are named, so removal is four commands.

```bash
systemctl --user disable --now searxng-local
rm -f ~/.config/systemd/user/searxng-local.service
systemctl --user daemon-reload
rm -rf ~/.local/share/searxng ~/.config/searxng
```

What that does, in order: stops the service and removes it from the boot set; deletes the unit
file; reloads systemd so the unit is forgotten; then deletes the clone, the venv, the copied
`serve.py`, the engine state, the generated settings and the secret.

Two things it deliberately does not touch:

- `~/.cache/web/last-live`, the one-second pacing stamp. It holds a timestamp, no query, and it
  is harmless; `rm -rf ~/.cache/web` if you want it gone.
- The `wsc` executable and the Python package. Removing those is your package manager's job:
  `pipx uninstall webscour`, `uv tool uninstall webscour`, or `pip uninstall webscour`.

After removal, `wsc search --source web` still runs: with no local backend it falls back to the
scrapers, prints one `backend <name>: <reason>` line per attempt on stderr, and `wsc doctor`
reports `VERDICT DOWN` with a hint. Nothing else breaks. `fetch`, `pdf`, `map` and `crawl` never
used the local service in the first place.

## If the unit will not start

```bash
systemctl --user status searxng-local
journalctl --user -u searxng-local -n 40
```

The usual causes, in order of frequency:

- `python3.11` was missing at install time. Set `SEARX_PYTHON` to an interpreter you have and run
  `wsc setup --force` to rebuild the venv.
- The port is already taken. `ss -ltn | grep 8888` names the holder.
- A requirements bump left the venv stale. `wsc setup --force` recreates it from the pinned commit.

A rebuilt venv takes a few minutes, because it is a real pip install of SearXNG's requirements.
Nothing about that install is a Python dependency of `wsc`; the tool itself still has none.

`docs/install.md` is the installer page, which also covers the uninstall from the package side.
