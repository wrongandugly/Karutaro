#!/usr/bin/env python3
"""Sonda Mercari — roda no GitHub Actions (Chrome completo, rede limpa).
Abre a busca da Mercari, conta os anuncios renderizados e grava o resultado
em mercari-probe/resultado.json (commitado de volta pelo workflow)."""
import json, time
from playwright.sync_api import sync_playwright

URL = "https://jp.mercari.com/search?keyword=CX-5%20%E3%82%AD%E3%83%A3%E3%83%AA%E3%82%A2"
out = {"ok": False, "items": 0, "samples": [], "title": "", "url": URL}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox", "--lang=ja-JP"])
    pg = b.new_page(
        locale="ja-JP",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    try:
        pg.wait_for_selector('a[href*="/item/"]', timeout=25000)
    except Exception:
        pass
    pg.wait_for_timeout(3000)
    out["title"] = pg.title()
    anchors = pg.query_selector_all('a[href*="/item/"]')
    out["items"] = len(anchors)
    seen = set()
    for a in anchors:
        href = a.get_attribute("href") or ""
        if href in seen:
            continue
        seen.add(href)
        txt = (a.inner_text() or "").strip().replace("\n", " ")
        if txt:
            out["samples"].append(txt[:120])
        if len(out["samples"]) >= 10:
            break
    out["ok"] = out["items"] > 0
    b.close()

out["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
with open("mercari-probe/resultado.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False)[:500])
