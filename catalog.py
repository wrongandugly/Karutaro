#!/usr/bin/env python3
"""Karutaro CATALOG builder (plugged 2026-11-28, Fabricio's pick).

Turns the facts notebook (facts.json) into catalogo.db, a SQLite
catalog with two tables (lugares, respostas). The file is the
catalogue: Datasette (Apache-2.0) serves it as a searchable web
catalogue wherever it is hosted later - no server code of ours.
"""
import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    facts = json.loads((BASE / "facts.json").read_text(
        encoding="utf-8"))
    db_path = BASE / "catalogo.db"
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.executescript("""
CREATE TABLE lugares (id INTEGER PRIMARY KEY, nome TEXT, url TEXT,
                      lido_em TEXT, camada TEXT);
CREATE TABLE respostas (lugar_id INTEGER, criterio TEXT,
                        rotulo TEXT, veredito TEXT, citacao TEXT,
                        via TEXT);
""")
    n_resp = 0
    for i, f in enumerate(facts, 1):
        db.execute("INSERT INTO lugares VALUES (?,?,?,?,?)",
                   (i, f.get("name", ""), f.get("url", ""),
                    f.get("read_at", ""), f.get("layer", "")))
        for a in f.get("answers", []):
            db.execute("INSERT INTO respostas VALUES (?,?,?,?,?,?)",
                       (i, a.get("criterion", ""), a.get("label", ""),
                        a.get("verdict", ""), a.get("quote", ""),
                        a.get("via", "")))
            n_resp += 1
    db.commit()
    db.close()
    print(f"catalogo: {len(facts)} lugares, {n_resp} respostas "
          f"-> catalogo.db")


if __name__ == "__main__":
    main()
