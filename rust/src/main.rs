//! `wsc`: one verb, `search`, and the two housekeeping flags.
//!
//! The argv parser is hand-rolled on purpose. There is exactly one verb with six flags; a
//! derive-based parser would be a dependency and a proc-macro compile for a `match` loop, and
//! the exit codes here are part of the contract with the Python CLI (`0` answered, `2` usage or
//! no answer, `1` help with no verb). Keeping them literal keeps them checkable.

use std::io::Write;

use webscour::backends;
use webscour::net::{self, FetchError};
use webscour::row::Row;
use webscour::search;
use webscour::selftest;
use webscour::sources;

/// A GitHub search: rows plus what is left of the unauthenticated rate limit.
type GhSearch = fn(&str, usize) -> Result<(Vec<Row>, Option<String>), FetchError>;

const MAIN_DOC: &str = "wsc - keyless search from the command line, with small output. Linux.

    wsc search \"<query>\" [--source SRC] [--limit N] [--category C] [--fresh [--since D]] [--json]
    wsc --self-test
    wsc --version

`--source` is one of web, github, so, hn, arxiv, discourse:<base>, rss:<feed-url>, or a keyless
API source:
wikipedia, openalex, crossref, arxiv-api, europepmc, pubmed, pypi, npm, crates, devto, wayback,
googlenews, bbc. `--fresh` restricts to the freshness rows (Google News, BBC, SearXNG news) and
sorts by publication date.

`--source web` asks a LOCAL SearXNG (127.0.0.1:8888, WEBSEARCH_SEARXNG overrides) first and
falls back to DuckDuckGo lite, DuckDuckGo html and Bing, in that order. At most one live web
query runs per second, across processes. Output is the answer: stderr carries failures only.";

fn main() {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let code = run(&argv);
    std::process::exit(code);
}

fn run(argv: &[String]) -> i32 {
    let Some(first) = argv.first() else {
        println!("{}", MAIN_DOC);
        return 1;
    };
    match first.as_str() {
        "-h" | "--help" => {
            println!("{}", MAIN_DOC);
            0
        }
        "-V" | "--version" => {
            println!("webscour {}", webscour::VERSION);
            0
        }
        "--self-test" => {
            let stdout = std::io::stdout();
            let mut out = stdout.lock();
            if selftest::run(&mut out) {
                let _ = writeln!(out, "all checks passed");
                0
            } else {
                1
            }
        }
        "search" => cmd_search(&argv[1..]),
        other => {
            eprintln!("unknown command {:?}", other);
            println!("{}", MAIN_DOC);
            2
        }
    }
}

/// The flags `search` understands, parsed once so an unknown flag is an error and not a
/// silently dropped word in the query.
struct SearchArgs {
    query: String,
    source: String,
    limit: usize,
    category: String,
    fresh: bool,
    since: String,
    json: bool,
    verbose: bool,
}

fn parse_search(argv: &[String]) -> Result<SearchArgs, String> {
    let mut a = SearchArgs {
        query: String::new(),
        source: "web".into(),
        limit: 8,
        category: String::new(),
        fresh: false,
        since: String::new(),
        json: false,
        verbose: false,
    };
    let mut i = 0;
    while i < argv.len() {
        let arg = &argv[i];
        let mut take = |name: &str| -> Result<String, String> {
            i += 1;
            argv.get(i)
                .cloned()
                .ok_or_else(|| format!("{} needs a value", name))
        };
        match arg.as_str() {
            "--source" => a.source = take("--source")?.trim().to_string(),
            "--limit" => {
                let v = take("--limit")?;
                // Clamped in i64 and only then narrowed: `--limit -3` is 1, and casting a
                // negative number to usize first would make it 30 instead.
                let n = v
                    .parse::<i64>()
                    .map_err(|_| format!("invalid --limit {:?}", v))?;
                a.limit = n.clamp(1, 30) as usize;
            }
            "--category" => a.category = take("--category")?,
            "--since" => a.since = take("--since")?,
            "--fresh" => a.fresh = true,
            "--json" => a.json = true,
            "-v" | "--verbose" => a.verbose = true,
            "-h" | "--help" => {
                println!("{}", MAIN_DOC);
                std::process::exit(0);
            }
            other if other.starts_with("--") => return Err(format!("unknown flag {:?}", other)),
            other => {
                if a.query.is_empty() {
                    a.query = other.to_string();
                } else {
                    a.query = format!("{} {}", a.query, other);
                }
            }
        }
        i += 1;
    }
    if a.query.trim().is_empty() {
        return Err("a query is required (wsc search \"<query>\" [--source SRC] [--limit N])".into());
    }
    Ok(a)
}

fn cmd_search(argv: &[String]) -> i32 {
    let a = match parse_search(argv) {
        Ok(a) => a,
        Err(e) => {
            eprintln!("search: {}", e);
            return 2;
        }
    };
    let mut note: Option<String> = None;

    if !a.since.is_empty() {
        if !valid_date(&a.since) {
            eprintln!("search: --since must be YYYY-MM-DD");
            return 2;
        }
        if !a.fresh {
            eprintln!("search: --since only means something with --fresh");
            return 2;
        }
    }

    let mut results: Vec<Row> = Vec::new();

    if a.fresh {
        if a.source != "web" {
            eprintln!(
                "search: --fresh is its own source set; drop --source {:?}",
                a.source
            );
            return 2;
        }
        let verbose = a.verbose;
        results = sources::fresh(
            &a.query,
            a.limit,
            &a.since,
            Some(move |q: &str, n: usize| backends::searx_news(q, n, verbose)),
            a.verbose,
        );
        if results.is_empty() {
            eprintln!("no fresh results (Google News and BBC RSS both empty for this query)");
            return 2;
        }
        return finish(&a, &results, &note);
    }

    // A category is a SearXNG parameter and nothing else, so any other source is a usage error
    // rather than a flag that is quietly ignored.
    if a.source != "web" && !a.category.is_empty() {
        eprintln!("search: --category only applies to --source web (SearXNG)");
        return 2;
    }

    match a.source.as_str() {
        "web" => {
            // A category is a SearXNG parameter and nothing else, so a categorised query has no
            // scraper fallback: DDG lite cannot be asked for `it` or `news`, and pretending
            // otherwise answers a different question than the one asked.
            results = backends::web_search(&a.query, a.limit, &a.category, a.verbose, &mut |line| {
                eprintln!("{}", line)
            });
        }
        "github" => {
            // `left` is only set by a call that answered, and the Python prints the last one it
            // saw: a source that failed has no rate limit to report, and a missing header is the
            // string "None" in both implementations rather than an invented number.
            let mut left: Option<Option<String>> = None;
            let calls: [(&str, GhSearch); 2] =
                [("repos", search::gh_repos), ("issues", search::gh_issues)];
            for (kind, fn_) in calls {
                match fn_(&a.query, a.limit) {
                    Ok((got, remaining)) => {
                        left = Some(remaining);
                        results.extend(got);
                    }
                    Err(e) => eprintln!("backend github-{}: {}", kind, e),
                }
            }
            results.truncate(a.limit);
            if let Some(remaining) = left {
                note = Some(format!(
                    "github rate limit remaining: {}",
                    remaining.unwrap_or_else(|| "None".into())
                ));
            }
        }
        "so" => match search::so_search(&a.query, a.limit) {
            Ok(r) => results = r,
            Err(e) => eprintln!("backend so: {}", e),
        },
        "hn" => match search::hn_search(&a.query, a.limit) {
            Ok(r) => results = r,
            Err(e) => eprintln!("backend hn: {}", e),
        },
        "arxiv" => match search::arxiv_search(&a.query, a.limit) {
            Ok(r) => results = r,
            Err(e) => eprintln!("backend arxiv: {}", e),
        },
        other if other.starts_with("rss:") => {
            // `rss:<feed-url>`: one request, the same reader the news sources use.
            let url = other.split_once(':').map(|(_, u)| u).unwrap_or("");
            match sources::rss_url(url, a.limit) {
                Ok(r) => results = r,
                Err(e) => eprintln!("backend rss: {}", e),
            }
        }
        other if other.starts_with("discourse:") => {
            let base = other.split_once(':').map(|(_, b)| b).unwrap_or("");
            match search::discourse_search(base, &a.query, a.limit) {
                Ok(r) => results = r,
                Err(e) => eprintln!("backend discourse: {}", e),
            }
        }
        other => {
            match sources::fetch(other, &a.query, a.limit) {
                Some(Ok(r)) => results = r,
                Some(Err(e)) => eprintln!("backend {}: {}", other, e),
                None => {
                    eprintln!(
                        "unknown --source {:?} ({})",
                        other,
                        sources::sources_help()
                    );
                    return 2;
                }
            }
        }
    }

    if results.is_empty() {
        eprintln!("no results");
        return 2;
    }
    finish(&a, &results, &note)
}

fn finish(a: &SearchArgs, results: &[Row], note: &Option<String>) -> i32 {
    print!("{}", net::render(results, a.json));
    if let Some(n) = note {
        if a.json {
            eprintln!("-- {}", n);
        } else {
            println!("-- {}", n);
        }
    }
    // A closed pipe is not an error for a CLI whose reader went first (`head -1`), so the
    // flush is checked and the result thrown away rather than turned into an exit code.
    let _ = std::io::stdout().flush();
    0
}

fn valid_date(text: &str) -> bool {
    let b = text.as_bytes();
    b.len() == 10
        && b[..4].iter().all(|c| c.is_ascii_digit())
        && b[4] == b'-'
        && b[5..7].iter().all(|c| c.is_ascii_digit())
        && b[7] == b'-'
        && b[8..10].iter().all(|c| c.is_ascii_digit())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn args(list: &[&str]) -> Vec<String> {
        list.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn a_query_with_flags_parses() {
        let a = parse_search(&args(&["ureq rust", "--source", "github", "--limit", "3"])).unwrap();
        assert_eq!(a.query, "ureq rust");
        assert_eq!(a.source, "github");
        assert_eq!(a.limit, 3);
    }

    #[test]
    fn an_unknown_flag_is_an_error_not_a_query_word() {
        assert!(parse_search(&args(&["x", "--sourcee", "hn"])).is_err());
    }

    #[test]
    fn the_limit_is_clamped_like_the_python() {
        assert_eq!(parse_search(&args(&["x", "--limit", "999"])).unwrap().limit, 30);
        assert_eq!(parse_search(&args(&["x", "--limit", "0"])).unwrap().limit, 1);
    }

    #[test]
    fn a_negative_limit_is_one_and_not_the_maximum() {
        assert_eq!(parse_search(&args(&["x", "--limit", "-3"])).unwrap().limit, 1);
        assert_eq!(parse_search(&args(&["x", "--limit", "-3"])).unwrap().limit, 1);
    }

    #[test]
    fn a_missing_query_is_a_usage_error() {
        assert!(parse_search(&args(&["--json"])).is_err());
    }
}
