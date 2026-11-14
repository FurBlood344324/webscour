"""The optional playwright fallback, in a virtual environment this tool owns.

A public install cannot borrow an interpreter from somewhere else on the machine. Before this
module existed, `playwright_python()` probed `sys.executable`, then every
`~/.pyenv/versions/*/bin/python3`, then whatever `python3` resolved to. On the operator's
machine only one scratch environment happened to carry playwright, so the tool worked by
accident there and would find nothing at all on a stranger's machine. Scanning another
person's environment manager is also not a thing a CLI should do.

So: one directory, `~/.local/share/webscour/render-venv`, created by `wsc setup --playwright`
and by nothing else. Playwright is never a dependency of the package, and `pip install
webscour` never runs this. `render-venv/README.md` records why.

The resolution order is also the order of authority: an explicit environment variable, then the
venv this tool owns, then the interpreter already running (a user who installed playwright
globally asked for that), then `python3` on PATH.
"""

import glob
import json
import os
import shutil
import subprocess
import sys

# The one place this tool is allowed to install Python packages into.
RENDER_VENV = os.path.join(os.path.expanduser("~"), ".local", "share", "webscour", "render-venv")

ENV_VAR = "WEBSCOUR_PLAYWRIGHT_PYTHON"
DEPRECATED_ENV_VAR = "WEB_PLAYWRIGHT_PYTHON"

BROWSER_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright")

# Printed when playwright is needed and nothing provides it. The fix is one command, because a
# hint that describes a fix the tool can perform itself is a hint that wastes the caller's time.
SETUP_HINT = (
    "no interpreter with playwright. Install the fallback into the venv this tool owns:\n"
    "  wsc setup --playwright"
)


_note_shown = False


def venv_python(root=None):
    return os.path.join(root or RENDER_VENV, "bin", "python")


def _imports_playwright(python):
    if not python or not os.path.exists(python):
        return False
    try:
        done = subprocess.run(
            [python, "-c", "import playwright.sync_api"], timeout=60, capture_output=True
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


def deprecated_note():
    """One line, once, when the old variable name is what made the fallback work."""
    global _note_shown
    if _note_shown:
        return
    _note_shown = True
    print(
        "%s is deprecated: rename it to %s (the old name still works for now)"
        % (DEPRECATED_ENV_VAR, ENV_VAR),
        file=sys.stderr,
    )


def candidates(root=None):
    """Every interpreter the fallback may use, in the order of authority. No user internals."""
    out = []
    explicit = os.environ.get(ENV_VAR) or ""
    if explicit:
        out.append(explicit)
    legacy = os.environ.get(DEPRECATED_ENV_VAR) or ""
    if legacy:
        if not explicit:
            deprecated_note()
        out.append(legacy)
    out.append(venv_python(root))
    out.append(sys.executable)
    out.append(shutil.which("python3") or "")
    seen, unique = set(), []
    for python in out:
        if python and python not in seen:
            seen.add(python)
            unique.append(python)
    return unique


def find(root=None):
    """The first candidate that can `import playwright.sync_api`, or ''. Pure probe, no writes."""
    for python in candidates(root):
        if _imports_playwright(python):
            return python
    return ""


def venv_exists(root=None):
    return os.path.exists(venv_python(root))


def healthy(root=None):
    """The venv exists and its interpreter imports playwright."""
    return _imports_playwright(venv_python(root))


def browser_builds(root=None):
    """The chromium revisions playwright expects, read from its own browsers.json."""
    python = venv_python(root) if healthy(root) else ""
    if not python:
        return []
    package = os.path.dirname(os.path.dirname(os.path.abspath(python)))
    found = []
    for path in glob.glob(
        os.path.join(
            package,
            "lib",
            "python*",
            "site-packages",
            "playwright",
            "driver",
            "package",
            "browsers.json",
        )
    ):
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        for browser in data.get("browsers") or []:
            if browser.get("name") in ("chromium", "chromium-headless-shell"):
                revision = str(browser.get("revision") or "")
                if revision and revision not in found:
                    found.append(revision)
    return found


def installed_builds():
    """The chromium revisions actually present in the browser cache."""
    found = []
    for path in glob.glob(os.path.join(BROWSER_CACHE, "chromium-*")):
        name = os.path.basename(path)
        revision = name.split("-", 1)[-1] if "-" in name else ""
        if revision.isdigit() and revision not in found:
            found.append(revision)
    return sorted(found)


def drift(root=None):
    """(wanted, present, ok). Mismatched is not fatal: the fallback launches what is installed."""
    wanted = browser_builds(root)
    present = installed_builds()
    if not wanted or not present:
        return wanted, present, False
    return wanted, present, any(w in present for w in wanted)


def status(root=None):
    """One dict for doctor and for `setup --playwright`: path, existence, health, drift, fix."""
    python = venv_python(root)
    exists = venv_exists(root)
    ok = healthy(root)
    wanted, present, matches = drift(root) if ok else ([], installed_builds(), False)
    if not exists:
        fix = "wsc setup --playwright"
    elif not ok:
        fix = "wsc setup --playwright --force"
    elif wanted and present and not matches:
        fix = "wsc setup --playwright (browser build drift: package wants %s, cache has %s)" % (
            ",".join(wanted),
            ",".join(present),
        )
    else:
        fix = ""
    return {
        "path": python,
        "exists": exists,
        "ok": ok,
        "wanted": wanted,
        "present": present,
        "browser_ok": matches,
        "fix": fix,
    }


def _run(cmd, timeout=1800):
    """Run a command that installs things, streaming nothing and returning (ok, last line)."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, "%s: %s" % (type(exc).__name__, str(exc)[:200])
    if done.returncode == 0:
        return True, ""
    tail = [
        line for line in (done.stderr or done.stdout or "").strip().splitlines() if line.strip()
    ]
    return False, tail[-1][:300] if tail else "exit %d" % done.returncode


def _missing_system_deps(root=None):
    """Whether the installed browser cannot start for want of a shared library.

    Asked without root and without launching a page: `ldd` on the browser binary names the
    library and exits non-zero. Only Linux has this; elsewhere the answer is no.
    """
    if not sys.platform.startswith("linux") or not shutil.which("ldd"):
        return False
    for pattern in (
        "chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
        "chromium-*/chrome-linux64/chrome",
        "chromium-*/chrome-linux/chrome",
    ):
        for binary in glob.glob(os.path.join(BROWSER_CACHE, pattern)):
            try:
                done = subprocess.run(["ldd", binary], capture_output=True, text=True, timeout=30)
            except (OSError, subprocess.SubprocessError):
                continue
            if "not found" in (done.stdout or ""):
                return True
    return False


def _pip_install(python, package):
    """Install one package into `python`'s environment with whichever installer is authoritative.

    `uv venv` creates a venv without pip on purpose (and python 3.12+ omits it too), so
    `python -m pip` is not a safe assumption. Order: the running interpreter's pip when it is
    the venv's own base, then `uv pip`, then `python -m ensurepip` and try once more.
    """
    commands = []
    if shutil.which("uv"):
        commands.append(["uv", "pip", "install", "--python", python, package])
    commands.append([python, "-m", "pip", "install", "--quiet", "--upgrade", package])
    last = "no installer worked"
    for cmd in commands:
        ok, err = _run(cmd)
        if ok:
            return True, ""
        last = err
    bootstrap, err = _run([python, "-m", "ensurepip", "--upgrade"])
    if bootstrap:
        ok, err = _run([python, "-m", "pip", "install", "--quiet", "--upgrade", package])
        if ok:
            return True, ""
        last = err
    return False, last


def setup(root=None, force=False, with_deps=False, dry_run=False):
    """`wsc setup --playwright`: idempotent, explicit, and never a post-install hook.

    Returns (ok, lines). A second run against a healthy venv prints one line and touches nothing.
    """
    root = root or RENDER_VENV
    python = venv_python(root)
    lines = []

    if healthy(root) and not force:
        wanted, present, matches = drift(root)
        if not matches and wanted:
            lines.append(
                "render-venv %s (browser build drift: wants %s, cache has %s; "
                "a launch still works)" % (root, ",".join(wanted), ",".join(present) or "none")
            )
        lines.append("ok render-venv")
        return True, lines

    if not os.path.exists(python):
        if dry_run:
            lines.append(
                "would create %s with uv venv" % root
                if shutil.which("uv")
                else "would create %s with python3 -m venv" % root
            )
            return True, lines
        os.makedirs(os.path.dirname(root), exist_ok=True)
        if shutil.which("uv"):
            ok, err = _run(["uv", "venv", root])
        else:
            ok, err = _run([sys.executable, "-m", "venv", root])
        if not ok:
            lines.append("cannot create %s: %s" % (root, err))
            return False, lines
        lines.append("created %s" % root)

    if not dry_run:
        ok, err = _pip_install(python, "playwright")
        if not ok:
            lines.append("installing playwright failed: %s" % err)
            return False, lines
    if not _imports_playwright(python) and not dry_run:
        lines.append("%s cannot import playwright after installing it" % python)
        return False, lines

    browser_flags = ["-m", "playwright", "install", "chromium"]
    if with_deps:
        browser_flags.append("--with-deps")
    ok, err = _run([python, *browser_flags])
    if not ok:
        lines.append("ok render-venv (the browser download failed: %s)" % err)
        lines.append("the venv is usable; finish the browser by hand with:")
        lines.append("  %s -m playwright install chromium --with-deps" % python)
        return True, lines

    if not with_deps and _missing_system_deps(python):
        # The package is installed and the browser downloaded, but a bare Linux box can lack
        # the shared libraries chromium links against, and --with-deps is the flag that fixes
        # that with root. Say so once, with the exact command, rather than guessing.
        lines.append("note: chromium may need system libraries; if a launch fails, run:")
        lines.append("  %s -m playwright install chromium --with-deps" % python)

    lines.append("ok render-venv")
    return True, lines
