# Biblioteca do Karutaro

O caderno de fatos verificados do caçador. Tudo aqui foi lido em **fonte oficial**
(site da estação, prefeitura, associação oficial ou ministério), com a citação
japonesa palavra por palavra, o link da fonte e a data da leitura guardados
junto de cada fato. O que a fonte oficial não diz fica **NÃO DIZ** (null) —
nunca chutado, nunca importado de agregador.

Transferida em 27/11/2026 por ordem do Fabricio. Regra permanente dele, da
mesma data: **toda pesquisa de dados feita pro Againdex ensina o robô** —
o resultado entra nesta biblioteca, neste formato.

## O método (como cada fato nasce)

1. Só página oficial vale como prova. Agregador, blog e buscador não provam nada.
2. Cada campo carrega: veredito + citação verbatim (JP) + URL da fonte + data.
3. Fronteiras duras:
   - Onsen/banho "perto" NÃO conta como banho da estação — só o da própria.
   - Tabela de preço de temporada antiga NÃO é reaproveitada; sem tabela
     vigente, o preço fica null com o motivo escrito.
   - Enumeração oficial completa sem o item = NÃO TEM; página sem enumeração
     = NÃO DIZ. São vereditos diferentes.
   - Proibição de pernoite só existe se a estação a publica por escrito.
   - Resposta em duas camadas quando a regra e a prática diferem:
     REGRA OFICIAL × PRÁTICA REAL, cada uma rotulada.
4. A contagem de cada província é conferida no registro oficial, nunca assumida.
5. Fechamento, reforma e mudança de endereço são registrados como alerta de
   atualidade na ficha — o dado apodrece, a ficha avisa.

## Conteúdo

### michi/ — estações de estrada (michi-no-eki)
- `base.json` — as 1.234 estações do registro MLIT de 4/9/2026 (nome, município,
  data de registro, site oficial).
- `ondas/*.json` — leituras a fundo, província a província. Em 27/11/2026:
  Saitama 21, Nagano 53, Gifu 55, Hokkaido 128 (a+b), Niigata 42, Yamagata 24,
  Fukushima 37 lidas; 340 casadas na página. Restam ~894 em 40 províncias.
- `municipios-coordenadas.json` — coordenadas (nível de município, aproximadas)
  de 835 dos 870 municípios com estação. Pino de mapa, não endereço.

### esqui/ — estações de esqui
- `ricas.json` — 105 fichas lidas na página oficial (preço 2026-27, regra de
  criança, nighter, temporada): Nagano e Hokkaido completas + Kagura e Zao.
- `niigata-parcial.json` — 52 de 55 lidas (onda interrompida; completar).
- `urls-oficiais.json` — site oficial das 375 estações da base (associação).

### banho/ — onde tomar banho fora de casa
- `onsen.json` — 6 onsen de excursão verificados um a um (tatuagem, criança,
  preço, banho privativo), região de Yudanaka/Shibu.
- `sento.json` — 563 casas de banho públicas em 6 províncias de Kantō, com a
  tarifa oficial (統制額) de cada província e a posição sobre tatuagem quando
  a associação a publica. Faltam 41 províncias.
- `cafes.json` — 481 lojas Kaikatsu Club com chuveiro (457 grátis, 24 pagas),
  endereço e página oficial de cada loja. Horário por loja não é publicado
  pela rede: NÃO DIZ, nunca "24h" presumido.

## Como isto se usa

- As páginas do Againdex (michi-no-eki, esqui, banhos) são geradas a partir
  destes dados.
- Quando o olho do robô ligar (rotação Groq + Gemini), ele relê as fontes,
  compara com este caderno e aponta o que mudou — preço novo, fechamento,
  reforma — em vez de começar do zero.
