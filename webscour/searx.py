"""The search-backend lifecycle: install it, measure it, check it.

Every verb here shells out to a script that ships beside the package (`searx/`), because those
scripts are the ones a user can read and run by hand. Nothing is reimplemented in Python: a
second implementation of "is SearXNG healthy" would drift from the first, and the point of
`wsc doctor` is that there is exactly one verdict.

`lightpanda` is a system binary, not a Python dependency. `setup` verifies it and prints the
install hint; it never downloads an executable, because a package install that fetches and runs
a binary is something a user would have to audit rather than trust.
"""

import os
import shutil
import subprocess
import sys

from .backends import warn

LIGHTPANDA_HINT = (
    "lightpanda: install it from one of these, then re-run `wsc doctor`:\n"
    "  Arch / AUR     yay -S lightpanda-bin      (nightly variant: lightpanda-nightly-bin)\n"
    '  any Linux      curl -fsSL https://pkg.lightpanda.io/install.sh | bash -s "<version>"\n'
    "  Debian/Ubuntu  the .deb published with each tagged release\n"
    "  Homebrew       brew install lightpanda-io/browser/lightpanda\n"
    "`wsc setup` verifies lightpanda on PATH and never downloads it for you."
)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)


def _share_candidates():
    """Where a wheel puts data files, relative to this module and to the interpreter.

    A package installed with `pip --prefix` keeps its data files under that prefix, which is not
    `sys.prefix`; the module's own location is the reliable anchor there, so both are offered.
    """
    here = os.path.dirname(HERE)  # .../webscour
    ups = [
        os.path.join(here, "..", "..", "..", "..", "share", "webscour", "searx"),
        os.path.join(here, "..", "..", "..", "share", "webscour", "searx"),
        os.path.join(sys.prefix, "share", "webscour", "searx"),
    ]
    try:
        import sysconfig

        ups.append(os.path.join(sysconfig.get_path("data") or "", "share", "webscour", "searx"))
    except (ImportError, KeyError):
        pass
    return [os.path.normpath(p) for p in ups]


def bundle_dir():
    """Where the SearXNG scripts live: env override, source checkout, then an install prefix.

    A source tree keeps them at `<repo>/searx`; an installed wheel puts them under
    `<prefix>/share/webscour/searx`. Both are legitimate, so both are searched, and an env
    override exists for packaging systems that do something else entirely.
    """
    candidates = [
        os.environ.get("WSC_SEARX_DIR") or "",
        os.path.join(REPO_ROOT, "searx"),
        *_share_candidates(),
    ]
    for path in candidates:
        if path and os.path.isdir(path) and os.path.exists(os.path.join(path, "install.sh")):
            return path
    return ""


def _script(name):
    base = bundle_dir()
    return os.path.join(base, name) if base else ""


def lightpanda_path():
    """Where lightpanda is, or ''. The render path requires it; doctor calls its absence a failure."""
    return shutil.which("lightpanda") or ""


def playwright_path():
    """An interpreter that can `import playwright`, or ''. A fallback, so its absence is a note."""
    from .backends import playwright_python

    return playwright_python()


def _run_script(path, argv, env=None):
    """Run a bundled script. A missing script is a packaging fault, and says so."""
    if not path or not os.path.exists(path):
        warn(
            "searx: the bundled scripts are missing (expected searx/ next to the package,"
            " or share/webscour/searx under this install); reinstall the package"
        )
        return 2
    cmd = (["bash", path] if path.endswith(".sh") else [sys.executable, path]) + list(argv)
    full_env = dict(os.environ)
    full_env.update(env or {})
    try:
        return subprocess.run(cmd, env=full_env, check=False).returncode
    except (OSError, subprocess.SubprocessError) as e:
        warn("searx: cannot run %s (%s)" % (os.path.basename(path), e))
        return 2


def install(argv):
    """`wsc setup`: the idempotent SearXNG installer, unchanged and unwrapped."""
    return _run_script(_script("install.sh"), argv)


def probe(argv):
    """The engine probe. What it reports is a measurement of this IP, not an opinion."""
    # probe-engines.py asks the CLI for the health verdict instead of judging on its own, so it
    # has to be told which command that is: inside an installed package there is no sibling
    # executable to call, and a probe with a second opinion would disagree with doctor.
    doctor_cmd = "%s -m webscour.cli doctor" % (sys.executable,)
    return _run_script(_script("probe-engines.py"), argv, env={"WSC_DOCTOR_CMD": doctor_cmd})
