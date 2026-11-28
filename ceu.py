# -*- coding: utf-8 -*-
"""
ceu.py — o robo do ceu (sala O CEU AGORA).
Le 4 fontes vivas e grava ceu-agora.json:
  fogos   = NASA FIRMS (VIIRS, mundo, ultimas 24h) — chave no cofre (NASA_FIRMS_KEY)
  avioes  = OpenSky (anonimo, dentro dos creditos: mundo 4 + Japao 3 por rodada)
  sismo   = USGS (feed publico M4.5+ 24h, sem chave)
  iss     = wheretheiss.at (sem chave)
Cada fonte falha sozinha: o que nao responder vira null + nota honesta no JSON.
"""
import csv
import io
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
JP_BOX = (30.0, 46.0, 129.0, 147.0)  # lat min/max, lon min/max


def get(url, timeout=60, headers=None):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _conta_firms(key, fonte):
    url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/%s/%s/world/1" % (key, fonte)
    raw = get(url, timeout=120).decode("utf-8", "replace")
    linhas = raw.splitlines()
    with open("ceu.log", "a", encoding="utf-8") as f:
        f.write("[ceu diag] %s -> %d bytes, %d linhas, cabecalho: %s\n"
                % (fonte, len(raw), len(linhas), (linhas[0][:110] if linhas else "VAZIO")))
    if not linhas or "latitude" not in linhas[0]:
        raise ValueError("resposta inesperada da FIRMS (%s)" % fonte)
    return list(csv.DictReader(io.StringIO(raw)))


def fogos(key):
    """NASA FIRMS: tenta SNPP, NOAA20 e MODIS; usa a primeira fonte com dados."""
    rows = None
    for fonte in ("VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"):
        try:
            r = _conta_firms(key, fonte)
        except Exception:
            continue
        if r:
            rows = r
            break
        if rows is None:
            rows = r
    if rows is None:
        raise ValueError("FIRMS nao respondeu em nenhuma fonte")
    primeira = raw.splitlines()[0] if raw.splitlines() else ""
    if "latitude" not in primeira:
        # a FIRMS respondeu texto de erro (ex.: chave invalida) em vez de CSV:
        # NUNCA contar isso como zero fogos — registra o comeco da resposta e falha.
        with open("ceu.log", "a", encoding="utf-8") as f:
            f.write("[ceu debug] FIRMS respondeu: " + raw[:160].replace("\n", " ") + "\n")
        raise ValueError("resposta inesperada da FIRMS")
    rows = list(csv.DictReader(io.StringIO(raw)))
    mundo = len(rows)
    japao = 0
    for r in rows:
        try:
            la, lo = float(r["latitude"]), float(r["longitude"])
        except Exception:
            continue
        if JP_BOX[0] <= la <= JP_BOX[1] and JP_BOX[2] <= lo <= JP_BOX[3]:
            japao += 1
    return {"mundo": mundo, "japao": japao, "fonte": "NASA FIRMS · VIIRS · ultimas 24h"}


def avioes():
    """OpenSky anonimo: estados globais (4 creditos) + caixa do Japao (3 creditos)."""
    out = {"mundo": None, "japao": None, "fonte": "OpenSky · ao vivo"}
    try:
        d = json.loads(get("https://opensky-network.org/api/states/all", timeout=90).decode())
        st = d.get("states") or []
        out["mundo"] = sum(1 for s in st if s[8] is False)
    except Exception as e:
        out["nota_mundo"] = type(e).__name__
    try:
        u = ("https://opensky-network.org/api/states/all?lamin=%s&lomin=%s&lamax=%s&lomax=%s"
             % (JP_BOX[0], JP_BOX[2], JP_BOX[1], JP_BOX[3]))
        d = json.loads(get(u, timeout=90).decode())
        st = d.get("states") or []
        out["japao"] = sum(1 for s in st if s[8] is False)
    except Exception as e:
        out["nota_japao"] = type(e).__name__
    return out


def sismo():
    d = json.loads(get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson",
                       timeout=60).decode())
    fs = [f for f in d.get("features", []) if isinstance(f["properties"].get("mag"), (int, float))]
    if not fs:
        return {"n": 0, "maior_mag": None, "maior_local": None, "fonte": "USGS · M4.5+ · 24h"}
    m = max(fs, key=lambda f: f["properties"]["mag"])
    return {"n": len(fs), "maior_mag": m["properties"]["mag"],
            "maior_local": m["properties"].get("place"), "fonte": "USGS · M4.5+ · 24h"}


def iss():
    d = json.loads(get("https://api.wheretheiss.at/v1/satellites/25544", timeout=30).decode())
    return {"lat": round(d["latitude"], 1), "lon": round(d["longitude"], 1),
            "alt_km": round(d["altitude"]), "vel_kmh": round(d["velocity"]),
            "fonte": "wheretheiss.at · ISS agora"}


def main():
    agora = datetime.now(JST)
    data = {"gerado_em": agora.strftime("%Y-%m-%d %H:%M JST")}
    key = os.environ.get("NASA_FIRMS_KEY", "").strip()
    if key:
        try:
            data["fogos"] = fogos(key)
        except Exception as e:
            data["fogos"] = {"mundo": None, "japao": None, "nota": type(e).__name__,
                             "fonte": "NASA FIRMS · VIIRS · ultimas 24h"}
    else:
        data["fogos"] = {"mundo": None, "japao": None, "nota": "sem chave no cofre",
                         "fonte": "NASA FIRMS · VIIRS · ultimas 24h"}
    for nome, fn in (("avioes", avioes), ("sismo", sismo), ("iss", iss)):
        try:
            data[nome] = fn()
        except Exception as e:
            data[nome] = {"nota": type(e).__name__}
    with open("ceu-agora.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    linha = "[ceu %s] fogos=%s avioes=%s sismo=%s iss=%s" % (
        agora.strftime("%Y-%m-%dT%H:%M"),
        (data.get("fogos") or {}).get("mundo"), (data.get("avioes") or {}).get("mundo"),
        (data.get("sismo") or {}).get("n"), bool(data.get("iss")))
    with open("ceu.log", "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    print(linha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
