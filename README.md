# Overdose Watch

**Live: https://kat-titter.github.io/overdose-watch/**

Are overdose deaths going down where we live and dance? This page puts official death counts for the
United States, California, Nevada, San Francisco, Alameda County and Washoe County next to every reported
overdose, cluster, health alert, drug-checking finding and new substance we can find in the Bay Area,
California and Nevada. Every report links its source.

Harm-reduction information, not medical advice. If someone won't wake up or isn't breathing normally,
call 911 and give Narcan.

## Data

- `data/trend.json`: drug overdose deaths in the 12 months ending each month.
  - [CDC NCHS VSRR provisional counts](https://data.cdc.gov/d/xkb8-kh2a), states and US, monthly. Uses predicted values, which adjust for reporting delay.
  - [CDC NCHS provisional county-level counts](https://data.cdc.gov/d/gb4e-yj24), quarterly.
  - [San Francisco OCME preliminary monthly counts](https://data.sf.gov/d/jxrr-bmra), summed over 12 months.
- `data/incidents.json`: one record per report, with its date, place, region, approximate position, kind,
  substances, exact molecules as reported, deaths (only when the source states a count), a short summary,
  and the source link. Field rules live in `tools/schema.py`.

## Updating

Every Monday a scheduled Claude task searches news, health departments, medical examiners, the DEA and CDC,
and drug-checking programs, then:

```bash
python3 tools/update_trend.py          # refresh official counts (standard library only)
python3 tools/add_incidents.py new.json # validate and merge new reports; skips ones already tracked
python3 tools/validate.py              # check everything before committing
```

Corrections are welcome: open an issue with the report and a source.

Made by Kat Titterton, San Francisco, as part of a harm-reduction project for Black Rock City and Bay Area dance floors.
