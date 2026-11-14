#!/usr/bin/env bash
# Install / refresh a LOCAL SearXNG that `wsc search --source web` uses as its
# first backend. No sudo, no docker, no system python: a venv under ~/.local/share,
# settings under ~/.config/searxng, one systemd USER unit bound to 127.0.0.1:8888.
# Idempotent: re-running it repairs the install and only restarts when it must.
#
#   ./install.sh [--force] [--no-start] [--check]
#     --force     recreate the venv and rewrite settings even when nothing changed
#     --no-start  install only; do not (re)start the unit
#     --check     report state and exit
#
# Engine selection is DATA, not opinion: probe-engines.py measures the engines and
# writes ~/.local/share/searxng/engines.json; this script renders that file into the
# `engines:` block of settings.yml. Without that file all candidates stay enabled.
set -euo pipefail

SEARX_COMMIT="de722ab1bc957fd2e648bc2404b9155db69c617f"
HOME_DIR="$HOME"
SRC="$HOME_DIR/.local/share/searxng/src"
ROOT="$HOME_DIR/.local/share/searxng"
VENV="$ROOT/venv"
CFG="$HOME_DIR/.config/searxng"
STATE="$ROOT/engines.json"
MARK="$VENV/.searx-install"
UNIT="$HOME_DIR/.config/systemd/user/searxng-local.service"
UNIT_NAME="searxng-local.service"
PORT=8888
BIND="127.0.0.1"
PY="${SEARX_PYTHON:-python3.11}"

FORCE=0
START=1
CHECK=0
for a in "$@"; do
    case "$a" in
        --force) FORCE=1 ;;
        --no-start) START=0 ;;
        --check) CHECK=1 ;;
        -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "install: unknown option $a" >&2; exit 2 ;;
    esac
done

say() { printf '%-14s %s\n' "$1" "$2"; }
die() { echo "install: $*" >&2; exit 1; }

# ---------------------------------------------------------------- preflight
[ "$(id -u)" -ne 0 ] || die "run as your user, not root (this installs a USER service)"
command -v git >/dev/null || die "git is missing"
command -v "$PY" >/dev/null || die "$PY is missing (set SEARX_PYTHON)"
command -v systemctl >/dev/null || die "systemctl is missing"

if [ "$CHECK" = 1 ]; then
    say "src" "$([ -d "$SRC/.git" ] && git -C "$SRC" rev-parse --short HEAD || echo missing)"
    say "venv" "$([ -x "$VENV/bin/granian" ] && echo present || echo missing)"
    say "settings" "$([ -f "$CFG/settings.yml" ] && stat -c %s "$CFG/settings.yml" || echo missing)"
    say "state" "$([ -f "$STATE" ] && echo present || echo 'absent (all candidates enabled)')"
    say "unit" "$(systemctl --user is-enabled "$UNIT_NAME" 2>&1 || true) / $(systemctl --user is-active "$UNIT_NAME" 2>&1 || true)"
    say "listen" "$(ss -ltn 2>/dev/null | awk -v p=":$PORT" '$4 ~ p {print $4}' | paste -sd, - || echo none)"
    exit 0
fi

# ---------------------------------------------------------------- source
mkdir -p "$ROOT" "$CFG" "$HOME_DIR/.config/systemd/user"
if [ ! -d "$SRC/.git" ]; then
    say "clone" "searxng @ ${SEARX_COMMIT:0:12} (shallow)"
    rm -rf "$SRC"
    git clone -q --filter=blob:none --no-checkout https://github.com/searxng/searxng.git "$SRC"
else
    say "clone" "present, fetching pinned commit"
fi
# The pin is a commit, not a tag: a tag can move, a hash cannot. Fetch it explicitly so
# this works both on a fresh clone and on one that already has an unrelated history.
if ! git -C "$SRC" cat-file -e "${SEARX_COMMIT}^{commit}" 2>/dev/null; then
    git -C "$SRC" fetch -q --depth 1 origin "$SEARX_COMMIT"
fi
git -C "$SRC" checkout -q --detach "$SEARX_COMMIT"
[ "$(git -C "$SRC" rev-parse HEAD)" = "$SEARX_COMMIT" ] || die "checkout did not land on $SEARX_COMMIT"
say "source" "$(git -C "$SRC" rev-parse --short HEAD) in $SRC"

# ---------------------------------------------------------------- venv
REQ_HASH="$(cat "$SRC/requirements.txt" "$SRC/requirements-server.txt" | sha256sum | cut -c1-16)"
WANT="$SEARX_COMMIT $REQ_HASH"
if [ "$FORCE" = 1 ] && [ -d "$VENV" ]; then
    say "venv" "recreating (--force)"
    rm -rf "$VENV"
fi
if [ ! -x "$VENV/bin/python" ]; then
    say "venv" "creating with $($PY -V 2>&1)"
    "$PY" -m venv "$VENV"
fi
if [ "$FORCE" = 1 ] || [ ! -f "$MARK" ] || [ "$(cat "$MARK")" != "$WANT" ]; then
    say "pip" "installing requirements ($REQ_HASH)"
    "$VENV/bin/pip" -q install --upgrade pip >/dev/null
    "$VENV/bin/pip" -q install -r "$SRC/requirements.txt" -r "$SRC/requirements-server.txt"
    printf '%s' "$WANT" >"$MARK"
else
    say "pip" "requirements unchanged, skipped"
fi
[ -x "$VENV/bin/granian" ] || die "granian is missing from the venv"

# ---------------------------------------------------------------- settings
# Generated, never hand-edited: re-running this script rewrites the file. The secret is
# kept outside it (secret_key, mode 600) so the file can be regenerated without churn.
umask 077
if [ ! -f "$CFG/secret_key" ]; then
    "$VENV/bin/python" -c 'import secrets; print(secrets.token_urlsafe(48))' >"$CFG/secret_key"
    say "secret" "generated at $CFG/secret_key (never in this repo)"
fi
SECRET="$(cat "$CFG/secret_key")"

NEW_CFG="$("$VENV/bin/python" - "$STATE" "$SECRET" <<'PY'
import json, sys

state_path, secret = sys.argv[1], sys.argv[2]
CANDIDATES = [
    "duckduckgo", "brave", "mojeek", "startpage", "qwant", "bing", "google",
    "wikipedia", "github", "stackoverflow", "arxiv", "hackernews", "yandex",
    "marginalia", "searchmysite",
]
try:
    with open(state_path, encoding="utf-8") as fh:
        state = json.load(fh)
    engines = [(e["name"], float(e.get("timeout", 4.0))) for e in state["engines"]]
except (OSError, ValueError, KeyError):
    engines = [(n, 4.0) for n in CANDIDATES]

head = """# SearXNG, local instance for the wsc CLI. GENERATED by searx/install.sh
# -- edit that script (or ~/.local/share/searxng/engines.json), not this file.
use_default_settings:
  engines:
    keep_only:
{keep_only}
general:
  instance_name: "local"
  debug: false
  donation_url: false
  contact_url: "http://127.0.0.1:8888/"   # wikimedia engines require it; loopback, never routable
  enable_metrics: true          # /stats/errors feeds `wsc doctor`; no query text
search:
  safe_search: 0
  autocomplete: ""              # no autocomplete: no keystroke ever leaves the box
  default_lang: "all"
  formats:
    - html
    - json
server:
  bind_address: "{bind}"
  port: {port}
  base_url: false
  limiter: false
  public_instance: false
  image_proxy: false
  secret_key: "{secret}"
outgoing:
  request_timeout: 4.0
  max_request_timeout: 6.0
  pool_connections: 20
  enable_http2: true
  retries: 0
  useragent_suffix: ""
ui:
  query_in_title: false
  default_theme: simple
"""

eng = ""
for name, timeout in engines:
    eng += "  - name: %s\n    disabled: false\n    inactive: false\n    timeout: %.1f\n" % (name, timeout)

sys.stdout.write(head.format(
    keep_only="".join("      - %s\n" % n for n, _ in engines),
    bind="127.0.0.1", port=8888, secret=secret,
))
sys.stdout.write("engines:\n")
sys.stdout.write(eng)
PY
)"

if [ ! -f "$CFG/settings.yml" ] || ! diff -q <(printf '%s' "$NEW_CFG") "$CFG/settings.yml" >/dev/null 2>&1 \
        || [ "$FORCE" = 1 ]; then
    printf '%s' "$NEW_CFG" >"$CFG/settings.yml"
    chmod 600 "$CFG/settings.yml"
    say "settings" "written, $(grep -c '^  - name:' "$CFG/settings.yml") engines, 127.0.0.1:$PORT"
    CHANGED=1
else
    say "settings" "unchanged"
    CHANGED=0
fi

# ---------------------------------------------------------------- runtime entrypoint
# A query-carrying URL is never written to the journal: serve.py filters those records before
# any handler sees them. Installed into the runtime dir, so the unit does not read the repo.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install -m 644 "$SCRIPT_DIR/serve.py" "$ROOT/serve.py"
say "entry" "$ROOT/serve.py"

# ---------------------------------------------------------------- unit
NEW_UNIT="[Unit]
Description=SearXNG local meta-search for the wsc CLI (127.0.0.1:$PORT)
Documentation=file://$ROOT/README.md
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$SRC
Environment=SEARXNG_SETTINGS_PATH=$CFG/settings.yml
Environment=GRANIAN_INTERFACE=wsgi
Environment=GRANIAN_HOST=$BIND
Environment=GRANIAN_PORT=$PORT
Environment=GRANIAN_LOG_LEVEL=warning
Environment=GRANIAN_LOG_ACCESS_ENABLED=false
Environment=GRANIAN_BLOCKING_THREADS=4
ExecStart=$VENV/bin/granian serve:app
Environment=PYTHONPATH=$ROOT:$SRC
Restart=on-failure
RestartSec=2
TimeoutStopSec=10
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$ROOT
# No log of the query text: stdout carries warnings only, and the access log is off.
StandardOutput=journal
StandardError=journal
SyslogIdentifier=searxng-local

[Install]
WantedBy=default.target
"
# compare with printf, not $(cat ...): command substitution eats the trailing newline and the
# unit would look changed on every run, restarting the service for nothing
if [ ! -f "$UNIT" ] || ! diff -q <(printf '%s' "$NEW_UNIT") "$UNIT" >/dev/null 2>&1; then
    printf '%s' "$NEW_UNIT" >"$UNIT"
    chmod 644 "$UNIT"
    systemctl --user daemon-reload
    say "unit" "written $UNIT"
    CHANGED=1
else
    say "unit" "unchanged"
fi

# ---------------------------------------------------------------- service
if ! systemctl --user is-enabled "$UNIT_NAME" >/dev/null 2>&1; then
    systemctl --user enable "$UNIT_NAME" >/dev/null
    say "enable" "enabled at boot (user session)"
fi
if [ "$START" = 1 ]; then
    if [ "$CHANGED" = 1 ] || ! systemctl --user is-active --quiet "$UNIT_NAME"; then
        systemctl --user restart "$UNIT_NAME" || die "unit failed to start: journalctl --user -u $UNIT_NAME -n 40"
        say "start" "restarted"
    else
        say "start" "already running"
    fi
    for _ in $(seq 1 40); do
        if timeout 1 bash -c "exec 3<>/dev/tcp/$BIND/$PORT" 2>/dev/null; then break; fi
        sleep 0.25
    done
    if timeout 5 curl -fsS "http://$BIND:$PORT/config" -o /dev/null 2>/dev/null; then
        say "listen" "$(ss -ltn 2>/dev/null | awk -v p=":$PORT" '$4 ~ p {print $4}' | paste -sd, -)"
    else
        say "listen" "not answering yet: journalctl --user -u $UNIT_NAME -n 40"
    fi
fi
say "done" "$(systemctl --user is-enabled "$UNIT_NAME" 2>&1)/$(systemctl --user is-active "$UNIT_NAME" 2>&1)"
