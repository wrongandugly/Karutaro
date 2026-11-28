# CATÁLOGO DE FONTES DA AGAINDEX
### De onde a casa bebe — fonte × o que dá × que sala alimenta × estado
Montado em 2026-11-28. Regra da casa: fato de mundo só entra com
fonte + data; "provado" = eu li a fonte ao vivo na data indicada.

## A ORDEM (definida com o Fabricio em 2026-11-28)
Critério: provado antes de não-provado · sem chave antes de com
chave · o que destrava sala antes de enfeite · terminar o aberto
antes de abrir o novo.
0. Fechar o aberto: coleta pousar + este catálogo na biblioteca.
1. **USGS no Oráculo** (provado, sem chave) — CÉU ganha "o mundo tremeu hoje".
2. **Nager.Date no Oráculo** (provado, sem chave) — CALENDÁRIO ganha os feriados do mundo (e a camada JP).
3. **Cadastro MLIT** (5 min, com ele) — destrava a prateleira CASA do QUANTO VALE?.
4. **Primeira caça de casa (Gyoda)** — relatório-teste da casa, duas camadas.
5. **World Bank** (sem chave) — o museu ganha o motor global.
6. **Listas vivas**: AMeDAS ("mais frio do Japão agora") + OpenAQ (ar do mundo).
7. **NASA + OpenSky** (chave grátis) — espetáculo: Terra e aviões ao vivo.
8. **As cestas do índice** — com a coleta andando, desenhar carro/banho/esqui.
9. **Conserto do Overpass** (a descoberta que falhou no formato).
10. **Publicação** — o "pode publicar" dele + endereço: a porteira de tudo.

## PROVADO (lido ao vivo)
| Fonte | O que dá | Alimenta | Provado em |
|---|---|---|---|
| JMA — previsão oficial (JSON, sem chave, CORS aberto) | tempo de hoje/amanhã por área, chuva %, máxima | Oráculo TEMPO (varal) — JÁ LIGADO | 2026-11-28 |
| JMA — AMeDAS (mapa JSON) | 1.286 estações: temperatura, chuva, vento AGORA | listas VIVAS ("o lugar mais frio do Japão agora") | 2026-11-28 |
| JMA — dados da sakura (páginas de dados) | 開花・満開 por cidade, série desde 1953 | sala/lista TEMPORADA | 2026-11-28 |
| P2P地震情報 API (grátis, sem chave) | terremotos do Japão em tempo real (hoje: 3 até 15h) | Oráculo CÉU/RUA — "o Japão tremeu hoje" | 2026-11-28 |
| MLIT — cadastro das 道の駅 | 1.234 estações, 1.229 com site oficial | Diretório/Sala de Honra — EM PRODUÇÃO | 2026-09-04 (registro) |
| MLIT — 不動産情報ライブラリ (reinfolib) | XIT001 transações 成約， XCT001 avaliações 鑑定， 地価公示， zoneamento, risco de desastre, escola/médico/estação/população | QUANTO VALE? casa | manual lido e API respondeu 401 (VIVA, pede a chave) em 2026-11-28 |
| HeartRails Express API (grátis, sem chave) | estações e linhas de trem (Yamanote: 30 estações) | Oráculo RUA / sala do trem | 2026-11-28 |
| Wikidata API (grátis) | cadastro estruturado do mundo (lugares, sites, coordenadas) | descoberta de listas e rankings | 2026-11-28 |
| Wikimedia Commons | fotos com licença livre (CC) | relatórios e capas | 2026-11-28 |
| MOTA (autoc-one) — tabela pública | 買取/下取り por ano e modelo, base resultados de leilão | QUANTO VALE? carro (camada da compra) | lido 2026-11-28 |
| Gulliver via kubotasmile — medianas públicas | mediana de avaliações por ano/modelo | QUANTO VALE? carro (conferência) | lido 2026-11-28 |
| Carsensor / 価格.com / UCAR — anúncios | preços pedidos, ano, km, loja | QUANTO VALE? carro (camada do pedido) + COLETA semanal | lido 2026-11-28 |

## PLUGADO NO ROBÔ (código pronto, esperando chave ou reteste)
| Fonte | O que dá | Estado |
|---|---|---|
| Overpass / OpenStreetMap | todos os lugares de um tipo numa área, com site e coordenadas | plugado (discover.py); o teste no servidor falhou no formato do pedido — consertar e retestar |
| Common Crawl | arquivo da web (páginas guardadas por domínio) | plugado (discover.py modo cc); sem teste ainda |
| Tavily (busca) | busca feita pra robô, 1.000 créditos/mês grátis | plug dormindo em hunter.py; falta a chave |
| OpenRouter (3º olho) | lente reserva de IA, camada grátis | plug dormindo; falta a chave |
| eBay Browse API | preços de produtos (5.000 chamadas/dia grátis) | plug dormindo (sweep_ebay); falta cadastro dev |
| Rakuten Ichiba API | preço novo mín–máx de produtos | plug dormindo; falta o app ID |

## MAPEADO (existe, é oficial — provar antes de usar)
| Fonte | O que dá | Alimenta |
|---|---|---|
| e-Stat API (governo; cadastro grátis) | censo, 空き家率 por cidade, **小売物価統計** (preço de varejo por cidade), emprego | listas ("cidade mais barata", "Japão vazio") + museu |
| JMA — terremotos/vulcões (feeds oficiais) | sismos e alertas vulcânicos (Fuji!) | Oráculo + E SE O FUJI ACORDAR? |
| Himawari (JMA/NICT) | foto da Terra a cada 10 min | Oráculo CÉU — "o Japão agora, do espaço" |
| 環境省 — 花粉 (はなこさん) | pólen ao vivo por estação | Oráculo TEMPORADA (a época sofrida) |
| 環境省 — そらまめくん | qualidade do ar (PM2.5 etc.) por estação | Oráculo CÉU/TEMPO |
| MLIT — 川の防災情報 | nível de rios e **貯水率 das represas** ao vivo | lista VIVA + Oráculo RUA |
| 資源エネルギー庁 — 石油製品価格調査 | **gasolina por província, toda semana** | lista VIVA "a gasolina mais barata do Japão" + BOLSO |
| 水産庁 —流通調査 | preço do peixe no atacado, por espécie e mercado | lista "o peixe da semana" （旬） |
| 厚労省 — 市区町村別生命表 | expectativa de vida por município | lista "onde se vive mais" |
| 国税庁 — 路線価 | valor fiscal da terra por rua | QUANTO VALE? casa (2ª camada de terra) |
| 国土数値情報 (MLIT) | arquivos do mapa: estações com passageiros, limites, uso do solo | esqueleto dos mapas + Oráculo RUA |
| PLATEAU (MLIT) | cidades em 3D oficiais | espetáculo visual (fase 2) |
| ハザードマップポータル (MLIT) | risco de inundação/deslizamento por endereço | QUANTO VALE? casa (camada do risco, tela pública) |
| RESAS API (内閣府; cadastro grátis) | economia regional: população, turismo, indústria | museu de dados |
| ODPT (cadastro grátis) | horários e **atrasos de trem em tempo real** | Oráculo RUA + sala do último trem |
| GTFS-JP | horários de ônibus abertos | sala do trem/ônibus |
| カーリル API | disponibilidade de livros em bibliotecas | ideia solta (lista de leitura) |
| GooBike / Mercari vendidos | moto e objetos: pedido × vendido | QUANTO VALE? moto/objetos |
| Rakuten Travel / Hot Pepper / Jalan (Recruit) | hotéis e restaurantes por área (grátis com chave) | listas de viagem e comida |
| Yahoo! Shopping API | preços de produtos (grátis com Client ID) | QUANTO TÁ? / BOLSO |
| JMA — 潮位 (marés) / 海上保安庁 | maré oficial por porto | lista de pesca/praia |

## PRATELEIRA GLOBAL (o gêmeo mundial de cada fonte — regra do Fabricio: nada nasce só-Japão)
O molde é global; o dado entra por país. O Japão é a primeira
prateleira porque é onde ele confere com os próprios olhos
(gabarito). Cada fonte japonesa tem seu gêmeo mundial:
| Japão | Mundo | Estado |
|---|---|---|
| JMA (tempo) | **Open-Meteo** (mundo inteiro, grátis, sem chave) | JÁ é a reserva do Oráculo — provado no protótipo |
| P2P地震 (sismos JP) | **USGS Earthquake API** (mundo, grátis, sem chave) | PROVADO 2026-11-28: 5 sismos M5+ desde ontem (Argentina, Laos, Chile) |
| (feriados JP) | **Nager.Date** (feriados de 100+ países, grátis) | PROVADO 2026-11-28: Brasil 2026 = 15 feriados |
| e-Stat (estatística JP) | **World Bank Open Data** + ONU/OMS/FAO + Our World in Data | mapeado (o museu global já nasceu com World Bank na receita) |
| MLIT imóveis | por país: Zillow (EUA), Idealista (ES/PT/IT)… o molde repete | mapeado |
| そらまめくん (ar JP) | **OpenAQ** (qualidade do ar do mundo) | mapeado |
| JMA sakura | fenologia local de cada país (ex.: cerejeiras de Washington — NPS) | mapeado |
| Overpass/OSM + Wikidata + Commons | **já nasceram globais** | em uso |
| Frankfurter (câmbio, BCE) | idem — o robô já usa pra USD→JPY | em produção no robô |
| eBay Browse | global (o plug do robô varre qualquer eBay) | plug dormindo |
| — (só mundo) | **NASA** (FIRMS: incêndios do planeta ao vivo; fotos da Terra), **OpenSky** (todos os aviões no céu, ao vivo), **GDACS** (alertas de desastre do mundo), **Smithsonian GVP** (todos os vulcões da Terra), **GeoNames** (todo lugar do mundo) | mapeado |

## RECUSADO (com o motivo)
- **Brave Search** — plano grátis acabou (fev/2026), exige cartão e proíbe guardar resultado.
- **Bing API** — aposentada em 2025-08-11. **Google Custom Search** — fechada pra novos, morre em 2027.
- **Firecrawl e Folo** — licença AGPL (a armadilha: contamina o produto).
- **Kakaku.com (preço de produtos)** — sem API pública.
- **USS (leilão de carros)** — dado só de lojista associado; a camada da compra vem das tabelas públicas (MOTA/Gulliver) calculadas sobre ele.
