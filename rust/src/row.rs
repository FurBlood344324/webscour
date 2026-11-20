//! The row: the one shape every source produces and every renderer takes.
//!
//! `title`, `url`, `snippet` are always there; `published` only when the source really carries a
//! publication date; `engines` when a backend can say which upstream answered. Nothing invents a
//! date: a Wikipedia article has none, and its last-edit stamp is not one.
//!
//! Two clipping styles live here on purpose, and both are visible in the output: the keyless
//! sources cut a snippet with `...` at parse time (`clip_dots`), while the renderer cuts with
//! `…` (`clip_ellipsis`). Same length, different mark, and a caller comparing two rows would
//! see it.

use serde_json::{Map, Value};

/// A snippet is cut at parse time, so every source yields rows of the same size.
pub const SNIPPET: usize = 200;

#[derive(Debug, Clone, Default, PartialEq)]
pub struct Row {
    pub title: String,
    pub url: String,
    pub snippet: String,
    pub published: Option<String>,
    pub engines: Vec<String>,
}

impl Row {
    /// A keyless-source row: clipped the way `sources._row` clips.
    pub fn new(title: &str, url: &str, snippet: &str) -> Row {
        Row {
            title: clip_dots(title, 300),
            url: url.to_string(),
            snippet: clip_dots(snippet, SNIPPET),
            published: None,
            engines: Vec::new(),
        }
    }

    /// A backend-parser row (SearXNG, DDG, Bing, GitHub, SO, HN, arXiv, Discourse): these return
    /// the text as the page gave it, and the renderer is what cuts it.
    pub fn raw(title: &str, url: &str, snippet: &str) -> Row {
        Row {
            title: title.to_string(),
            url: url.to_string(),
            snippet: snippet.to_string(),
            published: None,
            engines: Vec::new(),
        }
    }

    /// A keyless-source row that carries a real publication date.
    pub fn dated(title: &str, url: &str, snippet: &str, published: &str) -> Row {
        let mut r = Row::new(title, url, snippet);
        if !published.is_empty() {
            r.published = Some(published.to_string());
        }
        r
    }

    pub fn with_engines(mut self, engines: Vec<String>) -> Row {
        self.engines = engines;
        self
    }

    /// The output row, exactly the keys `--json` prints.
    pub fn to_json(&self) -> Value {
        let mut m = Map::new();
        // Insertion order is the renderer's: title, url, snippet, engines, published.
        m.insert("title".into(), Value::String(self.title.clone()));
        m.insert("url".into(), Value::String(self.url.clone()));
        m.insert(
            "snippet".into(),
            Value::String(clip_ellipsis(&self.snippet, SNIPPET)),
        );
        m.insert(
            "engines".into(),
            Value::Array(
                self.engines
                    .iter()
                    .filter(|e| !e.is_empty())
                    .cloned()
                    .map(Value::String)
                    .collect(),
            ),
        );
        if let Some(p) = &self.published {
            if !p.is_empty() {
                m.insert("published".into(), Value::String(p.clone()));
            }
        }
        Value::Object(m)
    }
}

/// Collapse whitespace, then cut at `n` characters with a single `…`.
pub fn clip_ellipsis(text: &str, n: usize) -> String {
    let joined = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let chars: Vec<char> = joined.chars().collect();
    if chars.len() <= n {
        return joined;
    }
    let head: String = chars[..n.saturating_sub(1)].iter().collect();
    format!("{}…", head.trim_end())
}

/// Collapse whitespace, then cut at `n` characters with `...`.
pub fn clip_dots(text: &str, n: usize) -> String {
    let joined = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let chars: Vec<char> = joined.chars().collect();
    if chars.len() <= n {
        return joined;
    }
    let head: String = chars[..n.saturating_sub(1)].iter().collect();
    format!("{}...", head.trim_end())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clip_joins_whitespace_and_cuts_with_three_dots() {
        assert_eq!(clip_dots(" a \n b ", 10), "a b");
        assert_eq!(clip_dots("abcdefgh", 5), "abcd...");
    }

    #[test]
    fn an_empty_date_is_no_date() {
        let r = Row::dated("t", "u", "s", "");
        assert!(r.published.is_none());
        assert!(r.to_json().get("published").is_none());
    }

    #[test]
    fn raw_rows_are_not_clipped_and_source_rows_are() {
        let long = "x".repeat(400);
        assert_eq!(Row::raw(&long, "u", &long).title.chars().count(), 400);
        // `clip_dots(text, 300)` keeps 299 characters and then `...`, so the row is 302
        // characters wide before the renderer cuts it to 200. That is the clipping rule, not a
        // rounding mistake here.
        let clipped = Row::new(&long, "u", &long);
        assert_eq!(clipped.title.chars().count(), 302);
        assert_eq!(clipped.snippet.chars().count(), 202);
    }
}
