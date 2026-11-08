#!/usr/bin/env python3
"""Rebuild data/compounds.json from San Francisco's monthly accidental-overdose reports.

The Office of the Chief Medical Examiner posts one PDF a month at a fixed address,
https://media.api.sf.gov/documents/YYYY_MM_OCME_Overdose_Report.pdf, whose cover letter gives the
year-to-date death count and, since 2024, the deaths involving each newer drug it tracks (xylazine,
bromazolam, fluorofentanyl, medetomidine ...). Web search rarely indexes these PDFs, so this script
probes the address pattern directly for every month since January 2025 (some months are skipped by
the OCME; a 403 or non-PDF answer means no report), caches the PDFs under ~/.cache/overdose-watch/ocme/,
reads the first page with macOS PDFKit (no Python packages needed) and writes one record per report.

usage: python3 tools/update_compounds.py [--quiet]
Prints one line per report that is new since the last run, so the weekly job can add it as an incident.
Standard library plus `osascript` only.
"""
import datetime, json, pathlib, re, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "compounds.json"
CACHE = pathlib.Path.home() / ".cache" / "overdose-watch" / "ocme"
URL = "https://media.api.sf.gov/documents/{y}_{m:02d}_OCME_Overdose_Report.pdf"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130 Safari/537.36"
FIRST = (2025, 1)
# the OCME's names for the drugs it singles out -> this site's keys (data/incidents.json uses the same words in `molecules`)
NAMES = {"fluoro fentanyl": "fluorofentanyl", "xylazine": "xylazine", "bromazolam": "bromazolam", "phenazolam": "phenazolam",
         "medetomidine": "medetomidine", "desalkyl gidazepam": "desalkylgidazepam", "ethyl bromazolam": "ethylbromazolam",
         "n-propionitrile chlorphine": "cychlorphine", "cychlorphine": "cychlorphine", "carfentanil": "carfentanil",
         "nitazene": "nitazenes", "nitazenes": "nitazenes"}


def months():
    y, m = FIRST
    today = datetime.date.today()
    while (y, m) <= (today.year, today.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def fetch(y, m):
    """Return the cached PDF path for a month, downloading it once; None when the OCME posted no report."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{y}_{m:02d}.pdf"
    miss = p.with_suffix(".none")
    if p.exists():
        return p
    if miss.exists() and (y, m) < (datetime.date.today().year, datetime.date.today().month):
        return None
    try:
        with urllib.request.urlopen(urllib.request.Request(URL.format(y=y, m=m), headers={"User-Agent": UA}), timeout=60) as r:
            data = r.read()
    except Exception:
        data = b""
    if data[:4] == b"%PDF":
        p.write_bytes(data)
        return p
    miss.write_text(datetime.date.today().isoformat())
    return None


def first_page_text(path):
    js = ('ObjC.import("PDFKit");var d=$.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(%s));'
          'd.isNil()?"":ObjC.unwrap(d.pageAtIndex(0).string)') % json.dumps(str(path))
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", js], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout
    try:  # a machine without PDFKit: PyMuPDF if it happens to be installed
        import fitz
        return fitz.open(str(path))[0].get_text()
    except Exception:
        sys.exit(f"could not read {path}: {r.stderr.strip()}")


def parse(text, url):
    """One record per period the cover letter reports on: its date, the period, the total and one count per drug.
    A quarterly letter lists two periods (the year just ended, revised, and the new year's first month)."""
    L = [l.strip() for l in text.split("\n")]
    merged, i = [], 0
    while i < len(L):  # 2025 letters put each bullet on its own line
        if L[i] == "•" and i + 1 < len(L):
            merged.append("• " + L[i + 1]); i += 2
        else:
            merged.append(L[i]); i += 1
    t = " ".join(merged)
    D = r"[A-Z][a-z]+ \d{1,2}, 20\d\d"
    day = lambda s: datetime.datetime.strptime(s, "%B %d, %Y").date().isoformat()
    date = re.search(rf"\b({D})\b", t)
    spans = list(re.finditer(rf"involving .+? from ({D}),? to ({D}),? are as follows", t))
    if not (date and spans):
        return []
    loose = lambda s: re.escape(s).replace(",", ",?").replace("\\ ", r"\s+")
    out = []
    for k, sp in enumerate(spans):
        A, B = sp.group(1), sp.group(2)
        total = (re.search(rf"deaths from {loose(A)},? to {loose(B)},? is (\d+)", t)
                 or re.search(rf"from {loose(A)},? to {loose(B)}\. During this period, the preliminary number of accidental overdose deaths is (\d+)", t)
                 or re.search(rf"from {loose(A)},? to {loose(B)}\. The number of accidental overdose deaths in this period was (\d+)", t))
        if not total and A.split()[0] == B.split()[0]:  # a one-month span: "... and for January 2025 is 59"
            total = re.search(rf"for {B.split()[0]} {B.split()[-1]} is (\d+)", t)
        if not total:
            continue
        seg = t[sp.end():spans[k + 1].start() if k + 1 < len(spans) else len(t)]
        counts, unknown = {}, []
        for name, n in re.findall(r"• ([A-Za-z][A-Za-z\- ]+?)[,:] (\d+)", seg):
            key = NAMES.get(name.strip().lower())
            if not key:
                key = re.sub(r"[^a-z0-9]+", "", name.lower()); unknown.append(name.strip())
            counts[key] = int(n)
        out.append({"date": day(date.group(1)), "from": day(A), "to": day(B), "total": int(total.group(1)),
                    "url": url, "counts": counts, "_unknown": unknown})
    return out


def main():
    quiet = "--quiet" in sys.argv
    old = json.loads(OUT.read_text()) if OUT.exists() else {"reports": []}
    known = {(r["url"], r["to"]) for r in old["reports"]}
    reports, flags, notes = [], [], []
    for y, m in months():
        p = fetch(y, m)
        if not p:
            continue
        url = URL.format(y=y, m=m)
        recs = parse(first_page_text(p), url)
        if not recs:
            flags.append(f"{url}: cover letter not parsed"); continue
        for r in recs:
            if r.pop("_unknown"):
                flags.append(f"{url}: drug names not in NAMES: {', '.join(r['counts'])}")
            reports.append(r)
    reports.sort(key=lambda r: (r["to"], r["date"]))
    for a, b in zip(reports, reports[1:]):
        if a["from"] == b["from"] and a["to"] < b["to"] and b["total"] <= a["total"]:
            b["note"] = f"the letter's total repeats the {a['date']} letter's; the OCME's monthly open data (data.sf.gov jxrr-bmra) has the count"
            notes.append(f"{b['url']}: total {b['total']} does not rise from {a['total']} (kept as stated, noted)")
    doc = {"generated": datetime.date.today().isoformat(),
           "metric": "Accidental overdose deaths in San Francisco involving each newer drug the Medical Examiner tracks, "
                     "year to date at each monthly report (preliminary; a drug's deaths can be revised down as cases close)",
           "source": {"name": "SF Office of the Chief Medical Examiner, monthly accidental overdose reports", "urlPattern": URL,
                      "names": NAMES},
           "reports": reports}
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    new = [r for r in reports if (r["url"], r["to"]) not in known]
    if not quiet:
        for r in new:
            c = ", ".join(f"{k} {v}" for k, v in sorted(r["counts"].items(), key=lambda kv: -kv[1]))
            print(f"new report {r['date']}: {r['from']} to {r['to']}, {r['total']} deaths; {c}; {r['url']}")
        print(f"compounds.json: {len(reports)} records, {len(new)} new" + (f"; FLAGS: " + " | ".join(flags) if flags else "")
              + (f"; notes: " + " | ".join(notes) if notes else ""))
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
