"""PASO 2 · Cargar datos con caché y mostrarlos.

Ejecutar:  ..\\.venv\\Scripts\\python.exe -m streamlit run paso_2_datos.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cafetería · datos", page_icon="☕", layout="wide")

# Ruta al CSV relativa a ESTE archivo: funciona sin importar desde qué carpeta
# ejecutes `streamlit run`.
ARCHIVO = Path(__file__).parent / "ventas_cafeteria.csv"


# NUEVO: @st.cache_data
# Recuerda que el script se repite en cada clic. Sin caché, el CSV se leería
# del disco en cada repetición. Con caché, se lee una vez y Streamlit guarda
# el DataFrame resultante (si cambian los argumentos, vuelve a leer).
@st.cache_data
def cargar_datos(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, parse_dates=["fecha"])
    return df


def pesos(valor: float) -> str:
    """Formato colombiano: $ 1.234.567"""
    return f"$ {valor:,.0f}".replace(",", ".")


df = cargar_datos(ARCHIVO)

st.title("Ventas de la cafetería")
st.write(f"{len(df):,} filas · {df['fecha'].min():%d/%m/%Y} a {df['fecha'].max():%d/%m/%Y}")

# NUEVO: st.metric muestra un número destacado (un KPI)
st.metric("Ingresos totales", pesos(df["ingresos"].sum()))

# NUEVO: st.dataframe muestra una tabla interactiva (ordenar, buscar, ampliar)
st.subheader("Primeras filas")
st.dataframe(df.head(20), hide_index=True)

# NUEVO: st.expander esconde contenido secundario hasta que el usuario lo abre
with st.expander("Ver resumen estadístico"):
    st.dataframe(df.describe(include="number"))  # solo columnas numéricas

with st.expander("Ver valores únicos"):
    st.write("**Sedes:**", ", ".join(df["sede"].unique()))
    st.write("**Categorías:**", ", ".join(df["categoria"].unique()))
    st.write("**Productos:**", ", ".join(df["producto"].unique()))
