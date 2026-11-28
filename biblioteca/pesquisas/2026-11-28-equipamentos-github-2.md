# Equipamentos do GitHub pro Karutaro — varredura 2 (2026-11-28)

Segunda varredura pedida pelo Fabricio ("outros repositórios ou APIs?").
Números conferidos AO VIVO na API do GitHub em 2026-11-28.

## Vereditos

### curl_cffi (lexiforest/curl_cffi) — PLUGAR (recomendado)
- 6.931 estrelas · licença MIT · código atualizado 2026-11-28 (hoje)
- O que é: disfarce leve — imita a "impressão digital" de conexão do
  Chrome de verdade. Muito bloqueio 403 é o site reconhecendo a
  conexão de robô, não a cara dele.
- Onde encaixa: degrau novo na escada de leitura, entre o Jina e o
  furtivo pesado — rápido, sem abrir navegador. Testar contra a
  web-komachi (que segurou até o furtivo).
- Fonte: https://github.com/lexiforest/curl_cffi

### Wayback Machine API (archive.org) — PLUGAR (barato, sem chave)
- API pública e grátis, sem cadastro. Conferida ao vivo 2026-11-28:
  respondeu; a foto arquivada mais perto da página da Tonbo é de
  2026-08-08, status 200.
- O que é: a máquina do tempo da internet — guarda "fotos" antigas
  das páginas.
- Onde encaixa: (1) página oficial fora do ar ou apagada → o robô lê
  a última foto arquivada em vez de desistir; (2) memória viva ganha
  prova do passado ("antes era assim, foto de tal data").
- Fonte: https://archive.org/help/wayback_api.php

### Tesseract OCR (tesseract-ocr/tesseract) — DEPOIS (lacuna real)
- 77.698 estrelas · licença Apache-2.0 · atualizado 2026-11-26
- O que é: lê texto dentro de IMAGEM. Site japonês adora publicar
  tabela de preço e regra como foto — hoje o olho passa reto por
  essas, porque imagem não vira texto na leitura.
- Ressalva honesta: OCR de japonês acerta menos que o de inglês;
  entra como tentativa rotulada, nunca como prova sozinho.
- Fonte: https://github.com/tesseract-ocr/tesseract

## Continua aberto da varredura 1
- Tavily (busca de verdade): plug dormindo no código, falta a chave
  grátis do Fabricio. Segue sendo o maior salto disponível.
