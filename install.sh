#!/bin/sh
# webscour installer. https://wsc.ashina.live/install.sh serves THIS file, from the repository
# root; there is no second copy that can drift. `.github/workflows/pages.yml` publishes it.
#
#   curl -LsSf https://wsc.ashina.live/install.sh | sh
#   WSC_VERSION=0.1.0 curl -LsSf https://wsc.ashina.live/install.sh | sh
#   ./install.sh --dry-run --verbose
#
# What it does: pick the best available tool installer (uv, then pipx, then pip --user), install
# the `webscour` distribution with it, then verify `wsc` on PATH and `wsc --version`. It never
# uses sudo, never edits a shell profile, and never runs `wsc setup`: that installs a systemd
# user unit and is a deliberate second step, printed at the end.
#
# POSIX sh on purpose. `set -eu` without pipefail, because this runs under dash, ash and
# bash-as-sh, and pipefail is a bash/ksh extension that dash rejects.
set -eu

PROG=wsc-install
URL=https://wsc.ashina.live/install.sh
MIN_PY=3.11

DRY_RUN=0
VERBOSE=0
ALLOW_ROOT=0
VERSION=${WSC_VERSION-}
SPEC=webscour

# ---------------------------------------------------------------- output

# Colour only when the stream being written is a terminal and NO_COLOR is unset. stderr has its
# own gate, so a redirected log never receives escape bytes.
use_colour_out=0
if [ -t 1 ] && [ -z "${NO_COLOR-}" ] && [ "${TERM-}" != dumb ]; then
    use_colour_out=1
fi
use_colour_err=0
if [ "$use_colour_out" = 1 ] && [ -t 2 ]; then
    use_colour_err=1
fi

c_bold='' c_dim='' c_green='' c_off=''
if [ "$use_colour_out" = 1 ]; then
    c_bold=$(printf '\033[1m')
    c_dim=$(printf '\033[2m')
    c_green=$(printf '\033[32m')
    c_off=$(printf '\033[0m')
fi
e_red='' e_off=''
if [ "$use_colour_err" = 1 ]; then
    e_red=$(printf '\033[31m')
    e_off=$(printf '\033[0m')
fi

say() { printf '%s\n' "$*"; }
say_dim() { printf '%s%s%s\n' "$c_dim" "$*" "$c_off"; }
warn() { printf '%s: warning: %s\n' "$PROG" "$*" >&2; }

# One line, and it says what to do next. No stack traces, no half-finished state called success.
FAILED=0
die() {
    FAILED=1
    printf '%s%s: error:%s %s\n' "$e_red" "$PROG" "$e_off" "$*" >&2
    exit 1
}

# `set -e` stops on a command that fails without a wrapper. This turns that into the same kind of
# line a deliberate refusal prints, so nothing exits non-zero and silent.
on_exit() {
    rc=$?
    if [ "$rc" -ne 0 ] && [ "$FAILED" = 0 ]; then
        printf '%s: stopped on an unexpected failure (exit %s), nothing further was changed; re-run with --verbose to see which step it was.\n' "$PROG" "$rc" >&2
    fi
}
trap on_exit EXIT

have() { command -v "$1" >/dev/null 2>&1; }
on_path() { case ":${PATH-}:" in *":$1:"*) return 0 ;; *) return 1 ;; esac; }

# The line is printed, never appended. Editing a shell profile changes every future session, which
# is not a decision an installer gets to make on someone else's behalf.
print_path_hint() {
    if [ "$BIN_ON_PATH" = 1 ]; then
        return 0
    fi
    say ""
    case ${SHELL-} in
        *fish)
            say_dim "$BIN_DIR is not on PATH in this shell. Add this line to your fish config:"
            say ""
            printf '  %s\n' "fish_add_path $BIN_DIR"
            ;;
        *)
            say_dim "$BIN_DIR is not on PATH in this shell. Add this line to your shell profile, then open a new shell:"
            say ""
            if [ "$BIN_DIR" = "$HOME/.local/bin" ]; then
                # shellcheck disable=SC2016  # a literal line to paste, not an expansion here
                printf '  %s\n' 'export PATH="$HOME/.local/bin:$PATH"'
            else
                printf '  %s\n' "export PATH=\"$BIN_DIR:\$PATH\""
            fi
            case ${SHELL-} in
                *zsh) say_dim "  that file is ~/.zshrc" ;;
                *bash) say_dim "  that file is ~/.bashrc" ;;
                *) say_dim "  that file is ~/.profile, unless your shell reads another one" ;;
            esac
            ;;
    esac
}

stepper() { printf '%s+ %s%s\n' "$c_dim" "$*" "$c_off"; }

print_next_steps() {
    say ""
    # SC2016: the backticks and the $PATH are text for a human to run, not expansions here.
    say_dim "next, by hand (this installer does not run either of them):"
    # shellcheck disable=SC2016
    printf '  %swsc setup%s                install the local SearXNG user unit, for `wsc search --source web`\n' "$c_bold" "$c_off"
    printf '  %swsc setup --playwright%s   optional render fallback, in a venv this tool owns\n' "$c_bold" "$c_off"
    printf '  %swsc doctor%s               one VERDICT line; DEGRADED names the piece that is missing\n' "$c_bold" "$c_off"
}

usage() {
    cat <<EOF
$PROG - install the webscour CLI (wsc) for one user

  curl -LsSf $URL | sh
  WSC_VERSION=0.1.0 curl -LsSf $URL | sh

options
  --dry-run      print the commands in order, change nothing
  --verbose      print the detected tool and each command before it runs
  --allow-root   proceed as root. Without it, root is refused: wsc setup installs a
                 systemd *user* unit, and as root that unit, its venv and its search
                 settings land in /root, where the user who runs wsc cannot see any
                 of them. Pass it only when root is the user who will run wsc.
  -h, --help     this text

environment
  WSC_VERSION    pin one exact release, for example 0.1.0
  NO_COLOR       any value disables colour

It installs the command, and stops there. It does not run \`wsc setup\`: that
installs a systemd user unit for SearXNG, a separate and deliberate step.
EOF
}

# ---------------------------------------------------------------- arguments

while [ $# -gt 0 ]; do
    case $1 in
        --dry-run) DRY_RUN=1 ;;
        --verbose) VERBOSE=1 ;;
        --allow-root) ALLOW_ROOT=1 ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            die "unknown argument '$1', nothing was changed; run --help for the accepted flags."
            ;;
    esac
    shift
done

if [ -n "$VERSION" ]; then
    case $VERSION in
        *[!0-9A-Za-z.-]*)
            die "WSC_VERSION='$VERSION' is not a release version, nothing was changed; use a tag such as 0.1.0."
            ;;
    esac
    SPEC="webscour==$VERSION"
fi

# ---------------------------------------------------------------- root

# A systemd *user* unit belongs to the person who runs it. Installing as root puts the unit, the
# venv and the search settings under /root, where that person's session cannot see any of it, so
# the install looks fine and then `wsc setup` and `wsc search --source web` fail. A dry run
# changes nothing, so it is allowed as root. Without `id` the question cannot be asked, and the
# check is skipped rather than printing a second, unhelpful error line.
if have id && [ "$(id -u 2>/dev/null)" = 0 ] && [ "$ALLOW_ROOT" = 0 ] && [ "$DRY_RUN" = 0 ]; then
    die "refusing to run as root, because wsc setup installs a systemd *user* unit; run this as yourself, or pass --allow-root to install into root's own home for root's own use. Nothing was changed."
fi

# ---------------------------------------------------------------- detect

RUNNER=''
WHY=''

if have uv; then
    RUNNER=uv
elif have pipx; then
    RUNNER=pipx
elif have python3; then
    pyver=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null) || pyver=''
    if ! python3 -m pip --version >/dev/null 2>&1; then
        WHY="the python3 on PATH ($pyver) has no pip module"
    elif ! python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        WHY="the python3 on PATH is $pyver and webscour needs $MIN_PY or newer"
    elif [ -f "$(python3 -c 'import sysconfig, os; print(os.path.join(sysconfig.get_path("stdlib"), "EXTERNALLY-MANAGED"))' 2>/dev/null || echo /nonexistent)" ]; then
        # PEP 668: Debian, Ubuntu, Fedora and Arch mark the system interpreter this way, and pip
        # then refuses `install --user` outright. Saying so here beats letting pip say it badly.
        WHY="the python3 on PATH is managed by the distribution (PEP 668), so pip refuses to install into it"
    elif ! python3 -c 'import sys; raise SystemExit(0 if sys.prefix == sys.base_prefix else 1)' 2>/dev/null; then
        # Inside a venv, `pip install --user` is refused too: user site-packages are invisible
        # there, so the binary would land outside the environment that produced it.
        WHY="the python3 on PATH is itself a virtual environment, where pip refuses --user installs"
    else
        RUNNER=pip
    fi
else
    WHY="no uv, no pipx and no python3 on PATH"
fi

if [ -z "$RUNNER" ]; then
    die "no usable installer: $WHY. Nothing was installed. Install uv (curl -LsSf https://astral.sh/uv/install.sh | sh) or pipx (python3 -m pip install --user pipx) and run this script again."
fi

case $RUNNER in
    uv) BIN_DIR=${UV_TOOL_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}} ;;
    pipx) BIN_DIR=${PIPX_BIN_DIR:-$HOME/.local/bin} ;;
    pip)
        BIN_DIR=$(python3 -m site --user-base 2>/dev/null) || BIN_DIR=''
        BIN_DIR=${BIN_DIR:-$HOME/.local}/bin
        ;;
esac

# The command, as both an argv (`set --`, so no eval and no re-quoting) and one printable line.
# The printed form is built from the same words in the same order, so --dry-run cannot drift.
case $RUNNER in
    uv) set -- uv tool install "$SPEC" ;;
    pipx) set -- pipx install "$SPEC" ;;
    pip) set -- python3 -m pip install --user "$SPEC" ;;
esac
INSTALL_CMD="$*"

# Computed once, before verification prepends the directory for its own check: the hint is about
# the shell the user will open next, not about the PATH this script fixed for itself.
BIN_ON_PATH=0
if on_path "$BIN_DIR"; then BIN_ON_PATH=1; fi

FAIL_HINT=''
if [ "$RUNNER" = pip ]; then
    FAIL_HINT=' If pip answers externally-managed-environment, this interpreter is owned by the distro: use uv or pipx instead (see docs/install.md).'
fi

if [ "$VERBOSE" = 1 ]; then
    # No pipelines here: each of these prints one line, so nothing depends on `head` or `cut`
    # being present on a minimal PATH.
    note=''
    case $RUNNER in
        uv) note=$(uv --version 2>/dev/null || true) ;;
        pipx) note=$(pipx --version 2>/dev/null || true) ;;
        pip) note=$(python3 -m pip --version 2>/dev/null || true) ;;
    esac
    printf '%srunner%s    %s  (%s)\n' "$c_dim" "$c_off" "$RUNNER" "$note"
    printf '%sbin%s       %s\n' "$c_dim" "$c_off" "$BIN_DIR"
    if [ "$BIN_ON_PATH" = 1 ]; then
        printf '%spath%s      on PATH\n' "$c_dim" "$c_off"
    else
        printf '%spath%s      not on PATH in this shell\n' "$c_dim" "$c_off"
    fi
fi

# ---------------------------------------------------------------- plan

if [ -n "$VERSION" ]; then
    printf '%swebscour%s %s\n' "$c_bold" "$c_off" "$VERSION"
else
    printf '%swebscour%s latest\n' "$c_bold" "$c_off"
fi
if [ "$DRY_RUN" = 1 ]; then
    say_dim "dry run: nothing is executed and no file is written; these are the commands, in order"
fi
say ""
stepper "$INSTALL_CMD"
stepper 'command -v wsc'
stepper 'wsc --version'

if [ "$DRY_RUN" = 1 ]; then
    print_path_hint
    print_next_steps
    exit 0
fi

# ---------------------------------------------------------------- install

say ""
if [ "$VERBOSE" = 1 ]; then
    stepper "$INSTALL_CMD"
fi
if ! "$@"; then
    die "\`$INSTALL_CMD\` failed, so nothing was verified; fix the error above and run this script again.$FAIL_HINT"
fi

# ---------------------------------------------------------------- verify

# The install directory is prepended for verification only, so a shell that has not sourced the
# new PATH line still gets a truthful answer about the binary that was just installed. BIN_ON_PATH
# remembers the unmodified answer, which is what the hint below reports.
if [ "$BIN_ON_PATH" = 0 ]; then
    PATH="$BIN_DIR:$PATH"
    export PATH
fi

if ! WSC_PATH=$(command -v wsc 2>/dev/null) || [ -z "$WSC_PATH" ]; then
    # The hint below has not printed yet at this point, so the line is repeated here: a failure
    # path that points at output the user never saw is not actionable.
    die "\`wsc\` is not on PATH after the install. Add this line to your shell profile, open a new shell, then run \`wsc --version\`: export PATH=\"$BIN_DIR:\$PATH\""
fi

if ! WSC_OUT=$(wsc --version 2>/dev/null) || [ -z "$WSC_OUT" ]; then
    die "\`wsc --version\` failed for $WSC_PATH, so the install is broken; remove that file and install with another method from docs/install.md."
fi

if [ -n "$VERSION" ] && [ "$WSC_OUT" != "webscour $VERSION" ]; then
    die "\`wsc --version\` reports '$WSC_OUT' but WSC_VERSION=$VERSION was requested, so an older copy wins at $(command -v wsc); remove it, or pin the version you mean."
fi

case $WSC_PATH in
    "$BIN_DIR"/*)
        printf '%sok%s        %s at %s\n' "$c_green" "$c_off" "$WSC_OUT" "$WSC_PATH"
        ;;
    *)
        # Shadowed: report both versions, because "ok webscour 0.0.1" after installing 0.1.0 reads
        # like the installer did nothing. The install worked; something older still wins on PATH.
        shadowed_out=$("$BIN_DIR/wsc" --version 2>/dev/null || echo "webscour (version unknown)")
        warn "installed $shadowed_out at $BIN_DIR/wsc, but \`wsc\` resolves to $WSC_PATH ($WSC_OUT) first; remove the older copy so one method owns the command"
        printf '%sok%s        %s at %s (shadowed by %s)\n' "$c_green" "$c_off" "$shadowed_out" "$BIN_DIR/wsc" "$WSC_PATH"
        ;;
esac

# ---------------------------------------------------------------- next

print_path_hint
print_next_steps
