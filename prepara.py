# -*- coding: utf-8 -*-
"""Mapa da Virada - DF : preparação dos dados.

Lê os arquivos OFICIAIS por seção do TSE (2026), filtra o DF, junta com o cadastro de
escolas (local de votação) e gera os CSVs usados pelo painel.

Cargos: governador (3) e presidente (1) — os dois do 2º turno no DF.
Cada linha do arquivo do TSE tem: zona, seção, local, cargo, nº do votável, votos e turno.
Branco = 95, Nulo = 96. O arquivo já traz a coluna NR_TURNO: quando sair o 2º turno,
basta rodar de novo que as linhas do turno 2 entram sozinhas.

Uso: python prepara.py
Saída: dados/escolas.csv, dados/zonas.csv, dados/candidatos.json, dados/validacao.txt
"""
import csv
import io
import json
import os
import re
import urllib.request
import zipfile
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "dados")
BRUTOS = os.path.join(DADOS, "brutos")
SAIDA_ESCOLAS = os.path.join(DADOS, "escolas.csv")
SAIDA_ZONAS = os.path.join(DADOS, "zonas.csv")
SAIDA_CAND = os.path.join(DADOS, "candidatos.json")
SAIDA_VALID = os.path.join(DADOS, "validacao.txt")

# cadastro oficial de locais de votação (escola, endereço, coordenadas, eleitores)
CADASTRO = r"C:\Users\caioh\Documents\py\eleicoes_df\secoes_2026_df\saida\locais_votacao_df_2026.csv"
# zona -> região administrativa (mesma tabela usada no painel do Max)
ZONAS_TS = r"C:\Users\caioh\Documents\js\apuracao-df-2026\src\data\zonas-df.ts"

CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao"
ARQUIVOS = {
    # apelido: (nome do zip, cargos que interessam nesse arquivo)
    "DF": ("votacao_secao_2026_DF.zip", {"3": "governador"}),
    "BR": ("votacao_secao_2026_BR.zip", {"1": "presidente"}),
}
CARGOS = {"3": "governador", "1": "presidente"}
EA20 = {  # arquivo de totalização oficial, por zona e no DF
    "governador": ("6259", "c0003"),
    "presidente": ("6257", "c0001"),
}
TURNO = "1"  # turno deste painel (o 2º entra quando o TSE publicar)
BRANCO, NULO = "95", "96"


# ------------------------------------------------------------------ utilidades
def n(v):
    return f"{int(v):,}".replace(",", ".")


def baixa(apelido):
    nome, _ = ARQUIVOS[apelido]
    destino = os.path.join(BRUTOS, nome)
    os.makedirs(BRUTOS, exist_ok=True)
    if not os.path.exists(destino) or os.path.getsize(destino) == 0:
        print(f"  baixando {nome}...")
        urllib.request.urlretrieve(f"{CDN}/{nome}", destino)
    print(f"  {nome}: {os.path.getsize(destino) / 1e6:.1f} MB")
    return destino


def le_zip(caminho):
    """Devolve (cabeçalho, gerador de linhas) do CSV dentro do zip."""
    z = zipfile.ZipFile(caminho)
    interno = [x for x in z.namelist() if x.endswith(".csv")][0]
    fh = z.open(interno)
    leitor = csv.reader(io.TextIOWrapper(fh, encoding="latin-1", newline=""), delimiter=";")
    cab = next(leitor)
    return cab, leitor


def vazio():
    return {"branco": 0, "nulo": 0, "compareceram": 0, "cand": defaultdict(int)}


# ------------------------------------------------------------------ 1. votos
print("== 1. lendo os arquivos oficiais por seção ==")
por_escola = defaultdict(vazio)      # (cargo, zona, local) -> votos
por_zona = defaultdict(vazio)        # (cargo, zona)        -> votos
nomes = defaultdict(dict)            # cargo -> numero -> nome oficial (do arquivo)
secoes = defaultdict(set)

for apelido, (nome_zip, cargos) in ARQUIVOS.items():
    caminho = baixa(apelido)
    cab, leitor = le_zip(caminho)
    i = {k: cab.index(k) for k in ("SG_UF", "NR_TURNO", "NR_ZONA", "NR_SECAO", "NR_LOCAL_VOTACAO",
                                   "CD_CARGO", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS")}
    lidas = 0
    for linha in leitor:
        if len(linha) < len(cab):
            continue
        if linha[i["SG_UF"]] != "DF" or linha[i["CD_CARGO"]] not in cargos:
            continue
        if linha[i["NR_TURNO"]] != TURNO:
            continue
        cargo = CARGOS[linha[i["CD_CARGO"]]]
        zona, local, secao = int(linha[i["NR_ZONA"]]), int(linha[i["NR_LOCAL_VOTACAO"]]), int(linha[i["NR_SECAO"]])
        votavel, votos = linha[i["NR_VOTAVEL"]], int(linha[i["QT_VOTOS"]] or 0)
        nomes[cargo][votavel] = linha[i["NM_VOTAVEL"]]
        for alvo in (por_escola[(cargo, zona, local)], por_zona[(cargo, zona)]):
            alvo["compareceram"] += votos
            if votavel == BRANCO:
                alvo["branco"] += votos
            elif votavel == NULO:
                alvo["nulo"] += votos
            else:
                alvo["cand"][votavel] += votos
        secoes[(cargo, zona, local)].add(secao)
        lidas += 1
    print(f"  {cargo}: {n(lidas)} linhas do DF (turno {TURNO})")

print(f"  escolas com votos: {len({(c, z, l) for (c, z, l) in por_escola})}")
print(f"  seções distintas: {len({(c, z, l, s) for (c, z, l), ss in secoes.items() for s in ss})}")

# ------------------------------------------------------------------ 2. cadastro
print("\n== 2. juntando com o cadastro de escolas ==")
texto = open(ZONAS_TS, encoding="utf-8").read()
RA = {str(int(m.group(1))): m.group(2) for m in re.finditer(r'"(\d{4})":\s*\{[^}]*?rotulo:\s*"([^"]+)"', texto)}
print(f"  zonas com RA: {len(RA)}")

cadastro = {}
with open(CADASTRO, encoding="utf-8-sig", newline="") as fh:
    for row in csv.DictReader(fh, delimiter=";"):
        cadastro[(int(row["zona"]), int(row["local"]))] = row
print(f"  escolas no cadastro: {len(cadastro)}")

# ------------------------------------------------------------------ 3. totalizações oficiais
print("\n== 3. lendo a totalização oficial (EA20) para conferir ==")


def pega_json(url):
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.load(r)


def oficiais_por_zona(cargo, zona):
    eleicao, ccargo = EA20[cargo]
    url = f"https://resultados.tse.jus.br/oficial/ele2026/{eleicao}/dados/df/df97012-z{zona:04d}-{ccargo}-e00{eleicao}-u.json"
    j = pega_json(url)
    return {str(c["n"]): int(c.get("vap") or 0)
            for agr in j["carg"][0]["agr"] for par in agr.get("par", []) for c in par.get("cand", [])}


def oficiais_df(cargo):
    eleicao, ccargo = EA20[cargo]
    url = f"https://resultados.tse.jus.br/oficial/ele2026/{eleicao}/dados/df/df-{ccargo}-e00{eleicao}-u.json"
    j = pega_json(url)
    globals()["_json_df_" + cargo] = j
    cands = [(str(c["n"]), c.get("nmu") or c.get("nm"), str(c.get("vap") or 0))
             for agr in j["carg"][0]["agr"] for par in agr.get("par", []) for c in par.get("cand", [])]
    return cands, j


def bonito(txt):
    """NOME OFICIAL EM MAIUSCULA -> Nome Oficial (mantendo as palavras curtas em minúscula)."""
    pequenas = {"de", "da", "do", "das", "dos", "e", "dos"}
    partes = []
    for p in str(txt).split():
        partes.append(p.lower() if p.lower() in pequenas and partes else p.capitalize())
    return " ".join(partes)


candidatos = {}
linhas_validacao = []
for cargo in ("governador", "presidente"):
    cands, j = oficiais_df(cargo)
    votos_of = {c[0]: int(c[2]) for c in cands}
    # nomes de urna oficiais
    lista = [{"numero": c[0], "nome": c[1], "votos_oficial": int(c[2])} for c in cands]
    lista.sort(key=lambda x: -x["votos_oficial"])
    dupla = [c["numero"] for c in lista[:2]]
    candidatos[cargo] = {"lista": lista, "dupla": dupla}
    print(f"  {cargo}: {len(lista)} candidatos | 2º turno: {dupla} "
          f"({[c['nome'] for c in lista[:2]]})")

    # conferência zona a zona (só candidatos com voto contado na totalização)
    ok = dif = 0
    for z in sorted({z for (c, z) in por_zona if c == cargo}):
        of = oficiais_por_zona(cargo, z)
        meu = por_zona[(cargo, z)]
        bate = all(meu["cand"].get(k, 0) == v for k, v in of.items())
        ok += bate
        dif += not bate
        if not bate:
            extras = {k: v for k, v in meu["cand"].items() if k not in of and v}
            faltam = {k: (meu["cand"].get(k, 0), v) for k, v in of.items() if meu["cand"].get(k, 0) != v}
            linhas_validacao.append(f"zona {z} ({cargo}): nao bate | fora da totalizacao: {extras} | diferentes: {faltam}")
    linhas_validacao.append(
        f"{cargo}: {ok}/19 zonas com TODOS os candidatos exatos | "
        f"branco {n(sum(por_zona[(cargo, z)]['branco'] for (c2, z) in por_zona if c2 == cargo))} | "
        f"nulo {n(sum(por_zona[(cargo, z)]['nulo'] for (c2, z) in por_zona if c2 == cargo))} | "
        f"compareceram {n(sum(por_zona[(cargo, z)]['compareceram'] for (c2, z) in por_zona if c2 == cargo))}"
    )
    print(f"    conferência: {ok}/19 zonas exatas")

open(SAIDA_VALID, "w", encoding="utf-8").write("\n".join(linhas_validacao) + "\n")

# ------------------------------------------------------------------ 4. CSVs do painel
print("\n== 4. gerando os CSVs do painel ==")
os.makedirs(DADOS, exist_ok=True)

# nome oficial (nome de urna, da totalização) com reserva no nome do arquivo por seção
def nome_do_candidato(cargo, numero):
    j = globals().get("_json_df_" + cargo) or {}
    for agr in j.get("carg", [{}])[0].get("agr", []):
        for par in agr.get("par", []):
            for c in par.get("cand", []):
                if str(c["n"]) == str(numero):
                    return bonito(c.get("nmu") or c.get("nm") or numero)
    return bonito(nomes[cargo].get(numero, numero))


candidatos_json = {}
for cargo in ("governador", "presidente"):
    numeros = sorted({k for (c, z, l), d in por_escola.items() if c == cargo for k in d["cand"]}, key=int)
    candidatos_json[cargo] = {
        "dupla": candidatos[cargo]["dupla"],
        "candidatos": [{"numero": num, "nome": nome_do_candidato(cargo, num)} for num in numeros],
    }
    print(f"   {cargo}: {len(numeros)} candidatos no painel -> "
          f"{[c['nome'] for c in candidatos_json[cargo]['candidatos']]}")
json.dump(candidatos_json, open(SAIDA_CAND, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def campos_de(cargo):
    return ([f"{cargo}_{c['numero']}" for c in candidatos_json[cargo]["candidatos"]]
            + [f"{cargo}_branco", f"{cargo}_nulo", f"{cargo}_compareceram"])


BASE = ["zona", "ra", "local", "escola", "bairro", "endereco", "latitude", "longitude", "eleitores", "n_secoes"]

with open(SAIDA_ESCOLAS, "w", encoding="utf-8-sig", newline="") as out:
    w = csv.writer(out, delimiter=";")
    w.writerow(BASE + campos_de("governador") + campos_de("presidente"))
    sem_cadastro = 0
    for (zona, local) in sorted(cadastro):
        cad = cadastro[(zona, local)]
        linha = [zona, RA.get(str(zona), ""), local, cad["escola"], cad["bairro"], cad["endereco"],
                 cad["latitude"], cad["longitude"], cad["eleitores"], cad["n_secoes"]]
        for cargo in ("governador", "presidente"):
            d = por_escola.get((cargo, zona, local))
            if d is None:
                sem_cadastro += 1
            for c in candidatos_json[cargo]["candidatos"]:
                linha.append(d["cand"].get(c["numero"], 0) if d else 0)
            linha += [d["branco"] if d else 0, d["nulo"] if d else 0, d["compareceram"] if d else 0]
        w.writerow(linha)
    print(f"   escolas: {len(cadastro)} | combinações escola+cargo sem votos: {sem_cadastro}")
print("   salvo:", SAIDA_ESCOLAS)

# por zona
with open(SAIDA_ZONAS, "w", encoding="utf-8-sig", newline="") as out:
    w = csv.writer(out, delimiter=";")
    w.writerow(["zona", "ra", "escolas", "eleitores", "secoes"] + campos_de("governador") + campos_de("presidente"))
    eleit_zona = defaultdict(int)
    escolas_zona = defaultdict(set)
    secoes_zona = defaultdict(int)
    for (zona, local), cad in cadastro.items():
        eleit_zona[zona] += int(cad["eleitores"])
        escolas_zona[zona].add(local)
        secoes_zona[zona] += int(cad["n_secoes"])
    for zona in sorted(eleit_zona):
        linha = [zona, RA.get(str(zona), ""), len(escolas_zona[zona]), eleit_zona[zona], secoes_zona[zona]]
        for cargo in ("governador", "presidente"):
            d = por_zona.get((cargo, zona))
            for c in candidatos_json[cargo]["candidatos"]:
                linha.append(d["cand"].get(c["numero"], 0) if d else 0)
            linha += [d["branco"] if d else 0, d["nulo"] if d else 0, d["compareceram"] if d else 0]
        w.writerow(linha)
print("   salvo:", SAIDA_ZONAS)

print("\n== validação ==")
print("\n".join(linhas_validacao))
