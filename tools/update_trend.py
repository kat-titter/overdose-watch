#!/usr/bin/env python3
"""Refresh data/trend.json: official overdose death counts, as totals for the 12 months ending each month.

Sources (public, read-only APIs):
  CDC NCHS VSRR provisional counts, states and US (monthly): https://data.cdc.gov/d/xkb8-kh2a
  CDC NCHS VSRR provisional county-level counts (quarterly):  https://data.cdc.gov/d/gb4e-yj24
  San Francisco OCME preliminary monthly counts (DataSF):     https://data.sf.gov/d/jxrr-bmra
Run: python3 tools/update_trend.py   (standard library only)
"""
import datetime, json, pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
MONTHS = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July",
                                         "August", "September", "October", "November", "December"])}
START = "2020-01"


def get(url, params):
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers={"User-Agent": "overdose-watch"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def state(code, name):
    rows = get("https://data.cdc.gov/resource/xkb8-kh2a.json",
               {"state": code, "indicator": "Number of Drug Overdose Deaths", "$limit": 5000})
    pts = {}
    for r in rows:
        v = r.get("predicted_value") or r.get("data_value")  # predicted adjusts for deaths still being reported
        if v:
            pts[f"{r['year']}-{MONTHS[r['month']]:02d}"] = round(float(v))
    return {"key": code.lower(), "name": name, "level": "nation" if code == "US" else "state",
            "source": "CDC NCHS, provisional counts adjusted for reporting delay", "url": "https://data.cdc.gov/d/xkb8-kh2a",
            "points": sorted((k, v) for k, v in pts.items() if k >= START)}


def county(fips, name):
    rows = get("https://data.cdc.gov/resource/gb4e-yj24.json", {"fips": fips.lstrip("0"), "$limit": 5000})  # stored without the leading zero
    pts = {f"{r['year']}-{int(r['month']):02d}": int(float(r["provisional_drug_overdose"]))
           for r in rows if r.get("provisional_drug_overdose")}
    return {"key": fips, "name": name, "level": "county",
            "source": "CDC NCHS, provisional county counts", "url": "https://data.cdc.gov/d/gb4e-yj24",
            "asOf": max(r["data_as_of"] for r in rows)[:10], "points": sorted((k, v) for k, v in pts.items() if k >= START)}


def san_francisco():
    rows = get("https://data.sf.gov/resource/jxrr-bmra.json", {"$limit": 5000})
    monthly = {r["month_start_date"][:7]: round(float(r["total_deaths"])) for r in rows if r.get("total_deaths")}
    keys = sorted(monthly)

    def prev(ym, n):
        y, m = map(int, ym.split("-")); t = y * 12 + m - 1 - n
        return f"{t // 12}-{t % 12 + 1:02d}"
    pts = [(k, sum(monthly[prev(k, i)] for i in range(12))) for k in keys if all(prev(k, i) in monthly for i in range(12))]
    return {"key": "sf", "name": "San Francisco", "level": "city",
            "source": "SF Office of the Chief Medical Examiner, preliminary monthly counts", "url": "https://data.sf.gov/d/jxrr-bmra",
            "asOf": max(r["data_as_of"] for r in rows)[:10], "points": pts, "monthly": sorted(monthly.items())}


def main():
    series = [state("US", "United States"), state("CA", "California"), state("NV", "Nevada"), san_francisco(),
              county("06001", "Alameda County (Oakland)"), county("32031", "Washoe County (Reno)")]
    for s in series:
        assert len(s["points"]) >= 24, f"{s['name']}: only {len(s['points'])} points"
    out = {"generated": datetime.date.today().isoformat(),
           "metric": "Drug overdose deaths in the 12 months ending each month", "series": series}
    path = ROOT / "data" / "trend.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    for s in series:
        k1, v1 = s["points"][-1]
        y, m = map(int, k1.split("-")); v0 = dict(s["points"]).get(f"{y - 1}-{m:02d}")
        print(f"{s['name']:<28} {k1}  {v1:>7,}   a year earlier {v0 if v0 is None else format(v0, ',')}"
              + (f"   {100 * (v1 - v0) / v0:+.0f}%" if v0 else ""))


if __name__ == "__main__":
    main()
