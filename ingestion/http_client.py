"""One place for HTTP downloads: timeouts, retries with backoff, and clear errors."""

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ingestion import config

log = logging.getLogger(__name__)


def make_session() -> requests.Session:
    # Retry on connection errors and on "busy" or server errors. backoff_factor=1 waits
    # roughly 1s, 2s, 4s between attempts, which is polite to free public APIs.
    retry = Retry(
        total=config.HTTP_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "industrial-input-cost-monitor (portfolio project)"
    return session


def fetch_bytes(session: requests.Session, url: str, params: dict | None = None) -> bytes:
    log.info("GET %s params=%s", url, params)
    response = session.get(url, params=params, timeout=config.HTTP_TIMEOUT_SECONDS)
    # Fail loudly on 4xx/5xx instead of saving an error page as if it were data
    response.raise_for_status()
    log.info("received %d bytes", len(response.content))
    return response.content
