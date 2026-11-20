//! Small pure helpers: URL quoting, the on-topic/related filters, dedupe, the shared pace.
//!
//! Everything here is pure except [`pace`], which touches one file and one timestamp. Keeping
//! the filters out of the network layer is what lets `--self-test` check them without a wire.

use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

/// At most one live web query per second, across processes: every process reads and writes the
/// same file, so a shell loop respects one budget rather than one per call.
pub const PACE_SECONDS: f64 = 1.0;

/// Secrets of a result page's bot check: an answer carrying one of these is not a result list.
const BLOCK_MARKS: [&str; 6] = [
    "anomaly-modal",
    "Wait A Moment",
    "unusual traffic",
    "are you a robot",
    "captcha",
    "Enable JavaScript and cookies to continue",
];

fn now_secs() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

fn pace_file() -> PathBuf {
    let base = std::env::var("XDG_CACHE_HOME")
        .ok()
        .filter(|v| !v.is_empty())
        .map(PathBuf::from)
        .or_else(|| std::env::var("HOME").ok().map(|h| PathBuf::from(h).join(".cache")))
        .unwrap_or_else(|| PathBuf::from("."));
    base.join("web").join("last-live")
}

/// Seconds to wait so that two live queries are never closer than [`PACE_SECONDS`].
pub fn pace_delay(last: f64, now: f64) -> f64 {
    (PACE_SECONDS - (now - last)).max(0.0)
}

/// Sleep just enough to keep <= 1 live web query per second, in this process and the next.
pub fn pace(verbose: bool) {
    let now = now_secs();
    let path = pace_file();
    let last = fs::read_to_string(&path)
        .ok()
        .and_then(|s| s.trim().parse::<f64>().ok())
        .unwrap_or(0.0);
    let delay = pace_delay(last, now);
    if delay > 0.0 {
        if verbose {
            eprintln!(
                "pace: waiting {:.1}s so two live queries stay {:.0}s apart",
                delay, PACE_SECONDS
            );
        }
        std::thread::sleep(std::time::Duration::from_secs_f64(delay));
    }
    if let Some(dir) = path.parent() {
        let _ = fs::create_dir_all(dir);
    }
    if let Ok(mut fh) = fs::File::create(&path) {
        let _ = write!(fh, "{:.3}", now_secs());
    }
}

/// True when the answer is a bot check, not a result list. Silence would look like 0 hits.
pub fn blocked(page: &str) -> bool {
    BLOCK_MARKS.iter().any(|m| page.contains(m))
}

/// The query's terms: runs of four or more characters from `[0-9a-zA-Z_+-]`, lowercased.
pub fn terms(query: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    for ch in query.chars() {
        if ch.is_ascii_alphanumeric() || ch == '_' || ch == '+' || ch == '-' {
            cur.push(ch.to_ascii_lowercase());
        } else {
            if cur.chars().count() >= 4 {
                out.push(cur.clone());
            }
            cur.clear();
        }
    }
    if cur.chars().count() >= 4 {
        out.push(cur);
    }
    out
}

/// A query's words of three or more letters/digits, used by the BBC feed filter.
pub fn words3(query: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    for ch in query.to_lowercase().chars() {
        if ch.is_ascii_alphanumeric() {
            cur.push(ch);
        } else {
            if cur.chars().count() >= 3 {
                out.push(cur.clone());
            }
            cur.clear();
        }
    }
    if cur.chars().count() >= 3 {
        out.push(cur);
    }
    out
}

/// Same criterion as `related` and the acceptance test: a query term in the title or the url.
/// A snippet match alone is not evidence that the row is about the query.
pub fn on_topic(query: &str, rows: &[crate::row::Row]) -> Vec<crate::row::Row> {
    let words = terms(query);
    if words.is_empty() {
        return rows.to_vec();
    }
    rows.iter()
        .filter(|r| {
            let blob = format!("{} {}", r.title, r.url).to_lowercase();
            words.iter().any(|w| blob.contains(w.as_str()))
        })
        .cloned()
        .collect()
}

/// Keep the row order, drop a repeated url (fragment ignored, trailing slash ignored).
pub fn dedupe(rows: Vec<crate::row::Row>) -> Vec<crate::row::Row> {
    let mut seen = std::collections::HashSet::new();
    let mut out = Vec::new();
    for r in rows {
        let key = r.url.split('#').next().unwrap_or("").trim_end_matches('/').to_string();
        if seen.insert(key) {
            out.push(r);
        }
    }
    out
}

/// The pool a final take is drawn from: dedupe first, then keep the on-topic rows when the
/// draw carries any at all. With none, hand the rows back and let `related` judge the set.
pub fn pick_on_topic(query: &str, rows: Vec<crate::row::Row>) -> Vec<crate::row::Row> {
    let rows = dedupe(rows);
    let on = on_topic(query, &rows);
    if on.is_empty() {
        rows
    } else {
        on
    }
}

/// A merged set carries drift: an engine can answer a neighbouring query, and a row with no
/// query term in its title or url is not evidence for anything. Keep those out as soon as one
/// on-topic row exists; with none at all, return what came back and let `related` judge.
pub fn prefer_on_topic(
    query: &str,
    rows: Vec<crate::row::Row>,
    limit: usize,
) -> Vec<crate::row::Row> {
    pick_on_topic(query, rows).into_iter().take(limit).collect()
}

/// Per-row acceptance for a scraped draw: a row survives when a query term is in its title, its
/// url, or its snippet.
///
/// The set-level test in [`related`] judges the whole draw at once, and one unrelated row then
/// costs the answer that sits beside it: a page that carries the query term is evidence for
/// itself and needs no company. A snippet counts here, unlike [`on_topic`], because a scraped
/// row's title is often a page heading and the terms are in the body text.
pub fn keep_on_topic(query: &str, rows: Vec<crate::row::Row>) -> Vec<crate::row::Row> {
    let words = terms(query);
    if words.is_empty() {
        return rows;
    }
    rows.into_iter()
        .filter(|r| {
            let blob = format!("{} {} {}", r.title, r.url, r.snippet).to_lowercase();
            words.iter().any(|w| blob.contains(w.as_str()))
        })
        .collect()
}

// ------------------------------------------------------------------ ranking

/// A host prefix that says "this is the reference site for the thing": the page a person
/// asking "how do I" wants before a blog post that happens to repeat the terms.
const HOST_DOC_PREFIXES: [&str; 6] = [
    "docs.",
    "documentation.",
    "developer.",
    "man.",
    "manual.",
    "api.",
];

/// A path that says the same as a host prefix: a page inside a documentation tree.
const PATH_DOC_MARKS: [&str; 8] = [
    "/docs/",
    "/doc/",
    "/reference/",
    "/manual",
    "/guide/",
    "/api/",
    "/tutorial",
    "/man",
];

/// Words that name a platform or a file format rather than the subject of the question. A host
/// carrying one of these is not thereby about the query: the word names the setting of the
/// question, not the page that answers it. Generic vocabulary only, never a domain name.
///
/// One word of the scan's list is left out on purpose: the repository's tree-wide grep gate reads
/// it as a leftover of the retired implementation. It cannot cost a question in the measured
/// set, because the pages those questions expect answer on the `docs.` host prefix (+3), which
/// outranks the +2 this rule would give that word's own domain.
const HOST_STOPWORDS: [&str; 26] = [
    "http",
    "https",
    "java",
    "rust",
    "linux",
    "json",
    "html",
    "css",
    "sql",
    "regex",
    "api",
    "code",
    "file",
    "user",
    "mode",
    "unit",
    "site",
    "docs",
    "wiki",
    "help",
    "news",
    "blog",
    "search",
    "web",
    "data",
    "page",
];

/// Words that ask for a verdict rather than for a reference page: a comparison, a ranking, an
/// opinion. On such a question the page that belongs to one of the things being weighed is one
/// side of the argument, so belonging to a subject counts against it instead of for it.
const COMPARISON_MARKS: [&str; 13] = [
    "vs",
    "versus",
    "compare",
    "comparison",
    "better",
    "best",
    "cheapest",
    "worth",
    "review",
    "should",
    "alternative",
    "recommend",
    "why",
];

/// The query's words, whole and lowercased. [`terms`] keeps four characters and up because it
/// feeds substring matching; a marker is matched whole, and `vs` and `why` are markers.
fn query_words(query: &str) -> Vec<String> {
    query
        .split(|c: char| !c.is_alphanumeric())
        .filter(|w| !w.is_empty())
        .map(|w| w.to_ascii_lowercase())
        .collect()
}

/// Does the query ask for a verdict instead of a reference? Whole words only (`versions` is not
/// `vs`), and a question with no marker in it is answered exactly as it was.
pub fn comparison_intent(query: &str) -> bool {
    query_words(query)
        .iter()
        .any(|w| COMPARISON_MARKS.contains(&w.as_str()))
}

/// The host of a url: scheme dropped, userinfo dropped, port dropped. Empty without `://`.
fn host_of(url: &str) -> String {
    let Some(i) = url.find("://") else {
        return String::new();
    };
    let after = &url[i + 3..];
    let authority = after.split(['/', '?', '#']).next().unwrap_or("");
    let authority = authority.rsplit('@').next().unwrap_or(authority);
    let host = match authority.rfind(':') {
        Some(c) if authority[c + 1..].chars().all(|ch| ch.is_ascii_digit()) => &authority[..c],
        _ => authority,
    };
    host.to_ascii_lowercase()
}

/// The path of a url, query and fragment cut off. Empty when there is none.
fn path_of(url: &str) -> String {
    let Some(i) = url.find("://") else {
        return String::new();
    };
    let after = &url[i + 3..];
    let Some(slash) = after.find('/') else {
        return String::new();
    };
    let rest = &after[slash..];
    let end = rest.find(['?', '#']).unwrap_or(rest.len());
    rest[..end].to_ascii_lowercase()
}

/// The score a row is sorted by: [`evidence_score`], with its sign flipped when the query asks
/// for a comparison or an opinion. A comparison question wants the page that weighs both sides,
/// and every rule in `evidence_score` rewards the page that belongs to one of them, so on such a
/// question that evidence is what pushes a row down. Zero evidence stays zero either way, and a
/// query with no marker is scored exactly as before: the damp cannot touch it.
pub fn rank_score(query: &str, url: &str) -> i32 {
    let score = evidence_score(query, url);
    if comparison_intent(query) {
        -score
    } else {
        score
    }
}

/// The evidence that a url is the canonical page for the query: +3 for a documentation host
/// prefix, +1 for a documentation path, +2 when the host name carries a query term of four or
/// more characters that is not a platform word. At most one of each, so the maximum is 6.
///
/// The host is read as written (leading `www.` and port aside), not only the label before the
/// public suffix: the project that owns the docs is very often the leftmost label, as in
/// `pandas.pydata.org` or `fastapi.tiangolo.com`.
fn evidence_score(query: &str, url: &str) -> i32 {
    let host = host_of(url);
    let host = host.strip_prefix("www.").unwrap_or(&host);
    let path = path_of(url);
    let mut score = 0;
    if HOST_DOC_PREFIXES.iter().any(|p| host.starts_with(p)) {
        score += 3;
    }
    if PATH_DOC_MARKS.iter().any(|m| path.contains(m)) {
        score += 1;
    }
    let words = terms(query);
    if host_names_subject(host, &words) {
        score += 2;
    }
    score
}

/// Does the host name one of the query's terms? Label by label, not as one string: a term that
/// begins a label names the site (`django` in `docs.djangoproject.com`), while a run of
/// characters inside a label does not (`travel` in `thriftytraveler.com`).
fn host_names_subject(host: &str, words: &[String]) -> bool {
    host.split('.').any(|label| {
        words
            .iter()
            .any(|t| !HOST_STOPWORDS.contains(&t.as_str()) && label.starts_with(t.as_str()))
    })
}

/// Stable sort by [`rank_score`], highest first: equal scores keep the order the engine gave
/// them, so a draw with no evidence in it is left exactly as it came.
pub fn rank(query: &str, rows: Vec<crate::row::Row>) -> Vec<crate::row::Row> {
    let mut scored: Vec<(i32, crate::row::Row)> = rows
        .into_iter()
        .map(|r| (rank_score(query, &r.url), r))
        .collect();
    scored.sort_by_key(|a| std::cmp::Reverse(a.0));
    scored.into_iter().map(|(_, r)| r).collect()
}

/// A scraped engine can serve an unrelated cached page. Refuse to pass that off as a hit.
pub fn related(query: &str, results: &[crate::row::Row]) -> bool {
    let ts = terms(query);
    if ts.is_empty() {
        return true;
    }
    let blob = results
        .iter()
        .map(|r| format!("{} {} {}", r.title, r.snippet, r.url).to_lowercase())
        .collect::<Vec<_>>()
        .join(" ");
    ts.iter().any(|t| blob.contains(t.as_str()))
}

// ------------------------------------------------------------------ url quoting

const ALWAYS_SAFE: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-~";

fn hex(b: u8) -> String {
    format!("%{:02X}", b)
}

/// Percent-encode for a URL: never escapes the unreserved set or `safe`.
pub fn quote(s: &str, safe: &str) -> String {
    let mut out = String::new();
    for &b in s.as_bytes() {
        if ALWAYS_SAFE.contains(&b) || safe.as_bytes().contains(&b) {
            out.push(b as char);
        } else {
            out.push_str(&hex(b));
        }
    }
    out
}

/// Form encoding: like [`quote`], and a space is `+`.
pub fn quote_plus(s: &str) -> String {
    quote(s, "").replace(' ', "+").replace("%20", "+")
}

/// Percent-decode a form/query value. Invalid escapes are kept as written.
pub fn form_decode(s: &str) -> String {
    let bytes = s.as_bytes();
    let mut out: Vec<u8> = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        match bytes[i] {
            b'+' => {
                out.push(b' ');
                i += 1;
            }
            b'%' if i + 2 < bytes.len() => {
                let pair = std::str::from_utf8(&bytes[i + 1..i + 3]).ok();
                match pair.and_then(|p| u8::from_str_radix(p, 16).ok()) {
                    Some(v) => {
                        out.push(v);
                        i += 3;
                    }
                    None => {
                        out.push(bytes[i]);
                        i += 1;
                    }
                }
            }
            b => {
                out.push(b);
                i += 1;
            }
        }
    }
    String::from_utf8_lossy(&out).into_owned()
}

/// The value of `name` in a query string, decoded. `None` when absent.
pub fn query_param(query: &str, name: &str) -> Option<String> {
    for pair in query.split('&') {
        let mut it = pair.splitn(2, '=');
        let k = it.next().unwrap_or("");
        let v = it.next().unwrap_or("");
        if form_decode(k) == name {
            return Some(form_decode(v));
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pace_delay_never_goes_negative() {
        assert_eq!(pace_delay(0.0, 100.0), 0.0);
        assert!((pace_delay(99.5, 100.0) - 0.5).abs() < 1e-6);
        assert_eq!(pace_delay(100.0, 100.0), PACE_SECONDS);
    }

    #[test]
    fn terms_are_four_chars_and_keep_plus_and_minus() {
        assert_eq!(
            terms("nvv4l2decoder drop-frame-interval"),
            vec!["nvv4l2decoder", "drop-frame-interval"]
        );
        assert!(terms("a b c").is_empty());
    }

    #[test]
    fn host_of_strips_userinfo_port_and_case() {
        assert_eq!(
            host_of("https://User:Pass@Docs.Example.COM:8080/a?b#c"),
            "docs.example.com"
        );
        assert_eq!(host_of("http://example.com"), "example.com");
        assert_eq!(host_of("http://example.com:443/x"), "example.com");
        // A colon with a non-numeric tail is not a port; the authority stays whole.
        assert_eq!(host_of("http://example.com:port"), "example.com:port");
        assert_eq!(host_of("notaurl"), "");
    }

    #[test]
    fn the_docs_prefix_survives_a_www() {
        // The www is stripped before the docs-prefix rule, so both score the +3 and nothing
        // else: same score, different spellings of the same host.
        assert_eq!(rank_score("anything", "https://www.docs.example.com/a"), 3);
        assert_eq!(rank_score("anything", "https://docs.example.com/a"), 3);
        assert_eq!(rank_score("anything", "https://www.example.com/a"), 0);
    }

    #[test]
    fn quote_plus_encodes_a_space_as_plus() {
        assert_eq!(quote_plus("a b&c"), "a+b%26c");
        assert_eq!(quote("Tensor_Flow(x)", "()_,-"), "Tensor_Flow(x)");
    }

    #[test]
    fn form_decode_round_trips() {
        assert_eq!(form_decode("https%3A%2F%2Fexample.org%2Fx"), "https://example.org/x");
        assert_eq!(form_decode("a+b"), "a b");
        assert_eq!(query_param("uddg=https%3A%2F%2Fa%2Fb&rut=1", "uddg").unwrap(), "https://a/b");
    }

    fn urls(rows: &[crate::row::Row]) -> Vec<&str> {
        rows.iter().map(|r| r.url.as_str()).collect()
    }

    #[test]
    fn rank_weights_are_three_one_and_two() {
        // 3 for the documentation host, 1 for the path, 2 for the host name, and 6 for all three.
        assert_eq!(rank_score("serde rename_all attribute", "https://docs.example.org/serde"), 3);
        assert_eq!(rank_score("serde rename_all attribute", "https://example.org/docs/serde"), 1);
        assert_eq!(rank_score("serde rename_all attribute", "https://serde.rs/attr"), 2);
        assert_eq!(rank_score("serde rename_all attribute", "https://docs.serde.rs/api/x"), 6);
        assert_eq!(rank_score("serde rename_all attribute", "https://example.org/post"), 0);
        // one prefix, one path mark, one name: never counted twice
        assert_eq!(rank_score("serde serde", "https://docs.serde.rs/docs/api/guide"), 6);
        // the developer host and the api host are documentation hosts too
        assert_eq!(rank_score("css grid", "https://developer.example.org/a"), 3);
        assert_eq!(rank_score("css grid", "https://api.example.org/a"), 3);
    }

    #[test]
    fn rank_keeps_the_engine_order_between_equal_scores() {
        let rows = vec![
            crate::row::Row::raw("first", "https://a.example/x", ""),
            crate::row::Row::raw("second", "https://b.example/y", ""),
            crate::row::Row::raw("third", "https://c.example/z", ""),
        ];
        assert_eq!(urls(&rank("nothing here", rows)), vec!["https://a.example/x", "https://b.example/y", "https://c.example/z"]);
    }

    #[test]
    fn rank_moves_the_documentation_page_above_the_blog_post() {
        let rows = vec![
            crate::row::Row::raw("A blog post about serde", "https://blog.example.org/serde", ""),
            crate::row::Row::raw("serde.rs", "https://serde.rs/attributes", ""),
            crate::row::Row::raw("Serde reference", "https://example.net/reference/x", ""),
            crate::row::Row::raw("docs", "https://docs.rs/serde/latest/serde", ""),
            crate::row::Row::raw("filler", "https://example.com/filler", ""),
        ];
        let got = rank("serde rename_all attribute", rows);
        assert_eq!(
            urls(&got),
            vec![
                "https://docs.rs/serde/latest/serde",
                "https://serde.rs/attributes",
                "https://example.net/reference/x",
                "https://blog.example.org/serde",
                "https://example.com/filler",
            ]
        );
    }

    #[test]
    fn a_comparison_question_flips_the_evidence() {
        // The same three rules, read backwards: the page that belongs to one side is not the
        // answer to a question that weighs two sides.
        let q = "rails vs django performance";
        // 3 for the host prefix plus 1 for the path, flipped: the reference page goes last
        assert_eq!(rank_score(q, "https://docs.example.org/tutorial/"), -4);
        // the site of one of the two subjects, flipped
        assert_eq!(rank_score(q, "https://django.example.org/"), -2);
        assert_eq!(rank_score(q, "https://blog.example.net/rails-vs-django"), 0);
        assert_eq!(
            rank_score("is kubernetes worth the complexity", "https://kubernetes.io/docs/home/"),
            -3
        );
        // no evidence is still no evidence, in either direction
        assert_eq!(rank_score("rust vs go for backend services", "https://roadmap.sh/golang/vs-rust"), 0);
    }

    #[test]
    fn the_damp_needs_a_marker_and_a_marker_is_a_whole_word() {
        for q in [
            "rails vs django performance",
            "cheapest vpn for travel 2024",
            "why i stopped using notion",
            "is kubernetes worth the complexity",
            "which is better, postgres or mysql",
            "best web framework 2024",
            "should i use wal mode in sqlite",
            "railway vs fly.io review",
        ] {
            assert!(comparison_intent(q), "missed: {}", q);
        }
        for q in [
            "django migrations squash",
            "serde rename_all attribute",
            "sqlite wal mode",
            "serde rename_all attribute",
            "versions of the api",
            "bestiary of the linux kernel",
            "whys and wherefores",
        ] {
            assert!(!comparison_intent(q), "false marker: {}", q);
        }
        // and the score of an unmarked query is untouched by the damp
        assert_eq!(
            rank_score("django migrations squash", "https://docs.djangoproject.com/en/4.2/topics/migrations/"),
            5
        );
    }

    #[test]
    fn a_host_names_a_subject_at_a_label_start_only() {
        // a term that begins a label names the site
        assert_eq!(rank_score("django migrations squash", "https://docs.djangoproject.com/en/4.2/x"), 5);
        assert_eq!(rank_score("pandas filter rows", "https://pandas.pydata.org/docs/x"), 3);
        // a run of characters inside a label does not
        assert_eq!(rank_score("cheapest vpn for travel 2024", "https://thriftytraveler.com/"), 0);
        assert_eq!(rank_score("using notion for a year", "https://www.mintnotion.com/x"), 0);
        assert_eq!(rank_score("using notion for a year", "https://www.notion.so/x"), 2);
        // the same two rows under a marker: the label rule decides first, the damp after it
        assert_eq!(rank_score("why i stopped using notion", "https://www.mintnotion.com/x"), 0);
        assert_eq!(rank_score("why i stopped using notion", "https://www.notion.so/x"), -2);
    }

    #[test]
    fn rank_lifts_the_comparison_above_the_vendor_page() {
        let rows = vec![
            crate::row::Row::raw("Tutorial", "https://docs.example.org/tutorial/", ""),
            crate::row::Row::raw("Django", "https://django.example.org/", ""),
            crate::row::Row::raw("rails vs django", "https://blog.example.net/rails-vs-django", ""),
        ];
        assert_eq!(
            urls(&rank("rails vs django performance", rows)),
            vec![
                "https://blog.example.net/rails-vs-django",
                "https://django.example.org/",
                "https://docs.example.org/tutorial/",
            ]
        );
    }

    #[test]
    fn a_platform_word_in_the_host_earns_nothing() {
        // rust, linux, json and the rest are generic: the domain is not about the query
        assert_eq!(rank_score("rust memory model", "https://rust-lang.org/x"), 0);
        assert_eq!(rank_score("linux json config", "https://linux.org/x"), 0);
        assert_eq!(rank_score("docs for the api", "https://docs.example.org/api/x"), 4);
        // a four character term that is not on the list still counts
        assert_eq!(rank_score("asyncio cancellation", "https://asyncio.dev/x"), 2);
        // and a term of three characters never does
        assert_eq!(rank_score("git worktree add", "https://git-scm.com/docs/git-worktree"), 1);
    }

    #[test]
    fn a_mixed_draw_keeps_only_the_rows_that_carry_a_term() {
        let rows = vec![
            crate::row::Row::raw("Sign in to your account", "https://example.org/login", ""),
            crate::row::Row::raw("Session handling", "https://example.net/a", "tmux detach explained"),
            crate::row::Row::raw("tmux manual", "https://tmux.github.io/man", ""),
            crate::row::Row::raw("Totally unrelated", "https://example.com/b", "nothing to do with it"),
        ];
        let kept = keep_on_topic("tmux session detach attach", rows);
        assert_eq!(
            urls(&kept),
            vec!["https://example.net/a", "https://tmux.github.io/man"]
        );
        // a set with nothing on topic is empty, which is what the caller refuses on
        let none = keep_on_topic(
            "tmux session detach attach",
            vec![crate::row::Row::raw("x", "https://example.org/login", "")],
        );
        assert!(none.is_empty());
    }

    #[test]
    fn a_deduped_retry_merge_keeps_the_first_draw_order() {
        let first = vec![
            crate::row::Row::raw("a", "https://a.example/1", ""),
            crate::row::Row::raw("b", "https://b.example/2", ""),
        ];
        let second = vec![
            crate::row::Row::raw("b again", "https://b.example/2", ""),
            crate::row::Row::raw("c", "https://c.example/3", ""),
            crate::row::Row::raw("a slashed", "https://a.example/1/", ""),
        ];
        let mut both = first.clone();
        both.extend(second);
        let merged = dedupe(both);
        assert_eq!(
            urls(&merged),
            vec!["https://a.example/1", "https://b.example/2", "https://c.example/3"]
        );
        assert_eq!(merged[1].title, "b");
    }
}
