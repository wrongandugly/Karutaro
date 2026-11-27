# SALA VAI ACONTECER? — análise completa (2026-11-27)

> Pedido do Fabricio: "faça todas as análises e visões possíveis dessa sala antes de concluirmos".
> Fontes: duas pesquisas ao vivo de 2026-11-27 (cenário global + Japão), relatórios com fontes por afirmação.
> Status: análise entregue no chat; decisões do Fabricio pendentes (lista no fim).

## A ideia
Sala de previsões estilo Polymarket, SEM dinheiro: perguntas sobre o futuro (esporte, tempo/natureza, dinheiro, mundo), cada uma com prazo e fonte oficial nomeada como "apito" antes do primeiro palpite. O povo vota SIM/NÃO; a média vira probabilidade viva; no prazo, a fonte oficial resolve; quem acertou soma reputação (taxa de acerto/cartão). É o pilar VAI da casa ("previsões sem dinheiro") ganhando porta. Nome proposto: VAI ACONTECER?

## Cenário global (provado, com fontes)
- Polymarket (dinheiro, cripto): volume anualizado 2026 ≈ US$105 bi, 700 mil+ usuários únicos/mês (Alea Research, nov/2026). Resolução por UMA Optimistic Oracle (caução ~US$750, disputa por voto de token). Valuation US$9 bi (rodada ICE, out/2025); US$21 bi reportado ago/2026, não confirmado como fechado.
- Kalshi (dinheiro, bolsa regulada CFTC): valuation US$40 bi (Series G, 29/10/2026); esporte = 78–87% do volume (Pew, set/2026); distribuição alugada (Robinhood >50% do fluxo); 20+ estados processaram/ordenaram saída.
- Manifold (play money): moeda Mana nunca sacável; dá pra COMPRAR Mana (irreversível). Set/2026: ~58 mil visitantes/dia, só ~700 traders ativos/dia, ~3.000/mês. O fim do componente resgatável (Sweepcash, mar/2025) cortou a atividade pela metade. O que segura: reputação, ligas, comunidade (racionalista/EA), liberdade de tópicos.
- Metaculus (reputação pura): 50 mil+ usuários, 15 mil+ perguntas, 1M+ previsões; Brier agregado ~0,107–0,111 (melhor histórico público). Vive de grants (US$8,8 mi+) + Metaculus Pro (torneios privados pagos por organizações).
- Precisão sem dinheiro: estudos revisados (Servan-Schreiber et al. 2004; Rosenbloom & Notz 2006; Atanasov et al. 2017) — play money ≈ dinheiro real em precisão; desenho da pergunta + agregação + seleção importam mais que a aposta.
- Retenção: engajamento segue EVENTO, não hábito — pós-Copa 2026, traders mensais da Polymarket caíram pela metade (667 mil → 336 mil). A maioria LÊ a probabilidade; minoria prevê (Manifold: ~1% dos visitantes/dia tradam).
- Maior risco estrutural do setor: DISPUTA DE RESOLUÇÃO (mercado do "terno do Zelensky", ~US$210 mi, jul/2025; mercado de minerais resolvido por whale de tokens UMA). Defesa: fonte nomeada + regra escrita antes + saída ANULADA.

## Japão (provado, com fontes)
- Lei: apostar bem patrimonial em resultado incerto = 賭博罪 (CP arts. 185/186); habilidade/análise NÃO elimina o acaso (Tribunal Distrital de Tóquio, 14/05/2015). Desde 25/09/2025, também é proibido APRESENTAR/INDUZIR sites ilegais de jogo (Lei de Medidas contra Dependência, art. 9-2). Polymarket em modo close-only para IPs JP; Bitbank ameaça suspender contas ligadas. FSA (abr/2026): "extrema cautela"; liga do PLD discute o tema (nov/2026); Polymarket mira aprovação JP até 2030.
- Sem dinheiro = legalidade POR DESENHO (análises Parks Law; Nagashima Ohno, out/2026): pontos gratuitos, não conversíveis, não transferíveis = zona segura. Pontos trocáveis por produtos + risco de perda = zona cinzenta (Parks, conservadora). Prêmios a usuários: regulados pela 景品表示法.
- Concorrentes JP já operando: MIRAIMA (Masentic, lançado 19/11/2025, "primeiro mercado de previsão do Japão"; pontos grátis ou comprados, trocáveis por PayPay/Rakuten/Amazon a partir de ~¥500; supervisão de grande escritório + lab Waseda; investimento de Keisuke Honda; empresa alega 1M usuários/mês — NÃO auditado) e POYP (HIMOROGI; pontos→moedas→えらべるPay; já tem perguntas de sakura e pólen). Nandora (なんドラ): previsão gratuita esporte+entretenimento, prêmios físicos por ranking, receita por PATROCÍNIO (100+ colaborações), conformidade TMI, acelerado pela Agência de Esportes. Precedente clássico: Yahoo!ズバリ予想 (2007) — pontos ヨソポ explicitamente não trocáveis. EsperaGol repete no site: pontos não compráveis/não resgatáveis = "não é jogo de azar".
- Cultura: JMA publicou previsão de sakura de 1951 a 2009 e SAIU (empresas privadas bastavam); hoje 5 empresas competem publicamente (WeatherNews, Weather Map, JWA, LBW, 日本気象) e a mídia compara acertos. 議席予測 dos jornais = gênero fixo de eleição. WeatherNews さくらプロジェクト: 2M+ relatórios da multidão. Ângulo "multidão × previsão oficial" como produto dedicado: NÃO encontrado (ausência de evidência) — espaço aparentemente livre.

## Mecânica proposta (desenho Jarbas)
- Cartão da pergunta: pergunta + prazo + apito (fonte oficial nomeada) + regra de resolução escrita ANTES. Média do povo só aparece com 100+ palpites (regra da casa; pesquisa confirma fragilidade <50).
- Palpite v1: SIM/NÃO + taxa de acerto + sequência (streak) no cartão pessoal. Nota tipo Brier (pune chute covarde/confiante errado) entra com o controle de % numa v2.
- O KARUTARO JOGA: nas perguntas de dado (tempo, sakura, mercado), o robô publica a previsão dele a partir de fontes/modelos oficiais — liga "você × o povo × o robô". Nenhum concorrente JP faz isso.
- Série âncora: O POVO × A PREVISÃO OFICIAL (sakura vs WeatherNews/JWA; eleições vs jornais) — ângulo sem dono no Japão.
- Ritmo: 3–5 perguntas/semana feitas à mão no começo (palavra mal escrita = disputa). Séries: jogo grande da semana; sakura (março); Copa Feminina 2027 no Brasil (24/6–25/7/2027) como primeira mega-série; especiais de fim de ano (primeira neve, fechamento do Nikkei).
- Resolução: prazo → robô confere a fonte nomeada → resultado + citação arquivados NESTA biblioteca → cartões atualizados. Pergunta quebrada (fonte some/muda) = ANULADA, ninguém ganha nem perde.
- Lista proibida (blindagem de marca, igual à Kalshi): nada de morte, desastre com vítima, crime. Sem login (identidade no aparelho, como o MYFUKU) + a mesma caixa de dados dos votos. Perguntas de usuários: NÃO no lançamento (curadoria nossa).

## Riscos (honestos)
1. Partida fria: termômetro com poucos votos mente. Mitigação: regra dos 100+, perguntas-semente empurradas pelo Instagram, cartão individual funciona desde o dia 1.
2. Assimetria ler×prever (~1% prevê): o cartão tem que valer como LEITURA (a % é a notícia), não só como urna.
3. Dependência de evento: cadência semanal + séries sazonais, nunca só evento.
4. Concorrência: MIRAIMA tem 1 ano de frente, dinheiro e advogados — mas o modelo deles (pontos→vale) atrai caçador de ポイ活, não fã de previsão; e é app (instalação) contra nossa web sem login. Nosso canto: pureza reputacional + apito oficial + a casa em volta (diretório alimenta tráfego).
5. Trabalho editorial semanal (perguntas + resoluções): eu + robô, limitado por desenho.
6. Clima regulatório esquentando (FSA/PLD 2026): o desenho conservador é a proteção; se um dia legalizarem dinheiro, nosso ativo é a multidão + históricos + marca, não a mecânica.

## Dinheiro (dentro do mapa dos 7 pagadores)
- Série patrocinada (modelo Nandora: marcas pagam pela série da semana).
- Sala de apoio (modelo Pudding/Patreon) — a casa se sustenta, a sala é uma das razões.
- B2B futuro: salas privadas de previsão interna para empresas (a análise da Parks cita esse uso como legal e viável).
- Tráfego cruzado: perguntas de neve/sakura empurram pras prateleiras de esqui/michi do diretório.
- NUNCA: vender voto/dado (doutrina), vender pontos (lei + pureza).

## Futuro
- Temporadas com campeão (年間予想王 — título que a Nandora prova funcionar).
- ALMANAQUE de fim de ano: todas as perguntas resolvidas, placar povo × oficial × robô — conteúdo puro Againdex.
- Integração com o VEREDITO DE HOJE: a pergunta do dia do oráculo é a porta de entrada diária da sala.
- Segundo país quando o inglês provar (o formato viaja; as fontes oficiais mudam).

## Decisões pendentes do Fabricio
1. Pureza travada? (só reputação, zero prêmio no lançamento)
2. Nome: VAI ACONTECER? trava?
3. Categorias de estreia: esporte + tempo/natureza primeiro; dinheiro/mundo depois?
4. O robô joga? (recomendação: sim)
5. Política/eleição entra? (cultura JP diz sim; cuidado redobrado na escrita)
6. Pontuação v1 simples (acerto + streak), Brier na v2?
