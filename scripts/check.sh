#!/usr/bin/env bash
# check.sh - the one command that means "is this releasable".
#
# Runs offline, in this order, and stops at the first failure:
#
#   lint      ruff check .
#   format    ruff format --check .
#   tests     python3 -m unittest discover -s tests
#   self-test python3 -m webscour --self-test   (offline by construction)
#   build     python3 -m build
#   twine     twine check dist/*
#   guards    version agreement, text hygiene, LICENSE, no dependencies, stdlib only, no home paths
#
# Every line is `PASS <name>` or `FAIL <name> :: <why>`, then a SUMMARY. Exit code is 0 only when
# every check passed.
#
# Offline is a property of the whole script, not a hope: network access is not used by any
# step, no post-install hook runs, and LIGHTPANDA=0 makes the render path skip its binary. Set
# BENCH=1 to also run tests/bench_extract.py against the committed baseline (that one needs
# the network, so it is off by default and never part of a release gate).
#
# Usage:
#   ./scripts/check.sh            # everything except the benchmark
#   BENCH=1 ./scripts/check.sh    # also the extraction benchmark
#   PYTHON=/path/to/python ./scripts/check.sh   # a specific interpreter (default: python3)

set -uo pipefail

export LIGHTPANDA=0
export PYTHONDONTWRITEBYTECODE=1
PY="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || { echo "FAIL cd :: $ROOT"; exit 1; }

pass=0
fail=0
names=()

report() { # name, 0|1, why
  local name="$1" rc="$2" why="${3:-}"
  if [ "$rc" -eq 0 ]; then
    echo "PASS $name"
    pass=$((pass + 1))
  else
    echo "FAIL $name :: ${why:0:200}"
    fail=$((fail + 1))
  fi
  names+=("$name")
}

# run_check <name> <command...> : stops the run at the first failure, like a release gate should
run_check() {
  local name="$1"
  shift
  local out
  if out=$("$@" 2>&1); then
    report "$name" 0
  else
    report "$name" 1 "$(printf '%s' "$out" | tail -3 | tr '\n' ' ')"
    summary
    exit 1
  fi
}

summary() {
  echo "SUMMARY pass=$pass fail=$fail"
  if [ "$fail" -eq 0 ]; then
    echo "release: OK (${#names[@]} checks, python $($PY -c 'import sys;print(sys.version.split()[0])'))"
  else
    echo "release: NOT READY"
  fi
}

# Tool discovery: ruff, build and twine are dev tools, not dependencies of the package. A venv
# in the tree wins, then PATH. A missing one is a FAIL, not a SKIP: a gate that cannot run its
# own lint is not a gate.
# The three tools are asked for as modules first, because `python3 -m build` is the invocation
# that exists everywhere a venv does, and then as commands.
# A module check, not an import check: a stale `build/` directory in the repo root is a
# namespace package that satisfies `import build` without being the tool, so the probe runs the
# module and reads its exit code. The dev venv is asked first: these are dev tools, not
# dependencies of the package, and requiring them in the system interpreter would make the gate
# un-runnable on a machine that keeps its package manager clean.
find_module() { # module-name
  # Two traps, both measured. (1) A stale ./build or ./dist in the repo root is a namespace package
  # in the current working directory, so `python -m build` finds that empty directory instead of
  # the tool. The probe therefore runs from /. (2) `[ -x "$PY"]` is false for a bare command name
  # like "python3" because -x tests a path, so the interpreter has to be resolved first; without
  # that the loop skipped every candidate and reported the tool as missing on a clean CI runner.
  local candidate
  for candidate in "$ROOT/.venv-dev/bin/python" "$PY"; do
    [ -n "$candidate" ] || continue
    case "$candidate" in
      */*) ;;
      *) candidate="$(command -v "$candidate" 2>/dev/null)" || continue ;;
    esac
    [ -n "$candidate" ] && [ -x "$candidate" ] || continue
    if ( cd / && "$candidate" -m "$1" --version >/dev/null 2>&1 ); then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

find_tool() { # tool-name, venv-relative-path, module-name
  local name="$1" in_venv="${2:-}" module="${3:-}"
  if [ -n "$in_venv" ] && [ -x "$ROOT/.venv-dev/bin/$in_venv" ]; then
    printf '%s' "$ROOT/.venv-dev/bin/$in_venv"
    return 0
  fi
  command -v "$name" 2>/dev/null
}

RUFF="$(find_tool ruff ruff)"
BUILD_PY="$(find_module build)"
TWINE_PY="$(find_module twine)"

# ------------------------------------------------------------------ lint + format
if [ -z "$RUFF" ]; then
  report ruff 1 "ruff is not installed; pip install ruff, or create .venv-dev and install ruff build twine"
  summary
  exit 1
fi
run_check lint "$RUFF" check .
run_check format "$RUFF" format --check .

# ------------------------------------------------------------------ tests
run_check tests "$PY" -m unittest discover -s tests
run_check self-test "$PY" -m webscour --self-test
run_check entry-point "$PY" -m webscour --version
run_check tag "$ROOT/scripts/check-tag.sh"

# ------------------------------------------------------------------ build + metadata
if [ -z "$BUILD_PY" ] || [ -z "$TWINE_PY" ]; then
  report build 1 "build and/or twine are not importable; pip install build twine"
  summary
  exit 1
fi
rm -rf dist build
run_check build "$BUILD_PY" -m build --wheel --sdist -o dist --no-isolation
run_check twine "$TWINE_PY" -m twine check dist/*

# ------------------------------------------------------------------ guards
# Each guard is a short python program: one fact, one exit code, a message a human can act on.
guard() { # name, python-source
  local name="$1" src="$2" out
  if out=$("$PY" -I -c "$src" 2>&1); then
    report "$name" 0
  else
    report "$name" 1 "$(printf '%s' "$out" | tail -3 | tr '\n' ' ')"
  fi
}

# A. one version, in one place. `__version__` is the source; the tag is the promise; the pi
#    manifest is a copy that has drifted before, which is why it is checked rather than trusted.
guard version "$(cat <<'PY'
import json, os, re, subprocess, sys, tomllib
root = os.getcwd()
init = open(os.path.join(root, "webscour", "__init__.py"), encoding="utf-8").read()
m = re.search(r'__version__\s*=\s*"([^"]+)"', init)
if not m:
    sys.exit("webscour/__init__.py has no __version__")
version = m.group(1)
meta = tomllib.load(open(os.path.join(root, "pyproject.toml"), "rb"))
if "version" in meta.get("project", {}):
    sys.exit("pyproject.toml pins a static version as well; dynamic = [version] is the rule")
attr = meta.get("tool", {}).get("setuptools", {}).get("dynamic", {}).get("version", {}).get("attr")
if attr != "webscour.__version__":
    sys.exit("pyproject.toml does not read its version from webscour.__version__")
for rel in ("package.json", "pi/package.json"):
    path = os.path.join(root, rel)
    if not os.path.exists(path):
        continue
    got = json.load(open(path, encoding="utf-8")).get("version")
    if got and got != version:
        sys.exit("%s says %s, webscour.__version__ says %s" % (rel, got, version))
try:
    tag = subprocess.run(["git", "describe", "--tags", "--exact-match"],
                         capture_output=True, text=True, cwd=root).stdout.strip()
except OSError:
    tag = ""
if tag and tag.lstrip("v") != version:
    sys.exit("tag %s does not match __version__ %s" % (tag, version))
print(version)
PY
)"

# B. text hygiene in the prose we wrote. Two rules with two different reasons: an em dash in our
#    own paragraphs is a punctuation habit that reads as machine-written, and an emoji outside a
#    data fixture is a font problem for every terminal that renders the source. Quoted program
#    output is exempt on purpose: `README.md` shows what `wsc` printed, and transpiling a real
#    capture to satisfy a style rule would be a lie about the output. Those lines are fenced, and
#    the fence is what the exemption looks for.
guard text-hygiene "$(cat <<'PY'
import os, re, sys
BAD = {"\u2014": "em dash", "\u2013": "en dash"}
EMOJI = ((0x1F300, 0x1FAFF), (0x2600, 0x27BF), (0xFE0F, 0xFE0F))
SKIP_DIRS = {".git", ".venv", ".venv-dev", "build", "dist", "__pycache__", ".mypy_cache"}
TEXT = {".py", ".md", ".toml", ".json", ".sh", ".yml", ".yaml", ".txt", ".cfg", ".in"}
hits = []
for base, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for name in files:
        if os.path.splitext(name)[1] not in TEXT:
            continue
        path = os.path.join(base, name)
        rel = os.path.relpath(path)
        if rel.startswith("tests/fixtures/"):
            continue          # captured pages: their bytes are evidence, not our prose
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        fenced = False
        for i, line in enumerate(lines, 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue                      # a capture of program output, not our prose
            for ch, label in BAD.items():
                if ch in line:
                    hits.append("%s:%d %s" % (rel, i, label))
            if any(a <= ord(c) <= b for c in line for a, b in EMOJI):
                hits.append("%s:%d emoji" % (rel, i))
if hits:
    sys.exit("; ".join(hits[:6]))
PY
)"

# C. the license is present, is MIT, and the metadata says so.
guard license "$(cat <<'PY'
import os, tomllib
text = open("LICENSE", encoding="utf-8").read()
if "MIT License" not in text:
    raise SystemExit("LICENSE does not say MIT License")
meta = tomllib.load(open("pyproject.toml", "rb"))["project"]
if meta.get("license") != "MIT":
    raise SystemExit("pyproject license is %r, not MIT" % meta.get("license"))
if "MIT" not in " ".join(meta.get("classifiers") or []) and not meta.get("license"):
    raise SystemExit("no MIT classifier")
PY
)"

# D. zero runtime dependencies, and no dependency could sneak in through an import.
guard no-dependencies "$(cat <<'PY'
import ast, os, sys, tomllib
meta = tomllib.load(open("pyproject.toml", "rb"))["project"]
deps = meta.get("dependencies")
if deps != []:
    sys.exit("dependencies must be exactly [] (found %r)" % (deps,))
if meta.get("requires-python") != ">=3.11":
    sys.exit("requires-python is %r, expected >=3.11" % meta.get("requires-python"))
STDLIB = set(sys.stdlib_module_names)
ALLOWED_LOCAL = {"webscour"}
bad = []
for name in sorted(os.listdir("webscour")):
    if not name.endswith(".py"):
        continue
    path = os.path.join("webscour", name)
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            roots = {(node.module or "").split(".")[0]}
        else:
            continue
        for root in roots:
            if root and root not in STDLIB and root not in ALLOWED_LOCAL:
                bad.append("%s imports %s" % (path, root))
if bad:
    sys.exit("; ".join(bad[:6]))
PY
)"

# E. nothing shipped names a home directory. A path with `furblood` in it is a bug on the first
#    machine that is not this one.
guard no-home-paths "$(cat <<'PY'
import os, sys
SKIP_DIRS = {".git", ".venv", ".venv-dev", "build", "dist", "__pycache__"}
SKIP_FILES = {"check.sh", "release.sh", "README.md", "CHANGELOG.md"}
SHIPPED = {".py", ".sh", ".json", ".toml", ".toml", ".cfg", ".in", ".md"}
bad = []
for base, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for name in files:
        if name in SKIP_FILES or os.path.splitext(name)[1] not in SHIPPED:
            continue
        rel = os.path.relpath(os.path.join(base, name))
        if rel.startswith("tests/") or rel.startswith("docs/"):
            continue
        try:
            text = open(os.path.join(base, name), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        for marker in ("/home/", "C:\\Users"):
            if marker in text:
                bad.append("%s contains %s" % (rel, marker))
if bad:
    sys.exit("; ".join(bad[:6]))
PY
)"

# F. the wheel holds exactly what it should: the package, the data files, nothing else.
guard wheel-contents "$(cat <<'PY'
import glob, sys, zipfile
wheels = sorted(glob.glob("dist/*.whl"))
if len(wheels) != 1:
    sys.exit("expected one wheel in dist/, found %d" % len(wheels))
names = zipfile.ZipFile(wheels[0]).namelist()
for required in ("webscour/__init__.py", "webscour/extract.py", "webscour/cli.py"):
    if required not in names:
        sys.exit("%s is not in the wheel" % required)
for forbidden in ("tests/", "bench_extract.py", "webscour/render_venv.py")[:1]:
    if any(n.startswith(forbidden) for n in names):
        sys.exit("%s leaked into the wheel" % forbidden)
data = [n for n in names if ".data/data/share/webscour/searx/" in n]
if len(data) != 4:
    sys.exit("expected the four searx data files, found %d" % len(data))
PY
)"

# G. every config file parses. A typo in `cliff.toml` or a workflow is invisible until a release
#    needs it, which is the worst possible moment to learn that it never parsed.
guard configs "$(cat <<'PY'
import os, sys, tomllib
for path in ("pyproject.toml", "cliff.toml"):
    try:
        with open(path, "rb") as handle:
            tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        sys.exit("%s: %s" % (path, exc))
try:
    import yaml
except ImportError:
    sys.exit(0)          # YAML is not a dependency of the package; skip when it is absent
for name in sorted(os.listdir(".github/workflows")):
    if not name.endswith((".yml", ".yaml")):
        continue
    path = os.path.join(".github/workflows", name)
    try:
        data = yaml.safe_load(open(path, encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.exit("%s: %s" % (path, exc))
    if not isinstance(data, dict) or "jobs" not in data:
        sys.exit("%s has no jobs" % path)
    if "runs-on:" not in open(path, encoding="utf-8").read():
        sys.exit("%s has a job with no runner" % path)
PY
)"

# H. the benchmark, only when asked. It needs the network and a reference venv, so it is never
#    part of the default gate.
if [ "${BENCH:-0}" = "1" ]; then
  guard bench "$(cat <<'PY'
import subprocess, sys
sys.exit(subprocess.run([sys.executable, "tests/bench_extract.py"],
                        capture_output=True, text=True).returncode)
PY
)"
else
  echo "SKIP bench (set BENCH=1 to check the extraction baseline; it needs the network)"
fi

summary
[ "$fail" -eq 0 ]
