# -*- coding: utf-8 -*-
"""Mapa da Virada - DF : carregamento, métricas e visual do painel.

Sem barra lateral: os filtros são desenhados na própria página.

Regra das contas (tudo sai dos arquivos oficiais por seção do TSE, 2026):
    compareceram = votos de todos os candidatos + brancos + nulos (do cargo, no local)
    abstenção    = eleitores do local (cadastro do TSE) − compareceram
    reservatório = votos dos outros candidatos + brancos + nulos + abstenção
                 = tudo o que NÃO foi para os dois que ficaram no 2º turno

Os "outros candidatos" são só candidaturas (brancos e nulos ficam em linhas próprias), por isso as
seis linhas do cartão somam exatamente o eleitorado da escola:
    nosso + adversário + outros + brancos + nulos + abstenção = compareceram + abstenção = eleitores
"""
import json
import os
import unicodedata

import pandas as pd
import streamlit as st

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "dados")

NOSSO_NUMERO = "13"  # Leandro Grass (governador) e Lula (presidente) — o nosso lado do 2º turno

CARGO_ROTULO = {"governador": "Governador", "presidente": "Presidente"}


# ------------------------------------------------------------------ dados
def sem_acento(txt) -> str:
    """'Águas Claras' -> 'AGUAS CLARAS' (busca funciona sem acento)."""
    limpo = "".join(c for c in unicodedata.normalize("NFKD", str(txt)) if not unicodedata.combining(c))
    return limpo.upper()


@st.cache_data(show_spinner=False)
def escolas() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DADOS, "escolas.csv"), sep=";", dtype={"zona": str, "local": str})
    numericas = ([c for c in df.columns if c[:1].isalpha() and "_" in c and c.split("_")[0] in CARGO_ROTULO]
                 + ["eleitores", "n_secoes"])
    for c in numericas:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    for c in ("latitude", "longitude"):
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    # campo único de busca: escola + endereço + bairro, sem acento
    df["busca"] = (df["escola"].fillna("") + " " + df["endereco"].fillna("")
                   + " " + df["bairro"].fillna("")).map(sem_acento)
    return df


@st.cache_data(show_spinner=False)
def zonas() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DADOS, "zonas.csv"), sep=";", dtype={"zona": str})
    for c in df.columns:
        if c not in ("zona", "ra"):
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(show_spinner=False)
def candidatos() -> dict:
    return json.load(open(os.path.join(DADOS, "candidatos.json"), encoding="utf-8"))


# ------------------------------------------------------------------ métricas
def metricas(df: pd.DataFrame, cargo: str) -> pd.DataFrame:
    """Devolve o df com as colunas que o painel usa (nosso, adversario, outros, ...)."""
    info = candidatos()[cargo]
    dupla = list(info["dupla"])
    if NOSSO_NUMERO not in dupla:          # segurança: se um dia nosso candidato não for da dupla
        dupla = [NOSSO_NUMERO] + [n for n in dupla if n != NOSSO_NUMERO]
    adversario = next(n for n in dupla if n != NOSSO_NUMERO)
    outros_nums = [c["numero"] for c in info["candidatos"] if c["numero"] not in dupla]
    nomes = {c["numero"]: c["nome"] for c in info["candidatos"]}

    d = df.copy()
    d["nosso"] = d[f"{cargo}_{NOSSO_NUMERO}"]
    d["adversario"] = d[f"{cargo}_{adversario}"]
    d["outros"] = d[[f"{cargo}_{n}" for n in outros_nums]].sum(axis=1)
    d["brancos"] = d[f"{cargo}_branco"]
    d["nulos"] = d[f"{cargo}_nulo"]
    d["bn"] = d["brancos"] + d["nulos"]
    d["compareceram"] = d[f"{cargo}_compareceram"]
    d["abstencao"] = d["eleitores"] - d["compareceram"]
    d["reservatorio"] = d["outros"] + d["bn"] + d["abstencao"]
    d["nosso_nome"] = nomes[NOSSO_NUMERO]
    d["adversario_nome"] = nomes[adversario]
    return d


def n(v) -> str:
    return f"{int(v):,}".replace(",", ".")


def pc(parte, total, casas: int = 1) -> str:
    if not total:
        return "—"
    return f"{parte / total * 100:.{casas}f}%".replace(".", ",")


# ------------------------------------------------------------------ identidade visual
# paleta do app do PDAF (#ff6a00 laranja + #1f2937 grafite), funcionando no claro e no escuro
NOSSO = "#ff6a00"        # Leandro Grass / Lula
ADVERSARIO = "#1f6feb"   # Celina Leão / Flavio Bolsonaro
CINZA = "#94a3b8"        # candidatos que saíram
BRANCO_C = "#eab308"     # brancos
NULO_C = "#ef4444"       # nulos
ABST_C = "#6b7280"       # abstenção
GRAFITE = "#1f2937"

CSS = """<style>
.faixa{background:#1f2937;border-bottom:4px solid #ff6a00;border-radius:10px;
       padding:14px 18px;margin-bottom:16px}
.faixa .t{color:#ff6a00;font-weight:800;font-size:26px;line-height:1.15}
.faixa .s{color:#ffffff;opacity:.9;font-size:14px;margin-top:2px}
.vi{margin-bottom:8px;padding:10px 12px;border:1px solid rgba(128,128,128,.32);border-radius:10px}
.vi .e{font-weight:600;line-height:1.25;overflow-wrap:anywhere}
.vi .end{font-size:12px;line-height:1.2;opacity:.8;margin-top:1px;overflow-wrap:anywhere}
.vi .s{font-size:12px;opacity:.65;margin-bottom:4px}
.vi .l{display:flex;align-items:center;gap:8px;margin-top:3px}
.vi .r{flex:0 0 42%;font-size:12px;line-height:1.15;overflow-wrap:anywhere}
.vi .b{flex:1;min-width:0}
.vi .b i{display:block;height:9px;border-radius:5px}
.vi .v{flex:0 0 74px;text-align:right;font-size:13px;white-space:nowrap}
.vi .v small{display:block;font-size:11px;opacity:.7;font-weight:400}
.vi .pit{font-size:11px;opacity:.6;margin-left:6px}
.vi .res{margin-top:7px;padding-top:6px;border-top:1px dashed rgba(128,128,128,.45);font-size:13px}
.vi .res b{font-weight:700}
.rodape{margin-top:24px;padding-top:10px;border-top:1px solid rgba(128,128,128,.3);
        font-size:12px;opacity:.75;text-align:center}
</style>"""


def faixa(titulo: str, subtitulo: str) -> None:
    st.markdown(f'{CSS}<div class="faixa"><div class="t">{titulo}</div>'
                f'<div class="s">{subtitulo}</div></div>', unsafe_allow_html=True)


def rodape(texto: str = "Criado por Caio Henrique Machado - DF") -> None:
    st.markdown(f'<div class="rodape">{texto}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ filtros na página
def seletor_zonas(df: pd.DataFrame, prefixo: str):
    zonas = sorted(df["zona"].unique(), key=int)
    rotulos = {z: f"zona {int(z):02d} · {df.loc[df['zona'] == z, 'ra'].iloc[0]}" for z in zonas}
    return st.multiselect("Zona / RA", zonas, format_func=lambda z: rotulos[z],
                          key=f"{prefixo}_zonas", placeholder="todas as zonas")


def busca_escola(prefixo: str, label: str = "Buscar escola, endereço ou bairro"):
    return st.text_input(label, "", key=f"{prefixo}_busca",
                         placeholder="ex.: la salle, SQS 102, águas claras")


def filtra(df: pd.DataFrame, zonas=None, busca: str = "") -> pd.DataFrame:
    """Filtros na mão do usuário — nunca automáticos. A busca cobre escola, endereço e bairro."""
    f = df
    if zonas:
        f = f[f["zona"].isin(zonas)]
    if busca and busca.strip():
        f = f[f["busca"].str.contains(sem_acento(busca.strip()), regex=False)]
    return f
