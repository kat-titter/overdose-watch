#!/usr/bin/env python3
"""Check data/incidents.json and data/trend.json before publishing. Exits non-zero on any problem."""
import json, pathlib, sys
from schema import problems

ROOT = pathlib.Path(__file__).resolve().parent.parent
bad = 0
doc = json.loads((ROOT / "data" / "incidents.json").read_text())
ids, urls = set(), {}
for r in doc["incidents"]:
    for p in problems(r):
        print(f"{r.get('id', '?')}: {p}"); bad += 1
    if r.get("id") in ids:
        print(f"{r['id']}: duplicate id"); bad += 1
    ids.add(r.get("id"))
trend = json.loads((ROOT / "data" / "trend.json").read_text())
for s in trend["series"]:
    if len(s["points"]) < 24 or any(v <= 0 for _, v in s["points"]):
        print(f"trend {s['name']}: too few or non-positive points"); bad += 1
print(f"{len(doc['incidents'])} incidents, {len(trend['series'])} trend series: " + ("OK" if not bad else f"{bad} problems"))
sys.exit(1 if bad else 0)
