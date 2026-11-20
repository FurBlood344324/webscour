# webscour on npm: deprecation notice

The npm package is not the tool and never was. It carries `skill/SKILL.md` and a `wsc` shim that
forwards to whatever `wsc` is already on PATH, so that `npx skills add webscour` and
`pi install npm:webscour` resolve by package name. The tool itself is now a Rust crate, installed
with `cargo install webscour`.

So the npm side is deprecated, not deleted. Deleting the package would free the name `webscour` on
npm for whoever registers it next, and a shim someone else can take over is worse than one that
carries a deprecation note. `npm deprecate` keeps the versions installable and prints the message on
every install, which is exactly the behaviour wanted here.

## The message

One message for every version, and it must not contain an em dash:

```text
Retired: webscour is a Rust crate now. Install the tool with: cargo install webscour (binary: wsc). This npm package only carried the agent skill and a wsc shim, it never installed the tool, and it is no longer maintained.
```

It is one line on purpose: the commands below quote it as a single argument, and `npm deprecate`
stores it verbatim. The same text goes on every version; the version only appears in the command,
never in the message, so a user comparing two installs does not see two different stories.

## The commands, one per published version

The live version list, read with `npm view webscour versions --json` on 2026-11-20:

```json
[
  "0.0.0-stage",
  "0.1.1",
  "0.1.3"
]
```

Three versions, three commands, run in this order:

```bash
npm deprecate webscour@0.0.0-stage "Retired: webscour is a Rust crate now. Install the tool with: cargo install webscour (binary: wsc). This npm package only carried the agent skill and a wsc shim, it never installed the tool, and it is no longer maintained."
npm deprecate webscour@0.1.1 "Retired: webscour is a Rust crate now. Install the tool with: cargo install webscour (binary: wsc). This npm package only carried the agent skill and a wsc shim, it never installed the tool, and it is no longer maintained."
npm deprecate webscour@0.1.3 "Retired: webscour is a Rust crate now. Install the tool with: cargo install webscour (binary: wsc). This npm package only carried the agent skill and a wsc shim, it never installed the tool, and it is no longer maintained."
```

A version range works too (`npm deprecate 'webscour@>=0.0.0' "<message>"`), and is one call instead
of three, but the per-version form is written out above because it is the form that fails loudly if
one version is missing or already gone, and because the range form applies silently to a future
version published by mistake.

## Operator checklist

1. `npm whoami` must print the account that owns the package. There is no dry run for `npm
   deprecate`: the first command that leaves the machine changes the registry.
2. Run the three commands above. `npm view webscour@<version> deprecated` printing the message back
   is the check that each one landed; the whole set in one call:
   `npm view webscour versions --json | python3 -c "import json,subprocess,sys; [print(v, subprocess.run(['npm','view','webscour@'+v,'deprecated'],capture_output=True,text=True).stdout.strip()) for v in json.load(sys.stdin)]"`
3. `https://www.npmjs.com/package/webscour` must show the deprecation banner on the package page and
   the message on every version tab.
4. Do not `npm unpublish` anything. Not a single version, not the package. The name stays registered
   for the same reason the PyPI name stays registered.
5. Nothing here is automated. No CI job, no release hook, no scheduled script: the package is
   deprecated once, by hand, and never published again.

## What replaces it

- The crate: `cargo install webscour`, binary `wsc`, version `0.2.0`, source at
  https://github.com/FurBlood344324/webscour (`rust/`).
- The agent skill: `skill/SKILL.md` in the repository,
  https://raw.githubusercontent.com/FurBlood344324/webscour/main/skill/SKILL.md. It is not inside the
  crate (`rust/` is the crate root, and `skill/` sits beside it in the repository), so a Rust install
  does not fetch it and the skill keeps being installed from the repository rather than from npm.
- The old Python package on PyPI: yanked, see `packaging/pypi/README-tombstone.md`.
