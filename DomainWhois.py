"""Extract domain from URL and resolve registration / creation date via WHOIS."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional
from urllib.parse import urlparse

import whois

logger = logging.getLogger(__name__)


def extract_domain_from_url(url: str) -> Optional[str]:
    if not url or not str(url).strip():
        return None
    u = str(url).strip()
    if not u.startswith(("http://", "https://")):
        u = "http://" + u
    try:
        parsed = urlparse(u)
    except Exception:
        return None
    host = parsed.netloc or (parsed.path.split("/")[0] if parsed.path else "")
    if not host:
        return None
    host = host.split("@")[-1]
    host = host.split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _coerce_to_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        s = value.strip()
        for fmt, n in (
            ("%Y-%m-%d", 10),
            ("%d-%b-%Y", 11),
            ("%d/%m/%Y", 10),
        ):
            try:
                return datetime.strptime(s[:n], fmt).date()
            except ValueError:
                continue
    return None


def get_domain_created_date(url: str) -> Optional[date]:
    """
    Return the domain registration / creation date from WHOIS, or None if unavailable.
    Network failures and unsupported TLDs are swallowed (logged at warning).
    """
    domain = extract_domain_from_url(url)
    if not domain:
        return None
    try:
        w = whois.whois(domain)
    except Exception as exc:
        logger.warning("WHOIS lookup failed for %s: %s", domain, exc)
        return None
    if w is None:
        return None
    created = getattr(w, "creation_date", None)
    if created is None and isinstance(w, dict):
        created = w.get("creation_date")
    dt = _coerce_to_date(created)
    if dt is not None:
        return dt
    # Some responses only expose registration in 'registered' or similar
    alt = getattr(w, "registered", None)
    if alt is None and isinstance(w, dict):
        alt = w.get("registered")
    return _coerce_to_date(alt)
