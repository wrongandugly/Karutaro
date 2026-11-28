#!/usr/bin/env python3
"""Karutaro DISCOVER tool (plugged 2026-11-28, Fabricio's pick).

Two discovery arms, both free and keyless:
- "osm": OpenStreetMap via the Overpass API - every mapped place
  of a kind inside a named area, with the official website tag
  when the map carries one. Candidate factory for fact hunts.
- "cc": Common Crawl's index - every archived URL under a
  domain, so a whole directory can be inventoried at once.

Reads discover-request.json, writes discover-result.json.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
JST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Karutaro/1.0 (hobby research robot)",
      "Accept": "application/json"}


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _post(url, data, timeout=90):
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(data).encode(), headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def discover_osm(req):
    area = req.get("area", "")
    tipo = req.get("tipo", "public_bath")
    limite = int(req.get("limite", 40))
    ql = (f'[out:json][timeout:50];area[name="{area}"]->.a;'
          f'(node["amenity"="{tipo}"](area.a);'
          f'way["amenity"="{tipo}"](area.a););'
          f'out center tags {limite};')
    raw = _post("https://overpass-api.de/api/interpreter",
                {"data": ql})
    items = []
    for el in json.loads(raw).get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        items.append({
            "nome": tags.get("name", ""),
            "site": tags.get("website") or
                    tags.get("contact:website", ""),
            "lat": lat, "lon": lon})
    return items


def discover_cc(req):
    dominio = req.get("dominio", "")
    limite = int(req.get("limite", 60))
    colls = json.loads(_get(
        "https://index.commoncrawl.org/collinfo.json"))
    idx = colls[0]["cdx-index-api"]
    raw = _get(f"{idx}?url={urllib.parse.quote(dominio)}/*"
               f"&output=json&limit={limite}")
    items = []
    for line in raw.splitlines():
        if line.strip():
            d = json.loads(line)
            items.append({"url": d.get("url", ""),
                          "arquivado_em": d.get("timestamp", ""),
                          "status": d.get("status", "")})
    return items


def main():
    req = json.loads((BASE / "discover-request.json").read_text(
        encoding="utf-8"))
    modo = req.get("modo", "osm")
    items = discover_osm(req) if modo == "osm" else discover_cc(req)
    out = {"modo": modo, "pedido": req, "itens": items,
           "gerado_em": datetime.now(JST).isoformat(timespec="seconds")}
    (BASE / "discover-result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"discover[{modo}]: {len(items)} itens")


if __name__ == "__main__":
    main()
