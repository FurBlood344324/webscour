# Saving output

A page read once and needed twice is the most common waste in an agent loop.

## The contract

`--save` writes what you just fetched into `./.webscour/`, one file per URL, named
`<hash>-<host>-<path>.md`. `index.json` beside it records URL, bytes, when, format and which route
answered. The directory is created on demand, its index is written by rename so a killed process
leaves no half-parsed JSON, and it is safe to delete at any time: nothing else depends on it.

Reading back is on by default. A `fetch` of the same URL inside 24 hours answers from the file and
prints `cache: hit (2m ago)` on stderr: 0.12 s instead of 0.3 to 0.9 s. That is the whole feature.

## Which flag does what

| Flag | Effect |
|---|---|
| `--save` | write the page into `./.webscour/` **and** print it |
| `--save-only` | write it, print one index line (`.webscour/<file>  text  44561 bytes`), not the page |
| (nothing) | no write; a cached copy is still read if one exists |
| `--fresh` | ignore the cache for this call (and re-save if `--save` is also given) |
| `--ttl 30m` / `--ttl 7d` | how old a cached copy may be before it stops counting (default 24 h) |
| `--no-cache` | neither read nor write; it also turns `--save` off, with a `-v` note |
| `--max-size N` | refuse to save a body over N bytes (default 5 MiB) |

Four verbs cover the directory:

    wsc cache list [--json]        # what is here: fetched, bytes, age, format, file
    wsc cache get <url>            # print it; on a miss, fetch it, save it, print it
    wsc cache prune --older-than 7d [--all]
    wsc cache path                 # the absolute path, for a script

`cache get` ignores the TTL on purpose: it is the "give me that page again" verb, so an old file is
still the answer. On a miss it fetches with `--save --fresh`, so the next call is always local.

## When to save

- You will read it more than once. Two reads are the break-even point.
- It is long and you only need parts: save once, then read a line range.
- You need it after the session; a file outlives the context window.
- You are about to summarise it, and the summary should be checkable later.

## When not to

- You need one line. `--grep` returns the line and its neighbours without writing anything.
- It is a `search`. Rows are already 200-char snippets; there is no page to keep.
- The answer is already in the cache. Check `wsc cache list` before fetching the same URL again.
- You do not own the directory. See below.

## Where it goes, and the one rule

`./.webscour/` is relative to the **agent's current working directory**, which is the project you are
working in. Deliberate: a repo that keeps its captures keeps them next to the code that needs them.

Never create `.webscour/` in the root of a project you did not create, and never in `/`. In a checkout
you do not own, fetch from a scratch directory you make for the job:

    mkdir -p /tmp/ws-$$ && cd /tmp/ws-$$ && wsc fetch "<url>" --save-only

A `.gitignore` containing `*` is written inside the directory on creation, so git never sees a
capture. If you keep captures deliberately, add `.webscour/` to the project's own `.gitignore`; never
commit the files.

## Reading it back in parts

The point of the file is that you do not have to print it:

    wsc cache path                                  # /path/to/project/.webscour
    grep -n -E "raise|TimeoutError" .webscour/<file>.md   # one question, a few lines
    wsc cache get "<url>" | sed -n '120,180p'        # one section, by line range
    scripts/page-sections.sh .webscour/<file>.md    # the heading map first

`wsc fetch "<url>" --grep "<re>"` is the one-request version when the excerpt is all you need; add
`--save` only if that excerpt is what you want on disk (see the first known gap).

## Known gaps, as of 0.1.0

- **`--save` writes exactly what it printed.** With `--grep` that is the excerpt, not the page, and a
  later plain `fetch` answers with the excerpt and calls it a `cache: hit`; `--fresh` is the only way
  back. Save and grep as two steps.
- **A cache hit replays the stored format and ignores `--grep`.** `--format markdown --save` makes
  every later read of that URL markdown, even asking for `text`; a `--grep` against a cached URL
  returns the head of the file. Grep the file yourself or pass `--fresh`.
- **`wsc pdf` has no `--save`.** Keep a paper with `wsc pdf <url> --max-chars 200000 > p.md`, or
  `wsc cache get <pdf url>`.
- **A body over `--max-size` is not saved**, and the fetch still succeeds:
  `save: 37814 bytes is over the 1000 byte save limit; raise it with --max-size`.
- **`--no-cache` plus `--save` writes nothing**: `save: --no-cache turns saving off too`. A caller who
  said "do not touch the cache" did not mean "except this once".
