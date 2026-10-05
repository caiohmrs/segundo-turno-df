# Painel do 2º turno — DF 2026 (governador e presidente) — plano para discutir

> Arquivo de discussão. Responda nas linhas `Resposta:` (ou marque `[x]`) — eu leio o arquivo
> inteiro antes de mexer em qualquer coisa.

## 1. O que descobri hoje (05/10) — muda o jogo

O TSE **já publicou os arquivos oficiais por seção de 2026**. Não precisamos mais da colheita
de urna (aquela que a CDN tirou do ar):

| arquivo | tamanho | o que tem |
|---|---|---|
| `votacao_secao_2026_DF.zip` | 14,4 MB | **governador, senador, federal e distrital** — por zona, seção, **local**, cargo, candidato e votos, com branco (95) e nulo (96) |
| `votacao_secao_2026_BR.zip` | 51 MB | **presidente** (todas as UFs; filtramos o DF) |

Pontos que importam:

- **Cada linha tem `NR_TURNO`** — hoje só tem turno 1. Quando sair o 2º turno (25/10), é o
  **mesmo arquivo**, com turno 2 nas linhas. O painel pode ser feito já preparado para isso.
- Cada linha traz **zona, seção e local** — dá para montar tudo por escola e por zona sem depender de urna.
- **Abstenção** = eleitores do local (cadastro do TSE) − comparecimento (soma dos votos do cargo).
  O cadastro de locais eu já tenho (622 locais, com endereço e coordenadas).
- Validei contra a totalização oficial (EA20): **bate 100%**, com uma única exceção explicada abaixo.

### A exceção (importante, e não é erro nosso)

No cargo **governador**, o candidato **55 (José Roberto Arruda)** aparece nas urnas com **8.456
votos** no DF, mas a totalização oficial **não contabiliza nenhum** dele — indeferido/sub judice.
É o mesmo caso do candidato 28 (Leonardo) que já tínhamos achado no presidente. Nas outras 12
candidaturas os números batem **exato nas 19 zonas**.

## 2. O quadro do 1º turno (números oficiais)

**Governador do DF** — válidos 1.661.693 · brancos 74.774 (4,1%) · nulos 81.454 (4,5%)

| candidato | votos | % dos válidos |
|---|---|---|
| Celina Leão (11) | 825.530 | 49,68% |
| **Leandro Grass (13)** | 569.930 | 34,30% |
| Paula Moreno (45) | 140.765 | 8,47% |
| Caputo (30) | 72.148 | 4,34% |
| Ricardo Cappelli (40) | 36.828 | 2,22% |
| Arruda (55) | 8.456 | não contabilizado |
| Samara (80) | 3.958 | 0,24% |
| outros 4 | 4.078 | 0,25% |

→ **2º turno: Celina Leão (11) × Leandro Grass (13)**

**Presidente no DF** — brancos 25.362 · nulos 33.169 (muito menos que no governador)

| candidato | votos no DF |
|---|---|
| Flávio Bolsonaro (22) | 909.616 |
| **Lula (13)** | 675.627 |
| Caiado (55) | 85.076 |
| Renan (14) | 46.714 |
| Cury (70) | 45.979 |
| Zema (30) | 4.915 |
| Samara (80) | 2.297 |
| outros 6 | 2.641 |

→ **2º turno: Flávio (22) × Lula (13)**

**Abstenção no DF: 426.067 (19,0% dos 2.243.988 aptos)** — é o maior "reservatório" de todos:
maior que todos os votos de branco+nulo somados.

## 3. O que o painel deve mostrar (minha proposta)

O foco que você pediu — **quem sobra no 1º turno** — vira o coração do painel. Por escola:

- **Disputa**: Celina × Grass (governador) e/ou Flávio × Lula (presidente)
- **Reservatório do 2º turno**: brancos + nulos + **abstenções** + votos dos candidatos que saíram
  (Paula Moreno, Caputo, Cappelli, etc.) — os votos que vão decidir

### Telas propostas (uma de cada vez, como fizemos no painel do Max)

1. **Escolas** (cartões) — uma escola por cartão, com barras: os dois do 2º turno, os outros
   candidatos e branco/nulo/abstenção
2. **Onde tem voto a recuperar** — ranking por escola (e por zona/RA) ordenado pelo tamanho do
   reservatório (branco + nulo + abstenção + votos dos que saíram), com o voto do Grass/Lula do lado
3. **Zonas** — o mesmo resumo agregado por zona/RA

Filtros na própria página (sem sidebar), igual ao painel do Max: zona/RA, busca por escola, e um
seletor de cargo (Governador / Presidente) e de turno (1º — e 2º quando sair).

## 4. Perguntas

1. **Estrutura:** uma página só com seletor de cargo (Governador/Presidente), ou duas páginas
   (uma de governador, uma de presidente)? — `Resposta:`
2. **Base:** por escola (como no painel do Max) — quer também por seção (dentro da escola)? — `Resposta:`
3. **O foco:** o ranking "onde tem voto a recuperar" deve somar branco + nulo + abstenção + votos
   dos candidatos que saíram? Ou prefere separar cada um? — `Resposta:`
4. **Quando sair o 2º turno (25/10):** quer o comparativo 1º × 2º turno no mesmo painel
   (só troca o turno), ou prefere um painel novo só do 2º turno? — `Resposta:`
5. **Visual:** mantenho o mesmo (Streamlit, laranja #ff6a00 + grafite, cartões, tema claro/escuro)? — `Resposta:`
6. **Repositório:** publico em `caiohmrs/segundo-turno-df` (mesmo esquema do votos-max, deploy no
   Streamlit Cloud)? — `Resposta:`
7. **Nome do painel** na faixa do título (ex.: "2º Turno DF 2026 — Governador e Presidente") — `Resposta:`

## 5. Como vou executar (depois das respostas)

- [ ] Pasta `C:\Users\caioh\Documents\py\2o turno` com o pipeline (baixa os dois zips, filtra o DF, junta com o cadastro de locais)
- [ ] CSVs de saída: por escola, por zona e por seção (governador e presidente, com branco/nulo/abstenção)
- [ ] Conferência contra a totalização oficial (EA20) zona a zona, como fizemos no Max
- [ ] App Streamlit com as telas acima, no mesmo molde visual
- [ ] Publicar no repositório e subir no Streamlit Cloud
