#!/usr/bin/env python3
"""Transcribe all 21 manuscript tables from the .docx into tables/manuscript/TableNN.csv.

These are verbatim copies of what the manuscript prints (including the designed benchmarks).
Computed tables are *re-generated* separately by scripts/make_tables.py and compared with these.
"""
import csv, pathlib, docx

ROOT = pathlib.Path(__file__).resolve().parents[1]
doc = docx.Document(ROOT / "manuscript" / "Circlip_Sleeve_QI_Grasp.docx")
out = ROOT / "tables" / "manuscript"; out.mkdir(parents=True, exist_ok=True)
assert len(doc.tables) == 21, len(doc.tables)
for i, t in enumerate(doc.tables, 1):
    rows = [[" ".join(c.text.split()) for c in r.cells] for r in t.rows]
    with open(out / f"Table{i:02d}.csv", "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
print("wrote", len(doc.tables), "tables to", out)
