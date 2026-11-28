# Varredura 3 — robô ver imagens + site mais legal (2026-11-28)

Pedido do Fabricio: repositórios pra (1) o robô enxergar imagens e
(2) deixar o site (a casa Againdex) mais legal. Números conferidos
AO VIVO na API do GitHub em 2026-11-28.

## Robô ver imagens

### Ligar a visão do Gemini — SEM PEÇA NOVA (recomendado)
- O olho do robô (Gemini) já é multimodal: ele VÊ imagem, não só
  texto. Hoje o robô só manda texto pra ele.
- A ligação: quando a página oficial guarda a regra/preço numa
  IMAGEM (tabela fotografada, banner), o robô manda a imagem pro
  Gemini ler. Zero licença nova, zero instalação; japonês dele é
  forte. Custo: cota da mesma chave que já existe.

### PaddleOCR (PaddlePaddle/PaddleOCR) — opção local forte
- 93.404 estrelas · Apache-2.0 · atualizado 2026-09
- OCR aberto mais forte em línguas asiáticas; roda local, sem
  depender de serviço. Instalação pesada (framework grande).

### Tesseract (tesseract-ocr/tesseract) — opção leve
- 77.698 estrelas · Apache-2.0 · atualizado 2026-11-26
- Leve e clássico; em japonês acerta menos que os dois acima.

### EasyOCR (JaidedAI/EasyOCR) — meio-termo
- 30.177 estrelas · Apache-2.0 · atualizado 2026-11-13

## Site mais legal (casa Againdex — entra quando mexermos na casa)

### html-to-image (bubkoo/html-to-image) — recomendado pro site
- 7.276 estrelas · MIT · atualizado 2026-11-25
- Transforma um pedaço da página numa IMAGEM pronta pra postar.
  É a peça do "cartão postável" de cada sala — o motor de
  descoberta nº 2 da casa (X e Instagram, 4:5).

### anime.js (juliangarnier/anime) — movimento
- 75.165 estrelas · MIT · atualizado 2026-11-02
- Motor de animação leve: portas que abrem, mascote que reage,
  números que contam. (O famoso GSAP tem licença própria, gratuita
  mas não-MIT; o anime.js faz o papel sem asterisco.)

### canvas-confetti (catdad/canvas-confetti) — comemoração
- 12.877 estrelas · ISC (permissiva) · atualizado 2025-10
- Chuva de confete de 2 KB pros momentos de veredito e conquista
  (VEREDITO DE HOJE, SO FAR) — alegria barata, combina com a casa.

### uPlot (leeoniya/uPlot) — gráficos leves
- 10.677 estrelas · MIT · atualizado 2026-11-27
- Gráfico de linha rápido e minúsculo pras salas de dados
  (observatório de preços, GASTAR) — a linguagem do museu.

### three.js (mrdoob/three.js) — reserva
- 119.580 estrelas · MIT · atualizado 2026-11-28
- 3D no navegador. Existe se um dia uma sala quiser; hoje pesaria
  no celular, que é a tela principal da casa.
