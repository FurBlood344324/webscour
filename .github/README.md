# These are thin wrappers. Nothing in this directory decides anything.

`scripts/check.sh` is the gate: lint, format, unit tests, `--self-test`, build, `twine check`,
and the guards (one version, text hygiene, license, `dependencies = []`, stdlib-only imports,
no home paths, wheel contents). Every workflow below calls it and reads its exit code. If a
workflow grows logic, that logic belongs in the script, not here.

Three properties the wrappers keep:

- **local-first.** Every check is runnable on a workstation with no Actions in the loop. The
  workflows exist so that a pull request from someone else gets the same answer, not so that CI
  is the only place a check exists.
- **no logic in YAML.** A workflow may set up an interpreter, run a script, upload an artifact.
  Anything with a condition more complex than "did it fail" is in `scripts/`.
- **no duplicated checks.** A check that runs here and also in `check.sh` is a second copy of a
  rule, and the second copy is the one that goes stale.

| File | Trigger | What it does |
|---|---|---|
| `ci.yml` | push, pull_request | matrix 3.11/3.12/3.13, each runs `./scripts/check.sh`; a separate `build` job uploads the wheel |
| `release.yml` | tag `v*` | verifies tag == `__version__`, downloads the built wheel, publishes with PyPI trusted publishing (OIDC), creates the GitHub Release |
| `upstream-check.yml` | manual only | live searches and one fetch, `continue-on-error: true`, never blocks anything |
| `deps.yml` | weekly | are the pinned `actions/*` refs still resolving, is lightpanda's nightly CLI still the same shape; opens an issue, changes no code |
