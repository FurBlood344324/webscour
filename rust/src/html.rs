//! The scraped result pages: DuckDuckGo lite, DuckDuckGo html, Bing.
//!
//! Each is one DOM pass with a selector per field. With a real HTML5 parser a selector says what
//! a hand-written token stream would and says it in one line, which is the point of paying for the
//! dependency. The pairing rule: a snippet belongs to the last title seen, and a row without both
//! a title and a url is dropped.

use scraper::{ElementRef, Html, Selector};

use crate::net::append_text;
use crate::row::Row;

/// Text of an element, with inline fragments joined the way a reader sees them.
///
/// Every text node is squeezed on its own and then folded with [`append_text`], which is what
/// keeps `Some <b>snippet</b>.` from becoming `Some snippet .` and `Snippet <b>text</b> here.`
/// from becoming a double space.
pub fn text_of(el: ElementRef<'_>) -> String {
    let mut parts: Vec<String> = Vec::new();
    collect_parts(el, &mut parts);
    let mut out = String::new();
    for p in parts {
        out = append_text(out.trim_end(), &p);
    }
    out.trim().to_string()
}

fn skipped(name: &str) -> bool {
    matches!(name, "script" | "style" | "noscript" | "template")
}

fn collect_parts(el: ElementRef<'_>, parts: &mut Vec<String>) {
    for child in el.children() {
        if let Some(t) = child.value().as_text() {
            let squeezed = t.split_whitespace().collect::<Vec<_>>().join(" ");
            if !squeezed.is_empty() {
                parts.push(squeezed);
            }
        } else if let Some(e) = ElementRef::wrap(child) {
            if skipped(e.value().name()) {
                continue;
            }
            collect_parts(e, parts);
        }
    }
}

fn sel(css: &str) -> Selector {
    Selector::parse(css).expect("static selector")
}

/// All elements matching `css`, in document order.
fn all<'a>(doc: &'a Html, css: &str) -> Vec<ElementRef<'a>> {
    let s = sel(css);
    doc.select(&s).collect()
}

fn finish(mut rows: Vec<Row>) -> Vec<Row> {
    for r in &mut rows {
        r.title = r.title.trim().to_string();
        r.snippet = r.snippet.trim().to_string();
        r.url = r.url.trim().to_string();
    }
    rows.retain(|r| !r.title.is_empty() && !r.url.is_empty());
    rows
}

/// `lite.duckduckgo.com/lite/`: a table, one `a.result-link` per row, one `td.result-snippet`.
pub fn parse_ddg_lite(page: &str) -> Vec<Row> {
    let doc = Html::parse_document(page);
    let titles = all(&doc, "a.result-link");
    let snippets = all(&doc, "td.result-snippet");
    let mut rows = Vec::new();
    for (i, a) in titles.iter().enumerate() {
        let mut row = Row::raw(
            &text_of(*a),
            &crate::net::unwrap_url(a.value().attr("href").unwrap_or("")),
            "",
        );
        if let Some(s) = snippets.get(i) {
            row.snippet = text_of(*s);
        }
        rows.push(row);
    }
    finish(rows)
}

/// `html.duckduckgo.com/html/`: each result is a container with its own title anchor and its
/// own snippet anchor.
///
/// Scoped to the container rather than to two flat lists, because a result with no snippet
/// would otherwise hand its snippet to the next row - a flat pass that pairs by "last title
/// seen" gets the same answer only while every row has both halves. The flat pairing
/// is kept as the fallback for a page shape with no `div.result`.
pub fn parse_ddg_html(page: &str) -> Vec<Row> {
    let doc = Html::parse_document(page);
    let a_sel = sel("a.result__a");
    let s_sel = sel(".result__snippet");
    let mut rows = Vec::new();
    for block in all(&doc, "div.result") {
        let Some(a) = block.select(&a_sel).next() else {
            continue;
        };
        let mut row = Row::raw(
            &text_of(a),
            &crate::net::unwrap_url(a.value().attr("href").unwrap_or("")),
            "",
        );
        if let Some(s) = block.select(&s_sel).next() {
            row.snippet = text_of(s);
        }
        rows.push(row);
    }
    if rows.is_empty() {
        // No container: fall back to document order.
        let titles: Vec<Row> = all(&doc, "a.result__a")
            .into_iter()
            .map(|a| {
                Row::raw(
                    &text_of(a),
                    &crate::net::unwrap_url(a.value().attr("href").unwrap_or("")),
                    "",
                )
            })
            .collect();
        rows = titles;
        for (i, s) in all(&doc, ".result__snippet").iter().enumerate() {
            if let Some(r) = rows.get_mut(i) {
                r.snippet = text_of(*s);
            }
        }
    }
    finish(rows)
}

/// Bing: `<li class=b_algo><h2><a href>Title</a></h2><p>snippet</p>`.
pub fn parse_bing(page: &str) -> Vec<Row> {
    let doc = Html::parse_document(page);
    let mut rows = Vec::new();
    let blocks = all(&doc, "li.b_algo");
    let scoped: Vec<scraper::ElementRef> = if blocks.is_empty() {
        // Some Bing shapes drop the class and keep the list; the anchor inside an h2 is the
        // constant, so it is the fallback rather than an empty answer.
        all(&doc, "h2 a[href^=\"http\"]")
            .into_iter()
            .collect()
    } else {
        blocks
    };
    for b in scoped {
        let anchor = if b.value().name() == "a" {
            Some(b)
        } else {
            let s = sel("h2 a[href^=\"http\"]");
            b.select(&s).next()
        };
        let Some(a) = anchor else { continue };
        let mut row = Row::raw(
            &text_of(a),
            &crate::net::unwrap_url(a.value().attr("href").unwrap_or("")),
            "",
        );
        if b.value().name() != "a" {
            let ps = sel("p");
            if let Some(p) = b.select(&ps).next() {
                row.snippet = text_of(p);
            }
        }
        rows.push(row);
    }
    finish(rows)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ddg_lite_pairs_title_and_snippet_and_fixes_the_scheme() {
        let page = r#"<html><body><table>
<tr><td>1.</td><td><a rel="nofollow" href="https://example.com/a" class="result-link">RetinaFace detector</a></td></tr>
<tr><td>&nbsp;</td><td class="result-snippet">A <b>single-stage</b> face detector.</td></tr>
<tr><td>2.</td><td><a rel="nofollow" href="//example.com/b" class="result-link">Second hit</a></td></tr>
<tr><td>&nbsp;</td><td class="result-snippet">Other snippet.</td></tr>
</table></body></html>"#;
        let rows = parse_ddg_lite(page);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].title, "RetinaFace detector");
        assert_eq!(rows[0].url, "https://example.com/a");
        assert!(rows[0].snippet.contains("single-stage"), "{}", rows[0].snippet);
        assert_eq!(rows[1].url, "https://example.com/b");
    }

    #[test]
    fn a_snippetless_result_does_not_steal_the_next_snippet() {
        let page = r#"<html><body>
<div class="result"><h2><a class="result__a" href="https://a/1">One</a></h2></div>
<div class="result"><h2><a class="result__a" href="https://a/2">Two</a></h2>
<a class="result__snippet">Second only</a></div></body></html>"#;
        let rows = parse_ddg_html(page);
        assert_eq!(rows[0].snippet, "");
        assert_eq!(rows[1].snippet, "Second only");
    }

    #[test]
    fn ddg_html_unwraps_the_redirect() {
        let page = r#"<html><body><div class="result results_links">
<h2 class="result__title"><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fx&amp;rut=1">Example title</a></h2>
<a class="result__snippet" href="https://example.org/x">Snippet <b>text</b> here.</a></div></body></html>"#;
        let rows = parse_ddg_html(page);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].title, "Example title");
        assert_eq!(rows[0].url, "https://example.org/x");
        assert_eq!(rows[0].snippet, "Snippet text here.");
    }

    #[test]
    fn bing_reads_the_anchor_in_the_heading_and_the_paragraph_below() {
        let page = r#"<html><body><ol id="b_results"><li class="b_algo"><h2><a href="https://example.net/b">Bing hit</a></h2>
<div class="b_caption"><p>Some <b>snippet</b>.</p></div></li>
<li class="b_algo"><h2><a href="https://example.net/c">Second bing</a></h2><p>More.</p></li></ol></body></html>"#;
        let rows = parse_bing(page);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].title, "Bing hit");
        assert_eq!(rows[0].url, "https://example.net/b");
        assert!(rows[0].snippet.contains("Some snippet."), "{:?}", rows[0].snippet);
    }
}
