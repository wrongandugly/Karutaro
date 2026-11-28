# Varredura 4 — livro, busca no site, mapas e gráficos (2026-11-28)

Quarta varredura pedida pelo Fabricio ("eu sei que tem vários").
Números conferidos AO VIVO na API do GitHub em 2026-11-28.

## WeasyPrint (Kozea/WeasyPrint) — o molde do livro
- 9.815 estrelas · BSD-3-Clause · atualizado 2026-11-24
- Transforma página HTML em PDF com qualidade de impressão.
- Onde encaixa: as fichas já nascem HTML — esta peça é o caminho
  ficha → livro impresso/ebook que o Fabricio perguntou em
  2026-11-28 ("isso viraria livro?"). Pluga como ferramenta no
  repo do robô (book.py), separada da caça.

## Pagefind (pagefind/pagefind) — busca dentro da casa
- 5.586 estrelas · MIT · atualizado 2026-11-26
- Busca de site estático que roda 100% no navegador, sem servidor.
- Onde encaixa: a casa é estática (GitHub Pages) e terá 1.234+
  fichas — o visitante busca "estação com banho em Nagano" sem a
  casa precisar de servidor. Entra na próxima mexida da casa.

## MapLibre GL (maplibre/maplibre-gl-js) — mapa liso
- 12.195 estrelas · código aberto (BSD; a API não confirmou
  automaticamente) · atualizado 2026-11-27
- Mapa vetorial suave (zoom contínuo, sem grade de quadradinhos)
  — evolução do mapa atual do diretório (Leaflet). Próxima mexida.

## ECharts (apache/echarts) — gráficos ricos
- 67.816 estrelas · Apache-2.0 · atualizado 2026-11-25
- A biblioteca de gráficos da Apache: barras, linhas, mapas de
  calor interativos. Linguagem visual das salas de dados do
  museu (parceiro do uPlot, da varredura 3: uPlot = leve/rápido,
  ECharts = rico/interativo).

## ArchiveBox (ArchiveBox/ArchiveBox) — a máquina do tempo dele
- 29.111 estrelas · MIT · atualizado 2026-11-27
- Arquivador pessoal da web: guarda cópia completa das páginas
  (HTML, foto, PDF) sob o controle dele.
- Onde encaixa (futuro): em vez de depender só do archive.org, o
  robô guardaria a PROVA das páginas oficiais que lê — a foto é
  dele, no arquivo dele. Peça pesada (um sistema inteiro); fica
  pra quando a casa estiver no ar e a prova virar rotina.
