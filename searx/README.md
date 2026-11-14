# searx: a local SearXNG as the first web backend

`wsc search --source web` asks a SearXNG on **127.0.0.1:8888** first, and falls back to the
scrapers only when that is unavailable. No API key, no credits, no docker and no sudo: a venv
under `~/.local/share/searxng`, settings under `~/.config/searxng`, one systemd **user** unit.

    wsc setup                                # idempotent install; --check state only, --force new venv
    wsc probe --doctor                       # unit, port, engine health, one verdict
    wsc probe --quality --write              # measure engines, then keep the survivors

The same scripts run by hand if you prefer to read them first:

    ./install.sh [--check|--force|--no-start]
    ./probe-engines.py --doctor
    ./probe-engines.py --quality --write

Pinned commit `de722ab1bc95` (searxng 1.0.0), python3.11, granian WSGI, loopback only. The
secret is generated at install time into `~/.config/searxng/secret_key` (mode 600) and never
enters a repository. Log level WARNING, access log off, `use_default_settings: true` plus
`keep_only`, engine timeout 5 s, request cap 6 s.

SearXNG logs the outgoing request URL, query included. The unit therefore runs `serve.py`
(copied to the runtime directory), which filters every log record and replaces any URL query
string with `?<query withheld>`. The journal keeps the engine errors and none of the terms.

## Engines, measured on a residential IP (2026-11-13, 30 generic queries)

Per-engine isolation is not usable: duckduckgo, google, mojeek, qwant, startpage, searchmysite
and yandex answer CAPTCHA, "access denied" or a parsing error from a residential IP, and brave
suspends after a few requests. The bar is **coverage** (how often an engine helps a merged
query) and **precision** (share of its rows that are on topic); kept means coverage >= 10 % and
precision >= 60 %. Median merged query 5.0 s.

| engine | cover | prec | rows | | engine | cover | prec | rows |
|---|---|---|---|---|---|---|---|---|
| naver | 90.0 % | 80.1 % | 403 | | wikibooks | 20.0 % | 93.8 % | 16 |
| abcnyheter | 70.0 % | 95.3 % | 214 | | wiby | 13.3 % | 42.9 % | 21 (dropped) |
| rawweb | 53.3 % | 98.8 % | 82 | | wikiversity, wikiquote | <=6.7 % | 100 % | 1-2 (dropped) |
| bing | 36.7 % | 60.0 % | 180 | | encyclosearch, wikisource | 3.3 % | 50 % | 2-14 (dropped) |
| yacy | 30.0 % | 96.7 % | 90 | | brave | 0 % this pass | n/a | kept by name |

Kept (7): **naver, abcnyheter, rawweb, bing, yacy, wikibooks, brave**. Brave is kept by name
rather than by score because it recovers when its 180 s suspension lapses. The arxiv, github,
stackoverflow and hackernews engines were dropped: `--source github|so|hn|arxiv` serves them
better and without a middleman.

## Failure modes

- **Down**: start the unit once, wait 8 s, then fall back to ddg-lite, ddg-html, bing. `-v`
  prints one `backend <name>: <reason>` line per attempt; exit 2 when nothing answers.
- **Degraded**: a few engines are suspended at any time. Fewer results, still answers. `wsc
  doctor` names the silent ones. brave, yacy, abcnyheter and reloado flap: expected, not a fault.
- **Drift**: bing sometimes answers a neighbouring query. A row whose title and url both lack
  every query term is dropped. `rm ~/.local/share/searxng/engines.json` re-enables every
  candidate.
