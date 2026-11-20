# AUR staging - not submitted

AUR registration is closed at the moment (2026-11-20). This directory is staged so that submission is
one short session when it opens. **No CI**: releases are cut by hand and this package is updated by hand
per release - no GitHub Actions, no automation.

Per-release checklist:

1. `pkgver` = the new version in `PKGBUILD`; replace `SKIP` in `sha256sums` (`updpkgsums`, or
   `sha256sum` of the downloaded `.crate`).
2. Regenerate: `makepkg --printsrcinfo > .SRCINFO`
3. Sanity build: `makepkg -rsf` in this directory (a clean chroot is better).
4. Submit / update:
   - one time: an SSH key for the AUR account (`ssh-keygen -t ed25519`), pubkey added to the account
   - `git clone ssh://aur@aur.archlinux.org/webscour.git`
   - copy `PKGBUILD` and `.SRCINFO` in, commit `webscour <ver>-<rel>`, push
5. Optional later: a `webscour-bin` sibling sourcing the GitHub release tarball (static musl binary),
   for machines without a Rust toolchain. Decide when the first release exists.

The crate itself is published to crates.io first; this package builds from the `.crate` tarball, so the
AUR entry never carries a source tarball of its own.
