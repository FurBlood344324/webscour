#!/usr/bin/env bash
# test-install.sh - does `install.sh --dry-run` still print the commands it is supposed to?
#
# The installer's whole value is the order it chooses: uv before pipx, pipx before pip, and a
# refusal when none of the three exists. That order lives in one `if` chain, and an edited chain
# is exactly the kind of drift nothing else catches: `sh -n` only proves the syntax, and there is
# no way to run the real install in CI. So this test simulates each environment with PATH stubs
# in a temp directory, runs the installer with --dry-run, and diffs the printed command list
# against the expected one. No network, no install, no writes outside the temp directory.
#
#   ./scripts/test-install.sh
#
# Each case: NO_COLOR, a private HOME, and a PATH that contains only the fixture directory plus
# the two coreutils the installer calls. That PATH is passed with `env` to the child, so this
# script's own PATH is never modified; it is saved and restored around the whole run anyway.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || { echo "FAIL cd :: $ROOT"; exit 1; }

ORIG_PATH="$PATH"
SH="$(command -v sh)" || { echo "FAIL sh :: no sh on PATH"; exit 1; }
TMP="$(mktemp -d "${TMPDIR:-/tmp}/wsc-test-install.XXXXXX")" || {
    echo "FAIL mktemp :: cannot create a temp directory"
    exit 1
}
cleanup() {
    PATH="$ORIG_PATH"
    rm -rf "$TMP"
}
trap cleanup EXIT

pass=0
fail=0
CASES=0

note() { printf '%s\n' "$*"; }

# ------------------------------------------------------------------ fixtures

# The installer calls `id -u` on the root check, and `sh` is this test's own interpreter.
# Symlinking the real ones keeps the fixture PATH minimal without pretending those tools came from
# a stub: a stub `id` would be a claim about the machine, and this test is about the installer.
FAKEBIN="$TMP/fixture"
mkdir -p "$FAKEBIN"
REAL_ID="$(command -v id)" || { echo "FAIL fixture :: no id on PATH"; exit 1; }
ln -s "$REAL_ID" "$FAKEBIN/id"
ln -s "$SH" "$FAKEBIN/sh"

# uv: exists, answers --version, and refuses to do anything else, so an accidental real install in
# the non-dry-run path would fail loudly instead of installing a package.
stub_uv() {
    cat >"$FAKEBIN/uv" <<'STUB'
#!/bin/sh
case $1 in
    --version) echo "uv 9.9.9 (fixture)" ;;
    tool) echo "fixture uv: refusing to run '$*' (this is a dry-run test)" >&2; exit 99 ;;
    *) exit 99 ;;
esac
STUB
    chmod +x "$FAKEBIN/uv"
}

stub_pipx() {
    cat >"$FAKEBIN/pipx" <<'STUB'
#!/bin/sh
case $1 in
    --version) echo "9.9.9" ;;
    install) echo "fixture pipx: refusing to run '$*' (this is a dry-run test)" >&2; exit 99 ;;
    *) exit 99 ;;
esac
STUB
    chmod +x "$FAKEBIN/pipx"
}

# python3: enough of an interpreter for the detection block (version, pip present, not
# externally managed) and for `site --user-base`, which decides the install directory. A stub
# rather than the real python3, because the real one differs per machine: a distro interpreter
# with an EXTERNALLY-MANAGED marker would take the refusal branch instead of the pip branch, and
# the test would pass or fail depending on who runs it.
stub_python3() {
    cat >"$FAKEBIN/python3" <<'STUB'
#!/bin/sh
case ${1-} in
    -m)
        case ${2-} in
            pip)
                case ${3-} in
                    --version) echo "pip 99.0 (fixture)"; exit 0 ;;
                    *) echo "fixture python3: refusing to run '$*'" >&2; exit 99 ;;
                esac
                ;;
            site) echo "$FIXTURE_HOME/.local"; exit 0 ;;
            *) exit 99 ;;
        esac
        ;;
    -c)
        case ${2-} in
            *version_info*) echo "3.12"; exit 0 ;;
            # The install.sh guards ask two questions this one answer satisfies: a version at or
            # above the floor, and an EXTERNALLY-MANAGED path that does not exist.
            *SystemExit*) exit 0 ;;
            *sysconfig*) echo "/nonexistent/EXTERNALLY-MANAGED"; exit 0 ;;
            *) exit 99 ;;
        esac
        ;;
    *) exit 99 ;;
esac
STUB
    chmod +x "$FAKEBIN/python3"
}

# ------------------------------------------------------------------ runner

# run_case <name> <expected-file> <exit-code> [env assignments...] [-- installer args...]
run_case() {
    local name="$1" expected="$2" want_rc="$3"
    shift 3
    local envs=()
    while [ $# -gt 0 ] && [ "$1" != "--" ]; do
        envs+=("$1")
        shift
    done
    [ "${1:-}" = "--" ] && shift

    CASES=$((CASES + 1))
    local out="$TMP/$name.out" err="$TMP/$name.err"
    # The child gets the fixture PATH through `env`, so this script's own PATH is untouched.
    # `${envs[@]+...}` because an empty array under `set -u` is an error before bash 4.4.
    local rc=0
    env PATH="$FAKEBIN" NO_COLOR=1 HOME="$TMP/home" FIXTURE_HOME="$TMP/home" \
        SHELL=/bin/bash ${envs[@]+"${envs[@]}"} \
        "$SH" "$ROOT/install.sh" --dry-run ${1+"$@"} >"$out" 2>"$err" || rc=$?

    local problems=''
    if [ "$rc" != "$want_rc" ]; then
        problems="exit code $rc, expected $want_rc"$'\n'
    fi

    # Only the "+" lines are the command list; everything else is prose and may change freely.
    sed -n 's/^+ //p' "$out" >"$TMP/$name.commands"
    if ! diff -u "$expected" "$TMP/$name.commands" >"$TMP/$name.diff"; then
        problems="${problems}command list differs from the expected order:"$'\n'"$(cat "$TMP/$name.diff")"$'\n'
    fi

    if [ -z "$problems" ]; then
        echo "PASS $name"
        pass=$((pass + 1))
    else
        echo "FAIL $name :: $problems"
        fail=$((fail + 1))
    fi
}

# assert_contains <case-name> <file> <text> <why>
assert_contains() {
    local name="$1" file="$2" text="$3" why="$4"
    if grep -qF -- "$text" "$file" 2>/dev/null; then
        echo "PASS $name ($why)"
        pass=$((pass + 1))
    else
        echo "FAIL $name :: expected '$text' ($why); output was:"
        sed 's/^/    /' "$file"
        fail=$((fail + 1))
    fi
}

assert_absent() {
    local name="$1" file="$2" text="$3" why="$4"
    if grep -qF -- "$text" "$file" 2>/dev/null; then
        echo "FAIL $name :: found '$text', which must never appear ($why)"
        fail=$((fail + 1))
    else
        echo "PASS $name ($why)"
        pass=$((pass + 1))
    fi
}

echo "# install.sh dry-run fixture test ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
echo "# fixture PATH: $FAKEBIN (uv, pipx, python3 are stubs; the installer never runs them)"
echo ""

# ------------------------------------------------------------------ case 1: uv wins

mkdir -p "$TMP/home"
cat >"$TMP/expect-uv.txt" <<'EOF'
uv tool install webscour
command -v wsc
wsc --version
EOF
stub_uv
stub_pipx
stub_python3
run_case uv-wins "$TMP/expect-uv.txt" 0
assert_contains uv-wins "$TMP/uv-wins.out" "uv tool install webscour" "uv is chosen when both exist"
assert_absent uv-wins "$TMP/uv-wins.out" "pipx install" "uv is not shadowed by pipx"
# shellcheck disable=SC2016  # the literal line install.sh prints, matched exactly
assert_contains uv-wins "$TMP/uv-wins.out" 'export PATH="$HOME/.local/bin:$PATH"' \
    "PATH line is printed, not written"
assert_contains uv-wins "$TMP/uv-wins.out" "wsc setup" "the post-install step is printed"
assert_contains uv-wins "$TMP/uv-wins.out" "wsc setup --playwright" "the optional fallback is printed"
assert_contains uv-wins "$TMP/uv-wins.out" "wsc doctor" "doctor is named as the check"
assert_absent uv-wins "$TMP/uv-wins.out" "sudo" "the installer never uses sudo"

# ------------------------------------------------------------------ case 1b: a pinned version

cat >"$TMP/expect-pin.txt" <<'EOF'
uv tool install webscour==0.1.0
command -v wsc
wsc --version
EOF
run_case uv-pinned "$TMP/expect-pin.txt" 0 WSC_VERSION=0.1.0
assert_contains uv-pinned "$TMP/uv-pinned.out" "webscour==0.1.0" "WSC_VERSION becomes an exact pin"

# ------------------------------------------------------------------ case 2: pipx, no uv

rm -f "$FAKEBIN/uv"
cat >"$TMP/expect-pipx.txt" <<'EOF'
pipx install webscour
command -v wsc
wsc --version
EOF
run_case pipx-fallback "$TMP/expect-pipx.txt" 0
assert_contains pipx-fallback "$TMP/pipx-fallback.out" "pipx install webscour" "pipx is used when uv is absent"

# ------------------------------------------------------------------ case 3: neither, so pip

rm -f "$FAKEBIN/pipx"
cat >"$TMP/expect-pip.txt" <<'EOF'
python3 -m pip install --user webscour
command -v wsc
wsc --version
EOF
run_case pip-last "$TMP/expect-pip.txt" 0
assert_contains pip-last "$TMP/pip-last.out" "python3 -m pip install --user webscour" \
    "pip --user is the last resort, never a bare pip install"

# ------------------------------------------------------------------ case 4: nothing at all

rm -f "$FAKEBIN/python3"
: >"$TMP/expect-none.txt"
run_case no-installer "$TMP/expect-none.txt" 1
assert_contains no-installer "$TMP/no-installer.err" "no usable installer" "the refusal is one line"
assert_contains no-installer "$TMP/no-installer.err" "astral.sh/uv" "the refusal names how to get uv"
assert_contains no-installer "$TMP/no-installer.err" "pipx" "the refusal names the alternative"

# ------------------------------------------------------------------ case 5: unknown flag

cat >"$TMP/expect-flag.txt" <<'EOF'
EOF
stub_uv
run_case unknown-flag "$TMP/expect-flag.txt" 1 -- --no-such-flag
assert_contains unknown-flag "$TMP/unknown-flag.err" "unknown argument" "an unknown flag stops before doing anything"

# ------------------------------------------------------------------ summary

echo ""
echo "SUMMARY pass=$pass fail=$fail"
if [ "$fail" -eq 0 ]; then
    echo "install: OK ($CASES simulated environments, no network, nothing installed)"
else
    echo "install: NOT OK"
fi

# scripts/check.sh is owned by another agent, so this test announces itself instead of editing it.
echo ""
note "NOTE: scripts/check.sh does not run this yet. Add ./scripts/test-install.sh to its guards"
note "      section (next to the other ./scripts/* checks) so a drifted install order fails the gate."

[ "$fail" -eq 0 ]
