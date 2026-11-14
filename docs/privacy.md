# Privacy

This page states what leaves the machine, what does not, what is logged, and how to check the
claims yourself. Everything here describes the default configuration: the bundled local SearXNG
on loopback, and nothing else. If you point the CLI at a remote SearXNG you have changed the
trust boundary, and the last section says what that means.

## What leaves the machine

Exactly one thing for a search: **the query**.

1. `wsc search "<query>"` sends the query text to `http://127.0.0.1:8888`, the local SearXNG,
   over loopback. That request also carries `format=json`, `safesearch=0` and `timeout_limit=6`.
2. SearXNG forwards the query to whichever of its enabled upstream engines your IP can use. That
   is the only step where the query leaves the machine, and it is SearXNG doing it, not this CLI.
3. `wsc fetch`, `wsc map` and `wsc crawl` send the URL you named, and nothing else, to the host
   that URL points at. There is no query in those requests.
4. `wsc search --source <service>` skips SearXNG and sends the query straight to that service.
   That is one service, named in the command, instead of a meta-search.

The outgoing request headers are fixed and minimal: one user agent string identifying a normal
browser, `Accept-Language: en-US,en;q=0.9`, and the accept header the request needs. There is no
cookie jar, no referrer, no client id, and no header carrying anything about you.

`wsc --self-test` is the exception that proves the rule: it opens no socket at all. It runs
offline by construction, and `scripts/check.sh` depends on that.

## What never leaves

None of these are read by the tool, so none of them can be sent:

- **URLs you fetch.** `map` and `crawl` send only the URL you gave them, plus the links they
  follow on that same origin. Nothing about what you fetched goes anywhere else.
- **Your working directory.** The tool never asks the process for it in order to identify you.
  Its cache directory is resolved relative to the working directory for a local file write only,
  and that path is never sent.
- **Your hostname.** No `gethostname` call exists in the code.
- **Your username and home path.** The tool resolves its own directories by expanding `~`,
  locally only. Nothing sends the result.
- **Your project names.** Nothing enumerates a project, a repository or a config file in your
  working tree.

That is not an assurance to take on faith. `wsc --self-test` includes a check named
`no identity in request` that reads the source of `webscour/cli.py` and fails if the assembly
`get` + `pass`, `gethost` + `name` or `get` + `login` appears anywhere in it. Those three are the
ways a Python program reads the pieces of an identity, and the check is why they are absent rather
than merely unused.

## What is logged

**The tool logs nothing.** It writes no log file, no history and no state about your queries. Two
files it does write are yours and local:

- `~/.cache/web/last-live` holds one floating point timestamp of the last live request, which is
  what enforces at most one web query per second across processes. It holds a number, not a
  query, and `cat` shows it.
- `./.webscour/` exists only if you asked for it with `--save`, `--save-only` or `cache get`. It
  contains the page text you asked to keep and an index beside it. `wsc cache path` prints the
  directory and `wsc cache prune --all` removes it.

**The bundled SearXNG drops the query.** Stock SearXNG logs the outgoing request URL at WARNING
from `searx.network.<engine>`, and that URL carries the query text as `?q=...`. The bundled unit
does three things about that:

- `GRANIAN_LOG_ACCESS_ENABLED=false` in the unit, so there is no access log at all.
- `GRANIAN_LOG_LEVEL=warning`, so nothing below a warning is emitted.
- `searx/serve.py` is the WSGI entrypoint instead of stock `searx.webapp`, and it installs a
  `logging.Filter` on the root logger, `searx`, `searx.network`, `searx.search`, `searx.webapp`
  and `granian`. The filter rewrites every URL query string in a record to `?<query withheld>`
  before any handler sees the record, keeping the host so the warning still says which engine was
  suspended.

Autocomplete is off in the generated settings (`autocomplete: ""`), so no keystroke leaves the
box. `query_in_title` is off. Metrics are on, because `/stats/errors` is what `wsc doctor` reads,
and that endpoint carries engine failure counts and no query text.

## How to verify it

Read the three files that make the claim. They are short and they are the actual mechanism.

```bash
sed -n '1,43p' searx/serve.py        # the filter, and the loggers it is installed on
sed -n '199,231p' searx/install.sh   # the unit: bind, access log, level, entrypoint
sed -n '128,164p' searx/install.sh   # the generated settings: autocomplete, metrics, bind
```

Then check the running machine rather than the source:

```bash
systemctl --user cat searxng-local        # the installed unit, with its environment
ss -ltn | grep 8888                       # one row, and it starts 127.0.0.1:
journalctl --user -u searxng-local -n 50  # recent records; no query text in any of them
```

Run a query you can recognise, then read the journal:

```bash
wsc search "privacy-check-marker-<a word you never use>" --limit 1
journalctl --user -u searxng-local --since "2 min ago"
```

You will see the engine warnings, if any, with `?<query withheld>` where a URL would have carried
your terms, and no record containing the marker. That is the whole claim, and it is falsifiable in
two commands.

To check what actually leaves your machine to the internet rather than to loopback, watch the
sockets:

```bash
ss -tunp | grep -i searx                  # the SearXNG process's outbound connections
```

Those connections go to the upstream engines, and they carry the query. That is what a
meta-search does.

## Where the tool sits, and where it does not protect you

- **Your IP is your identity to the upstream engines.** A local proxy does not change that. The
  point of the local SearXNG is that no third party sees who is asking through an API key, not
  that the request is anonymous.
- **Send generic technical terms.** Private context in a query is a mistake regardless of the log
  settings, because the upstream engine receives the query by design.
- **A direct `--source` is a direct request.** A service named on the command line sees the query
  and your IP, from your machine, with no middleman. Those services keep their own logs, and this
  tool has no say in that.
- **`fetch`, `map` and `crawl` reveal the URL to that site.** A crawl of a private intranet host
  is visible to that host. The tool paces requests but does not hide them.

## If you point it at a remote SearXNG

The CLI reads one environment variable for the backend:

```bash
export WEBSEARCH_SEARXNG="https://searx.example.net"
wsc search "sqlite wal mode"
```

That changes the trust boundary completely, and you should be explicit about how:

- **The query travels over the network to that host** before it reaches any engine, so the
  operator of that instance sees it, and so does every hop in between unless the URL is https.
- **The log claim stops applying.** `searx/serve.py` and the generated settings belong to the
  bundled unit on your machine. A remote instance runs whatever its operator installed.
- **`wsc doctor` reports on that host, not on yours.** It will call a remote instance healthy and
  endorse it, because health is all it measures.

The default is loopback, and the reason to keep it there is that it is the only configuration in
which every claim on this page is a property of code you can read on your own disk.

Related: [self-hosting](self-hosting.md) covers what `wsc setup` writes and how to remove it, and
[sources](sources.md) names the services a direct `--source` query reaches.
