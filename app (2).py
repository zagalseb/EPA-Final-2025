import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Full Play-By-Play", layout="wide")

# ---- Archivo ----
XLSX_PATH = "/workspaces/EPA-Final-2025/Play_by_Play_2025 (5).xlsx"  # en Streamlit Cloud: súbelo al repo o usa uploader

# ---- Columnas (según tu XLSX) ----
COL_Q = "Cuarto"
COL_TEAM = "Team"
COL_DOWN = "Down"
COL_TOGO = "DST"
COL_LOC = "Yarda Inicial"
COL_DETAIL = "Play-By-Play"
COL_RES = "Resultado"
COL_EPB = "EPA BEFORE"
COL_EPA = "EPA"
COL_MTY = "MTY Score"
COL_UANL = "UANL Score"
COL_PLAYTYPE = "Tipo Jugada"

# ---- Cargar ----
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data(XLSX_PATH)

# ---- Normalizar Cuarto (por typos) ----
df[COL_Q] = df[COL_Q].astype(str).str.strip()
df[COL_Q] = df[COL_Q].replace({
    "3er cuato": "3er cuarto",
    "3er caurto": "3er cuarto",
})

# ---- UI Header ----
st.markdown("## Full Play-By-Play")

# ---- Filtros ----
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

with c1:
    q_opts = ["Todos"] + sorted(df[COL_Q].dropna().unique().tolist())
    quarter = st.selectbox("Cuarto", q_opts, index=0)

with c2:
    t_opts = ["Todos"] + sorted(df[COL_TEAM].dropna().astype(str).unique().tolist())
    team = st.selectbox("Team", t_opts, index=0)

with c3:
    d_opts = ["Todos"] + sorted(df[COL_DOWN].dropna().astype(str).unique().tolist())
    down = st.selectbox("Down", d_opts, index=0)

with c4:
    search = st.text_input("Buscar en Play-By-Play", value="")

f = df.copy()
if quarter != "Todos":
    f = f[f[COL_Q].astype(str) == quarter]
if team != "Todos":
    f = f[f[COL_TEAM].astype(str) == team]
if down != "Todos":
    f = f[f[COL_DOWN].astype(str) == down]
if search.strip():
    f = f[f[COL_DETAIL].astype(str).str.contains(search, case=False, na=False)]

# ---- Estilo tipo PFR ----
def row_bg(row):
    res = str(row.get(COL_RES, "")).strip().upper()
    ptype = str(row.get(COL_PLAYTYPE, "")).strip().upper()
    detail = str(row.get(COL_DETAIL, "")).strip().upper()

    # TD
    if res == "TD" or " TD" in detail or "TOUCHDOWN" in detail:
        return "background-color: #b7f7b7;"
    # INT
    if res == "INT" or "INTERCEP" in detail or "INT" in detail:
        return "background-color: #ffcccc;"
    # “especiales” (por tipo jugada)
    if ptype in {"KICKOFF","PUNT","PAT","FIELD GOAL","FG","RK","RP"}:
        return "background-color: #ffe6b3;"
    # Castigos / misc
    if "CASTIGO" in ptype or "PENAL" in detail:
        return "background-color: #e8e8e8;"
    return ""

def styler(df_show):
    sty = df_show.style.apply(lambda r: [row_bg(r)] * len(df_show.columns), axis=1)
    fmt = {}
    if "EPB" in df_show.columns: fmt["EPB"] = "{:.3f}"
    if "EPA" in df_show.columns: fmt["EPA"] = "{:.3f}"
    if fmt:
        sty = sty.format(fmt)
    sty = sty.set_properties(**{"white-space": "nowrap"})
    return sty

# ---- Tabla (orden tipo PFR) ----
show_cols = [
    COL_Q, COL_TEAM, COL_DOWN, COL_TOGO, COL_LOC,
    COL_MTY, COL_UANL,
    COL_DETAIL,
    COL_EPB, COL_EPA
]
show_cols = [c for c in show_cols if c in f.columns]

view = f[show_cols].copy()

# Renombrar encabezados como PFR
rename = {
    COL_TOGO: "ToGo",
    COL_LOC: "Location",
    COL_EPB: "EPB",
}
view = view.rename(columns=rename)

st.dataframe(styler(view), use_container_width=True, height=680)
