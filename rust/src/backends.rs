//! The web backend: a local SearXNG first, then the three scrapers, and the pacing around them.
//!
//! SearXNG is one loopback call, so it is cheap and it is first. When it is down or answers
//! nothing, the scrapers run in a fixed order - DDG lite, DDG html, Bing - because that is
//! the order someone actually got a page from, and the first one that answers ends the chain.
//! A circuit that silently skipped a backend would report an empty web instead of a closed door,
//! so each failure is one line on stderr.

use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};

use serde_json::Value;

use crate::html;
use crate::net::{self, FetchError, Response, UA, ARCHIVE_UA};
use crate::row::Row;
use crate::util;

/// Local SearXNG: the first web backend. A loopback call, so it is cheap; the upstream engines
/// are what would notice a hammering client, and they sit behind one process, not us.
pub fn searx_base() -> String {
    std::env::var("WEBSEARCH_SEARXNG")
        .unwrap_or_else(|_| "http://127.0.0.1:8888".to_string())
        .trim_end_matches('/')
        .to_string()
}

pub const SEARX_UNIT: &str = "searxng-local";
/// > the server-side 6 s cap, so a slow answer is not read as a dead port.
pub const SEARX_TIMEOUT: u64 = 15;
pub const SEARX_START_WAIT: f64 = 8.0;
/// Fewer merged rows than this means an upstream flapped, not that the web is empty.
pub const SEARX_RETRY_BELOW: usize = 5;

/// A searxng answer thinner than this is a quality signal, not an answer: the scraper chain is
/// asked as well. Three rows is the floor, because hit@3 with two rows has no room under it.
pub const SEARX_FALLBACK_BELOW: usize = 3;

/// SearXNG JSON -> (rows, unresponsive engine names). Pure, so `--self-test` can use it.
pub fn parse_searxng(doc: &Value) -> (Vec<Row>, Vec<String>) {
    let mut got = Vec::new();
    if let Some(results) = doc.get("results").and_then(|v| v.as_array()) {
        for r in results {
            let mut url = r
                .get("url")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim()
                .to_string();
            if url.is_empty() {
                continue;
            }
            let primary = r
                .get("engine")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            let mut names: Vec<String> = r
                .get("engines")
                .and_then(|v| v.as_array())
                .map(|a| {
                    a.iter()
                        .filter_map(|e| e.as_str())
                        .filter(|e| !e.is_empty())
                        .map(|e| e.to_string())
                        .collect()
                })
                .unwrap_or_default();
            if names.is_empty() && !primary.is_empty() {
                names.push(primary.clone());
            }
            if url.starts_with("https://www.google.com/url") || url.starts_with("http://www.google.com/url")
            {
                url = net::unwrap_url(&url);
                if url.is_empty() {
                    continue; // an opaque redirect shell: drop the row rather than print junk
                }
            }
            let title = r
                .get("title")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim()
                .to_string();
            let title = if title.is_empty() { url.clone() } else { title };
            let snippet = r
                .get("content")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .trim()
                .to_string();
            got.push(Row::raw(&title, &url, &snippet).with_engines(names));
        }
    }
    let dead: Vec<String> = doc
        .get("unresponsive_engines")
        .and_then(|v| v.as_array())
        .map(|a| {
            a.iter()
                .map(|e| match e {
                    Value::Array(pair) => pair
                        .first()
                        .map(|n| match n {
                            Value::String(s) => s.clone(),
                            other => other.to_string(),
                        })
                        .unwrap_or_default(),
                    other => other.to_string(),
                })
                .collect()
        })
        .unwrap_or_default();
    (got, dead)
}

fn searx_netloc() -> (String, u16) {
    let base = searx_base();
    let rest = base.split("://").nth(1).unwrap_or(&base);
    let authority = rest.split('/').next().unwrap_or(rest);
    match authority.rsplit_once(':') {
        Some((host, port)) => (host.to_string(), port.parse().unwrap_or(8888)),
        None => (authority.to_string(), 8888),
    }
}

fn port_open(host: &str, port: u16) -> bool {
    let addrs = match (host, port).to_socket_addrs() {
        Ok(a) => a.collect::<Vec<_>>(),
        Err(_) => return false,
    };
    addrs
        .into_iter()
        .any(|addr| TcpStream::connect_timeout(&addr, Duration::from_millis(500)).is_ok())
}

/// The port may refuse because the user unit is stopped: start it once, wait, re-check.
pub fn searx_start() -> bool {
    let (host, port) = searx_netloc();
    if port_open(&host, port) {
        return true;
    }
    let started = std::process::Command::new("systemctl")
        .args(["--user", "start", SEARX_UNIT])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status();
    if started.is_err() {
        return false;
    }
    let deadline = Instant::now() + Duration::from_secs_f64(SEARX_START_WAIT);
    while Instant::now() < deadline {
        if port_open(&host, port) {
            return true;
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    false
}

fn searx_ask(params: &str, verbose: bool) -> Result<(Vec<Row>, Vec<String>), FetchError> {
    let path = format!("{}/search?{}", searx_base(), params);
    let ask = |live: bool| -> Result<Value, FetchError> {
        if live {
            util::pace(verbose);
        }
        let resp = net::http(&path, None, Some("application/json"), SEARX_TIMEOUT)?;
        serde_json::from_str(&resp.body)
            .map_err(|e| FetchError::new(format!("local SearXNG returned invalid JSON ({})", e)))
    };
    let data = match ask(true) {
        Ok(v) => v,
        Err(first) => {
            if !searx_start() {
                return Err(FetchError::new(format!(
                    "local SearXNG {} not answering ({}) and {} did not start",
                    searx_base(),
                    first,
                    SEARX_UNIT
                )));
            }
            ask(true)?
        }
    };
    let (mut rows, dead) = parse_searxng(&data);
    for r in &mut rows {
        r.url = net::unwrap_url(&r.url);
    }
    rows.retain(|r| !r.url.is_empty());
    Ok((rows, dead))
}

/// The SearXNG query for `--source web`. A `category` is passed through as `--category` and
/// nothing else, because DuckDuckGo lite cannot be asked for `it` or `news`.
pub fn searx_web(query: &str, limit: usize, category: &str, verbose: bool) -> Result<Vec<Row>, FetchError> {
    let mut params = vec![
        format!("q={}", util::quote_plus(query)),
        "format=json".to_string(),
        "safesearch=0".to_string(),
        "timeout_limit=6".to_string(),
    ];
    if !category.is_empty() {
        params.push(format!("categories={}", util::quote_plus(category)));
    }
    let params = params.join("&");
    let (mut got, mut dead) = searx_ask(&params, verbose)?;
    if !dead.is_empty() && verbose {
        eprintln!(
            "searxng: {} engine(s) down: {}",
            dead.len(),
            dead.iter().take(8).cloned().collect::<Vec<_>>().join(", ")
        );
    }
    // An engine that timed out at that instant does not mean the web is empty, and it does not
    // mean the answer is unrelated either. One retry only: a loop here is the scraper behaviour
    // this tool exists to avoid.
    let first_pick = util::prefer_on_topic(query, got.clone(), limit);
    if got.len() < SEARX_RETRY_BELOW || !util::related(query, &first_pick) {
        // Both draws are kept. A second draw is another look at the same question, not a
        // replacement for the first: the rows only the first found are evidence too, and the
        // merge is deduped and ranked, so the retry can no longer lose a row.
        let (again, dead2) = searx_ask(&params, verbose)?;
        got = merge_draws(got, again);
        for name in dead2 {
            if !dead.contains(&name) {
                dead.push(name);
            }
        }
    }
    let pool = util::pick_on_topic(query, got);
    let got: Vec<Row> = util::rank(query, pool).into_iter().take(limit).collect();
    if got.is_empty() {
        return Err(FetchError::new(format!("no results ({} engines down)", dead.len())));
    }
    if !util::related(query, &got) {
        return Err(FetchError::new("results unrelated to the query"));
    }
    Ok(got)
}

/// Two draws of the same question as one list: the first draw keeps its order and its rows, the
/// second contributes what the first did not carry, and a repeated url is kept once.
pub fn merge_draws(first: Vec<Row>, second: Vec<Row>) -> Vec<Row> {
    let mut both = first;
    both.extend(second);
    util::dedupe(both)
}

/// The SearXNG `news` category, tolerant: no local SearXNG is not an error for `--fresh`.
pub fn searx_news(query: &str, limit: usize, verbose: bool) -> Vec<Row> {
    match searx_web(query, limit, "news", verbose) {
        Ok(rows) => rows
            .into_iter()
            .map(|mut r| {
                if r.published.is_none() {
                    r.published = Some(String::new());
                }
                r
            })
            .collect(),
        Err(e) => {
            if verbose {
                eprintln!("fresh: searxng news: {}", e);
            }
            Vec::new()
        }
    }
}

/// Per-row acceptance for a scraped draw.
///
/// A page mixes the answer with cached noise, and the set-level test used to throw the whole
/// page away on one unrelated row, including the answer standing next to it. A row that carries
/// a query term is kept on its own evidence; the set is refused only when not one row does,
/// which is the cached-page and bot-check case.
fn accept_draw(query: &str, rows: Vec<Row>) -> Result<Vec<Row>, FetchError> {
    if rows.is_empty() {
        return Ok(rows);
    }
    let kept = util::keep_on_topic(query, rows);
    if kept.is_empty() {
        return Err(FetchError::new("results unrelated to the query"));
    }
    Ok(kept)
}

fn scrape(name: &str, query: &str, limit: usize, verbose: bool) -> Result<Vec<Row>, FetchError> {
    // The scrapers are live web queries like any other, and this path used to skip the pace.
    util::pace(verbose);
    let got = match name {
        "ddg-lite" => {
            let body = format!("q={}", util::quote_plus(query));
            let resp = net::http("https://lite.duckduckgo.com/lite/", Some(&body), None, net::TIMEOUT)?;
            check_blocked(&resp.body)?;
            html::parse_ddg_lite(&resp.body)
        }
        "ddg-html" => {
            let url = format!(
                "https://html.duckduckgo.com/html/?q={}",
                util::quote_plus(query)
            );
            let resp = net::http(&url, None, None, net::TIMEOUT)?;
            check_blocked(&resp.body)?;
            html::parse_ddg_html(&resp.body)
        }
        _ => {
            let url = format!(
                "https://www.bing.com/search?q={}&count={}",
                util::quote_plus(query),
                limit.max(10)
            );
            let resp = net::http(&url, None, None, net::TIMEOUT)?;
            check_blocked(&resp.body)?;
            let rows = html::parse_bing(&resp.body);
            if rows.is_empty() && resp.body.contains("There are no results for") {
                return Err(FetchError::new("the engine returned an empty result page"));
            }
            rows
        }
    };
    // The same ranking as the searxng path, so both routes sort alike, and the take(limit) comes
    // after it: a documentation row that sat below the cut can still reach the output.
    let kept = accept_draw(query, got)?;
    Ok(util::rank(query, kept).into_iter().take(limit).collect())
}

fn check_blocked(page: &str) -> Result<(), FetchError> {
    if util::blocked(page) {
        return Err(FetchError::new("blocked by bot check"));
    }
    Ok(())
}

/// The whole web chain: SearXNG (unless a category rules the scrapers out), then the fallbacks
/// in that same order. `warn` is where each lost backend is reported.
pub fn web_search<W: FnMut(&str)>(
    query: &str,
    limit: usize,
    category: &str,
    verbose: bool,
    warn: &mut W,
) -> Vec<Row> {
    let mut results = Vec::new();
    match searx_web(query, limit, category, verbose) {
        Ok(rows) => results = rows,
        Err(e) => warn(&format!("backend searxng: {}", e)),
    }
    if results.len() < SEARX_FALLBACK_BELOW && category.is_empty() {
        for name in ["ddg-lite", "ddg-html", "bing"] {
            match scrape(name, query, limit, verbose) {
                Ok(rows) if !rows.is_empty() => {
                    // A scraper draw replaces a thin searxng answer only when it is longer: a
                    // shorter draw is not a better one.
                    if rows.len() > results.len() {
                        results = rows;
                    }
                    break;
                }
                Ok(_) => warn(&format!("backend {}: 0 results", name)),
                Err(e) => warn(&format!("backend {}: {}", name, e)),
            }
        }
    }
    results
}

/// The archive's own UA, for the one host that refuses a browser's.
pub fn archive_get(url: &str, timeout: u64) -> Result<Response, FetchError> {
    net::http_as(url, None, Some("application/json"), timeout, ARCHIVE_UA)
}

/// Kept so the UA constant is exercised: a caller reading this file should find the reason the
/// archive is special without leaving the module.
pub fn archive_ua() -> &'static str {
    ARCHIVE_UA
}

/// The browser UA every other request here sends.
pub fn ua() -> &'static str {
    UA
}

#[cfg(test)]
mod tests {
    use super::*;

    const FIX: &str = r#"{
      "query": "asyncio cancellation",
      "results": [
        {"url": "https://example.org/asyncio", "title": "Asyncio task cancellation",
         "content": "How cancellation propagates.", "engine": "brave", "engines": ["brave", "naver"]},
        {"url": "https://example.net/b", "title": "Second hit", "content": "Other text.",
         "engine": "bing", "engines": ["bing"]},
        {"url": "", "title": "no url, dropped", "content": "x", "engine": "bing", "engines": ["bing"]}
      ],
      "answers": [], "corrections": [], "infoboxes": [], "suggestions": [],
      "unresponsive_engines": [["qwant", "Suspended: access denied"], ["mojeek", "CAPTCHA"]]
    }"#;

    #[test]
    fn searxng_rows_keep_their_engine_provenance_and_the_dead_list() {
        let (rows, dead) = parse_searxng(&serde_json::from_str(FIX).unwrap());
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].title, "Asyncio task cancellation");
        assert_eq!(rows[0].engines, vec!["brave", "naver"]);
        assert_eq!(rows[0].snippet, "How cancellation propagates.");
        assert_eq!(rows[1].engines, vec!["bing"]);
        assert_eq!(dead, vec!["qwant", "mojeek"]);
        assert!(util::related("asyncio cancellation", &rows[..1]));
        assert!(!util::related("deepstream nvstreammux live-source", &rows[..1]));
    }

    #[test]
    fn a_google_redirect_shell_is_unwrapped_or_dropped() {
        let doc: Value = serde_json::from_str(FIX).unwrap();
        let (mut rows, _) = parse_searxng(&doc);
        let real = Row::raw(
            "x",
            "https://www.google.com/url?opi=1&q=https%3A%2F%2Fexample.com%2Freal&uoh=3",
            "",
        );
        let opaque = Row::raw("y", "https://www.google.com/url?opi=1&uoh=3", "");
        rows.push(real);
        rows.push(opaque);
        let fixed: Vec<Row> = rows
            .into_iter()
            .map(|mut r| {
                r.url = net::unwrap_url(&r.url);
                r
            })
            .filter(|r| !r.url.is_empty())
            .collect();
        assert_eq!(fixed[0].url, "https://example.org/asyncio");
        assert_eq!(fixed[2].url, "https://example.com/real");
        assert_eq!(fixed.len(), 3);
    }

    #[test]
    fn the_drift_filter_keeps_only_the_on_topic_row() {
        let rows = vec![
            Row::raw("About Get Help", "https://support.microsoft.com/x", ""),
            Row::raw("nvv4l2decoder drop-frame-interval", "https://example.com/a", ""),
            Row::raw("Interval to drop frames", "https://docs.nvidia.com/b", "drop-frame-interval=5"),
            Row::raw("unrelated", "https://example.org/c", "nvv4l2decoder note"),
        ];
        let got = util::prefer_on_topic("nvv4l2decoder drop-frame-interval", rows.clone(), 8);
        assert_eq!(got.len(), 1);
        assert_eq!(got[0].url, "https://example.com/a");
        // nothing on topic: hand the rows back and let related() judge the set
        let nothing = vec![rows[0].clone(), rows[3].clone()];
        assert_eq!(util::prefer_on_topic("nvv4l2decoder drop-frame-interval", nothing, 8).len(), 2);
        // a duplicate url is one row
        let mut dup = rows.clone();
        dup.push(rows[1].clone());
        assert_eq!(util::dedupe(dup).len(), rows.len());
    }

    #[test]
    fn a_retry_merges_both_draws_and_keeps_the_first_order() {
        let first = vec![
            Row::raw("a", "https://a.example/1", "").with_engines(vec!["brave".into()]),
            Row::raw("b", "https://b.example/2", ""),
        ];
        let second = vec![
            Row::raw("c", "https://c.example/3", ""),
            Row::raw("b again", "https://b.example/2", ""),
            Row::raw("d", "https://d.example/4", ""),
        ];
        let merged = merge_draws(first, second);
        let urls: Vec<String> = merged.iter().map(|r| r.url.clone()).collect();
        assert_eq!(
            urls,
            vec!["https://a.example/1", "https://b.example/2", "https://c.example/3", "https://d.example/4"]
        );
        // the first draw's row is the one that stays, provenance and all
        assert_eq!(merged[1].title, "b");
        assert_eq!(merged[0].engines, vec!["brave"]);
        // ranking after the merge is stable, so a draw with no evidence keeps this order
        let ranked = util::rank("nothing here", merged);
        let ranked_urls: Vec<String> = ranked.iter().map(|r| r.url.clone()).collect();
        assert_eq!(ranked_urls, urls);
    }

    #[test]
    fn a_scraped_draw_is_accepted_row_by_row() {
        // a bing page: the answer at four with noise above and below it
        let page = vec![
            Row::raw("Sign in", "https://example.org/login", ""),
            Row::raw("Rate limits", "https://example.net/notes", "unrelated text"),
            Row::raw("OpenCV: Reading and writing images", "https://example.com/a", ""),
            Row::raw("C++ interface", "https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html", "read a frame here"),
            Row::raw("Cookie policy", "https://example.org/cookies", ""),
        ];
        let kept = accept_draw("opencv read video frame", page).expect("a mixed draw must survive");
        let urls: Vec<&str> = kept.iter().map(|r| r.url.as_str()).collect();
        // the row whose only match is in the snippet survives too
        assert_eq!(urls.len(), 2);
        assert_eq!(urls[0], "https://example.com/a");
        assert!(urls[1].contains("docs.opencv.org"));
        // an entirely unrelated page is still refused, so the chain moves on
        let junk = vec![Row::raw("Sign in", "https://example.org/login", "")];
        assert!(accept_draw("opencv read video frame", junk).is_err());
        // an empty draw is not "unrelated", it is empty
        assert_eq!(accept_draw("opencv read video frame", Vec::new()).unwrap().len(), 0);
    }
}
