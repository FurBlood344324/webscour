"""Granian entrypoint for the local SearXNG: searx.webapp plus one policy.

SearXNG logs the *outgoing request URL* at WARNING from ``searx.network.<engine>``, and that
URL carries the query text. The access log is already off and the level is WARNING, but a
warning about a suspended engine still writes ``...?q=<the user's query>`` into the journal.
Here every log record is filtered before it reaches a handler: every URL query string in a record is replaced by a placeholder, so the journal keeps the operational warnings and none of the
queries. This file is installed by websearch-searx/install.sh, outside the pinned checkout.
"""

import logging
import re

import searx.webapp as _webapp

_URL_QUERY = re.compile(r"(https?://[^\s?]+)\?\S*")


class _NoQueryText(logging.Filter):
    """Redact the query string of any URL a record quotes (host kept, so the warning stays useful)."""

    def filter(self, record):
        try:
            msg = record.getMessage()
        except Exception:  # a broken format string must not silence the record
            return True
        if "?" not in msg:
            return True
        # Engines name the parameter q, query, text, p, wd...: redact every URL query string.
        record.msg = _URL_QUERY.sub(r"\1?<query withheld>", msg)
        record.args = ()
        return True


_FILTER = _NoQueryText()
for _logger in [logging.getLogger()] + [
    logging.getLogger(name)
    for name in ("searx", "searx.network", "searx.search", "searx.webapp", "granian")
]:
    _logger.addFilter(_FILTER)
    for _handler in _logger.handlers:
        _handler.addFilter(_FILTER)

app = _webapp.app
