#!/usr/bin/env python3
"""Merge new reports into data/incidents.json.

usage: python3 tools/add_incidents.py new.json
new.json holds a JSON list of incidents (same fields as data/incidents.json). Each is validated; one whose id
or url is already tracked is skipped and reported. Nothing is written if any new report is invalid.
"""
import datetime, json, pathlib, sys
from schema import problems, tidy

ROOT = pathlib.Path(__file__).resolve().parent.parent
path = ROOT / "data" / "incidents.json"
doc = json.loads(path.read_text())
new = json.loads(pathlib.Path(sys.argv[1]).read_text())
have_ids = {r["id"] for r in doc["incidents"]}
have_urls = {r["url"] for r in doc["incidents"]}
errors, added = [], []
for r in new:
    p = problems(r)
    if p:
        errors.append(f"{r.get('id', '?')}: " + "; ".join(p)); continue
    if r["id"] in have_ids or r["url"] in have_urls:
        print(f"skip (already tracked): {r['id']}"); continue
    added.append(r); have_ids.add(r["id"]); have_urls.add(r["url"])
if errors:
    print("\n".join(errors)); sys.exit(1)
if added:
    doc["incidents"] = tidy(doc["incidents"] + added)
    doc["updated"] = datetime.date.today().isoformat()
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(f"added {len(added)}: " + ", ".join(r["id"] for r in added))
