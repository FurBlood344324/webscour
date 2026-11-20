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

/// A merged set carries drift: an engine can answer a neighbouring query, and a row with no
/// query term in its title or url is not evidence for anything. Keep those out as soon as one
/// on-topic row exists; with none at all, return what came back and let `related` judge.
pub fn prefer_on_topic(
    query: &str,
    rows: Vec<crate::row::Row>,
    limit: usize,
) -> Vec<crate::row::Row> {
    let rows = dedupe(rows);
    let on = on_topic(query, &rows);
    let pick = if on.is_empty() { rows } else { on };
    pick.into_iter().take(limit).collect()
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
}
