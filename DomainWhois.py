"""Extract domain from URL and resolve registration / creation date via WHOIS."""
from __future__ import annotations

import io
import logging
import re
import subprocess
from contextlib import redirect_stderr, redirect_stdout
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


def _to_idna(domain: str) -> Optional[str]:
    try:
        return domain.encode("idna").decode("ascii")
    except Exception:
        return None


def _extract_created_from_whois_result(w) -> Optional[date]:
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


def _query_whois_server(domain: str, server: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["whois", "-h", server, domain],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    out = result.stdout or ""
    return out if out.strip() else None


def _extract_created_from_text(raw: str) -> Optional[date]:
    # Handles formats like:
    # created:       2016-07-28T07:21:18Z
    # Creation Date: 1995-08-14T04:00:00Z
    patterns = [
        r"(?im)^\s*created\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"(?im)^\s*creation date\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"(?im)^\s*registered on\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
    ]
    for pattern in patterns:
        m = re.search(pattern, raw)
        if m:
            return _coerce_to_date(m.group(1))
    return None


def get_domain_created_date(url: str) -> Optional[date]:
    """
    Return the domain registration / creation date from WHOIS, or None if unavailable.
    Network failures and unsupported TLDs are swallowed (logged at warning).
    """
    domain = extract_domain_from_url(url)
    if not domain:
        return None

    # Try punycode first for IDN domains like *.рф, then fallback to original.
    candidates = []
    idna_domain = _to_idna(domain)
    if idna_domain:
        candidates.append(idna_domain)
    if domain not in candidates:
        candidates.append(domain)

    last_error: Optional[Exception] = None
    for d in candidates:
        try:
            sink = io.StringIO()
            with redirect_stdout(sink), redirect_stderr(sink):
                w = whois.whois(d)
            parsed = _extract_created_from_whois_result(w)
            if parsed is not None:
                return parsed
        except Exception as exc:
            last_error = exc
            continue

    # Fallback for TCI zones (.ru / .рф): direct query to whois.tcinet.ru.
    # This path works in environments where python-whois socket flow fails.
    tci_candidate = idna_domain or domain
    if tci_candidate.endswith((".ru", ".xn--p1ai")):
        raw = _query_whois_server(tci_candidate, "whois.tcinet.ru")
        if raw:
            parsed = _extract_created_from_text(raw)
            if parsed is not None:
                return parsed
    if last_error is not None:
        logger.warning(
            "WHOIS lookup failed for %s (candidates=%s): %s",
            domain,
            candidates,
            last_error,
        )
    return None
