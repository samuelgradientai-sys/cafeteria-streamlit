"""PASO 1 · Lo mínimo: texto, widgets y el ciclo de ejecución.

Ejecutar:  python -m streamlit run paso_1_hola.py
"""
from datetime import datetime

import streamlit as st

# Siempre es la PRIMERA instrucción de Streamlit del archivo
st.set_page_config(page_title="Mi cafetería", page_icon="☕")

# --- Texto -----------------------------------------------------------------
st.title("Mi primera app en Streamlit")
st.write("Streamlit convierte un script de Python en una página web.")
st.markdown("Acepta **markdown**: *cursiva*, `código` y listas:\n- una\n- dos")

st.divider()

# --- Widgets -----------------------------------------------------------------
# Un widget DIBUJA un control y DEVUELVE lo que el usuario eligió.
nombre = st.text_input("¿Cómo te llamas?")
tazas = st.slider("¿Cuántas tazas de café tomas al día?", min_value=0, max_value=10, value=2)
bebida = st.radio("¿Cuál prefieres?", ["Americano", "Capuchino", "Latte"], horizontal=True)

# --- La idea clave -------------------------------------------------------------
# Cada vez que tocas un widget, Streamlit vuelve a ejecutar ESTE ARCHIVO COMPLETO
# de arriba hacia abajo. Por eso `nombre`, `tazas` y `bebida` siempre traen el
# valor más reciente, y un simple `if` basta para reaccionar.
if nombre:
    st.success(f"Hola, {nombre}. Tomas {tazas} tazas de {bebida.lower()} al día.")

if tazas > 4:
    st.warning("Eso es bastante café.")
elif tazas == 0:
    st.info("¿Seguro que esta app es para ti?")

# Mueve el slider y mira cómo cambia la hora: es la prueba de que el script se repitió.
st.caption(f"Este script se ejecutó a las {datetime.now():%H:%M:%S}")
