//! `webscour` as a library, because the parsers are the part that deserves tests and the
//! binary is a thin argv reader over them.
//!
//! The module graph is one-way, the same one the Python keeps: `row` and `util` have no
//! dependencies, `net` depends on `util`, the parsers depend on `row` + `net`, and the CLI
//! depends on everything. Nothing here needs an async runtime: every command is one request in
//! front of a reader.

pub mod backends;
pub mod html;
pub mod net;
pub mod row;
pub mod search;
pub mod selftest;
pub mod sources;
pub mod util;

pub use row::Row;

/// The version the crate was built as, printed by `wsc --version`.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// The output helpers the renderer and the backend chain share.
pub fn render(rows: &[Row], json: bool) -> String {
    net::render(rows, json)
}
