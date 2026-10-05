# -*- coding: utf-8 -*-
"""Mapa da Virada - DF : painel do 2º turno (governador e presidente), escola por escola.

Uma página: seletor de cargo, filtros na própria página, **mapa clicável** e o cartão da escola
escolhida (pelo mapa, pelo seletor ou pela busca). A lista completa de cartões e a tabela ficam
em opções na própria página. Rodapé com o crédito no fim.
"""
import streamlit as st

import dados

st.set_page_config(page_title="Mapa da Virada - DF", page_icon="🗺", layout="wide")

base = dados.escolas()

dados.faixa(
    "Mapa da Virada - DF",
    "2º turno 2026 · governador e presidente · toque no mapa ou busque a escola",
)

# ---------------------------------------------------------------- filtros na própria página
c1, c2, c3 = st.columns([1, 2, 2])
with c1:
    rotulo = st.radio("Cargo", list(dados.CARGO_ROTULO.values()), key="mv_cargo")
with c2:
    zonas = dados.seletor_zonas(base, "mv")
with c3:
    busca = dados.busca_escola("mv")

cargo = next(k for k, v in dados.CARGO_ROTULO.items() if v == rotulo)
m = dados.metricas(base, cargo)
f = dados.filtra(m, zonas, busca)

ORDENS = {
    "Reservatório do 2º turno (maior primeiro)": "reservatorio",
    "Abstenção (maior primeiro)": "abstencao",
    "Brancos + nulos (maior primeiro)": "bn",
    "Votos do nosso lado (maior primeiro)": "nosso",
    "Votos do adversário (maior primeiro)": "adversario",
    "Nome da escola (A→Z)": "escola",
}
o1, o2, o3, o4 = st.columns([3, 2, 2, 2])
ordem = o1.selectbox("Ordenar por", list(ORDENS), key="mv_ordem")
detalhar = o2.toggle("Detalhar um por um", key="mv_detalhar",
                     help="mostra, dentro do cartão, o voto de cada candidato que saiu do 2º turno")
ver_tabela = o3.toggle("Ver em tabela", key="mv_tabela")
ver_todas = o4.toggle("Ver todas as escolas", key="mv_todas",
                      help="em vez do cartão da escola escolhida, lista os cartões de todas as escolas filtradas")

coluna_ordem = ORDENS[ordem]
f = f.sort_values(coluna_ordem, ascending=(coluna_ordem == "escola")).reset_index(drop=True)

# ---------------------------------------------------------------- números do filtro
aptos = int(f["eleitores"].sum())
reserv = int(f["reservatorio"].sum())
abst = int(f["abstencao"].sum())
bn = int(f["bn"].sum())
nosso = int(f["nosso"].sum())
adv = int(f["adversario"].sum())
nome_nosso = f["nosso_nome"].iloc[0] if len(f) else ""
nome_adv = f["adversario_nome"].iloc[0] if len(f) else ""

st.caption(
    f"**{dados.n(len(f))}** escolas · **{dados.n(aptos)}** eleitores aptos · "
    f"nosso lado **{dados.n(nosso)}** × adversário **{dados.n(adv)}** · "
    f"nada disso decide o 2º turno: quem decide é o reservatório"
)

k = st.columns(5)
k[0].metric("Reservatório do 2º turno", dados.n(reserv), f"{dados.pc(reserv, aptos)} do eleitorado",
            delta_color="off")
k[1].metric("Abstenção", dados.n(abst), f"{dados.pc(abst, aptos)} dos aptos", delta_color="off")
k[2].metric("Brancos + nulos", dados.n(bn), f"{dados.pc(bn, aptos)} dos aptos", delta_color="off")
k[3].metric(f"Nosso lado · {nome_nosso}", dados.n(nosso), f"{dados.pc(nosso, aptos)} dos aptos",
            delta_color="off")
k[4].metric(f"Adversário · {nome_adv}", dados.n(adv), f"{dados.pc(adv, aptos)} dos aptos",
            delta_color="off")

st.caption(
    "Como ler o cartão: cada linha é a fatia do **eleitorado da escola** — as seis somam 100%. "
    "**Reservatório do 2º turno** = votos dos candidatos que saíram + brancos + nulos + abstenções, "
    "ou seja, tudo o que não foi para os dois que ficaram."
)

# ---------------------------------------------------------------- mapa
st.markdown("##### Onde está o voto")
st.caption(
    f"Toque na bolinha para abrir a escola. **Laranja** = {nome_nosso} está na frente na escola · "
    f"**azul** = {nome_adv} está na frente · bolinha sempre do mesmo tamanho (não cresce com os votos)."
)

if len(f):
    retorno = dados.mapa_escolas(f, st.session_state.get("mv_escola"))
    clicada = dados.escola_do_clique(f, retorno.get("last_object_clicked") if retorno else None)
    if clicada and clicada != st.session_state.get("mv_escola"):
        st.session_state["mv_escola"] = clicada
        st.rerun()

# ---------------------------------------------------------------- cartões
info = dados.candidatos()[cargo]
outros = [(c["nome"], f"{cargo}_{c['numero']}") for c in info["candidatos"]
          if c["numero"] not in info["dupla"]]


def linha(rotulo, valor, cor, maximo, total, negrito=False):
    largura = (valor / maximo * 100) if maximo else 0
    classe = "v f" if negrito else "v"
    return (f'<div class="l"><div class="r">{rotulo}</div>'
            f'<div class="b"><i style="width:{largura:.1f}%;background:{cor}"></i></div>'
            f'<div class="{classe}">{dados.n(valor)}<small>{dados.pc(valor, total)}</small></div></div>')


def cartao(r) -> str:
    total = r["eleitores"] or 1
    valores = [r["nosso"], r["adversario"], r["outros"], r["brancos"], r["nulos"], r["abstencao"]]
    if detalhar:
        valores += [int(r[col]) for _, col in outros]
    maximo = max(valores) or 1
    bairro = str(r["bairro"] or "").strip()
    endereco = str(r["endereco"] or "").strip()
    if bairro and dados.sem_acento(bairro) not in dados.sem_acento(r["ra"]):
        endereco = f"{endereco} · {bairro}" if endereco else bairro
    p = [f'<div class="vi"><div class="e">{r["escola"]}</div>']
    if endereco:
        p.append(f'<div class="end">{endereco}</div>')
    p.append(f'<div class="s">zona {int(r["zona"]):02d} · {r["ra"]} · '
             f'{dados.n(r["eleitores"])} eleitores · {int(r["n_secoes"])} seções</div>')
    p.append(linha(f'{r["nosso_nome"]} <span class="pit">nosso</span>', r["nosso"],
                   dados.NOSSO, maximo, total))
    p.append(linha(f'{r["adversario_nome"]} <span class="pit">adversário</span>', r["adversario"],
                   dados.ADVERSARIO, maximo, total))
    p.append(linha('Outros candidatos <span class="pit">saíram do 2º turno</span>', r["outros"],
                   dados.CINZA, maximo, total))
    if detalhar:
        for nome, col in outros:
            valor = int(r[col])
            if valor:
                p.append(linha(f'&nbsp;&nbsp;&nbsp;{nome}', valor, dados.CINZA, maximo, total))
    p.append(linha("Brancos", r["brancos"], dados.BRANCO_C, maximo, total))
    p.append(linha("Nulos", r["nulos"], dados.NULO_C, maximo, total))
    p.append(linha("Abstenção", r["abstencao"], dados.ABST_C, maximo, total))
    p.append(f'<div class="res">Reservatório do 2º turno: '
             f'<b>{dados.n(r["reservatorio"])} votos</b> '
             f'({dados.pc(r["reservatorio"], total)} do eleitorado)</div></div>')
    return "".join(p)


if not len(f):
    st.info("Nenhuma escola com esse filtro. Limpe a busca ou escolha outra zona.")
elif ver_tabela:
    t = f[["escola", "endereco", "bairro", "zona", "ra", "eleitores", "nosso", "adversario", "outros",
           "brancos", "nulos", "abstencao", "reservatorio"]].copy()
    t["reservatorio_%"] = (t["reservatorio"] / t["eleitores"].replace(0, 1) * 100).round(1)
    t.columns = ["Escola", "Endereço", "Bairro", "Zona", "RA", "Eleitores",
                 f"{nome_nosso} (nosso)", f"{nome_adv} (adversário)", "Outros (saiu)", "Brancos",
                 "Nulos", "Abstenção", "Reservatório", "Reservatório %"]
    st.dataframe(t, width="stretch", hide_index=True)
elif ver_todas:
    st.markdown("".join(cartao(r) for _, r in f.iterrows()), unsafe_allow_html=True)
else:
    locais = list(f["local"])
    rotulos = {r["local"]: f'{r["escola"]} — reservatório {dados.n(r["reservatorio"])} '
                           f'({dados.pc(r["reservatorio"], r["eleitores"])})'
               for _, r in f.iterrows()}
    if st.session_state.get("mv_escola") not in locais:
        st.session_state["mv_escola"] = locais[0]
    escolhida = st.selectbox(
        "Escola (na ordenação escolhida)", locais,
        index=locais.index(st.session_state["mv_escola"]),
        format_func=lambda l: rotulos[l], key="mv_escola",
        help="o mapa e a busca alimentam esta escolha",
    )
    posicao = locais.index(escolhida) + 1
    st.caption(f"**{posicao}º de {len(f)}** na ordenação escolhida — "
               f"use o mapa, o seletor acima ou a busca para trocar de escola")
    st.markdown(cartao(f[f["local"] == escolhida].iloc[0]), unsafe_allow_html=True)

# ---------------------------------------------------------------- resumo por zona
with st.expander("Resumo por zona / RA"):
    z = dados.metricas(dados.zonas(), cargo)
    if zonas:
        z = z[z["zona"].isin(zonas)]
    z = z.sort_values("reservatorio", ascending=False)
    zt = z[["zona", "ra", "escolas", "eleitores", "nosso", "adversario", "outros", "brancos",
            "nulos", "abstencao", "reservatorio"]].copy()
    zt["reservatorio_%"] = (zt["reservatorio"] / zt["eleitores"].replace(0, 1) * 100).round(1)
    zt.columns = ["Zona", "RA", "Escolas", "Eleitores", f"{nome_nosso} (nosso)",
                  f"{nome_adv} (adversário)", "Outros (saiu)", "Brancos", "Nulos", "Abstenção",
                  "Reservatório", "Reservatório %"]
    st.dataframe(zt, width="stretch", hide_index=True)

dados.rodape()
