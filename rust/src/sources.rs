//! The keyless sources: one free endpoint per kind of question.
//!
//! Each is two things in one place, as in the Python: a pure parser (JSON or feed in, rows out)
//! and the one request that feeds it. The parsers are pure so `--self-test` exercises them with
//! no network - the same rule `search.rs` and `html.rs` follow.
//!
//! Every endpoint here was measured before it was ported: no key, no login, a 200 and a body
//! with the fact in it. The sources that failed that test (Reddit 403, Semantic Scholar 429
//! without a key, GDELT 429, Openverse 403, Mojeek 403, Marginalia's bot wall) are listed in
//! `docs/routing.md` in the Python tree so nobody spends an afternoon rediscovering them.
//!
//! Row shape is the same everywhere: title, url, snippet, plus `published` when the source really
//! carries a publication date. Nothing invents one: a Wikipedia article has no publication date,
//! and pretending its last-edit timestamp is one would corrupt `--fresh`.

use serde_json::Value;

use crate::net::{self, FetchError};
use crate::row::Row;
use crate::search::js_num;
use crate::util;

const JSON_ACCEPT: &str = "application/json";

/// The names `--source` accepts from the API table. `arxiv` is the API route already
/// (`export.arxiv.org`), so `arxiv-api` is an alias for it rather than a second implementation.
pub const API_SOURCES: [&str; 14] = [
    "wikipedia",
    "openalex",
    "crossref",
    "arxiv",
    "arxiv-api",
    "europepmc",
    "pubmed",
    "pypi",
    "npm",
    "crates",
    "devto",
    "wayback",
    "googlenews",
    "bbc",
];

pub const FRESH_SOURCES: [&str; 2] = ["googlenews", "bbc"];

/// The SearXNG categories passed through as `--category`. Opt-in and never a default: a category
/// changes which engines answer, so it changes the answer.
pub const CATEGORIES: [&str; 7] = ["general", "it", "science", "news", "images", "files", "social"];

/// Every name `--source` accepts, in one string: the error message and help text are the same
/// list, so a name can never be accepted by the parser and missing from the message that lists it.
pub fn sources_help() -> String {
    let names: Vec<&str> = API_SOURCES
        .iter()
        .copied()
        .filter(|s| *s != "arxiv-api")
        .collect();
    format!("web|github|so|hn|discourse:<base>|{}", names.join("|"))
}

// ------------------------------------------------------------------ small helpers

/// True only for a value that carries a month and a day, not just a year.
fn full_date(value: &str) -> bool {
    let b = value.as_bytes();
    b.len() >= 7
        && b[..4].iter().all(|c| c.is_ascii_digit())
        && (b[4] == b'-' || b[4] == b'/')
        && b[5].is_ascii_digit()
        && b[6].is_ascii_digit()
}

/// The many ways these APIs spell a date, to `YYYY-MM-DD`. Empty when it cannot be read.
pub fn iso_date(value: &str) -> String {
    let v = value.trim();
    let b = v.as_bytes();
    if b.len() >= 10
        && b[..4].iter().all(|c| c.is_ascii_digit())
        && b[4] == b'-'
        && b[5..7].iter().all(|c| c.is_ascii_digit())
        && b[7] == b'-'
        && b[8..10].iter().all(|c| c.is_ascii_digit())
    {
        return format!("{}-{}-{}", &v[..4], &v[5..7], &v[8..10]);
    }
    if b.len() >= 10
        && b[..4].iter().all(|c| c.is_ascii_digit())
        && b[4] == b'/'
        && b[5..7].iter().all(|c| c.is_ascii_digit())
        && b[7] == b'/'
        && b[8..10].iter().all(|c| c.is_ascii_digit())
    {
        return format!("{}-{}-{}", &v[..4], &v[5..7], &v[8..10]);
    }
    String::new()
}

pub const MONTHS: [&str; 12] = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/// Strip every `<...>` tag. Entities are left as they are: the Python contract unescapes only
/// in the rss path, which calls `html_unescape` itself; every other source prints the raw text.
pub fn strip_tags(text: &str) -> String {
    let mut out = String::new();
    let mut depth = 0;
    for ch in text.chars() {
        match ch {
            '<' => depth += 1,
            '>' if depth > 0 => depth -= 1,
            c if depth == 0 => out.push(c),
            _ => {}
        }
    }
    out
}

/// The five named entities plus numeric ones. These feeds use nothing more exotic.
pub fn html_unescape(text: &str) -> String {
    let mut out = String::new();
    let bytes: Vec<char> = text.chars().collect();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == '&' {
            let rest: String = bytes[i..].iter().take(12).collect();
            if let Some(semi) = rest.find(';') {
                let entity = &rest[1..semi];
                let replacement = match entity {
                    "amp" => Some('&'),
                    "lt" => Some('<'),
                    "gt" => Some('>'),
                    "quot" => Some('"'),
                    "apos" => Some('\''),
                    "nbsp" => Some('\u{a0}'),
                    other if other.starts_with("#x") || other.starts_with("#X") => {
                        u32::from_str_radix(&other[2..], 16).ok().and_then(char::from_u32)
                    }
                    other if other.starts_with('#') => {
                        other[1..].parse::<u32>().ok().and_then(char::from_u32)
                    }
                    _ => None,
                };
                if let Some(c) = replacement {
                    out.push(c);
                    i += semi + 1;
                    continue;
                }
            }
        }
        out.push(bytes[i]);
        i += 1;
    }
    out
}

fn get_str<'a>(v: &'a Value, key: &str) -> &'a str {
    v.get(key).and_then(|x| x.as_str()).unwrap_or("")
}

fn get_arr<'a>(v: &'a Value, key: &str) -> &'a [Value] {
    v.get(key)
        .and_then(|x| x.as_array())
        .map(|a| a.as_slice())
        .unwrap_or(&[])
}

// ------------------------------------------------------------------ pure parsers

/// MediaWiki `list=search`. The snippet carries `<span class="searchmatch">` highlight markup.
pub fn parse_wikipedia(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for it in get_arr(doc.get("query").unwrap_or(&Value::Null), "search") {
        let title = get_str(it, "title").to_string();
        let snippet = strip_tags(get_str(it, "snippet"));
        let slug = util::quote(&title.replace(' ', "_"), "()_,-");
        out.push(Row::new(
            &title,
            &format!("https://en.wikipedia.org/wiki/{}", slug),
            &snippet,
        ));
    }
    out
}

/// OpenAlex knows the year and nothing finer, and a year sorted against a full date is a lie
/// about precision, so `published` stays empty and the year lives in the snippet.
pub fn parse_openalex(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for w in get_arr(doc, "results") {
        let year = w.get("publication_year").cloned().unwrap_or(Value::Null);
        let venue = w
            .get("best_oa_location")
            .and_then(|l| l.get("source"))
            .and_then(|s| s.get("display_name"))
            .and_then(|s| s.as_str())
            .unwrap_or("")
            .to_string();
        let mut title = get_str(w, "display_name").to_string();
        if title.is_empty() {
            title = get_str(w, "title").to_string();
        }
        let mut bits: Vec<String> = Vec::new();
        if !year.is_null() {
            let y = js_num(&year);
            if !y.is_empty() && y != "null" {
                bits.push(y);
            }
        }
        if !venue.is_empty() {
            bits.push(venue);
        }
        bits.push(format!(
            "{} citations",
            w.get("cited_by_count").map(js_num).unwrap_or_else(|| "0".into())
        ));
        let mut url = get_str(w, "doi").to_string();
        if url.is_empty() {
            url = get_str(w, "id").to_string();
        }
        if let Some(rest) = url.strip_prefix("https://doi.org/https://") {
            url = rest.to_string();
        }
        let year_text = if year.is_null() { String::new() } else { js_num(&year) };
        let published = if full_date(&year_text) { iso_date(&year_text) } else { String::new() };
        out.push(Row::dated(&title, &url, &bits.join(" · "), &published));
    }
    out
}

pub fn parse_crossref(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    let message = doc.get("message").cloned().unwrap_or(Value::Null);
    for it in get_arr(&message, "items") {
        let title = it
            .get("title")
            .and_then(|t| t.as_array())
            .and_then(|a| a.first())
            .and_then(|t| t.as_str())
            .unwrap_or("");
        if title.is_empty() {
            continue;
        }
        let date: Vec<Value> = it
            .get("issued")
            .and_then(|i| i.get("date-parts"))
            .and_then(|d| d.as_array())
            .and_then(|a| a.first())
            .and_then(|p| p.as_array())
            .cloned()
            .unwrap_or_default();
        let published = if date.len() >= 3 {
            date.iter()
                .map(|p| format!("{:02}", p.as_u64().unwrap_or(0)))
                .collect::<Vec<_>>()
                .join("-")
        } else {
            String::new()
        };
        let venue = it
            .get("container-title")
            .and_then(|c| c.as_array())
            .and_then(|a| a.first())
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let mut bits: Vec<String> = Vec::new();
        if !venue.is_empty() {
            bits.push(venue.to_string());
        }
        if let Some(n) = it.get("is-referenced-by-count") {
            if n.as_u64().unwrap_or(0) != 0 {
                bits.push(format!("{} citations", js_num(n)));
            }
        }
        let mut url = get_str(it, "URL").to_string();
        if url.is_empty() {
            let doi = get_str(it, "DOI");
            if !doi.is_empty() {
                url = format!("https://doi.org/{}", doi);
            }
        }
        out.push(Row::dated(title, &url, &bits.join(" · "), &published));
    }
    out
}

/// Atom, with the one field `search::parse_arxiv` drops: `<published>`.
pub fn parse_arxiv_api(xml_text: &str) -> Vec<Row> {
    let doc = match roxmltree::Document::parse(xml_text) {
        Ok(d) => d,
        Err(_) => return Vec::new(),
    };
    let mut out = Vec::new();
    for entry in doc
        .descendants()
        .filter(|n| n.has_tag_name((ATOM_NS, "entry")))
    {
        let text = |name: &str| -> String {
            entry
                .children()
                .find(|c| c.has_tag_name((ATOM_NS, name)))
                .and_then(|c| c.text())
                .unwrap_or("")
                .to_string()
        };
        let published = iso_date(&text("published"));
        out.push(Row::dated(
            &text("title"),
            text("id").trim(),
            &text("summary"),
            &published,
        ));
    }
    out
}

const ATOM_NS: &str = "http://www.w3.org/2005/Atom";

pub fn parse_europepmc(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    let list = doc.get("resultList").cloned().unwrap_or(Value::Null);
    for it in get_arr(&list, "result") {
        let title = get_str(it, "title").to_string();
        if get_str(it, "source") == "PPR" && title.is_empty() {
            continue;
        }
        let url = if !get_str(it, "doi").is_empty() {
            format!("https://doi.org/{}", get_str(it, "doi"))
        } else if !get_str(it, "pmid").is_empty() {
            format!("https://pubmed.ncbi.nlm.nih.gov/{}/", get_str(it, "pmid"))
        } else {
            format!(
                "https://europepmc.org/article/{}/{}",
                get_str(it, "source"),
                get_str(it, "id")
            )
        };
        let bits: Vec<String> = [get_str(it, "journalTitle"), get_str(it, "authorString")]
            .iter()
            .filter(|b| !b.is_empty())
            .map(|b| b.to_string())
            .collect();
        let raw_date = if !get_str(it, "firstPublicationDate").is_empty() {
            get_str(it, "firstPublicationDate")
        } else {
            get_str(it, "pubYear")
        };
        out.push(Row::dated(&title, &url, &bits.join(" · "), &iso_date(raw_date)));
    }
    out
}

/// `esummary.fcgi`: `result.uids` is the order, and the same keys also hold the records.
pub fn parse_pubmed(doc: &Value) -> Vec<Row> {
    let result = doc.get("result").cloned().unwrap_or(Value::Null);
    let mut out = Vec::new();
    for uid in get_arr(&result, "uids") {
        let uid_text = js_num(uid);
        let it = result.get(&uid_text).cloned().unwrap_or(Value::Null);
        let title = get_str(&it, "title").trim_end_matches('.').to_string();
        if title.is_empty() {
            continue;
        }
        let journal = if !get_str(&it, "fulljournalname").is_empty() {
            get_str(&it, "fulljournalname")
        } else {
            get_str(&it, "source")
        };
        out.push(Row::dated(
            &title,
            &format!("https://pubmed.ncbi.nlm.nih.gov/{}/", uid_text),
            journal,
            &pubmed_date(&it),
        ));
    }
    out
}

/// `2026 Nov 13` and `2026 Nov` are the two shapes esummary uses.
fn pubmed_date(record: &Value) -> String {
    let text = get_str(record, "pubdate");
    let parts: Vec<&str> = text.split_whitespace().collect();
    if parts.len() < 2 || parts[0].len() != 4 || !parts[0].chars().all(|c| c.is_ascii_digit()) {
        return String::new();
    }
    let month = match MONTHS.iter().position(|m| *m == parts[1]) {
        Some(i) => i + 1,
        None => 1,
    };
    let day = parts
        .get(2)
        .and_then(|d| d.parse::<u32>().ok())
        .unwrap_or(1);
    format!("{}-{:02}-{:02}", parts[0], month, day)
}

pub fn parse_pypi(doc: &Value) -> Vec<Row> {
    let info = doc.get("info").cloned().unwrap_or(Value::Null);
    let version = get_str(&info, "version").to_string();
    let files = doc
        .get("releases")
        .and_then(|r| r.get(&version))
        .and_then(|f| f.as_array())
        .cloned()
        .unwrap_or_default();
    let mut uploaded = String::new();
    if let Some(first) = files.first() {
        let raw = if !get_str(first, "upload_time_iso_8601").is_empty() {
            get_str(first, "upload_time_iso_8601")
        } else {
            get_str(first, "upload_time")
        };
        uploaded = raw.chars().take(10).collect();
    }
    let mut bits: Vec<String> = vec![
        if version.is_empty() { "?".into() } else { version },
        get_str(&info, "summary").to_string(),
    ];
    if !get_str(&info, "requires_python").is_empty() {
        bits.push(format!("python {}", get_str(&info, "requires_python")));
    }
    if !uploaded.is_empty() {
        bits.push(format!("released {}", uploaded));
    }
    let url = if !get_str(&info, "project_url").is_empty() {
        get_str(&info, "project_url")
    } else {
        get_str(&info, "package_url")
    };
    vec![Row::dated(
        get_str(&info, "name"),
        url,
        &bits
            .iter()
            .filter(|b| !b.is_empty())
            .cloned()
            .collect::<Vec<_>>()
            .join(" · "),
        &uploaded,
    )]
}

pub fn parse_npm(doc: &Value) -> Vec<Row> {
    let mut bits: Vec<String> = vec![
        if get_str(doc, "version").is_empty() {
            "?".into()
        } else {
            get_str(doc, "version").to_string()
        },
        get_str(doc, "description").to_string(),
    ];
    match doc.get("license") {
        Some(Value::String(s)) if !s.is_empty() => bits.push(s.clone()),
        Some(Value::Object(_)) => bits.push("see license".into()),
        _ => {}
    }
    if let Some(node) = doc.get("engines").and_then(|e| e.get("node")).and_then(|n| n.as_str()) {
        bits.push(format!("node {}", node));
    }
    if let Some(dep) = doc.get("deprecated") {
        let text = match dep {
            Value::String(s) => s.clone(),
            other => other.to_string(),
        };
        if !text.is_empty() {
            bits.push(format!("DEPRECATED: {}", text));
        }
    }
    let repo_url = doc
        .get("repository")
        .and_then(|r| r.get("url").and_then(|u| u.as_str()))
        .unwrap_or("");
    let mut url = if repo_url.is_empty() {
        get_str(doc, "homepage").to_string()
    } else {
        repo_url.to_string()
    };
    url = url.replace("git+", "");
    if url.ends_with(".git") {
        url.truncate(url.len() - 4);
    }
    vec![Row::new(
        get_str(doc, "name"),
        &url,
        &bits
            .iter()
            .filter(|b| !b.is_empty())
            .cloned()
            .collect::<Vec<_>>()
            .join(" · "),
    )]
}

pub fn parse_crates(doc: &Value) -> Vec<Row> {
    let krate = doc.get("crate").cloned().unwrap_or(Value::Null);
    let versions = get_arr(doc, "versions");
    let mut bits: Vec<String> = vec![
        if get_str(&krate, "max_version").is_empty() {
            "?".into()
        } else {
            get_str(&krate, "max_version").to_string()
        },
        get_str(&krate, "description").to_string(),
    ];
    if let Some(d) = krate.get("recent_downloads") {
        if d.as_u64().unwrap_or(0) != 0 {
            bits.push(format!("{} downloads (90d)", js_num(d)));
        }
    }
    let updated: String = get_str(&krate, "updated_at").chars().take(10).collect();
    if !updated.is_empty() {
        bits.push(format!("updated {}", updated));
    }
    if let Some(first) = versions.first() {
        if first.get("yanked").and_then(|y| y.as_bool()).unwrap_or(false) {
            bits.push("latest yanked".into());
        }
    }
    let url = if !get_str(&krate, "repository").is_empty() {
        get_str(&krate, "repository")
    } else {
        get_str(&krate, "homepage")
    };
    vec![Row::dated(
        get_str(&krate, "name"),
        url,
        &bits
            .iter()
            .filter(|b| !b.is_empty())
            .cloned()
            .collect::<Vec<_>>()
            .join(" · "),
        &updated,
    )]
}

pub fn parse_devto(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for it in doc.as_array().map(|a| a.as_slice()).unwrap_or(&[]) {
        let mut bits: Vec<String> = Vec::new();
        if let Some(m) = it.get("reading_time_minutes") {
            if m.as_u64().unwrap_or(0) != 0 {
                bits.push(format!("{} min read", js_num(m)));
            }
        }
        if let Some(r) = it.get("positive_reactions_count") {
            if r.as_u64().unwrap_or(0) != 0 {
                bits.push(format!("{} reactions", js_num(r)));
            }
        }
        let tags: Vec<String> = get_arr(it, "tag_list")
            .iter()
            .filter_map(|t| t.as_str())
            .take(5)
            .map(|t| t.to_string())
            .collect();
        if !tags.is_empty() {
            bits.push(tags.join(", "));
        }
        out.push(Row::dated(
            get_str(it, "title"),
            get_str(it, "url"),
            &bits.join(" · "),
            &iso_date(get_str(it, "published_at")),
        ));
    }
    out
}

/// CDX JSON: `[[timestamp, original, statuscode], ...]` with a header row.
pub fn parse_wayback(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for row in doc.as_array().map(|a| a.as_slice()).unwrap_or(&[]) {
        let cells = match row.as_array() {
            Some(c) if c.len() >= 2 => c,
            _ => continue,
        };
        let stamp = match cells[0].as_str() {
            Some(s) => s.to_string(),
            None => continue,
        };
        let original = cells[1].as_str().unwrap_or("").to_string();
        if stamp == "timestamp" || stamp == "urlkey" {
            continue;
        }
        let status = cells
            .get(2)
            .and_then(|v| v.as_str())
            .unwrap_or("?")
            .to_string();
        let date = if stamp.len() >= 8 {
            format!("{}-{}-{}", &stamp[..4], &stamp[4..6], &stamp[6..8])
        } else {
            String::new()
        };
        let head: String = stamp.chars().take(8).collect();
        out.push(Row::dated(
            &format!("{} ({})", original, head),
            &format!("https://web.archive.org/web/{}id_/{}", stamp, original),
            &format!(
                "archived {}, status {}",
                if date.is_empty() { "?".to_string() } else { date.clone() },
                status
            ),
            &date,
        ));
    }
    out
}

/// RSS 2.0 and Atom, the two shapes a news feed uses. Returns rows with a real date.
pub fn parse_rss(xml_text: &str) -> Vec<Row> {
    let doc = match roxmltree::Document::parse(xml_text) {
        Ok(d) => d,
        Err(_) => return Vec::new(),
    };
    let mut out = Vec::new();
    for item in doc.descendants() {
        let local = item.tag_name().name();
        if local != "item" && local != "entry" {
            continue;
        }
        let field = |name: &str| -> String {
            item.children()
                .find(|c| c.tag_name().name() == name)
                .and_then(|c| c.text())
                .unwrap_or("")
                .to_string()
        };
        let mut title = html_unescape(&field("title"));
        let mut link = field("link");
        if link.is_empty() {
            if let Some(child) = item
                .children()
                .find(|c| c.tag_name().name() == "link" && c.attribute("href").is_some())
            {
                link = child.attribute("href").unwrap_or("").to_string();
            }
        }
        let raw_date = {
            let p = field("pubDate");
            let q = field("published");
            let r = field("updated");
            if !p.is_empty() {
                p
            } else if !q.is_empty() {
                q
            } else {
                r
            }
        };
        let mut published = iso_date(&raw_date);
        if published.is_empty() {
            published = rfc822_date(&raw_date);
        }
        let source = html_unescape(&field("source"));
        if !source.is_empty() {
            let suffix = format!(" - {}", source);
            if title.ends_with(&suffix) {
                title.truncate(title.len() - suffix.len());
                title = title.trim_end().to_string();
            }
        }
        let desc = {
            let d = field("description");
            if d.is_empty() {
                field("summary")
            } else {
                d
            }
        };
        let mut snippet = collapse(&html_unescape(&strip_tags(&desc)));
        // Google News repeats the headline and then the outlet inside <description>. Left alone
        // that prints the title three times per row and reads as a bug in the output.
        if !title.is_empty() && snippet.to_lowercase().starts_with(&title.to_lowercase()) {
            snippet = snippet[title.len()..]
                .trim_start_matches([' ', '-', '|', ':'])
                .to_string();
        }
        for repeat in [&title, &source] {
            if repeat.is_empty() {
                continue;
            }
            let low = snippet.to_lowercase();
            let needle = repeat.to_lowercase();
            if low.ends_with(&needle) {
                let cut = snippet.len() - repeat.len();
                snippet = snippet[..cut].trim_end_matches([' ', '-', '|', ':']).to_string();
            }
        }
        let snippet = collapse(&snippet);
        let snippet = if source.is_empty() {
            snippet
        } else if snippet.is_empty() {
            source.clone()
        } else {
            format!("{} · {}", source, snippet)
        };
        out.push(Row::dated(&title, &link, &snippet, &published));
    }
    out
}

fn collapse(text: &str) -> String {
    text.replace('\u{a0}', " ").split_whitespace().collect::<Vec<_>>().join(" ")
}

/// `Sat, 14 Nov 2026 19:43:32 GMT` -> `2026-11-14`. Empty when it is not that shape.
pub fn rfc822_date(text: &str) -> String {
    let cleaned: String = text
        .chars()
        .map(|c| if c.is_ascii_alphabetic() || c.is_ascii_digit() || c == ' ' { c } else { ' ' })
        .collect();
    let parts: Vec<&str> = cleaned.split_whitespace().collect();
    for i in 0..parts.len().saturating_sub(2) {
        let day = parts[i];
        let month = parts[i + 1];
        let year = parts[i + 2];
        if year.len() != 4 || !year.chars().all(|c| c.is_ascii_digit()) {
            continue;
        }
        if let Some(m) = MONTHS.iter().position(|x| *x == month) {
            if let Ok(d) = day.parse::<u32>() {
                return format!("{}-{:02}-{:02}", year, m + 1, d);
            }
        }
    }
    String::new()
}

// ------------------------------------------------------------------ the requests

fn first_word(query: &str) -> String {
    query
        .split_whitespace()
        .next()
        .unwrap_or("")
        .to_lowercase()
}

pub fn wikipedia(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit={}&srsearch={}",
        limit,
        util::quote_plus(query)
    );
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let mut rows = parse_wikipedia(&doc);
    rows.truncate(limit);
    Ok(rows)
}

pub fn openalex(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://api.openalex.org/works?per-page={}&search={}",
        limit,
        util::quote_plus(query)
    );
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let mut rows = parse_openalex(&doc);
    rows.truncate(limit);
    Ok(rows)
}

pub fn crossref(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://api.crossref.org/works?rows={}&query={}",
        limit,
        util::quote_plus(query)
    );
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let mut rows = parse_crossref(&doc);
    rows.truncate(limit);
    Ok(rows)
}

pub fn arxiv_api(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://export.arxiv.org/api/query?max_results={}&search_query={}",
        limit,
        util::quote(&format!("all:{}", query), "")
    );
    let resp = net::http(&url, None, None, net::TIMEOUT)?;
    let mut rows = parse_arxiv_api(&resp.body);
    rows.truncate(limit);
    Ok(rows)
}

pub fn europepmc(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize={}&query={}",
        limit,
        util::quote_plus(query)
    );
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let mut rows = parse_europepmc(&doc);
    rows.truncate(limit);
    Ok(rows)
}

/// Two calls, because esearch returns ids and esummary returns the facts.
pub fn pubmed(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let search_url = format!(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax={}&term={}",
        limit,
        util::quote_plus(query)
    );
    let ids = net::get_json(&search_url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let found: Vec<String> = ids
        .get("esearchresult")
        .and_then(|r| r.get("idlist"))
        .and_then(|l| l.as_array())
        .map(|a| {
            a.iter()
                .filter_map(|v| v.as_str())
                .take(limit)
                .map(|s| s.to_string())
                .collect()
        })
        .unwrap_or_default();
    if found.is_empty() {
        return Ok(Vec::new());
    }
    let summary_url = format!(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={}",
        found.join(",")
    );
    let summary = net::get_json(&summary_url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let mut rows = parse_pubmed(&summary);
    rows.truncate(limit);
    Ok(rows)
}

pub fn pypi(query: &str, _limit: usize) -> Result<Vec<Row>, FetchError> {
    let name = util::quote(&first_word(query), "");
    let url = format!("https://pypi.org/pypi/{}/json", name);
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    Ok(parse_pypi(&doc))
}

pub fn npm(query: &str, _limit: usize) -> Result<Vec<Row>, FetchError> {
    let name = util::quote(&first_word(query), "");
    let url = format!("https://registry.npmjs.org/{}/latest", name);
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    Ok(parse_npm(&doc))
}

pub fn crates(query: &str, _limit: usize) -> Result<Vec<Row>, FetchError> {
    let name = util::quote(&first_word(query), "");
    let url = format!("https://crates.io/api/v1/crates/{}", name);
    // crates.io answers 403 to a client with no contact story in its UA, and it is slower.
    let doc = net::get_json(&url, Some(JSON_ACCEPT), 20)?;
    Ok(parse_crates(&doc))
}

/// dev.to has tags, not full text: the query becomes one tag (`python`, `asyncio`).
pub fn devto(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let tag: String = first_word(query)
        .chars()
        .filter(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
        .collect();
    let tag = if tag.is_empty() { "webdev".to_string() } else { tag };
    let url = format!(
        "https://dev.to/api/articles?per_page={}&tag={}",
        limit,
        util::quote(&tag, "")
    );
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let mut rows = parse_devto(&doc);
    rows.truncate(limit);
    Ok(rows)
}

/// The query is a URL or a host: CDX lists snapshots, newest last.
pub fn wayback(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let target = util::quote(query.trim(), "");
    let url = format!(
        "https://web.archive.org/cdx/search/cdx?url={}&output=json&limit=-{}&fl=timestamp,original,statuscode&filter=statuscode:200",
        target, limit
    );
    let resp = net::http(&url, None, Some(JSON_ACCEPT), 15)?;
    let body = resp.body.trim();
    let doc: Value = if body.is_empty() {
        Value::Array(vec![])
    } else {
        serde_json::from_str(body).map_err(|e| FetchError::new(format!("invalid JSON: {}", e)))?
    };
    let mut rows = parse_wayback(&doc);
    rows.truncate(limit);
    Ok(rows)
}

pub fn googlenews(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q={}",
        util::quote_plus(query)
    );
    let resp = net::http(&url, None, None, net::TIMEOUT)?;
    let mut rows = parse_rss(&resp.body);
    rows.truncate(limit);
    Ok(rows)
}

/// One outlet, no query facility: the query filters its latest feed, newest first.
///
/// A query with no match in the feed returns the newest items rather than nothing, because
/// "what happened today" is the question this source answers and the filter is a convenience.
pub fn bbc(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let resp = net::http("https://feeds.bbci.co.uk/news/rss.xml", None, None, net::TIMEOUT)?;
    let mut rows = parse_rss(&resp.body);
    rows.sort_by(|a, b| {
        b.published
            .clone()
            .unwrap_or_default()
            .cmp(&a.published.clone().unwrap_or_default())
    });
    let terms = util::words3(query);
    if !terms.is_empty() {
        let hit: Vec<Row> = rows
            .iter()
            .filter(|r| {
                let blob = format!("{} {}", r.title, r.snippet).to_lowercase();
                terms.iter().any(|t| blob.contains(t.as_str()))
            })
            .cloned()
            .collect();
        if !hit.is_empty() {
            rows = hit;
        }
    }
    rows.truncate(limit);
    Ok(rows)
}

/// One source's request: `(query, limit) -> rows`. Named so the table below reads as a table.
pub type Fetcher = fn(&str, usize) -> Result<Vec<Row>, FetchError>;

/// The fetcher table: one name per source, `arxiv-api` an alias rather than a second call.
///
/// Lookup and call are separate on purpose. `--self-test` and the fixture suite check that every
/// declared name is in the table; if that check had to call the fetcher it would put thirteen
/// live requests in a test run, which is both slow and exactly the scraper habit this tool
/// exists not to have.
pub fn fetcher(name: &str) -> Option<Fetcher> {
    let f: Fetcher = match name {
        "wikipedia" => wikipedia,
        "openalex" => openalex,
        "crossref" => crossref,
        "arxiv" | "arxiv-api" => arxiv_api,
        "europepmc" => europepmc,
        "pubmed" => pubmed,
        "pypi" => pypi,
        "npm" => npm,
        "crates" => crates,
        "devto" => devto,
        "wayback" => wayback,
        "googlenews" => googlenews,
        "bbc" => bbc,
        _ => return None,
    };
    Some(f)
}

/// The one request for a named source.
pub fn fetch(name: &str, query: &str, limit: usize) -> Option<Result<Vec<Row>, FetchError>> {
    fetcher(name).map(|f| f(query, limit))
}

/// The freshness merge, pure: drop rows with no date, apply the floor, dedupe, newest first.
///
/// Split out of [`fresh`] because it is the part with a rule in it, and a rule that can only be
/// reached through two live feeds is a rule nobody will test twice.
pub fn merge_fresh(rows: Vec<Row>, limit: usize, since: &str) -> Vec<Row> {
    let mut seen = std::collections::HashSet::new();
    let mut merged: Vec<Row> = Vec::new();
    for row in rows {
        let Some(published) = row.published.clone().filter(|p| !p.is_empty()) else {
            continue;
        };
        if !since.is_empty() && published.as_str() < since {
            continue;
        }
        let key = row
            .url
            .split('#')
            .next()
            .unwrap_or("")
            .trim_end_matches('/')
            .to_string();
        if !seen.insert(key) {
            continue;
        }
        merged.push(row);
    }
    merged.sort_by(|a, b| b.published.cmp(&a.published));
    merged.truncate(limit);
    merged
}

/// One feed the caller named: `rss:<url>`, parsed with the same RSS/Atom reader the news
/// sources use, and cut to `limit`. The Python has no such source; this is the smallest way to
/// let a caller point the tool at a feed the tables have never heard of, and it is one request.
pub fn rss_url(url: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let resp = net::http(url, None, None, net::TIMEOUT)?;
    let mut rows = parse_rss(&resp.body);
    rows.truncate(limit);
    Ok(rows)
}

/// The freshness sources, merged and sorted by publication date, newest first.
///
/// `searx` is the callable that answers the SearXNG `news` category, injected so this module does
/// not import the search backend and a box without SearXNG still runs `--fresh`.
pub fn fresh<F>(query: &str, limit: usize, since: &str, searx: Option<F>, verbose: bool) -> Vec<Row>
where
    F: Fn(&str, usize) -> Vec<Row>,
{
    let mut rows: Vec<Row> = Vec::new();
    for name in FRESH_SOURCES {
        match fetch(name, query, limit) {
            Some(Ok(mut got)) => rows.append(&mut got),
            Some(Err(e)) if verbose => eprintln!("fresh: {}: {}", name, e),
            _ => {}
        }
    }
    if let Some(f) = searx {
        rows.extend(f(query, limit));
    }
    merge_fresh(rows, limit, since)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn v(text: &str) -> Value {
        serde_json::from_str(text).unwrap()
    }

    #[test]
    fn wikipedia_strips_the_highlight_and_builds_the_url() {
        let doc = v(r#"{"query":{"search":[{"title":"Transformer (deep learning)",
            "snippet":"a family of <span class=\"searchmatch\">transformer</span> models"}]}}"#);
        let rows = parse_wikipedia(&doc);
        assert_eq!(rows[0].url, "https://en.wikipedia.org/wiki/Transformer_(deep_learning)");
        assert!(!rows[0].snippet.contains("span"));
        assert!(rows[0].published.is_none(), "an article has no publication date");
    }

    #[test]
    fn openalex_keeps_the_year_in_the_snippet_only() {
        let doc = v(r#"{"results":[{"display_name":"The Heroes of CRISPR",
            "doi":"https://doi.org/10.1016/j.cell.2015.12.041","publication_year":2016,
            "cited_by_count":542,"best_oa_location":{"source":{"display_name":"Cell"}}}]}"#);
        let row = &parse_openalex(&doc)[0];
        assert_eq!(row.url, "https://doi.org/10.1016/j.cell.2015.12.041");
        assert!(row.snippet.contains("542 citations"));
        assert!(row.snippet.contains("Cell"));
        assert!(row.published.is_none());
        assert!(row.snippet.contains("2016"));
    }

    #[test]
    fn crossref_carries_the_issued_date_and_drops_a_titleless_item() {
        let doc = v(r#"{"message":{"items":[{"title":["A paper"],"DOI":"10.1/x",
            "URL":"https://doi.org/10.1/x","container-title":["Journal of Tests"],
            "is-referenced-by-count":7,"issued":{"date-parts":[[2020,10,1]]}}]}}"#);
        let row = &parse_crossref(&doc)[0];
        assert_eq!(row.title, "A paper");
        assert_eq!(row.published.as_deref(), Some("2020-10-01"));
        assert!(row.snippet.contains("Journal of Tests"));
        let empty = v(r#"{"message":{"items":[{"DOI":"10.1/x"}]}}"#);
        assert!(parse_crossref(&empty).is_empty());
    }

    #[test]
    fn arxiv_api_keeps_published_and_flattens_the_summary() {
        let atom = r#"<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All You Need</title>
    <summary> The dominant sequence transduction models are based on complex recurrent or
convolutional neural networks. </summary>
  </entry>
</feed>"#;
        let row = &parse_arxiv_api(atom)[0];
        assert_eq!(row.published.as_deref(), Some("2017-06-12"));
        assert!(!row.snippet.contains('\n'));
        assert_eq!(row.url, "http://arxiv.org/abs/1706.03762v7");
    }

    #[test]
    fn europepmc_prefers_the_doi_then_the_pmid() {
        let doc = v(r#"{"resultList":{"result":[{"title":"With DOI","doi":"10.1/a","journalTitle":"J"},
            {"title":"No DOI","pmid":"123","journalTitle":"J"}]}}"#);
        let rows = parse_europepmc(&doc);
        assert_eq!(rows[0].url, "https://doi.org/10.1/a");
        assert_eq!(rows[1].url, "https://pubmed.ncbi.nlm.nih.gov/123/");
    }

    #[test]
    fn pubmed_keeps_uid_order_and_reads_both_date_shapes() {
        let doc = v(r#"{"result":{"uids":["2","1"],
            "2":{"title":"Second.","fulljournalname":"J Two","pubdate":"2026 Nov 13"},
            "1":{"title":"First.","source":"J One","pubdate":"2026 Nov"}}}"#);
        let rows = parse_pubmed(&doc);
        assert_eq!(rows[0].title, "Second");
        assert_eq!(rows[1].title, "First");
        assert_eq!(rows[0].published.as_deref(), Some("2026-11-13"));
        assert_eq!(rows[1].published.as_deref(), Some("2026-11-01"));
        assert!(parse_pubmed(&v(r#"{"result":{"uids":["1"],"1":{"title":""}}}"#)).is_empty());
    }

    #[test]
    fn pypi_reports_the_release_and_its_date() {
        let doc = v(r#"{"info":{"name":"requests","version":"2.34.2",
            "summary":"Python HTTP for Humans.","requires_python":">=3.10",
            "project_url":"https://pypi.org/project/requests/"},
            "releases":{"2.34.2":[{"upload_time_iso_8601":"2026-05-14T19:25:26.443000Z"}]}}"#);
        let row = &parse_pypi(&doc)[0];
        assert_eq!(row.title, "requests");
        assert!(row.snippet.contains("2.34.2"));
        assert_eq!(row.published.as_deref(), Some("2026-05-14"));
    }

    #[test]
    fn npm_flags_a_deprecated_package() {
        let doc = v(r#"{"name":"old-thing","version":"1.0.0","deprecated":"use new-thing"}"#);
        assert!(parse_npm(&doc)[0].snippet.contains("DEPRECATED"));
    }

    #[test]
    fn crates_reports_downloads_and_a_yanked_latest() {
        let doc = v(r#"{"crate":{"name":"serde","max_version":"1.0.229",
            "description":"A generic serialization framework","recent_downloads":434411314,
            "updated_at":"2026-07-18T23:05:13Z","repository":"https://github.com/serde-rs/serde"},
            "versions":[{"num":"1.0.229","yanked":true}]}"#);
        let row = &parse_crates(&doc)[0];
        assert!(row.snippet.contains("downloads (90d)"));
        assert!(row.snippet.contains("yanked"));
        assert_eq!(row.url, "https://github.com/serde-rs/serde");
    }

    #[test]
    fn devto_carries_tags_and_reading_time() {
        let doc = v(r#"[{"title":"Follow a live blockchain","url":"https://dev.to/x/y",
            "published_at":"2026-11-12T21:50:21Z","reading_time_minutes":4,
            "tag_list":["python","asyncio"]}]"#);
        let row = &parse_devto(&doc)[0];
        assert_eq!(row.published.as_deref(), Some("2026-11-12"));
        assert!(row.snippet.contains("python"));
        assert!(row.snippet.contains("4 min read"));
    }

    #[test]
    fn wayback_skips_the_header_row_and_uses_id() {
        let doc = v(r#"[["timestamp","original","statuscode"],
            ["20261113195909","https://example.com/","200"]]"#);
        let row = &parse_wayback(&doc)[0];
        assert!(row.url.contains("/20261113195909id_/"));
        assert_eq!(row.published.as_deref(), Some("2026-11-13"));
    }

    const RSS: &str = r#"<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Story one - Outlet</title><link>https://ex.com/1</link>
<pubDate>Sat, 14 Nov 2026 19:43:32 GMT</pubDate>
<description>&lt;a&gt;Story one&lt;/a&gt; Outlet</description><source>Outlet</source></item>
<item><title>Old story</title><link>https://ex.com/2</link>
<pubDate>Mon, 02 Jan 2026 10:00:00 GMT</pubDate><description>text</description></item>
</channel></rss>"#;

    #[test]
    fn rss_dates_become_iso_and_the_outlet_is_not_repeated() {
        let rows = parse_rss(RSS);
        assert_eq!(rows[0].published.as_deref(), Some("2026-11-14"));
        assert_eq!(rows[1].published.as_deref(), Some("2026-01-02"));
        assert_eq!(rows[0].title, "Story one");
        assert_eq!(rows[0].snippet, "Outlet");
    }

    #[test]
    fn an_atom_feed_reads_the_same_way_and_broken_xml_is_empty() {
        let atom = r#"<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom item</title><link href="https://ex.com/a"/><published>2026-03-04T00:00:00Z</published>
<summary>body</summary></entry></feed>"#;
        let row = &parse_rss(atom)[0];
        assert_eq!(row.url, "https://ex.com/a");
        assert_eq!(row.published.as_deref(), Some("2026-03-04"));
        assert!(parse_rss("<rss><channel><item>").is_empty());
    }

    #[test]
    fn every_declared_source_has_a_fetcher_and_the_help_lists_it() {
        let help = sources_help();
        for name in API_SOURCES {
            assert!(fetcher(name).is_some(), "{} has no fetcher", name);
            if name != "arxiv-api" {
                assert!(help.contains(name), "{} is missing from the help", name);
            }
        }
    }

    #[test]
    fn the_fresh_merge_sorts_by_date_and_drops_undated_rows() {
        let rows = vec![
            Row::dated("old", "https://a/1", "", "2026-11-01"),
            Row::dated("new", "https://b/2", "", "2026-11-14"),
            Row::raw("undated", "https://c/3", ""),
        ];
        let got = merge_fresh(rows, 5, "");
        assert_eq!(
            got.iter().map(|r| r.title.as_str()).collect::<Vec<_>>(),
            vec!["new", "old"]
        );
    }

    #[test]
    fn the_fresh_merge_applies_the_since_floor_and_dedupes_urls() {
        let rows = vec![
            Row::dated("dated", "https://a/1", "", "2026-11-10"),
            Row::dated("same url", "https://a/1#frag", "", "2026-11-11"),
            Row::dated("too old", "https://a/2", "", "2026-11-01"),
        ];
        // First occurrence wins, the same as the Python: the merge is first-seen-wins on the
        // url before it is sorted, so a fragment cannot smuggle a second copy in.
        let got = merge_fresh(rows.clone(), 5, "2026-11-01");
        assert_eq!(
            got.iter().map(|r| r.title.as_str()).collect::<Vec<_>>(),
            vec!["dated", "too old"]
        );
        // The later copy is the one that survives the floor, and it arrives after the first
        // copy was dropped for being too old - the url is still only seen once.
        let late = merge_fresh(rows.clone(), 5, "2026-11-11");
        assert_eq!(late.len(), 1);
        assert_eq!(late[0].title, "same url");
        assert!(merge_fresh(rows, 5, "2026-11-15").is_empty());
    }

    #[test]
    fn iso_dates_read_the_shapes_the_apis_send() {
        assert_eq!(iso_date("2026-11-10T21:50:21Z"), "2026-11-10");
        assert_eq!(iso_date("2026/11/10"), "2026-11-10");
        assert_eq!(iso_date("2016"), "");
    }
}
