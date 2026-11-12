"""PASO 4 · KPIs en columnas y gráficas con Plotly.

Ejecutar:  python -m streamlit run paso_4_graficas.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Cafetería · gráficas", page_icon="☕", layout="wide")

ARCHIVO = Path(__file__).parent / "ventas_cafeteria.csv"

# NUEVO: un color FIJO por sede. Si dejas que Plotly los asigne solo, al quitar
# una sede en el filtro las demás cambian de color y el usuario se confunde.
COLORES_SEDE = {"Centro": "#2a78d6", "Norte": "#eb6834", "Universidad": "#1baf7a"}
COLOR_UNICO = "#2a78d6"


@st.cache_data
def cargar_datos(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, parse_dates=["fecha"])


def pesos(valor: float) -> str:
    return f"$ {valor:,.0f}".replace(",", ".")


df = cargar_datos(ARCHIVO)

st.title("Ventas de la cafetería")

with st.sidebar:
    st.header("Filtros")
    sedes = sorted(df["sede"].unique())
    sedes_sel = st.multiselect("Sede", sedes, default=sedes)
    categorias = sorted(df["categoria"].unique())
    categorias_sel = st.multiselect("Categoría", categorias, default=categorias)
    fecha_min, fecha_max = df["fecha"].min().date(), df["fecha"].max().date()
    rango = st.date_input(
        "Rango de fechas", value=(fecha_min, fecha_max),
        min_value=fecha_min, max_value=fecha_max,
    )

if len(rango) != 2:
    st.info("Selecciona también la fecha final del rango.")
    st.stop()
inicio, fin = rango

filtro = df[
    df["sede"].isin(sedes_sel)
    & df["categoria"].isin(categorias_sel)
    & df["fecha"].between(pd.Timestamp(inicio), pd.Timestamp(fin))
]
if filtro.empty:
    st.warning("No hay datos con esos filtros.")
    st.stop()

# --- KPIs ----------------------------------------------------------------------
ingresos = filtro["ingresos"].sum()
unidades = filtro["cantidad"].sum()
precio_promedio = ingresos / unidades if unidades else 0
estrella = filtro.groupby("producto")["cantidad"].sum().idxmax()

# NUEVO: st.columns(4) crea 4 columnas; cada una recibe un elemento
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingresos", pesos(ingresos), border=True)
c2.metric("Unidades vendidas", f"{unidades:,}".replace(",", "."), border=True)
c3.metric("Precio promedio por unidad", pesos(precio_promedio), border=True)
c4.metric("Producto más vendido", estrella, border=True)

# --- Gráfica 1: evolución en el tiempo -----------------------------------------
st.subheader("Ingresos semanales por sede")

# Primero se prepara la tabla con pandas (agrupar por semana y sede)...
semanal = (
    filtro.groupby([pd.Grouper(key="fecha", freq="W-MON", label="left"), "sede"])["ingresos"]
    .sum()
    .reset_index()
)

# ...y después se le pasa a Plotly.
fig_linea = px.line(
    semanal,
    x="fecha",
    y="ingresos",
    color="sede",
    color_discrete_map=COLORES_SEDE,
    markers=True,
    labels={"fecha": "Semana", "ingresos": "Ingresos", "sede": "Sede"},
)
fig_linea.update_traces(line_width=2, marker_size=8)
fig_linea.update_layout(separators=",.", hovermode="x unified", yaxis_tickprefix="$ ")

# NUEVO: st.plotly_chart dibuja cualquier figura de Plotly (con zoom y tooltip)
st.plotly_chart(fig_linea)

# --- Gráficas 2 y 3: lado a lado -------------------------------------------------
izq, der = st.columns(2)

with izq:
    st.subheader("Ingresos por producto")
    por_producto = (
        filtro.groupby("producto", as_index=False)["ingresos"].sum()
        .sort_values("ingresos")  # ordenado: la barra más larga queda arriba
    )
    fig_prod = px.bar(
        por_producto, x="ingresos", y="producto", orientation="h",
        labels={"ingresos": "Ingresos", "producto": ""},
        color_discrete_sequence=[COLOR_UNICO],
    )
    fig_prod.update_layout(separators=",.", xaxis_tickprefix="$ ")
    st.plotly_chart(fig_prod)

with der:
    st.subheader("Ingresos por sede")
    por_sede = filtro.groupby("sede", as_index=False)["ingresos"].sum()
    fig_sede = px.bar(
        por_sede, x="sede", y="ingresos", color="sede",
        color_discrete_map=COLORES_SEDE,
        labels={"ingresos": "Ingresos", "sede": ""},
    )
    fig_sede.update_layout(separators=",.", yaxis_tickprefix="$ ", showlegend=False)
    st.plotly_chart(fig_sede)
