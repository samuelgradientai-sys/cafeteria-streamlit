"""PASO 3 · Filtros en la barra lateral.

Ejecutar:  python -m streamlit run paso_3_filtros.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cafetería · filtros", page_icon="☕", layout="wide")

ARCHIVO = Path(__file__).parent / "ventas_cafeteria.csv"


@st.cache_data
def cargar_datos(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, parse_dates=["fecha"])


def pesos(valor: float) -> str:
    return f"$ {valor:,.0f}".replace(",", ".")


df = cargar_datos(ARCHIVO)

st.title("Ventas de la cafetería")

# NUEVO: todo lo que va dentro de `with st.sidebar:` aparece en la barra lateral
with st.sidebar:
    st.header("Filtros")

    sedes = sorted(df["sede"].unique())
    sedes_sel = st.multiselect("Sede", sedes, default=sedes)

    categorias = sorted(df["categoria"].unique())
    categorias_sel = st.multiselect("Categoría", categorias, default=categorias)

    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()
    # Si `value` es una tupla (inicio, fin), el widget pide un RANGO de fechas
    rango = st.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )

# Mientras el usuario está eligiendo, el rango puede tener solo la fecha inicial.
# NUEVO: st.stop() detiene el script aquí; lo que sigue no se dibuja.
if len(rango) != 2:
    st.info("Selecciona también la fecha final del rango.")
    st.stop()
inicio, fin = rango

# NUEVO: aplicar los filtros. Esto ya no es Streamlit, es pandas normal:
# los widgets solo nos dieron las listas y fechas elegidas.
filtro = df[
    df["sede"].isin(sedes_sel)
    & df["categoria"].isin(categorias_sel)
    & df["fecha"].between(pd.Timestamp(inicio), pd.Timestamp(fin))
]

# Siempre protege la app contra el caso "no quedó nada"
if filtro.empty:
    st.warning("No hay datos con esos filtros. Prueba seleccionando más opciones.")
    st.stop()

st.metric("Ingresos (con filtros)", pesos(filtro["ingresos"].sum()))
st.caption(f"Mostrando {len(filtro):,} de {len(df):,} filas")
st.dataframe(filtro, hide_index=True)
