#!/usr/bin/env python3
"""Draw every structure in mol/sdf as inline SVG and write data/molecules.json ({key: svg}).

One bond length for all, so the molecules compare honestly (fentanyl and carfentanil side by side differ by
one group, and the drawing shows that). Bonds use currentColor; the page colours them with its ink.
PubChem 2D records (the first line of each .sdf is its CID). usage: python3 tools/build_mols.py
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mol2svg import load, svg  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOND = 13  # px; labels then sit at the drawer's 10 px floor, the smallest text on the page that still reads
LABELS = {"fentanyl": "Fentanyl", "fluorofentanyl": "Fluorofentanyl (a fluorine on the aniline ring)",
          "methylfentanyl": "Methylfentanyl (a methyl on the piperidine ring)", "carfentanil": "Carfentanil (a methyl ester on the piperidine)",
          "cychlorphine": "Cychlorphine, a benzimidazolone opioid", "n-desethyl-isotonitazene": "N-desethyl isotonitazene, a nitazene",
          "n-pyrrolidino-protonitazene": "N-pyrrolidino protonitazene, a nitazene", "bromazolam": "Bromazolam, a triazolobenzodiazepine",
          "ethylbromazolam": "Ethyl bromazolam", "phenazolam": "Phenazolam", "desalkylgidazepam": "Desalkylgidazepam",
          "xylazine": "Xylazine, an alpha-2 agonist sedative", "medetomidine": "Medetomidine, an alpha-2 agonist sedative"}

out = {}
for p in sorted((ROOT / "mol" / "sdf").glob("*.sdf")):
    mol = load(p.stem)
    out[p.stem] = {"cid": p.read_text().split("\n", 1)[0].strip(), "svg": svg(mol, BOND, label=LABELS.get(p.stem, p.stem))}
(ROOT / "data" / "molecules.json").write_text(json.dumps(out, ensure_ascii=False) + "\n")
print(f"molecules.json: {len(out)} structures at bond {BOND} px: " + ", ".join(out))
