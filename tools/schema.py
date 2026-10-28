"""Shared rules for data/incidents.json (used by validate.py and add_incidents.py). Every report counts deaths."""
import datetime, re

REQUIRED = ["id", "date", "datePrec", "title", "place", "region", "geo", "lat", "lon", "kind", "subs", "molecules",
            "deaths", "summary", "source", "url", "added", "via"]
ENUMS = {"datePrec": {"day", "month", "year"}, "region": {"Bay Area", "California", "Nevada", "US"},
         "geo": {"city", "county", "site", "region", "state", "nation"},
         "kind": {"death", "cluster", "data"}}
SUBS = {"fentanyl", "carfentanil", "cychlorphine", "nitazenes", "bromazolam", "medetomidine", "xylazine", "all"}


def problems(row):
    """Return a list of human-readable problems with one incident (empty when it is valid)."""
    out = [f"missing {k}" for k in REQUIRED if k not in row]
    if out:
        return out
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,59}", row["id"]):
        out.append("id must be lowercase letters, digits and hyphens, 3-60 chars")
    for k in ("date", "added"):
        try:
            datetime.date.fromisoformat(row[k])
        except (TypeError, ValueError):
            out.append(f"{k} must be YYYY-MM-DD")
    for k, allowed in ENUMS.items():
        if row[k] not in allowed:
            out.append(f"{k} must be one of {sorted(allowed)}")
    if not isinstance(row["subs"], list) or not row["subs"] or not set(row["subs"]) <= SUBS:
        out.append(f"subs must be a non-empty list from {sorted(SUBS)}")
    if not (isinstance(row["lat"], (int, float)) and -90 <= row["lat"] <= 90 and isinstance(row["lon"], (int, float)) and -180 <= row["lon"] <= 180):
        out.append("lat/lon must be numbers")
    if not (isinstance(row["deaths"], int) and row["deaths"] >= 1):
        out.append("deaths must be the death count the source states (a whole number, 1 or more)")
    if not (isinstance(row["url"], str) and row["url"].startswith(("https://", "http://"))):
        out.append("url must be the source link (every report needs a citation)")
    for k, n in (("title", 90), ("summary", 320), ("source", 80), ("place", 80)):
        if not isinstance(row[k], str) or not row[k].strip() or len(row[k]) > n:
            out.append(f"{k} must be text of at most {n} characters")
    return out


def tidy(rows):
    """Newest first, then by id, with keys in schema order."""
    rows = sorted(rows, key=lambda r: r["id"])
    rows.sort(key=lambda r: r["date"], reverse=True)
    return [{k: r[k] for k in REQUIRED} for r in rows]
