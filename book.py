#!/usr/bin/env python3
"""Karutaro BOOK mold (WeasyPrint, BSD-3, plugged 2026-11-28).

Turns the facts notebook (facts.json) into a print-ready PDF
guide: one ficha per place - verdicts, verbatim quotes, source,
read date. Triggered by a push of book-request.json. The data
was always book-shaped; this is just another mold for it.
"""
import json
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

BASE = Path(__file__).resolve().parent
JST = timezone(timedelta(hours=9))
VLABEL = {"sim": "PODE", "nao": "NÃO PODE", "nao_diz": "NÃO DIZ"}


def main():
    facts = json.loads((BASE / "facts.json").read_text(
        encoding="utf-8"))
    today = datetime.now(JST).strftime("%d/%m/%Y")
    parts = ["""<!DOCTYPE html><html lang="pt"><head><meta
charset="utf-8"><style>
@page { size: A5; margin: 16mm 14mm; }
body { font-family: "Noto Sans CJK JP", sans-serif; color: #111; }
h1 { font-size: 26pt; margin: 30mm 0 4mm; }
.sub { color: #555; font-size: 11pt; }
.ficha { page-break-inside: avoid; border-top: 2px solid #111;
  padding-top: 4mm; margin-top: 8mm; }
.ficha h2 { font-size: 14pt; margin: 0 0 2mm; }
.verd { font-weight: bold; }
.quote { color: #333; font-size: 9.5pt; margin: 1mm 0 2mm 4mm; }
.src { color: #777; font-size: 8pt; word-break: break-all; }
</style></head><body>"""]
    parts.append(f"<h1>Karutaro — guia conferido</h1>"
                 f"<p class='sub'>Vereditos com citação da página "
                 f"oficial. Conferido até {today}.</p>")
    for f in facts:
        parts.append("<div class='ficha'>")
        parts.append(f"<h2>{escape(f.get('name', ''))}</h2>")
        for a in f.get("answers", []):
            v = VLABEL.get(a.get("verdict"), a.get("verdict", ""))
            parts.append(
                f"<p><span class='verd'>{escape(a.get('label', ''))}"
                f" — {v}</span></p>")
            if a.get("quote"):
                parts.append(
                    f"<p class='quote'>“{escape(a['quote'])}”</p>")
        parts.append(
            f"<p class='src'>Fonte: {escape(f.get('url', ''))} · "
            f"lido em {escape((f.get('read_at', '') or '')[:10])}</p>")
        parts.append("</div>")
    parts.append("</body></html>")
    from weasyprint import HTML
    HTML(string="".join(parts)).write_pdf(
        str(BASE / "livro.pdf"))
    print(f"livro: {len(facts)} fichas -> livro.pdf")


if __name__ == "__main__":
    main()
