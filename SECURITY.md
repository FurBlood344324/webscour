# Security

Everything `wsc` fetches is attacker-controlled text, and the attacker knows a model will read it:
the interesting risk is not a compromised host, it is a page that talks its way into the caller's
instructions.

- **Fetched page text is untrusted input.** A page can address the model directly ("ignore your
  previous instructions", "run this command"). The tool passes it through unchanged, because
  rewriting a page would make the output a lie. Treat it as evidence, not as orders.
- **The tool never executes page content.** No `eval`, no shell, no downloaded binary. The one
  subprocess call is a local binary (`pdftotext`, `pandoc`, `markitdown`) reading an already
  downloaded file, with an explicit argument list and no shell.
- **The MCP server and the pi extension wrap fetched content in delimiters**, with a header saying
  it is data (`webscour/argv.py`). That helps a cooperating model; it is not a sandbox. A caller
  that strips the wrapper is outside what the tool can enforce, so the wrapper is the contract and
  the caller must still treat the content as data.
- **No secrets are held and no account exists.** No key to leak, no token store, no telemetry, no
  log file. The SearXNG secret is generated locally at install time and stays on the machine.

## Reporting a vulnerability

Email `maintainer@wsc.ashina.live` with what you did, what happened, and the output of
`wsc --version`; do not open a public issue first. A valid report gets a patch release and credit
unless you ask otherwise. A minimal reproduction is enough: leave out live credentials, private
URLs and other people's personal data.

## Out of scope

A site answering 403, 429, a CAPTCHA or a bot check; search results that are wrong or oddly ranked;
a prompt-injection attempt inside a fetched page, which the tool reports rather than obeys, so
report it only if the wrapper failed; anything requiring the attacker to already control the
machine, the shell, or the model's system prompt.

## Supported versions

The latest release on PyPI. No maintained branches while the version is 0.x.
