# Overdose Watch

**Live: https://kat-titter.github.io/overdose-watch/**

Are overdose deaths going down where we live and dance? This page puts official death counts for the
United States, California, Nevada, San Francisco, Alameda County and Washoe County next to every reported
overdose death and cluster of deaths we can find, with the drug each one names in its own colour (fentanyls,
orphines, nitazenes, benzos, animal sedatives). Every report links its primary source: the agency that counted the deaths.

Harm-reduction information, not medical advice. If someone won't wake up or isn't breathing normally,
call 911 and give Narcan.

## Data

- `data/trend.json`: drug overdose deaths in the 12 months ending each month; for the US, California and Nevada also the
  CDC's counts involving opioids, fentanyl (synthetic opioids), methamphetamine (psychostimulants) and cocaine, which overlap.
  - [CDC NCHS VSRR provisional counts](https://data.cdc.gov/d/xkb8-kh2a), states and US, monthly. Uses predicted values, which adjust for reporting delay.
  - [CDC NCHS provisional county-level counts](https://data.cdc.gov/d/gb4e-yj24), quarterly.
  - [San Francisco OCME preliminary monthly counts](https://data.sf.gov/d/jxrr-bmra), summed over 12 months.
- `data/incidents.json`: one record per report of deaths, with its date, place, region, approximate position, kind
  (a death, a cluster or a data release), substances (the first sets the map colour; `all` for all-drug totals), exact
  molecules as reported, the death count the source states, a short summary, and the source link. Field rules live
  in `tools/schema.py`.
- `data/compounds.json`: San Francisco deaths involving each newer drug the Medical Examiner tracks (xylazine,
  bromazolam, fluorofentanyl, medetomidine ...), year to date at each monthly letter, 2024 onward. One record per
  period a letter reports, with the letter's URL. Two letters repeat the previous month's total; those carry a `note`.
- `data/molecules.json`: one drawn structure per compound in the page's table (`{key: {cid, svg}}`), from the PubChem
  2D records in `mol/sdf/`, all at one bond length so the molecules compare honestly.

## Updating

Every Monday a scheduled job (Claude) refreshes the official counts and looks for new reports of deaths. It cites
trusted primary sources only (medical examiners and coroners, health departments, the CDC, the White House drug
policy office); news coverage can point to a report but is never the citation.
Reports published in the past week get a yellow ring on the map. The job runs:

```bash
python3 tools/update_trend.py          # refresh official counts (standard library only)
python3 tools/update_compounds.py      # read the SF Medical Examiner's new monthly letters into compounds.json
python3 tools/add_incidents.py new.json # validate and merge new reports; skips ones already tracked
python3 tools/validate.py              # check everything before committing
```

Web search never surfaces the Medical Examiner's letters, so `update_compounds.py` probes their fixed address
(`https://media.api.sf.gov/documents/YYYY_MM_OCME_Overdose_Report.pdf`) for every month, reads each new PDF with
macOS PDFKit (no Python packages) and caches it under `~/.cache/overdose-watch/`. The job also opens the agencies'
own news pages before searching.

Structures: drop a PubChem 2D SDF into `mol/sdf/<key>.sdf` and run `python3 tools/build_mols.py`, which draws every
structure with `tools/mol2svg.py` (bonds in `currentColor`, so the page colours them) into `data/molecules.json`;
the page's `COMPOUNDS` list in `index.html` gives each key its row.

Corrections are welcome: open an issue with the report and a source.

Made by Kat Titterton, San Francisco, as part of a harm-reduction project for Black Rock City and Bay Area dance floors.
