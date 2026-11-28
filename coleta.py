#!/usr/bin/env python3
"""Karutaro COLETA — coleta semanal de precos (a coleta silenciosa).

Toda semana varre anuncios publicos de um modelo e guarda a foto
da semana em coleta-<slug>.json: quantos anuncios, a mediana geral
e a mediana dos de km alta. Com as semanas, nasce a curva de preco
e o QUANTO VALE? ganha precisao. So leitura; nada e inventado:
sem anuncio lido, a semana registra zero com o motivo no log.
"""
import json
import os
import statistics
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

ALVOS = [
    {
        "slug": "cx5-ke",
        "nome": "Mazda CX-5 XD geracao KE (LDA-KE2FW)",
        "buscas": [
            "CX-5 KE2FW XD ディーゼル 中古車 価格.com",
            "CX-5 KE2FW 中古 カーセンサー 価格 万円",
        ],
        "dominios": ["kakaku.com", "ucar.mitsubishi-motors.co.jp",
                     "carsensor.net", "goo-net.com"],
        "max_paginas": 4,
    },
]

PROMPT = (
    "Extraia TODOS os anuncios de carro usado desta pagina (o anuncio "
    "principal E os anuncios semelhantes listados nela). Para cada um: "
    "ano (int), km em 万km (numero, ex 9.4), preco do carro em 万円 "
    "(numero, ex 36.8 — o 車両価格, NAO o total com taxas). "
    "Responda SOMENTE JSON neste formato exato: "
    '{"anuncios": [{"ano": 2014, "km": 9.4, "preco": 36.8}]}. '
    "Se nao houver anuncio, responda {\"anuncios\": []}."
)


def log(msg):
    linha = f"[coleta {datetime.now(JST):%Y-%m-%dT%H:%M:%S}] {msg}"
    print(linha, flush=True)
    with open("coleta.log", "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def coletar_alvo(hunter, alvo):
    vistos = {}
    for busca in alvo["buscas"]:
        try:
            achados = hunter.web_search(busca)
        except Exception as e:
            log(f"busca falhou ({busca[:30]}...): {type(e).__name__}")
            continue
        urls = []
        for a in achados:
            u = a.get("url", "")
            if any(d in u for d in alvo["dominios"]) and u not in urls:
                urls.append(u)
        for url in urls[: alvo["max_paginas"]]:
            try:
                texto = hunter.rescue_text(url, "")
            except Exception as e:
                log(f"leitura falhou {url[:60]}: {type(e).__name__}")
                continue
            if not texto or len(texto) < 400:
                log(f"pagina vazia ou bloqueada: {url[:60]}")
                continue
            try:
                r = hunter.eye_json(
                    PROMPT + "\n\nPAGINA:\n" + texto[:11000])
            except Exception as e:
                log(f"olho falhou em {url[:50]}: {type(e).__name__}")
                continue
            for an in (r or {}).get("anuncios", []):
                try:
                    ano = int(an["ano"])
                    km = float(an["km"])
                    preco = float(an["preco"])
                except Exception:
                    continue
                if 2011 <= ano <= 2018 and 0 < km < 40 and 5 < preco < 400:
                    vistos[(ano, round(km, 1), round(preco, 1))] = {
                        "ano": ano, "km": km, "preco": preco}
            log(f"{url[:60]} -> acumulado {len(vistos)} anuncios")
    return sorted(vistos.values(), key=lambda x: x["preco"])


def main():
    import hunter  # o cerebro do robo: busca, leitura e olho

    hoje = datetime.now(JST).strftime("%Y-%m-%d")
    for alvo in ALVOS:
        anuncios = coletar_alvo(hunter, alvo)
        arq = f"coleta-{alvo['slug']}.json"
        hist = []
        if os.path.exists(arq):
            with open(arq, encoding="utf-8") as f:
                hist = json.load(f)
        precos = [a["preco"] for a in anuncios]
        altos = [a["preco"] for a in anuncios if a["km"] >= 8.5]
        semana = {
            "data": hoje,
            "alvo": alvo["nome"],
            "anuncios": len(anuncios),
            "mediana_geral": statistics.median(precos) if precos else None,
            "mediana_km_alta": statistics.median(altos) if altos else None,
            "lista": anuncios,
        }
        hist = [h for h in hist if h["data"] != hoje] + [semana]
        with open(arq, "w", encoding="utf-8") as f:
            json.dump(hist, f, ensure_ascii=False, indent=1)
        log(f"{alvo['slug']}: {len(anuncios)} anuncios | mediana "
            f"{semana['mediana_geral']} | km alta {semana['mediana_km_alta']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
