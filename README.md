# KARUTARO — Manual do dono

*Você pede. Ele caça.*
Este arquivo é o manual do sistema, escrito para o dono (Fabricio), em linguagem simples.
Se um dia o Jarbas (o assistente que construiu isto) sumir, **este manual + este repositório são tudo o que qualquer pessoa precisa para cuidar do Karutaro.**

---

## O mapa — são 4 peças

| Peça | O que é | Onde |
|---|---|---|
| **A página** | A vitrine onde você pede e lê as entregas | https://wrongandugly.github.io/Karutaro/ (com **K maiúsculo** — o endereço é sensível a isso) |
| **O robô** | O programa `hunter.py`, que varre Yahoo! Auctions, Yahooフリマ, Jimoty, Up Garage, Mercari e Rakuten | neste repositório |
| **A vigia** | O relógio do GitHub Actions (`.github/workflows/hunt.yml`) que acorda o robô **a cada 6 horas** e quando chega um pedido novo | aba **Actions** deste repositório |
| **O caderno** | Os arquivos `wants.json` (os pedidos), `board.json` e `results-N.json` (as entregas) e `facts.json` (a biblioteca de fatos lidos) | neste repositório |

## Como saber se está vivo (30 segundos)

1. **Abra a página.** No topo, "última varredura" mostra quando o robô trabalhou pela última vez. Nunca deve passar de ~6 horas.
2. **Aba Actions do repositório.** As corridas "karutaro-hunt" devem estar verdes. Vermelho = alguma fonte ou o robô falhou naquela rodada (a entrega anterior continua valendo).
3. **Commits chamados "caca: entrega atualizada".** É a assinatura do robô gravando uma entrega nova no caderno.

## Como pedir uma caça

1. Na página, preencha o formulário (o quê, tipo produto ou fato, teto, detalhes) e aperte o botão vermelho.
2. Abre a tela do GitHub com tudo preenchido — aperte o botão verde **Submit new issue**. (Essa tela é a confirmação; sem ela o pedido não entra.)
3. Em alguns minutos a entrega aparece na página (recarregue) e um comentário do robô aparece naquela issue.

## Se o Jarbas sumir

**Continua funcionando sozinho, sem ele:**
- A vigia de 6 em 6 horas, as caçadas, as entregas na página, o formulário.
- O robô **não usa nenhuma chave do Jarbas para trabalhar** — ele roda com a permissão interna do próprio GitHub Actions.

**Para:**
- Consertos quando um site muda o formato (o robô marca a fonte como "não respondeu" e segue com as outras).
- Funções novas e a leitura dos fatos "indecisos" (o turno do olho, enquanto o leitor for o Jarbas).

**O que fazer:** qualquer programador ou outro assistente de IA consegue assumir. Mostre a essa pessoa **este manual e o arquivo `hunter.py`** — está tudo em um repositório público, sem peças escondidas.

## Chaves e contas — o que é de quem

- **Sua conta do GitHub é a chave-mestra de tudo** (deste robô, do MYFUKU e do jogo — tudo mora nela). Guarde a senha e a verificação em duas etapas dela como guarda a chave de casa. Se perder o GitHub, perde o acesso a tudo; sem ele, o Jarbas não é problema nenhum.
- **O token "Jarbas"** (acesso rápido do assistente a este repositório) **vence em 19/02/2027** e pode ser revogado por você a qualquer momento em Settings → Developer settings → Personal access tokens. Revogar corta o acesso do Jarbas — **o robô não é afetado**.
- **A chave do Gemini** (se um dia for criada para o olho) fica no cofre do GitHub: Settings do repositório → Secrets and variables → Actions → `GEMINI_API_KEY`. A cota do Gemini é **por projeto do Google**: chave em projeto novo = cota separada da do MYFUKU.

## Problemas conhecidos

- **Página dá 404:** confira o **K maiúsculo** no endereço (`/Karutaro/`). Se persistir, veja se o Pages está ligado: Settings → Pages → Deploy from a branch → main / (root).
- **Entrega veio vazia:** pode ser mercado (nada dentro do teto) ou fontes fora do ar naquela rodada — a própria página lista quais fontes não responderam.
- **Caça de fato diz "o olho ainda não foi ligado":** falta a chave do Gemini no cofre (acima), ou o leitor ainda é o Jarbas e a leitura está na fila.
- **Pedido duplicado:** enviar o formulário duas vezes cria dois pedidos iguais; um deles pode falhar na gravação — o caderno fica com um só. Sem dano.

## Os arquivos (uma linha cada)

- `index.html` — a página inteira (formulário + quadro de entregas).
- `hunter.py` — o robô: fontes, classificação, vereditos, o olho e a trava da citação.
- `intake.py` — transforma a issue do formulário em pedido no caderno.
- `wants.json` — os pedidos ativos. `board.json` — a entrega mais recente (é o que a página lê).
- `results-N.json` — a entrega de cada pedido. `facts.json` — a biblioteca de fatos (lugar, veredito, trecho, data).
- `.github/workflows/hunt.yml` — a vigia (gatilhos: pedido novo, mudança no caderno, relógio de 6h).
- `hunter.log` — o diário do robô, útil para qualquer pessoa diagnosticar uma falha.

---

*Manual escrito em 25/11/2026, junto com a primeira noite de vigia do Karutaro.*
