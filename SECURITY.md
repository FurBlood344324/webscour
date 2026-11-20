# Security

Everything `wsc` fetches is attacker-controlled text, and the attacker knows a model will read it:
the interesting risk is not a compromised host, it is a search result that talks its way into the
caller's instructions.

- **Fetched result text is untrusted input.** A title, a snippet or an abstract can address the
  model directly ("ignore your previous instructions", "run this command"). The tool passes it
  through unchanged, because rewriting a payload would make the output a lie. Treat it as evidence,
  not as orders.
- **The tool never executes page content.** No `eval`, no shell, no subprocess, no downloaded
  binary. It is one process making HTTP requests and printing rows.
- **No secrets are held and no account exists.** No key to leak, no token store, no telemetry, no
  log file. The only file written is the one-second pacing stamp under `$XDG_CACHE_HOME/web/`.
- **The tool is not a sandbox for the model.** A caller that reads a snippet as an instruction is
  outside what any CLI can enforce; the CLI's job is to hand over the text and name the source.

## Reporting a vulnerability

Email `maintainer@wsc.ashina.live` with what you did, what happened, and the output of
`wsc --version`; do not open a public issue first. A valid report gets a patch release and credit
unless you ask otherwise. A minimal reproduction is enough: leave out live credentials, private
queries and other people's personal data.

## Out of scope

A site answering 403, 429, a CAPTCHA or a bot check; search results that are wrong or oddly ranked;
a prompt-injection attempt inside a result, which the tool reports rather than obeys; anything
requiring the attacker to already control the machine, the shell, or the model's system prompt.

## Supported versions

The latest release on crates.io. No maintained branches while the version is 0.x.
