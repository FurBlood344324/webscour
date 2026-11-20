//! Everything that talks to the wire, and the one failure type every command catches.
//!
//! `FetchError` carries the status code rather than burying it in the message: the fallback
//! chain has to tell "no such host" from "429, wait" from "404, the page is gone", and string
//! matching on an error message is how that distinction rots the first time it is reworded.

use std::time::Duration;

use crate::util;

/// A browser-shaped UA, because most sites refuse a bare library one.
/// The archive is the exception, and it says so in its own constant.
pub const UA: &str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

/// web.archive.org answers 429 to a browser-shaped UA and 200 to an honest one. Measured, so it
/// gets its own string rather than a general apology.
pub const ARCHIVE_UA: &str = "webscour/0.1 (+https://github.com/FurBlood344324/webscour)";

/// Read cap: a PDF is not a search result, and a hostile body must not become memory.
pub const MAX_BYTES: u64 = 6_000_000;

#[derive(Debug, Clone)]
pub struct FetchError {
    pub message: String,
    pub status: Option<u16>,
}

impl FetchError {
    pub fn new(message: impl Into<String>) -> FetchError {
        FetchError {
            message: message.into(),
            status: None,
        }
    }
    pub fn status(code: u16) -> FetchError {
        FetchError {
            message: format!("HTTP {}", code),
            status: Some(code),
        }
    }
}

impl std::fmt::Display for FetchError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.message)
    }
}

impl std::error::Error for FetchError {}

impl From<ureq::Error> for FetchError {
    fn from(e: ureq::Error) -> FetchError {
        match &e {
            ureq::Error::StatusCode(code) => FetchError::status(*code),
            ureq::Error::Timeout(_) => FetchError::new("timeout"),
            other => {
                let text = other.to_string();
                let short: String = text.chars().take(120).collect();
                FetchError::new(format!("{}: {}", kind_of(other), short))
            }
        }
    }
}

fn kind_of(e: &ureq::Error) -> &'static str {
    match e {
        ureq::Error::Timeout(_) => "Timeout",
        ureq::Error::StatusCode(_) => "HTTPError",
        ureq::Error::Io(_) => "IOError",
        ureq::Error::HostNotFound => "HostNotFound",
        ureq::Error::ConnectionFailed => "ConnectionFailed",
        ureq::Error::TooManyRedirects => "TooManyRedirects",
        ureq::Error::Tls(_) => "TLS",
        ureq::Error::BodyExceedsLimit(_) => "BodyExceedsLimit",
        _ => "Error",
    }
}

/// A request long enough for a slow engine, short enough to be a CLI.
pub const TIMEOUT: u64 = 15;

pub struct Response {
    pub body: String,
    pub status: u16,
    /// Everything lowercased: header names are case-insensitive and callers want `x-ratelimit-remaining`.
    pub headers: Vec<(String, String)>,
}

impl Response {
    pub fn header(&self, name: &str) -> Option<String> {
        let want = name.to_ascii_lowercase();
        self.headers
            .iter()
            .find(|(k, _)| *k == want)
            .map(|(_, v)| v.clone())
    }
}

/// GET (or POST when `form` is given). The body is text: every caller here parses it.
pub fn http(url: &str, form: Option<&str>, accept: Option<&str>, timeout: u64) -> Result<Response, FetchError> {
    http_as(url, form, accept, timeout, UA)
}

/// The same request with an explicit UA, for the one host that refuses the browser's.
pub fn http_as(
    url: &str,
    form: Option<&str>,
    accept: Option<&str>,
    timeout: u64,
    ua: &str,
) -> Result<Response, FetchError> {
    let config = ureq::Agent::config_builder()
        .timeout_global(Some(Duration::from_secs(timeout)))
        .build();
    let agent: ureq::Agent = config.into();
    let mut req = agent
        .get(url)
        .header("User-Agent", ua)
        .header("Accept-Language", "en-US,en;q=0.9");
    if let Some(a) = accept {
        req = req.header("Accept", a);
    }
    let result = match form {
        Some(body) => agent
            .post(url)
            .header("User-Agent", ua)
            .header("Accept-Language", "en-US,en;q=0.9")
            .header("Content-Type", "application/x-www-form-urlencoded")
            .send(body),
        None => req.call(),
    };
    let mut resp = result?;
    let status = resp.status().as_u16();
    let headers: Vec<(String, String)> = resp
        .headers()
        .iter()
        .map(|(k, v)| {
            (
                k.as_str().to_ascii_lowercase(),
                v.to_str().unwrap_or("").to_string(),
            )
        })
        .collect();
    let bytes = resp
        .body_mut()
        .with_config()
        .limit(MAX_BYTES)
        .read_to_vec()
        .map_err(|e| FetchError::new(format!("body: {}", e)))?;
    // Decode with replacement, an invalid byte becoming U+FFFD: a latin-1 byte in a
    // title must not kill the whole backend.
    let body = String::from_utf8_lossy(&bytes).into_owned();
    Ok(Response {
        body,
        status,
        headers,
    })
}

/// GET and parse JSON, with the failure named by the source that asked.
pub fn get_json(url: &str, accept: Option<&str>, timeout: u64) -> Result<serde_json::Value, FetchError> {
    let resp = http(url, None, accept, timeout)?;
    serde_json::from_str(&resp.body).map_err(|e| FetchError::new(format!("invalid JSON: {}", e)))
}

/// `[engine]` provenance, rendered as `[a,b]`. Empty when no backend named itself.
pub fn engine_tag(engines: &[String]) -> String {
    let names: Vec<&str> = engines.iter().filter(|e| !e.is_empty()).map(|e| e.as_str()).take(3).collect();
    if names.is_empty() {
        String::new()
    } else {
        format!("  [{}]", names.join(","))
    }
}

/// One line of the numbered row format, plus its snippet line when it has one.
pub fn format_row(index: usize, r: &crate::row::Row) -> String {
    let mut out = String::new();
    out.push_str(&format!(
        "{}. {} - {}{}\n",
        index,
        crate::row::clip_ellipsis(&r.title, 160),
        r.url,
        engine_tag(&r.engines)
    ));
    let snip = crate::row::clip_ellipsis(&r.snippet, crate::row::SNIPPET);
    let dated = match &r.published {
        Some(p) if !p.is_empty() => format!("[{}] {}", p, snip),
        _ => snip,
    };
    if !dated.trim().is_empty() {
        out.push_str(&format!("   {}\n", dated));
    }
    out
}

/// The block for a list of rows, both formats.
pub fn render(rows: &[crate::row::Row], json: bool) -> String {
    if json {
        return render_json(rows);
    }
    rows.iter()
        .enumerate()
        .map(|(i, r)| format_row(i + 1, r))
        .collect()
}

/// The `--json` block: `indent=1`, keys in insertion order, non-ASCII written as itself.
///
/// Written by hand rather than through `to_string_pretty` because the indent width and the key
/// order are both part of what a caller can see: a front end that diffed the two outputs would
/// otherwise spend an afternoon on whitespace and then distrust the diff.
pub fn render_json(rows: &[crate::row::Row]) -> String {
    let items: Vec<serde_json::Value> = rows.iter().map(|r| r.to_json()).collect();
    let mut out = write_json(&serde_json::Value::Array(items), 0);
    out.push('\n');
    out
}

/// `indent=1`: a container puts each element on its own line at depth + 1, and a scalar sits
/// where it is. Non-ASCII is written as itself.
fn write_json(value: &serde_json::Value, depth: usize) -> String {
    let pad = " ".repeat(depth);
    let inner_pad = " ".repeat(depth + 1);
    match value {
        serde_json::Value::Object(map) if !map.is_empty() => {
            let body: Vec<String> = map
                .iter()
                .map(|(k, v)| format!("{}{}: {}", inner_pad, quote_json(k), write_json(v, depth + 1)))
                .collect();
            format!("{{\n{}\n{}}}", body.join(",\n"), pad)
        }
        serde_json::Value::Object(_) => "{}".to_string(),
        serde_json::Value::Array(items) if !items.is_empty() => {
            let body: Vec<String> = items
                .iter()
                .map(|v| format!("{}{}", inner_pad, write_json(v, depth + 1)))
                .collect();
            format!("[\n{}\n{}]", body.join(",\n"), pad)
        }
        serde_json::Value::Array(_) => "[]".to_string(),
        other => write_scalar(other),
    }
}

fn write_scalar(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::String(s) => quote_json(s),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Null => "null".to_string(),
        other => other.to_string(),
    }
}

/// A JSON string, with the standard escapes and no others: non-ASCII is written as itself.
fn quote_json(text: &str) -> String {
    let mut out = String::from("\"");
    for ch in text.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{08}' => out.push_str("\\b"),
            '\u{0c}' => out.push_str("\\f"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

/// Joining inline fragments, because a snippet that reads "requires , and" is a broken
/// snippet: a space goes between two non-empty pieces unless the second starts with closing
/// punctuation or the first ends with an opening bracket or a slash.
pub fn append_text(have: &str, add: &str) -> String {
    if have.is_empty() {
        return add.to_string();
    }
    let first = add.chars().next().unwrap_or(' ');
    let last = have.chars().last().unwrap_or(' ');
    if ",.;:!?)]}%".contains(first) || "([{/".contains(last) {
        format!("{}{}", have, add)
    } else {
        format!("{} {}", have, add)
    }
}

/// Unwrap the redirect shells DDG and Bing put in front of a result URL.
pub fn unwrap_url(href: &str) -> String {
    let mut href = href.trim().to_string();
    if let Some(rest) = href.strip_prefix("//") {
        href = format!("https://{}", rest);
    }
    let (scheme, after) = match href.find("://") {
        Some(i) => (&href[..i], &href[i + 3..]),
        None => ("", href.as_str()),
    };
    let (authority, path_query) = match after.find('/') {
        Some(i) => (&after[..i], &after[i..]),
        None => (after, ""),
    };
    let query = path_query.find('?').map(|i| &path_query[i + 1..]).unwrap_or("");
    let _ = scheme;
    if authority.contains("duckduckgo.com") && path_query.starts_with("/l/") {
        if let Some(real) = util::query_param(query, "uddg") {
            return real;
        }
    } else if authority == "www.google.com" || authority == "google.com" {
        if path_query.starts_with("/url") {
            // An opaque shell: the target is not recoverable, so do not print junk.
            return match util::query_param(query, "q") {
                Some(real) if real.starts_with("http://") || real.starts_with("https://") => real,
                _ => String::new(),
            };
        }
    } else if authority.ends_with("bing.com") && path_query.starts_with("/ck/a") {
        if let Some(u) = util::query_param(query, "u") {
            if let Some(raw) = u.strip_prefix("a1") {
                if let Some(bytes) = base64url_decode(raw) {
                    if let Ok(text) = String::from_utf8(bytes) {
                        return text;
                    }
                }
            }
        }
    }
    href
}

fn base64url_decode(s: &str) -> Option<Vec<u8>> {
    let mut acc: u32 = 0;
    let mut bits = 0;
    let mut out = Vec::new();
    for ch in s.chars() {
        let v = match ch {
            'A'..='Z' => ch as u32 - 'A' as u32,
            'a'..='z' => ch as u32 - 'a' as u32 + 26,
            '0'..='9' => ch as u32 - '0' as u32 + 52,
            '-' => 62,
            '_' => 63,
            '=' => break,
            _ => return None,
        };
        acc = (acc << 6) | v;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push(((acc >> bits) & 0xff) as u8);
        }
    }
    Some(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ddg_redirect_is_unwrapped() {
        assert_eq!(
            unwrap_url("//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fx&rut=1"),
            "https://example.org/x"
        );
    }

    #[test]
    fn a_relative_url_is_left_alone() {
        assert_eq!(unwrap_url("https://example.net/b"), "https://example.net/b");
    }

    #[test]
    fn an_opaque_google_shell_is_dropped() {
        assert_eq!(unwrap_url("https://www.google.com/url?opi=1&uoh=3"), "");
    }

    #[test]
    fn append_text_does_not_invent_spaces_before_punctuation() {
        assert_eq!(append_text("Hello", ", world"), "Hello, world");
        assert_eq!(append_text("Hello", "world"), "Hello world");
    }
}
