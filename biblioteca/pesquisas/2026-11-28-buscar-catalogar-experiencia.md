# Varredura 5 — buscar em diretórios, catalogar, experiência (2026-11-28)

Quinta varredura, nos três sabores pedidos pelo Fabricio: "buscar
diretórios, catalogar algo, uma experiência diferente". Números
conferidos AO VIVO na API do GitHub em 2026-11-28.

## BUSCAR EM DIRETÓRIOS (descoberta de lugares)

### Overpass / OpenStreetMap — o diretório-mapa do mundo (serviço)
- O OpenStreetMap é o cadastro aberto do planeta: cada onsen,
  estação e loja com nome, coordenadas e — o ouro — a tag do
  SITE OFICIAL de muitos lugares.
- Uso: o robô pergunta "todos os banhos num raio de X com site
  oficial" e ganha candidatos prontos pra ler, sem depender só de
  buscador. API grátis (Overpass), sem chave.
- Estado: da minha oficina a API respondeu 406 (ela é chata com
  formato de pedido); provar do GitHub se o Fabricio escolher.

### Common Crawl — o arquivo da web inteira (serviço)
- Um arquivo público que varre a web há anos; o índice dele
  responde "quais URLs existem neste domínio/tema" de graça.
- Uso: achar TODAS as páginas de um diretório (ex.: todos os
  sites de michi-no-eki) de uma vez — matéria-prima das ondas.

## CATALOGAR

### Datasette (simonw/datasette) — o catálogo publicável
- 11.684 estrelas · Apache-2.0 · atualizado 2026-11-26
- Transforma qualquer banco SQLite num catálogo navegável e
  pesquisável na web, com API junto.
- Uso: a biblioteca do robô (milhares de fichas) viraria um
  catálogo público consultável — a "sala de honra" com busca
  de verdade, sem construir servidor do zero.

## EXPERIÊNCIA DIFERENTE

### Howler.js (goldfire/howler.js) — som
- 25.467 estrelas · MIT · atualizado 2025-11
- Áudio no navegador sem dor: a casa ganharia SOM — água de
  onsen numa ficha, o "plim" do veredito, a carta de domingo
  lida. Sentido novo, custo quase zero.

### Photo-Sphere-Viewer (mistic100/Photo-Sphere-Viewer) — 360°
- 2.414 estrelas · MIT · atualizado 2026-11-26
- Mostra foto 360° arrastável no navegador: "estar dentro" da
  estação ou do banho sem sair da ficha. Experiência de presença
  com foto comum de celular.

### A-Frame (aframevr/aframe) — sala 3D com HTML
- 17.723 estrelas · MIT · atualizado 2026-07 (maduro e estável)
- Monta cena 3D/VR com tags HTML simples: uma sala do museu
  pra ANDAR dentro, no navegador do celular. O passo além do
  360° — fica de reserva até a casa ter público pedindo.
