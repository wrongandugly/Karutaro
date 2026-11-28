# Peças e licenças do Karutaro

Organizado em 2026-11-28, a pedido do Fabricio. Este arquivo é o
mapa de tudo que o robô usa — o papel que um comprador ou advogado
pediria numa auditoria (due diligence). Não é parecer jurídico.

## O que é 100% do Fabricio (o ativo)

- O código próprio: `hunter.py`, `wave.py`, `intake.py` e as
  páginas do quadro — escritos para este projeto.
- Os dados: `biblioteca/`, `facts.json` e as fichas — a compilação
  (seleção, formato PODE/NÃO PODE/NÃO DIZ, citações com fonte e
  data) é obra dele.
- As marcas: Wrong and Ugly, Againdex, Karutaro.
- As contas: GitHub, Groq, Google — todas no nome dele.

## Peças de código aberto plugadas (permissão de uso comercial)

Regra da casa: **só entra peça permissiva** (MIT, BSD, Apache).
Licença copyleft forte (AGPL/GPL) não entra — ela poderia obrigar
a abrir o código próprio.

| Peça | Papel no robô | Licença | Fonte |
|---|---|---|---|
| Scrapling | Navegador furtivo (resgate final da leitura) | BSD-3-Clause | github.com/D4Vinci/Scrapling |
| Trafilatura | Peneira de texto (limpa artigos) | Apache-2.0 | github.com/adbar/trafilatura |
| Crawl4AI | Varredor de sites (ferramenta de onda) | Apache-2.0 | github.com/unclecode/crawl4ai |
| curl_cffi | Disfarce leve de conexão | MIT | github.com/lexiforest/curl_cffi |
| Playwright | Navegador dos braços de produto | Apache-2.0 | github.com/microsoft/playwright |

Condições dessas licenças (resumo): pode usar, modificar e vender
produto com a peça dentro; deve manter o aviso de direitos do
autor junto ao produto; não pode dizer que a peça é sua nem usar
o nome do autor como sua marca.

## Serviços consultados (nada do código deles vive aqui)

O robô só conversa com eles pela internet; valem os termos de uso
de cada um, e as chaves ficam no cofre do GitHub, nas contas do
Fabricio.

- Groq e Google Gemini — o "olho" (leitura e julgamento das páginas)
- Jina Reader — resgate de leitura de páginas difíceis
- archive.org (Wayback Machine) — fotos antigas das páginas
- Yahoo! Japan — busca de candidatos
- frankfurter.app — câmbio pra converter preço do eBay
- GitHub Actions + Pages — a oficina onde o robô roda e o quadro

## Plugs prontos, dormindo (só falta a chave dele)

- Tavily — busca profissional (1.000/mês grátis no plano atual)
- OpenRouter — terceira lente do olho
- eBay Browse API e Rakuten Ichiba API — preços de produtos

## Peças avaliadas e recusadas

- Firecrawl — licença AGPL-3.0 (risco pro código próprio)
- Folo — licença AGPL-3.0
- GitHub Models — serviço encerrado em 2026-07-30
- Brave Search API — termos proíbem guardar os resultados
  (mataria a biblioteca)
