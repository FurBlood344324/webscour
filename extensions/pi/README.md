# webscour for pi

One pi extension, one tool: `web_scour`. It shells out to the local `wsc` CLI, so the extraction,
the pacing, the cache and the source table all come from the Python package and none of them is
reimplemented in TypeScript.

## Install

From this checkout:

```bash
pi -e ~/projects/webscour/extensions/pi/webscour.ts
```

To keep it available in every session, copy it into pi's extension directory:

```bash
cp extensions/pi/webscour.ts ~/.pi/agent/extensions/
```

`wsc` must be on `PATH` (`pipx install webscour`, or `pip install --user -e .` from the repo).
If it lives somewhere unusual, point the extension at it:

```bash
export WEBSEARCH_WSC=/path/to/wsc
```

## Why it is outside the wheel

The wheel is the CLI: Python, standard library, no front end. This directory is TypeScript, it
exists for one host, and it has no Python dependency of its own. Packaging it in the wheel would
make every `pip install webscour` carry a file that only a pi user can run, and it would put a
second copy of the argv mapping where the first copy cannot see it. So it ships in the repo and
`pip install` never touches it.

## The argv mapping

This file does not build a command line. It calls `wsc tool-argv --json '<params>'` and runs what
comes back, which is `webscour/argv.py`: the same function `mcp/server.py` calls. That is the one
place a tool call becomes flags, and it is the same process the MCP server uses.

## The untrusted-content warning

Every page's text is returned inside `<<<webscour:untrusted-content>>>` delimiters, prefixed with
a line saying it is data and not instructions. A CLI prints to a terminal a human is watching; a
tool result is read by a model that may act on it, and that is the difference this wrapper exists
for. The same text is in `mcp/server.py`, from the same source in `webscour/argv.py`.
