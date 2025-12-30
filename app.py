import streamlit as st
import pandas as pd
import numpy as np

import os


st.set_page_config(page_title="Full Play-By-Play", layout="wide")

# Ruta relativa al repo (mismo folder que app.py)
XLSX_PATH = os.path.join(os.path.dirname(__file__), "Play_by_Play_2025 (5).xlsx")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")  # explícito
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data(XLSX_PATH)

# -----------------------
# Parsers robustos
# -----------------------
def parse_quarter(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().lower()
    if s.isdigit():
        v = int(s)
        return v if 1 <= v <= 4 else np.nan
    if s.startswith("1"): return 1
    if s.startswith("2"): return 2
    if s.startswith("3"): return 3
    if s.startswith("4"): return 4
    return np.nan

def parse_down(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().lower()
    if s.isdigit():
        v = int(s)
        return v if 1 <= v <= 4 else np.nan
    if s.startswith("1"): return 1
    if s.startswith("2"): return 2
    if s.startswith("3"): return 3
    if s.startswith("4"): return 4
    return np.nan

# Convertir a números
df[COL_Q] = df[COL_Q].apply(parse_quarter).astype("Int64")
df[COL_DOWN] = df[COL_DOWN].apply(parse_down).astype("Int64")
df[COL_DST]  = pd.to_numeric(df.get(COL_DST, np.nan), errors="coerce").astype("Int64")
df[COL_MTY]  = pd.to_numeric(df.get(COL_MTY, np.nan), errors="coerce").astype("Int64")
df[COL_UANL] = pd.to_numeric(df.get(COL_UANL, np.nan), errors="coerce").astype("Int64")

# -----------------------
# Detectar fin de posesión
# (robusto por si falta alguna columna)
# -----------------------
team_col = "Team"
res_col = "Resultado"
ptype_col = "Tipo Jugada"

df["Team_next"] = df[team_col].shift(-1) if team_col in df.columns else None

res_upper = df[res_col].astype(str).str.upper() if res_col in df.columns else pd.Series([""] * len(df))
ptype_upper = df[ptype_col].astype(str).str.upper() if ptype_col in df.columns else pd.Series([""] * len(df))

team_change = (df[team_col].astype(str) != df["Team_next"].astype(str)) if team_col in df.columns else False
is_td_int = res_upper.isin(["TD", "INT"])
is_punt = ptype_upper.isin(["PUNT"])

df["end_of_possession"] = team_change | is_td_int | is_punt

# -----------------------
# Vista
# -----------------------
st.markdown("## Full Play-By-Play")

# ---- Columnas EPA ----
COL_EPB  = "EPA BEFORE"
COL_EPAF = "EPA AFTER"
COL_EPA  = "EPA"

# Asegurar numéricos
for c in [COL_EPB, COL_EPAF, COL_EPA]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# ---- Columnas a mostrar ----
show_cols = [
    COL_Q, COL_DOWN, COL_DST,
    COL_MTY, COL_UANL,
    COL_DETAIL,
    COL_EPB, COL_EPAF, COL_EPA
]

missing = [c for c in show_cols if c not in df.columns]
if missing:
    st.error(f"Faltan columnas en el XLSX: {missing}\nDisponibles: {list(df.columns)}")
    st.stop()

view = df[show_cols].copy()

# ---- Limpieza de columnas numéricas ----
for c in [COL_Q, COL_DOWN, COL_DST, COL_MTY, COL_UANL]:
    view[c] = view[c].astype("Int64").astype(str).replace("<NA>", "")

# ---- Formato EPA ----
def fmt3(x):
    return "" if pd.isna(x) else f"{float(x):.3f}"

def epa_badge(x):
    if pd.isna(x):
        return ""
    v = float(x)
    if v >= 2.0:
        return f"🟩🟩 {v:.3f}"
    if v >= 0.75:
        return f"🟩 {v:.3f}"
    if v <= -2.0:
        return f"🟥🟥 {v:.3f}"
    if v <= -0.75:
        return f"🟥 {v:.3f}"
    return f"🟨 {v:.3f}"

view[COL_EPB]  = view[COL_EPB].apply(fmt3)
view[COL_EPAF] = view[COL_EPAF].apply(fmt3)
view[COL_EPA]  = view[COL_EPA].apply(epa_badge)

# -----------------------
# Línea negra (separador)
# -----------------------
def border_drive(row):
    if df.loc[row.name, "end_of_possession"]:
        return ["border-bottom: 3px solid black"] * len(view.columns)
    return [""] * len(view.columns)

styled = (
    view.style
    .apply(border_drive, axis=1)
    .set_properties(**{"white-space": "nowrap", "font-size": "12px"})
)

st.dataframe(
    styled,
    height=700,
    use_container_width=True
)

# ===============================
# EXPECTED POINTS SUMMARY (PFR)
# ===============================

st.markdown("---")
st.markdown("### Expected Points Summary")

# ---- Normaliza headers otra vez por seguridad ----
df.columns = [c.strip() for c in df.columns]

def pick_col(df, candidates):
    """Regresa la primera columna existente de una lista de opciones."""
    for c in candidates:
        if c in df.columns:
            return c
    return None

COL_TEAM = pick_col(df, ["Team", "TEAM", "team"])
COL_TIPO = pick_col(df, ["Tipo", "TIPO"])
COL_PLAY = pick_col(df, ["Play type", "Play Type", "PlayType", "Playtype", "PLAY TYPE"])
COL_EPA  = pick_col(df, ["EPA", "Epa"])
COL_RES  = pick_col(df, ["Resultado", "RESULTADO", "Result", "RESULT"])

missing = [name for name, col in [
    ("Team", COL_TEAM),
    ("Tipo", COL_TIPO),
    ("Play type", COL_PLAY),
    ("EPA", COL_EPA),
    ("Resultado", COL_RES),
] if col is None]

if missing:
    st.error(f"No encontré estas columnas en el XLSX: {missing}")
    st.write("Columnas disponibles:", list(df.columns))
    st.stop()

# ---- Filtrar solo jugadas regulares ----
reg = df[df[COL_TIPO].astype(str).str.strip().str.lower().eq("regular")].copy()

# ---- Tipos + EPA numérico ----
reg[COL_EPA] = pd.to_numeric(reg[COL_EPA], errors="coerce")
reg[COL_PLAY] = reg[COL_PLAY].astype(str).str.strip().str.lower()
reg[COL_RES]  = reg[COL_RES].astype(str).str.strip().str.upper()

reg["is_pass"] = reg[COL_PLAY].eq("pase")   # tu etiqueta real
reg["is_rush"] = reg[COL_PLAY].eq("run")    # tu etiqueta real
reg["is_tovr"] = reg[COL_RES].eq("INT")     # tu etiqueta real

teams = sorted(reg[COL_TEAM].dropna().astype(str).unique().tolist())

# ---- OFFENSE ----
off_tot  = reg.groupby(COL_TEAM)[COL_EPA].sum()
off_pass = reg[reg["is_pass"]].groupby(COL_TEAM)[COL_EPA].sum()
off_rush = reg[reg["is_rush"]].groupby(COL_TEAM)[COL_EPA].sum()
off_tovr = reg[reg["is_tovr"]].groupby(COL_TEAM)[COL_EPA].sum()

off = pd.DataFrame(index=teams)
off["Tot"]  = off_tot.reindex(teams).fillna(0.0)
off["Pass"] = off_pass.reindex(teams).fillna(0.0)
off["Rush"] = off_rush.reindex(teams).fillna(0.0)
off["TOvr"] = off_tovr.reindex(teams).fillna(0.0)

# ---- DEFENSE = - (ofensiva del rival) ----
total_tot  = reg[COL_EPA].sum(skipna=True)
total_pass = reg.loc[reg["is_pass"], COL_EPA].sum(skipna=True)
total_rush = reg.loc[reg["is_rush"], COL_EPA].sum(skipna=True)
total_tovr = reg.loc[reg["is_tovr"], COL_EPA].sum(skipna=True)

def_tot, def_pass, def_rush, def_tovr = {}, {}, {}, {}
for t in teams:
    def_tot[t]  = -(total_tot  - off.loc[t, "Tot"])
    def_pass[t] = -(total_pass - off.loc[t, "Pass"])
    def_rush[t] = -(total_rush - off.loc[t, "Rush"])
    def_tovr[t] = -(total_tovr - off.loc[t, "TOvr"])

summary = pd.DataFrame(index=teams)
summary.index.name = "Tm"

summary["Off Tot"]  = off["Tot"]
summary["Off Pass"] = off["Pass"]
summary["Off Rush"] = off["Rush"]
summary["Off TOvr"] = off["TOvr"] 

summary["Def Tot"]  = pd.Series(def_tot)
summary["Def Pass"] = pd.Series(def_pass)
summary["Def Rush"] = pd.Series(def_rush)
summary["Def TOvr"] = pd.Series(def_tovr)

st.dataframe(
    summary.style.format("{:.3f}").set_properties(**{"white-space": "nowrap", "font-size": "12px"}),
    height=220,
    use_container_width=True
)

st.markdown("---")
st.markdown("### EPA por Jugador (Regular)")

COL_TIPO   = "Tipo"
COL_TEAM   = "Team"
COL_PLAY   = "Play type"      # Run / Pase
COL_EPA    = "EPA"
COL_PLAYER = "Nombre jugador"
COL_QB     = "Nombre QB"

need_cols = [COL_TIPO, COL_TEAM, COL_PLAY, COL_EPA, COL_PLAYER, COL_QB]
missing = [c for c in need_cols if c not in df.columns]
if missing:
    st.warning(f"No puedo calcular EPA por jugador/QB. Faltan columnas: {missing}")
else:
    reg = df[df[COL_TIPO].astype(str).str.strip().str.lower().eq("regular")].copy()

    # tipado
    reg[COL_EPA] = pd.to_numeric(reg[COL_EPA], errors="coerce")
    reg[COL_PLAY] = reg[COL_PLAY].astype(str).str.strip()
    reg[COL_PLAYER] = reg[COL_PLAYER].astype(str).str.strip()
    reg[COL_QB] = reg[COL_QB].astype(str).str.strip()

    # limpiar vacíos
    reg = reg.dropna(subset=[COL_EPA])

    # -------------------------
    # 1) EPA por jugador (overall)
    # -------------------------
    by_player = (
        reg[(reg[COL_PLAYER] != "") & (reg[COL_PLAYER].str.lower() != "nan")]
        .groupby([COL_TEAM, COL_PLAYER])[COL_EPA]
        .agg(plays="count", epa_total="sum", epa_per_play="mean")
        .reset_index()
        .sort_values(["epa_total"], ascending=False)
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        team_opt = ["Todos"] + sorted(reg[COL_TEAM].dropna().unique().tolist())
        team_filter = st.selectbox("Equipo (jugadores)", team_opt, index=0)
    with c2:
        min_plays = st.number_input("Min jugadas (jugadores)", min_value=1, value=5, step=1)
    with c3:
        top_n = st.number_input("Top N (jugadores)", min_value=5, value=15, step=5)

    tmp = by_player.copy()
    if team_filter != "Todos":
        tmp = tmp[tmp[COL_TEAM] == team_filter]
    tmp = tmp[tmp["plays"] >= min_plays].head(int(top_n))

    st.dataframe(
        tmp.style.format({"epa_total":"{:.3f}", "epa_per_play":"{:.3f}"}),
        use_container_width=True,
        height=420
    )

    # -------------------------
    # 2) QB EPA (solo pases)
    # -------------------------
    st.markdown("### QB EPA (solo pases)")

    pass_df = reg[reg[COL_PLAY].str.lower().eq("pase")].copy()
    qb_tbl = (
        pass_df[(pass_df[COL_QB] != "") & (pass_df[COL_QB].str.lower() != "nan")]
        .groupby([COL_TEAM, COL_QB])[COL_EPA]
        .agg(dropbacks="count", epa_total="sum", epa_per_dropback="mean")
        .reset_index()
        .sort_values(["epa_total"], ascending=False)
        .rename(columns={COL_QB: "QB"})
    )

    c4, c5, c6 = st.columns([1, 1, 1])
    with c4:
        team_opt2 = ["Todos"] + sorted(pass_df[COL_TEAM].dropna().unique().tolist())
        team_filter2 = st.selectbox("Equipo (QB)", team_opt2, index=0)
    with c5:
        min_db = st.number_input("Min pases (QB)", min_value=1, value=8, step=1)
    with c6:
        top_n_qb = st.number_input("Top N (QB)", min_value=5, value=10, step=5)

    qb_show = qb_tbl.copy()
    if team_filter2 != "Todos":
        qb_show = qb_show[qb_show[COL_TEAM] == team_filter2]
    qb_show = qb_show[qb_show["dropbacks"] >= min_db].head(int(top_n_qb))

    st.dataframe(
        qb_show.style.format({"epa_total":"{:.3f}", "epa_per_dropback":"{:.3f}"}),
        use_container_width=True,
        height=320
    )
