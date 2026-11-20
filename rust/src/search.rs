//! The structured endpoints: GitHub, Stack Overflow, Hacker News, arXiv's Atom feed, Discourse.
//!
//! Every parser here is pure - a `serde_json::Value` or a feed string in, rows out - so the
//! fixture tests and `--self-test` exercise them with no network, which is the reason a parser
//! can be checked at all when the endpoint is having a bad afternoon.
//!
//! Row shape is `Row::raw`: these sources return what the page gave, and the renderer cuts it.

use serde_json::Value;

use crate::net::{self, FetchError};
use crate::row::Row;

const JSON_ACCEPT: &str = "application/json";
const GH_ACCEPT: &str = "application/vnd.github+json";

/// `https://api.github.com/search/repositories`: full name, stars, language.
pub fn parse_github_repos(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for it in doc.get("items").and_then(|v| v.as_array()).cloned().unwrap_or_default() {
        let mut bits: Vec<String> = Vec::new();
        if let Some(l) = it.get("language").and_then(|v| v.as_str()) {
            if !l.is_empty() {
                bits.push(l.to_string());
            }
        }
        if let Some(s) = it.get("stargazers_count") {
            if !s.is_null() {
                bits.push(format!("{} stars", js_num(s)));
            }
        }
        let desc = it.get("description").and_then(|v| v.as_str()).unwrap_or("");
        let snippet = if bits.is_empty() {
            desc.to_string()
        } else {
            format!("{} · {}", desc, bits.join(" · "))
        };
        out.push(Row::raw(
            it.get("full_name").and_then(|v| v.as_str()).unwrap_or(""),
            it.get("html_url").and_then(|v| v.as_str()).unwrap_or(""),
            &snippet,
        ));
    }
    out
}

/// `https://api.github.com/search/issues`: the row title carries `repo#number`.
pub fn parse_github_issues(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for it in doc.get("items").and_then(|v| v.as_array()).cloned().unwrap_or_default() {
        let repo_url = it.get("repository_url").and_then(|v| v.as_str()).unwrap_or("");
        let repo = repo_url.rsplit("/repos/").next().unwrap_or(repo_url);
        let number = it
            .get("number")
            .map(js_num)
            .unwrap_or_else(|| "?".to_string());
        let title = it.get("title").and_then(|v| v.as_str()).unwrap_or("");
        let body: String = it
            .get("body")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .chars()
            .take(crate::row::SNIPPET)
            .collect();
        out.push(Row::raw(
            &format!("{}#{} {}", repo, number, title),
            it.get("html_url").and_then(|v| v.as_str()).unwrap_or(""),
            &format!("{} · {}", it.get("state").and_then(|v| v.as_str()).unwrap_or(""), body),
        ));
    }
    out
}

/// `api.stackexchange.com`: score in the title, answered/open and the tags in the snippet.
pub fn parse_so(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for it in doc.get("items").and_then(|v| v.as_array()).cloned().unwrap_or_default() {
        let tags = it
            .get("tags")
            .and_then(|v| v.as_array())
            .map(|a| {
                a.iter()
                    .filter_map(|t| t.as_str())
                    .collect::<Vec<_>>()
                    .join(", ")
            })
            .unwrap_or_default();
        let score = it
            .get("score")
            .map(js_num)
            .unwrap_or_else(|| "None".to_string());
        let answered = it
            .get("is_answered")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let snip = if tags.is_empty() {
            if answered { "answered".to_string() } else { "open".to_string() }
        } else {
            format!("{} · {}", if answered { "answered" } else { "open" }, tags)
        };
        out.push(Row::raw(
            &format!(
                "{} (score {})",
                it.get("title").and_then(|v| v.as_str()).unwrap_or(""),
                score
            ),
            it.get("link").and_then(|v| v.as_str()).unwrap_or(""),
            &snip,
        ));
    }
    out
}

/// `hn.algolia.com`: the story's own url, or the discussion when it has none.
pub fn parse_hn(doc: &Value) -> Vec<Row> {
    let mut out = Vec::new();
    for it in doc.get("hits").and_then(|v| v.as_array()).cloned().unwrap_or_default() {
        let url = it
            .get("url")
            .and_then(|v| v.as_str())
            .filter(|u| !u.is_empty())
            .map(|u| u.to_string())
            .unwrap_or_else(|| {
                format!(
                    "https://news.ycombinator.com/item?id={}",
                    it.get("objectID").and_then(|v| v.as_str()).unwrap_or("")
                )
            });
        let title = it
            .get("title")
            .and_then(|v| v.as_str())
            .or_else(|| it.get("story_title").and_then(|v| v.as_str()))
            .unwrap_or("");
        out.push(Row::raw(
            title,
            &url,
            &format!(
                "{} points · {} comments",
                it.get("points").map(js_num).unwrap_or_else(|| "None".into()),
                it.get("num_comments").map(js_num).unwrap_or_else(|| "None".into())
            ),
        ));
    }
    out
}

/// `export.arxiv.org/api/query`: Atom, and this route drops `<published>` (the `arxiv-api`
/// keyless source is the one that keeps it, because a search result here is a paper, not a date).
pub fn parse_arxiv(xml_text: &str) -> Vec<Row> {
    let doc = match roxmltree::Document::parse(xml_text) {
        Ok(d) => d,
        Err(_) => return Vec::new(),
    };
    let mut out = Vec::new();
    for entry in doc.descendants().filter(|n| n.has_tag_name((ATOM, "entry"))) {
        let title = child_text(entry, "title");
        let id = child_text(entry, "id");
        let summary = child_text(entry, "summary");
        out.push(Row::raw(&squeeze(&title), id.trim(), &squeeze(&summary)));
    }
    out
}

/// `discourse:<base>/search.json`: the topics carry the titles, the posts carry the blurbs.
pub fn parse_discourse_search(doc: &Value, base: &str) -> Vec<Row> {
    let mut blurbs: std::collections::HashMap<String, String> = std::collections::HashMap::new();
    if let Some(posts) = doc.get("posts").and_then(|v| v.as_array()) {
        for p in posts {
            let topic = p.get("topic_id").map(js_num).unwrap_or_default();
            let blurb = p.get("blurb").and_then(|v| v.as_str()).unwrap_or("");
            if !topic.is_empty() && !blurb.is_empty() {
                blurbs.entry(topic).or_insert_with(|| blurb.to_string());
            }
        }
    }
    let mut out = Vec::new();
    if let Some(topics) = doc.get("topics").and_then(|v| v.as_array()) {
        for t in topics {
            let tid = t.get("id").map(js_num).unwrap_or_default();
            let own = t.get("blurb").and_then(|v| v.as_str()).unwrap_or("");
            let snippet = if own.is_empty() {
                blurbs.get(&tid).cloned().unwrap_or_default()
            } else {
                own.to_string()
            };
            out.push(Row::raw(
                t.get("title").and_then(|v| v.as_str()).unwrap_or(""),
                &format!("{}/t/{}", base.trim_end_matches('/'), tid),
                &snippet,
            ));
        }
    }
    out
}

// ------------------------------------------------------------------ the requests

pub fn gh_repos(query: &str, limit: usize) -> Result<(Vec<Row>, Option<String>), FetchError> {
    let url = format!(
        "https://api.github.com/search/repositories?per_page={}&q={}",
        limit,
        crate::util::quote_plus(query)
    );
    let resp = net::http(&url, None, Some(GH_ACCEPT), net::TIMEOUT)?;
    let doc: Value = serde_json::from_str(&resp.body)
        .map_err(|e| FetchError::new(format!("invalid JSON: {}", e)))?;
    Ok((parse_github_repos(&doc), resp.header("x-ratelimit-remaining")))
}

pub fn gh_issues(query: &str, limit: usize) -> Result<(Vec<Row>, Option<String>), FetchError> {
    let url = format!(
        "https://api.github.com/search/issues?per_page={}&q={}",
        limit,
        crate::util::quote_plus(query)
    );
    let resp = net::http(&url, None, Some(GH_ACCEPT), net::TIMEOUT)?;
    let doc: Value = serde_json::from_str(&resp.body)
        .map_err(|e| FetchError::new(format!("invalid JSON: {}", e)))?;
    Ok((parse_github_issues(&doc), resp.header("x-ratelimit-remaining")))
}

pub fn so_search(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&site=stackoverflow&pagesize={}&q={}",
        limit,
        crate::util::quote_plus(query)
    );
    let doc = net::get_json(&url, None, net::TIMEOUT)?;
    Ok(parse_so(&doc))
}

pub fn hn_search(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://hn.algolia.com/api/v1/search?hitsPerPage={}&query={}",
        limit,
        crate::util::quote_plus(query)
    );
    let doc = net::get_json(&url, None, net::TIMEOUT)?;
    Ok(parse_hn(&doc))
}

pub fn arxiv_search(query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "https://export.arxiv.org/api/query?max_results={}&search_query={}",
        limit,
        crate::util::quote(&format!("all:{}", query), "")
    );
    let resp = net::http(&url, None, None, net::TIMEOUT)?;
    Ok(parse_arxiv(&resp.body))
}

pub fn discourse_search(base: &str, query: &str, limit: usize) -> Result<Vec<Row>, FetchError> {
    let url = format!(
        "{}/search.json?q={}",
        base.trim_end_matches('/'),
        crate::util::quote_plus(query)
    );
    let doc = net::get_json(&url, Some(JSON_ACCEPT), net::TIMEOUT)?;
    let mut rows = parse_discourse_search(&doc, base);
    rows.truncate(limit);
    Ok(rows)
}

// ------------------------------------------------------------------ small helpers

const ATOM: &str = "http://www.w3.org/2005/Atom";

fn child_text(node: roxmltree::Node<'_, '_>, name: &str) -> String {
    node.children()
        .find(|c| c.has_tag_name((ATOM, name)))
        .and_then(|c| c.text())
        .unwrap_or("")
        .to_string()
}

fn squeeze(text: &str) -> String {
    text.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// A JSON number as text: no `.0` on an integer.
pub fn js_num(v: &Value) -> String {
    match v {
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                i.to_string()
            } else if let Some(f) = n.as_f64() {
                format!("{}", f)
            } else {
                n.to_string()
            }
        }
        Value::String(s) => s.clone(),
        other => other.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn github_repos_report_language_and_stars() {
        let doc: Value = serde_json::from_str(
            r#"{"total_count":1,"items":[{"full_name":"serengil/retinaface",
                "html_url":"https://github.com/serengil/retinaface","description":"RetinaFace in Keras",
                "stargazers_count":2100,"language":"Python"}]}"#,
        )
        .unwrap();
        let rows = parse_github_repos(&doc);
        assert_eq!(rows[0].url, "https://github.com/serengil/retinaface");
        assert!(rows[0].snippet.contains("Python") && rows[0].snippet.contains("2100 stars"));
    }

    #[test]
    fn github_issues_carry_repo_and_number_in_the_title() {
        let doc: Value = serde_json::from_str(
            r#"{"total_count":1,"items":[{"title":"How to drop frames",
                "html_url":"https://github.com/x/y/issues/12","number":12,"state":"open",
                "body":"body text","repository_url":"https://api.github.com/repos/x/y"}]}"#,
        )
        .unwrap();
        assert_eq!(parse_github_issues(&doc)[0].title, "x/y#12 How to drop frames");
    }

    #[test]
    fn so_marks_answered_and_keeps_the_tags() {
        let doc: Value = serde_json::from_str(
            r#"{"items":[{"title":"nvv4l2decoder drop-frame-interval",
                "link":"https://stackoverflow.com/q/1","tags":["python","gstreamer"],"score":5,
                "is_answered":true}]}"#,
        )
        .unwrap();
        let rows = parse_so(&doc);
        assert_eq!(rows[0].url, "https://stackoverflow.com/q/1");
        assert!(rows[0].snippet.contains("answered"));
        assert!(rows[0].title.contains("score 5"));
    }

    #[test]
    fn hn_falls_back_to_the_discussion_url() {
        let doc: Value = serde_json::from_str(
            r#"{"hits":[{"title":"A story","url":"https://example.com/s","objectID":"42",
                "points":10,"num_comments":3},{"title":"No link","objectID":"43","points":1,
                "num_comments":0}]}"#,
        )
        .unwrap();
        let rows = parse_hn(&doc);
        assert_eq!(rows[0].url, "https://example.com/s");
        assert_eq!(rows[1].url, "https://news.ycombinator.com/item?id=43");
    }

    #[test]
    fn arxiv_atom_is_flattened_and_has_no_date() {
        let xml = r#"<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1905.00641v1</id>
<title>RetinaFace: Single-stage Dense Face Localisation</title><summary>We present a face detector.</summary>
</entry></feed>"#;
        let rows = parse_arxiv(xml);
        assert_eq!(rows[0].url, "http://arxiv.org/abs/1905.00641v1");
        assert!(rows[0].title.starts_with("RetinaFace"));
        assert!(rows[0].published.is_none());
    }

    #[test]
    fn discourse_uses_the_blurb_from_the_matching_post() {
        let doc: Value = serde_json::from_str(
            r#"{"topics":[{"id":123456,"title":"NVStreammux live-source","posts_count":4}],
                "posts":[{"topic_id":123456,"blurb":"set live-source to 1"}]}"#,
        )
        .unwrap();
        let rows = parse_discourse_search(&doc, "https://forums.developer.nvidia.com");
        assert_eq!(rows[0].url, "https://forums.developer.nvidia.com/t/123456");
        assert_eq!(rows[0].snippet, "set live-source to 1");
    }
}
