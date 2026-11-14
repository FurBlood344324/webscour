#!/usr/bin/env node
// The npm package exists so that `npx skills add webscour` and `pi install npm:webscour` resolve by
// package name, not so that npm installs a second copy of the tool. The tool is Python, stdlib only;
// this shim finds it and hands over, and says what to install when it cannot.
//
// It never downloads anything and never installs on its own: an install hook that fetches a binary is
// exactly what this project argues against.

const { spawn, spawnSync } = require("node:child_process");

const HINT = [
  "webscour is a Python CLI, and this npm package only carries its agent skill.",
  "Install the tool, then run this again:",
  "",
  "    pipx install webscour",
  "    # or: uv tool install webscour",
  "    # or: curl -LsSf https://wsc.ashina.live/install.sh | sh",
  "",
  "After that, `wsc` is on PATH and this shim simply runs it.",
].join("\n");

function which(name) {
  const probe = process.platform === "win32" ? "where" : "which";
  const r = spawnSync(probe, [name], { encoding: "utf8" });
  if (r.status !== 0) return "";
  return r.stdout.split("\n")[0].trim();
}

const exe = which("wsc");
if (!exe) {
  process.stderr.write(HINT + "\n");
  process.exit(1);
}

const child = spawn(exe, process.argv.slice(2), { stdio: "inherit" });
child.on("exit", (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exit(code === null ? 1 : code);
});
child.on("error", (err) => {
  process.stderr.write("webscour: could not run " + exe + ": " + err.message + "\n");
  process.exit(1);
});
