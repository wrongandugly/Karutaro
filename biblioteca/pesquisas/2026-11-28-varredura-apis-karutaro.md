# Varredura de APIs pro Karutaro — 2026-11-28

> Pedido do Fabricio: "faça uma análise de APIs, uma varredura, e veja tudo que podemos colocar nele para melhorar".
> Método: planos e preços conferidos AO VIVO em 28/11/2026, em fontes de novembro/2026 (páginas e docs dos próprios serviços, via comparativos datados). Veredito por API + o que ela conserta no robô.

## BUSCA (hoje: DuckDuckGo mudo + Yahoo raspado — o braço mais fraco)

- **Tavily** — busca feita pra agentes. GRÁTIS: 1.000 créditos/mês, SEM cartão (busca básica = 1 crédito; avançada = 2). A mesma chave tem Extract (ler página = 1 crédito/5 URLs). Pago: US$0,008/crédito. **Conserta: busca E leitura num plugue só.**
- **Serper** — resultados do GOOGLE via API (é assim que robô usa Google). 2.500 buscas grátis na abertura, sem cartão (uso único); depois US$1/1.000.
- **Jina Search (s.jina.ai)** — busca na mesma chave do Jina Reader: chave nova vem com 10M tokens; cada busca ~10.000 tokens → ~1.000 buscas grátis.
- **Exa** — US$10 de crédito/mês (~1.400 buscas), sem cartão. Alternativa de busca.
- **SerpApi** — 250 buscas/mês grátis; depois caro (US$25/1.000). Só pra motor específico.
- **Brave Search API — EVITAR**: o plano grátis acabou (fev/2026); hoje US$5 de crédito/mês (~1.000 buscas) COM cartão, e os termos PROÍBEM guardar os resultados — incompatível com a biblioteca do Karutaro.
- **MORTOS (conferido)**: Bing Search API (aposentada em 11/08/2025); Google Custom Search JSON (fechada pra novos clientes, desliga 01/01/2027); GitHub Models (aposentado 30/07/2026).

## LEITURA (hoje: fetch cru — quebra em JavaScript, PDF e bloqueio)

- **Jina Reader (r.jina.ai)** — ⭐ o plugue mais fácil: funciona SEM chave (20 leituras/min por IP); devolve o texto limpo da página JÁ MONTADA (executa o JavaScript) e lê PDF. Com chave grátis: 10M tokens, 500 leituras/min. Pago ~US$0,25/1.000 páginas. **Conserta: toda a classe de "página veio vazia/quebrada".**
- **Tavily Extract** — mesma chave da busca (acima).
- **Firecrawl** — 1.000 créditos/mês grátis, sem cartão; busca + leitura (leitura pesada em JS custa mais créditos).

## OLHO (hoje: Groq + Gemini, grátis)

- **OpenRouter** — 1 chave, centenas de modelos. Modelos `:free`: 50 chamadas/dia grátis (1.000/dia após comprar US$10 UMA vez). A lista grátis muda toda semana (nov/2026: Nemotron 3 Ultra, Gemma 4, Inkling…). **Uso ideal: TERCEIRA lente / desempate** quando Groq e Gemini discordam. Usar o id roteador `openrouter/free` pra não quebrar quando a lista gira.
- **Cloudflare Workers AI** — 10.000 neurônios/dia grátis ≈ 100–500 chamadas curtas/dia (Llama 3.3 70B etc.), sem cartão. Quarta lente possível.
- **Cerebras — NÃO vale**: em 2026 não tem mais plano grátis durável; só vale de US$5 que vence em 30 dias e exige cartão.
- DeepSeek/Mistral: baratos, sem camada grátis durável — pular por agora.

## PRODUTOS (o caçador — hoje raspa Mercari/Yahoo Auctions)

- **eBay Browse API** — OFICIAL e GRÁTIS: 5.000 chamadas/dia; preço, foto, leilão (lances + hora do fim). Cadastro em developer.ebay.com (~1 dia útil + passo de conformidade). **Território de caça novo e legal.**
- **Rakuten Ichiba API (IchibaItem/Search)** — oficial, grátis com app ID (Rakuten Developers). **A régua de preço novo oficial do método.**
- **Yahoo! Shopping API (itemSearch)** — oficial, grátis com Client ID (Yahoo!デベロッパーネットワーク). Idem.
- **Amazon PA-API** — exige conta Amazon Associates com vendas; deixar pra depois.
- Mercari: sem API pública — a raspagem atual continua sendo o caminho.

## TRADUÇÃO

- **DeepL** — o plano Free antigo (500 mil caracteres/mês) não se vende mais; conta nova ganha 1M de caracteres UMA vez só. O próprio olho já traduz. **Pular.**

## ORDEM DE PLUGUE RECOMENDADA (tudo ¥0 no nosso volume)

1. **Jina Reader** (leitura) — sem chave pra começar; esforço: uma tarde.
2. **Tavily** (busca + leitura reserva) — aposenta DDG/Yahoo raspados.
3. **OpenRouter** (terceira lente do olho) — desempate grátis.
4. **eBay + Rakuten** (produtos) — quando o caçador de produtos voltar à pauta.

Cada plugue = 1 chave nova no cofre do GitHub + 1 pedaço de código, sempre com o "pode" do Fabricio, um de cada vez.
