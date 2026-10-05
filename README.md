# Mapa da Virada - DF

Painel do **2º turno de 2026 no DF** (governador e presidente), por escola de votação, para
mostrar **onde está o voto que decide**: o reservatório (candidatos que saíram + brancos +
nulos + abstenções).

- 2º turno do **governador**: Celina Leão (11) × Leandro Grass (13)
- 2º turno do **presidente**: Flavio Bolsonaro (22) × Lula (13)

## Como o painel funciona

- **Uma página**: seletor de cargo (governador/presidente), filtro de zona/RA e busca por **escola,
  endereço ou bairro** (sem acento).
- **Mapa** com uma bolinha fixa por escola — **laranja** onde o nosso lado está na frente na escola,
  **azul** onde quem está na frente é o adversário. Tocar na bolinha abre a escola.
- **Cartão da escola escolhida** (pelo mapa, pelo seletor ou pela busca), com as seis fatias do
  eleitorado e o reservatório do 2º turno em destaque.
- Alternativas na própria página: **Ver todas as escolas** (cartões) e **Ver em tabela**; e o
  **resumo por zona/RA** no fim.

## De onde vêm os números (100% fonte oficial)

| dado | fonte |
|---|---|
| governador, senador, federal e distrital por seção | `votacao_secao_2026_DF.zip` (dados abertos do TSE) |
| presidente por seção | `votacao_secao_2026_BR.zip` (dados abertos do TSE) |
| escola, endereço, coordenadas e eleitores | `eleitorado_local_votacao_2026.zip` (cadastro do TSE) |
| zona → região administrativa | `apuracao-df-2026/src/data/zonas-df.ts` |

Os arquivos por seção têm **zona, seção, local, cargo, candidato, votos e `NR_TURNO`** — ou seja,
quando o TSE publicar o 2º turno, **é o mesmo arquivo**: basta rodar `prepara.py` de novo.

Contas do painel (cada cartão soma exatamente o eleitorado da escola):

```
compareceram = votos de todos os candidatos + brancos + nulos (do cargo, no local)
abstenção    = eleitores do local − compareceram
reservatório = outros candidatos + brancos + nulos + abstenção
```

Os "outros candidatos" são só candidaturas (branco e nulo ficam em linhas próprias), então as seis
linhas do cartão somam exatamente o eleitorado da escola.

## Conferência

`prepara.py` compara, zona a zona, os votos por candidato do arquivo por seção com a
totalização oficial (EA20) e grava o resultado em `dados/validacao.txt`.
Turno 1 de 2026: **19/19 zonas com todos os candidatos exatos** nos dois cargos.

Uma ressalva honesta: no governador, **José Roberto Arruda (55) tem 8.456 votos nas urnas que a
totalização oficial não contabiliza** (candidatura indeferida/sub judice) — o mesmo caso do
Leonardo (28) no presidente. Esses votos aparecem na linha "outros candidatos".

## Como rodar

```bash
python prepara.py     # baixa os arquivos oficiais, gera dados/*.csv e confere contra a totalização
streamlit run app.py  # abre o painel
```

## Como atualizar no 2º turno (25/10)

1. `python prepara.py` (baixa o arquivo atualizado; as linhas do turno 2 entram sozinhas)
2. ajustar `TURNO` em `prepara.py` para `"2"` e rodar de novo
3. subir no git — o Streamlit Cloud atualiza o app sozinho
