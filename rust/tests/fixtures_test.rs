//! The fixture suite, read from disk - the same payloads `--self-test` compiles in.
//!
//! `src/selftest.rs` embeds these files with `include_str!` because a released binary has no
//! checkout beside it. This file reads them at run time instead, so the two paths cannot agree
//! by accident: a fixture edited into something the embedded copy also rejects would still have
//! to satisfy the assertions here, written as tests with names that say what broke.

use std::fs;
use std::path::PathBuf;

use serde_json::Value;
use webscour::{backends, html, net, row::Row, search, sources, util};

fn fixture(name: &str) -> String {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join(name);
    fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {}", path.display(), e))
}

fn json(name: &str) -> Value {
    serde_json::from_str(&fixture(name)).expect("fixture is valid JSON")
}

#[test]
fn searxng_fixture_yields_two_rows_and_two_dead_engines() {
    let (rows, dead) = backends::parse_searxng(&json("searxng.json"));
    assert_eq!(rows.len(), 2, "the row with no url must be dropped");
    assert_eq!(rows[0].engines, vec!["brave", "naver"]);
    assert_eq!(dead, vec!["qwant", "mojeek"]);
}

#[test]
fn the_fallback_pages_each_parse_to_their_own_shape() {
    let lite = html::parse_ddg_lite(&fixture("ddg_lite.html"));
    assert_eq!(lite.len(), 2);
    assert_eq!(lite[0].url, "https://example.com/a");
    assert_eq!(lite[1].url, "https://example.com/b", "// must become https://");

    let html_page = html::parse_ddg_html(&fixture("ddg_html.html"));
    assert_eq!(html_page.len(), 1);
    assert_eq!(html_page[0].url, "https://example.org/x");
    assert_eq!(html_page[0].snippet, "Snippet text here.");

    let bing = html::parse_bing(&fixture("bing.html"));
    assert_eq!(bing.len(), 2);
    assert_eq!(bing[0].snippet, "Some snippet.");
}

#[test]
fn the_bot_check_page_is_recognised_and_a_result_page_is_not() {
    assert!(util::blocked(&fixture("anomaly.html")));
    assert!(!util::blocked(&fixture("bing.html")));
}

#[test]
fn github_fixtures_keep_repo_and_issue_provenance() {
    let repos = search::parse_github_repos(&json("gh_repos.json"));
    assert_eq!(repos[0].title, "serengil/retinaface");
    assert!(repos[0].snippet.contains("2100 stars"));
    let issues = search::parse_github_issues(&json("gh_issues.json"));
    assert_eq!(issues[0].title, "x/y#12 How to drop frames");
}

#[test]
fn stack_overflow_and_hn_fixtures_parse() {
    assert_eq!(
        search::parse_so(&json("so.json"))[0].url,
        "https://stackoverflow.com/q/1"
    );
    assert_eq!(search::parse_hn(&json("hn.json"))[0].url, "https://example.com/s");
}

#[test]
fn the_two_arxiv_routes_differ_only_in_the_date() {
    let plain = search::parse_arxiv(&fixture("arxiv.xml"));
    assert_eq!(plain[0].url, "http://arxiv.org/abs/1905.00641v1");
    assert!(plain[0].published.is_none(), "the search route has no date");

    let api = sources::parse_arxiv_api(&fixture("arxiv_api.xml"));
    assert_eq!(api[0].published.as_deref(), Some("2017-06-12"));
}

#[test]
fn discourse_fixture_builds_the_topic_url_and_finds_the_blurb() {
    let rows = search::parse_discourse_search(&json("discourse.json"), "https://forums.developer.nvidia.com");
    assert_eq!(rows[0].url, "https://forums.developer.nvidia.com/t/123456");
    assert_eq!(rows[0].snippet, "set live-source to 1");
}

#[test]
fn every_keyless_fixture_carries_the_fact_a_reader_searches_for() {
    let w = sources::parse_wikipedia(&json("wikipedia.json"));
    assert_eq!(w[0].url, "https://en.wikipedia.org/wiki/Transformer_(deep_learning)");
    assert!(w[0].published.is_none());

    let o = sources::parse_openalex(&json("openalex.json"));
    assert!(o[0].snippet.contains("542 citations"));
    assert!(o[0].published.is_none(), "a year is not a date");

    let c = sources::parse_crossref(&json("crossref.json"));
    assert_eq!(c.len(), 1, "the titleless item is dropped");
    assert_eq!(c[0].published.as_deref(), Some("2020-10-01"));

    let e = sources::parse_europepmc(&json("europepmc.json"));
    assert_eq!(e[1].url, "https://pubmed.ncbi.nlm.nih.gov/123/");

    let p = sources::parse_pubmed(&json("pubmed.json"));
    assert_eq!(p[0].published.as_deref(), Some("2026-11-13"));
    assert_eq!(p[1].published.as_deref(), Some("2026-11-01"));

    let py = sources::parse_pypi(&json("pypi.json"));
    assert_eq!(py[0].published.as_deref(), Some("2026-05-14"));

    assert!(sources::parse_npm(&json("npm.json"))[0].snippet.contains("DEPRECATED"));
    assert!(sources::parse_crates(&json("crates.json"))[0].snippet.contains("yanked"));
    assert_eq!(
        sources::parse_devto(&json("devto.json"))[0].published.as_deref(),
        Some("2026-11-12")
    );
    assert!(sources::parse_wayback(&json("wayback.json"))[0]
        .url
        .contains("/20261113195909id_/"));
}

#[test]
fn feeds_keep_the_date_and_drop_the_repeated_outlet() {
    let rss = sources::parse_rss(&fixture("rss.xml"));
    assert_eq!(rss[0].title, "Story one");
    assert_eq!(rss[0].snippet, "Outlet");
    assert_eq!(rss[1].published.as_deref(), Some("2026-01-02"));
    let atom = sources::parse_rss(&fixture("atom.xml"));
    assert_eq!(atom[0].url, "https://ex.com/a");
}

#[test]
fn the_renderer_is_the_numbered_format_with_an_engine_tag() {
    let rows = vec![
        Row::raw("Asyncio task cancellation", "https://example.org/asyncio", "text")
            .with_engines(vec!["brave".into(), "naver".into()]),
        Row::dated("Dated", "https://example.net/d", "s", "2026-11-14"),
    ];
    let out = net::render(&rows, false);
    assert!(out.contains("1. Asyncio task cancellation - https://example.org/asyncio  [brave,naver]\n"));
    assert!(out.contains("2. Dated - https://example.net/d\n   [2026-11-14] s\n"));
    let js = net::render(&rows, true);
    let parsed: Value = serde_json::from_str(&js).unwrap();
    assert_eq!(parsed[0]["engines"][0], "brave");
    assert!(parsed[1]["published"] == "2026-11-14");
    assert!(parsed[0].get("published").is_none());
}

#[test]
fn the_source_table_is_complete_and_the_help_matches_it() {
    let help = sources::sources_help();
    for name in sources::API_SOURCES {
        assert!(sources::fetcher(name).is_some(), "{} has no fetcher", name);
        if name != "arxiv-api" {
            assert!(help.contains(name), "{} is missing from the help", name);
        }
    }
    assert_eq!(sources::FRESH_SOURCES, ["googlenews", "bbc"]);
}
