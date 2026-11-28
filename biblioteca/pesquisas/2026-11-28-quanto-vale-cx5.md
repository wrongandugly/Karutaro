# QUANTO VALE? — pesquisa do relatório-teste do CX-5 (2026-11-28)

Ideia trazida pelo Fabricio (anúncio do kurumauritai no X):
digitar modelo/ano/km e receber um relatório-cartão de valor.
Veredito dele: montar um teste — e o molde é PRA TUDO
(carro, casa, objetos), não só carro.

## Dados conferidos ao vivo em 2026-11-28 (CX-5 XD, LDA-KE2FW)

### Camada do pedido (anúncios, preço do carro)
- 2014 · 9,4万km · ¥368.000 — kakaku.com/kuruma (Carsensor)
- 2014 · 8,9万km · ¥530.000 — idem (anúncio semelhante)
- 2013 · 9,8万km · ¥348.000 — idem (anúncio semelhante)
- 2016 · 4,7万km · ¥800.000 — ucar.mitsubishi-motors.co.jp
- 2013 · 5,1万km · ¥600.000 — kakaku.com/kuruma
- 2016 · 4,4万km · ¥1.040.000 — kakaku (XD Proactive, Saitama)
- 2013 · 5,3万km · ¥735.000 — UCAR (semelhante)
- 2014 · 5,8万km · ¥873.000 — kakaku (semelhante)
Km parecida com a do Fabricio (91.167 km): mediana ¥368.000,
faixa ¥348.000–¥530.000 → valor estimado do relatório ¥370.000.

### Camada da compra (買取, MOTA/autoc-one, base leilões reais)
Geração KE (inclui LDA-KE2FW), 買取査定価格 por ano:
2016: ¥426–801 mil · 2015: ¥358–807 mil · 2014: ¥275–782 mil ·
2013: ¥268–683 mil · 2012: ¥276–677 mil. 下取り ~10% abaixo.
Conferência (kubotasmile/Gulliver): KE 2016 mediana ~¥600 mil;
KE 2013 mediana ~¥350 mil.

### Fontes do molde geral
- Carro: anúncios (Carsensor/Goo-net/価格.com) × 買取 (MOTA e
  afins, base leilão USS — o dado bruto do USS é de membros).
- Casa: camada oficial = preços de transação do MLIT
  (土地総合情報システム, público); pedido = Suumo/Homes.
- Moto/objetos: GooBike; Mercari/Yahoo vendidos (o robô já varre).

Relatório-teste: againdex-site/vale-teste.html (build-vale.py).
