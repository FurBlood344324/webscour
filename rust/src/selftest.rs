//! `wsc --self-test`: the offline checks over the captured payloads.
//!
//! The fixtures are compiled in with `include_str!` rather than read from `tests/fixtures`.
//! A released binary has no source tree next to it, and a self-test that needs the checkout is
//! a self-test that fails on the machine it is meant to reassure. The same files are what
//! `tests/fixtures_test.rs` reads, so the two paths cannot describe different payloads.

use crate::backends;
use crate::html;
use crate::net;
use crate::row::Row;
use crate::sources;
use crate::util;

pub const FIX_SEARXNG: &str = include_str!("../tests/fixtures/searxng.json");
pub const FIX_DDG_LITE: &str = include_str!("../tests/fixtures/ddg_lite.html");
pub const FIX_DDG_HTML: &str = include_str!("../tests/fixtures/ddg_html.html");
pub const FIX_BING: &str = include_str!("../tests/fixtures/bing.html");
pub const FIX_ANOMALY: &str = include_str!("../tests/fixtures/anomaly.html");
pub const FIX_GH_REPOS: &str = include_str!("../tests/fixtures/gh_repos.json");
pub const FIX_GH_ISSUES: &str = include_str!("../tests/fixtures/gh_issues.json");
pub const FIX_SO: &str = include_str!("../tests/fixtures/so.json");
pub const FIX_HN: &str = include_str!("../tests/fixtures/hn.json");
pub const FIX_ARXIV: &str = include_str!("../tests/fixtures/arxiv.xml");
pub const FIX_ARXIV_API: &str = include_str!("../tests/fixtures/arxiv_api.xml");
pub const FIX_DSC: &str = include_str!("../tests/fixtures/discourse.json");
pub const FIX_WIKIPEDIA: &str = include_str!("../tests/fixtures/wikipedia.json");
pub const FIX_OPENALEX: &str = include_str!("../tests/fixtures/openalex.json");
pub const FIX_CROSSREF: &str = include_str!("../tests/fixtures/crossref.json");
pub const FIX_EUROPEPMC: &str = include_str!("../tests/fixtures/europepmc.json");
pub const FIX_PUBMED: &str = include_str!("../tests/fixtures/pubmed.json");
pub const FIX_PYPI: &str = include_str!("../tests/fixtures/pypi.json");
pub const FIX_NPM: &str = include_str!("../tests/fixtures/npm.json");
pub const FIX_CRATES: &str = include_str!("../tests/fixtures/crates.json");
pub const FIX_DEVTO: &str = include_str!("../tests/fixtures/devto.json");
pub const FIX_WAYBACK: &str = include_str!("../tests/fixtures/wayback.json");
pub const FIX_RSS: &str = include_str!("../tests/fixtures/rss.xml");
pub const FIX_ATOM: &str = include_str!("../tests/fixtures/atom.xml");

fn json(text: &str) -> serde_json::Value {
    serde_json::from_str(text).expect("fixture is valid JSON")
}

/// A check either passes or names the assertion that failed.
type Check = (&'static str, fn() -> Result<(), String>);

fn want(condition: bool, detail: impl FnOnce() -> String) -> Result<(), String> {
    if condition {
        Ok(())
    } else {
        Err(detail())
    }
}

fn checks() -> Vec<Check> {
    vec![
        ("searxng parse", searxng),
        ("searxng google unwrap", google_unwrap),
        ("drift filter", drift_filter),
        ("ddg lite", ddg_lite),
        ("ddg html", ddg_html),
        ("bing", bing),
        ("bot-check detection", bot_check),
        ("github repos", gh_repos),
        ("github issues", gh_issues),
        ("stack overflow", so),
        ("hacker news", hn),
        ("arxiv atom", arxiv),
        ("discourse search", discourse_search),
        ("wikipedia", wikipedia),
        ("openalex", openalex),
        ("crossref", crossref),
        ("arxiv api date", arxiv_api),
        ("europepmc", europepmc),
        ("pubmed", pubmed),
        ("pypi", pypi),
        ("npm", npm),
        ("crates", crates),
        ("devto", devto),
        ("wayback", wayback),
        ("rss dates", rss),
        ("rss outlet dedupe", rss_outlet),
        ("atom feed", atom_feed),
        ("broken xml is empty", broken_xml),
        ("source table", source_table),
        ("pace guard", pace_guard),
        ("engine tag", engine_tag),
        ("row format", row_format),
        ("json row shape", row_json),
        ("month-only dates", dates),
        ("fresh merge", fresh_merge),
    ]
}

/// Run every check; the caller prints. The boolean is "all passed".
pub fn run(out: &mut impl std::io::Write) -> bool {
    let mut passed = 0;
    let all = checks();
    for (name, f) in &all {
        match f() {
            Ok(()) => {
                passed += 1;
                let _ = writeln!(out, "PASS {}", name);
            }
            Err(why) => {
                let _ = writeln!(out, "FAIL {} :: {}", name, why);
            }
        }
    }
    let _ = writeln!(out, "SUMMARY pass={} fail={}", passed, all.len() - passed);
    passed == all.len()
}

// ------------------------------------------------------------------ the checks

fn searxng() -> Result<(), String> {
    let (rows, dead) = backends::parse_searxng(&json(FIX_SEARXNG));
    want(rows.len() == 2, || format!("{} rows", rows.len()))?;
    want(rows[0].title == "Asyncio task cancellation", || rows[0].title.clone())?;
    want(rows[0].engines == vec!["brave", "naver"], || format!("{:?}", rows[0].engines))?;
    want(rows[0].snippet == "How cancellation propagates.", || rows[0].snippet.clone())?;
    want(rows[1].engines == vec!["bing"], || format!("{:?}", rows[1].engines))?;
    want(dead == vec!["qwant", "mojeek"], || format!("{:?}", dead))?;
    want(util::related("asyncio cancellation", &rows[..1]), || "not related".into())?;
    want(!util::related("deepstream nvstreammux live-source", &rows[..1]), || {
        "unrelated query passed".into()
    })
}

fn google_unwrap() -> Result<(), String> {
    let (mut rows, _) = backends::parse_searxng(&json(FIX_SEARXNG));
    rows.push(Row::raw(
        "x",
        "https://www.google.com/url?opi=1&q=https%3A%2F%2Fexample.com%2Freal&uoh=3",
        "",
    ));
    for r in &mut rows {
        r.url = net::unwrap_url(&r.url);
    }
    want(rows[0].url == "https://example.org/asyncio", || rows[0].url.clone())?;
    want(rows[2].url == "https://example.com/real", || rows[2].url.clone())
}

fn drift_filter() -> Result<(), String> {
    let rows = vec![
        Row::raw("About Get Help", "https://support.microsoft.com/x", ""),
        Row::raw("nvv4l2decoder drop-frame-interval", "https://example.com/a", ""),
        Row::raw("Interval to drop frames", "https://docs.nvidia.com/b", "drop-frame-interval=5"),
        Row::raw("unrelated", "https://example.org/c", "nvv4l2decoder note"),
    ];
    let got = util::prefer_on_topic("nvv4l2decoder drop-frame-interval", rows.clone(), 8);
    want(got.len() == 1 && got[0].url == "https://example.com/a", || {
        format!("{:?}", got.iter().map(|r| &r.url).collect::<Vec<_>>())
    })?;
    let mut dup = rows.clone();
    dup.push(rows[1].clone());
    want(util::dedupe(dup).len() == rows.len(), || "dedupe lost or kept a row".into())?;
    let nothing = vec![rows[0].clone(), rows[3].clone()];
    want(
        util::prefer_on_topic("nvv4l2decoder drop-frame-interval", nothing, 8).len() == 2,
        || "an all-off-topic set was pruned to nothing".into(),
    )
}

fn ddg_lite() -> Result<(), String> {
    let r = html::parse_ddg_lite(FIX_DDG_LITE);
    want(r.len() == 2, || format!("{} rows", r.len()))?;
    want(r[0].title == "RetinaFace detector", || r[0].title.clone())?;
    want(r[0].url == "https://example.com/a", || r[0].url.clone())?;
    want(r[0].snippet.contains("single-stage"), || r[0].snippet.clone())?;
    want(r[1].url == "https://example.com/b", || r[1].url.clone())
}

fn ddg_html() -> Result<(), String> {
    let r = html::parse_ddg_html(FIX_DDG_HTML);
    want(r.len() == 1, || format!("{} rows", r.len()))?;
    want(r[0].title == "Example title", || r[0].title.clone())?;
    want(r[0].url == "https://example.org/x", || r[0].url.clone())?;
    want(r[0].snippet.contains("Snippet text here."), || r[0].snippet.clone())
}

fn bing() -> Result<(), String> {
    let r = html::parse_bing(FIX_BING);
    want(r.len() == 2, || format!("{} rows", r.len()))?;
    want(r[0].title == "Bing hit", || r[0].title.clone())?;
    want(r[0].url == "https://example.net/b", || r[0].url.clone())?;
    want(r[0].snippet.contains("Some snippet."), || r[0].snippet.clone())
}

fn bot_check() -> Result<(), String> {
    want(util::blocked(FIX_ANOMALY), || "bot-check page not detected".into())?;
    want(!util::blocked(FIX_BING), || "real result page flagged as blocked".into())
}

fn gh_repos() -> Result<(), String> {
    let r = crate::search::parse_github_repos(&json(FIX_GH_REPOS));
    want(r[0].url == "https://github.com/serengil/retinaface", || r[0].url.clone())?;
    want(
        r[0].snippet.contains("Python") && r[0].snippet.contains("2100 stars"),
        || r[0].snippet.clone(),
    )
}

fn gh_issues() -> Result<(), String> {
    let r = crate::search::parse_github_issues(&json(FIX_GH_ISSUES));
    want(r[0].title == "x/y#12 How to drop frames", || r[0].title.clone())
}

fn so() -> Result<(), String> {
    let r = crate::search::parse_so(&json(FIX_SO));
    want(r[0].url == "https://stackoverflow.com/q/1", || r[0].url.clone())?;
    want(r[0].snippet.contains("answered"), || r[0].snippet.clone())
}

fn hn() -> Result<(), String> {
    let r = crate::search::parse_hn(&json(FIX_HN));
    want(r[0].url == "https://example.com/s", || r[0].url.clone())
}

fn arxiv() -> Result<(), String> {
    let r = crate::search::parse_arxiv(FIX_ARXIV);
    want(r[0].url == "http://arxiv.org/abs/1905.00641v1", || r[0].url.clone())?;
    want(r[0].title.starts_with("RetinaFace"), || r[0].title.clone())
}

fn discourse_search() -> Result<(), String> {
    let r = crate::search::parse_discourse_search(
        &json(FIX_DSC),
        "https://forums.developer.nvidia.com",
    );
    want(
        r[0].url == "https://forums.developer.nvidia.com/t/123456",
        || r[0].url.clone(),
    )?;
    want(r[0].snippet == "set live-source to 1", || r[0].snippet.clone())
}

fn wikipedia() -> Result<(), String> {
    let r = sources::parse_wikipedia(&json(FIX_WIKIPEDIA));
    want(
        r[0].url == "https://en.wikipedia.org/wiki/Transformer_(deep_learning)",
        || r[0].url.clone(),
    )?;
    want(!r[0].snippet.contains("span"), || r[0].snippet.clone())?;
    want(r[0].published.is_none(), || "a wiki article grew a publication date".into())
}

fn openalex() -> Result<(), String> {
    let r = sources::parse_openalex(&json(FIX_OPENALEX));
    want(r[0].url == "https://doi.org/10.1016/j.cell.2015.12.041", || r[0].url.clone())?;
    want(r[0].snippet.contains("542 citations"), || r[0].snippet.clone())?;
    want(r[0].published.is_none(), || "a year was passed off as a date".into())
}

fn crossref() -> Result<(), String> {
    let r = sources::parse_crossref(&json(FIX_CROSSREF));
    want(r.len() == 1, || format!("{} rows (a titleless item survived)", r.len()))?;
    want(r[0].published.as_deref() == Some("2020-10-01"), || format!("{:?}", r[0].published))
}

fn arxiv_api() -> Result<(), String> {
    let r = sources::parse_arxiv_api(FIX_ARXIV_API);
    want(r[0].published.as_deref() == Some("2017-06-12"), || format!("{:?}", r[0].published))?;
    want(!r[0].snippet.contains('\n'), || "the summary kept a newline".into())
}

fn europepmc() -> Result<(), String> {
    let r = sources::parse_europepmc(&json(FIX_EUROPEPMC));
    want(r[0].url == "https://doi.org/10.1/a", || r[0].url.clone())?;
    want(r[1].url == "https://pubmed.ncbi.nlm.nih.gov/123/", || r[1].url.clone())
}

fn pubmed() -> Result<(), String> {
    let r = sources::parse_pubmed(&json(FIX_PUBMED));
    want(r[0].title == "Second" && r[1].title == "First", || format!("{:?}", r[0].title))?;
    want(r[0].published.as_deref() == Some("2026-11-13"), || format!("{:?}", r[0].published))?;
    want(r[1].published.as_deref() == Some("2026-11-01"), || format!("{:?}", r[1].published))
}

fn pypi() -> Result<(), String> {
    let r = sources::parse_pypi(&json(FIX_PYPI));
    want(r[0].title == "requests", || r[0].title.clone())?;
    want(r[0].published.as_deref() == Some("2026-05-14"), || format!("{:?}", r[0].published))
}

fn npm() -> Result<(), String> {
    let r = sources::parse_npm(&json(FIX_NPM));
    want(r[0].snippet.contains("DEPRECATED"), || r[0].snippet.clone())?;
    want(r[0].url == "https://github.com/x/old-thing", || r[0].url.clone())
}

fn crates() -> Result<(), String> {
    let r = sources::parse_crates(&json(FIX_CRATES));
    want(r[0].snippet.contains("downloads (90d)"), || r[0].snippet.clone())?;
    want(r[0].snippet.contains("yanked"), || r[0].snippet.clone())?;
    want(r[0].url == "https://github.com/serde-rs/serde", || r[0].url.clone())
}

fn devto() -> Result<(), String> {
    let r = sources::parse_devto(&json(FIX_DEVTO));
    want(r[0].published.as_deref() == Some("2026-11-12"), || format!("{:?}", r[0].published))?;
    want(r[0].snippet.contains("4 min read"), || r[0].snippet.clone())
}

fn wayback() -> Result<(), String> {
    let r = sources::parse_wayback(&json(FIX_WAYBACK));
    want(r[0].url.contains("/20261113195909id_/"), || r[0].url.clone())?;
    want(r[0].published.as_deref() == Some("2026-11-13"), || format!("{:?}", r[0].published))
}

fn rss() -> Result<(), String> {
    let r = sources::parse_rss(FIX_RSS);
    want(
        r.len() == 2
            && r[0].published.as_deref() == Some("2026-11-14")
            && r[1].published.as_deref() == Some("2026-01-02"),
        || format!("{:?}", r.iter().map(|x| x.published.clone()).collect::<Vec<_>>()),
    )
}

fn rss_outlet() -> Result<(), String> {
    let r = sources::parse_rss(FIX_RSS);
    want(r[0].title == "Story one", || r[0].title.clone())?;
    want(r[0].snippet == "Outlet", || r[0].snippet.clone())?;
    want(r[0].snippet.matches("Outlet").count() == 1, || r[0].snippet.clone())
}

fn atom_feed() -> Result<(), String> {
    let r = sources::parse_rss(FIX_ATOM);
    want(r[0].url == "https://ex.com/a", || r[0].url.clone())?;
    want(r[0].published.as_deref() == Some("2026-03-04"), || format!("{:?}", r[0].published))
}

fn broken_xml() -> Result<(), String> {
    want(sources::parse_rss("<rss><channel><item>").is_empty(), || {
        "broken XML produced rows".into()
    })
}

fn source_table() -> Result<(), String> {
    let help = sources::sources_help();
    for name in sources::API_SOURCES {
        want(sources::fetcher(name).is_some(), || format!("{} has no fetcher", name))?;
        if name != "arxiv-api" {
            want(help.contains(name), || format!("{} missing from the help", name))?;
        }
    }
    Ok(())
}

fn pace_guard() -> Result<(), String> {
    want(util::pace_delay(0.0, 100.0) == 0.0, || "a stale stamp slept".into())?;
    want((util::pace_delay(99.5, 100.0) - 0.5).abs() < 1e-6, || "half a second was wrong".into())?;
    want(util::pace_delay(100.0, 100.0) == util::PACE_SECONDS, || "zero gap did not pace".into())
}

fn engine_tag() -> Result<(), String> {
    let tag = net::engine_tag(&["brave".into(), "naver".into()]);
    want(tag == "  [brave,naver]", || tag.clone())?;
    want(net::engine_tag(&[]).is_empty(), || "an empty engine list printed a tag".into())
}

fn row_format() -> Result<(), String> {
    let line = net::format_row(
        1,
        &Row::raw("t", "u", "s").with_engines(vec!["brave".into()]),
    );
    want(line == "1. t - u  [brave]\n   s\n", || line.escape_debug().to_string())?;
    let dated = net::format_row(2, &Row::dated("t", "u", "s", "2026-11-14"));
    want(dated == "2. t - u\n   [2026-11-14] s\n", || dated.escape_debug().to_string())
}

fn row_json() -> Result<(), String> {
    let v = Row::raw("t", "u", "s").to_json();
    want(v.get("engines").is_some(), || "the engines key is missing".into())?;
    want(v.get("published").is_none(), || "an empty date became a key".into())
}

fn fresh_merge() -> Result<(), String> {
    let rows = vec![
        Row::dated("old", "https://a/1", "", "2026-11-01"),
        Row::dated("new", "https://b/2", "", "2026-11-14"),
        Row::raw("undated", "https://c/3", ""),
    ];
    let got = sources::merge_fresh(rows.clone(), 5, "");
    want(
        got.iter().map(|r| r.title.as_str()).collect::<Vec<_>>() == vec!["new", "old"],
        || format!("{:?}", got.iter().map(|r| &r.title).collect::<Vec<_>>()),
    )?;
    want(sources::merge_fresh(rows, 5, "2026-11-11").len() == 1, || {
        "the since floor let an older row through".into()
    })
}

fn dates() -> Result<(), String> {
    want(sources::iso_date("2026-11-10T21:50:21Z") == "2026-11-10", || "iso failed".into())?;
    want(sources::iso_date("2026/11/10") == "2026-11-10", || "slash date failed".into())?;
    want(sources::rfc822_date("Sat, 14 Nov 2026 19:43:32 GMT") == "2026-11-14", || {
        "rfc822 failed".into()
    })
}
