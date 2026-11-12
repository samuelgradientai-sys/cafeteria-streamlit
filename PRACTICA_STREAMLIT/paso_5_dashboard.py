"""PASO 5 · Dashboard completo: pestañas, estado de sesión, formularios y descarga.

Ejecutar:  ..\\.venv\\Scripts\\python.exe -m streamlit run paso_5_dashboard.py

Sigue el orden recomendado en la clase (s2a, sección 13.1):
  1 importar · 2 configurar · 3 funciones · 4 cargar · 5 filtros
  6 aplicar filtros · 7 indicadores · 8 gráficas · 9 tablas
"""
# 1. Importar librerías ---------------------------------------------------------
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# 2. Configurar la página -------------------------------------------------------
st.set_page_config(page_title="Cafetería · dashboard", page_icon="☕", layout="wide")

ARCHIVO = Path(__file__).parent / "ventas_cafeteria.csv"
COLORES_SEDE = {"Centro": "#2a78d6", "Norte": "#eb6834", "Universidad": "#1baf7a"}
COLOR_UNICO = "#2a78d6"
ESCALA_AZUL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # claro → oscuro
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


# 3. Funciones de carga y procesamiento -----------------------------------------
@st.cache_data
def cargar_datos(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, parse_dates=["fecha"])
    df["mes"] = df["fecha"].dt.to_period("M").astype(str)
    df["dia_semana"] = pd.Categorical(
        df["fecha"].dt.dayofweek.map(dict(enumerate(DIAS))), categories=DIAS, ordered=True
    )
    return df


def pesos(valor: float) -> str:
    return f"$ {valor:,.0f}".replace(",", ".")


def filtros_sidebar(df: pd.DataFrame):
    """Dibuja los filtros y devuelve lo que el usuario eligió."""
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
        st.caption("Los colores de cada sede se mantienen aunque filtres.")
    return sedes_sel, categorias_sel, rango


def aplicar_filtros(df, sedes_sel, categorias_sel, inicio, fin) -> pd.DataFrame:
    return df[
        df["sede"].isin(sedes_sel)
        & df["categoria"].isin(categorias_sel)
        & df["fecha"].between(pd.Timestamp(inicio), pd.Timestamp(fin))
    ]


# 4. Cargar datos ---------------------------------------------------------------
df = cargar_datos(ARCHIVO)

# 5. Crear filtros --------------------------------------------------------------
sedes_sel, categorias_sel, rango = filtros_sidebar(df)
if len(rango) != 2:
    st.info("Selecciona también la fecha final del rango.")
    st.stop()

# 6. Aplicar filtros ------------------------------------------------------------
filtro = aplicar_filtros(df, sedes_sel, categorias_sel, *rango)
if filtro.empty:
    st.warning("No hay datos con esos filtros.")
    st.stop()

st.title("Dashboard de ventas · Cafetería")
st.caption(f"{rango[0]:%d/%m/%Y} – {rango[1]:%d/%m/%Y} · {', '.join(sedes_sel)}")

# NUEVO: st.tabs crea pestañas. OJO: Streamlit ejecuta el código de TODAS las
# pestañas en cada repetición, no solo el de la que está abierta.
tab_resumen, tab_productos, tab_dias, tab_datos, tab_bitacora = st.tabs(
    ["Resumen", "Productos", "Días de la semana", "Datos", "Bitácora"]
)

# 7. Indicadores + 8. Gráficas --------------------------------------------------
with tab_resumen:
    ingresos = filtro["ingresos"].sum()
    unidades = filtro["cantidad"].sum()

    # NUEVO: delta en st.metric → compara el último mes con el anterior
    por_mes = filtro.groupby("mes")["ingresos"].sum()
    if len(por_mes) >= 2:
        ultimo, anterior = por_mes.iloc[-1], por_mes.iloc[-2]
        delta = f"{(ultimo - anterior) / anterior:+.1%} vs mes anterior"
    else:
        ultimo, delta = por_mes.iloc[-1], None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos", pesos(ingresos), border=True)
    c2.metric("Unidades vendidas", f"{unidades:,}".replace(",", "."), border=True)
    c3.metric("Precio promedio por unidad", pesos(ingresos / unidades), border=True)
    c4.metric(
        f"Ingresos de {por_mes.index[-1]}", pesos(ultimo), delta=delta, border=True,
        help="Si el rango corta un mes a la mitad, la comparación no es justa.",
    )

    semanal = (
        filtro.groupby([pd.Grouper(key="fecha", freq="W-MON", label="left"), "sede"])["ingresos"]
        .sum().reset_index()
    )
    fig = px.line(
        semanal, x="fecha", y="ingresos", color="sede", color_discrete_map=COLORES_SEDE,
        markers=True, title="Ingresos semanales por sede",
        labels={"fecha": "Semana", "ingresos": "Ingresos", "sede": "Sede"},
    )
    fig.update_traces(line_width=2, marker_size=8)
    fig.update_layout(separators=",.", hovermode="x unified", yaxis_tickprefix="$ ")
    st.plotly_chart(fig)

with tab_productos:
    resumen = (
        filtro.groupby(["producto", "categoria"], as_index=False)
        .agg(unidades=("cantidad", "sum"), ingresos=("ingresos", "sum"))
        .sort_values("ingresos", ascending=False)
    )
    resumen["participacion"] = resumen["ingresos"] / resumen["ingresos"].sum() * 100

    izq, der = st.columns([3, 2])
    with izq:
        fig = px.bar(
            resumen.sort_values("ingresos"), x="ingresos", y="producto", orientation="h",
            title="Ingresos por producto", color_discrete_sequence=[COLOR_UNICO],
            labels={"ingresos": "Ingresos", "producto": ""},
        )
        fig.update_layout(separators=",.", xaxis_tickprefix="$ ")
        st.plotly_chart(fig)
    with der:
        # NUEVO: column_config da formato a las columnas de la tabla
        st.dataframe(
            resumen,
            hide_index=True,
            column_config={
                "producto": "Producto",
                "categoria": "Categoría",
                "unidades": st.column_config.NumberColumn("Unidades", format="%d"),
                "ingresos": st.column_config.NumberColumn("Ingresos", format="$ %d"),
                "participacion": st.column_config.ProgressColumn(
                    "Participación", format="%.1f%%", min_value=0, max_value=100
                ),
            },
        )

with tab_dias:
    st.write("Ingreso promedio por día, en **millones de pesos**. ¿Qué pasa en la sede Universidad el fin de semana?")
    diario = filtro.groupby(["fecha", "dia_semana", "sede"], observed=True)["ingresos"].sum().reset_index()
    matriz = (
        diario.groupby(["sede", "dia_semana"], observed=True)["ingresos"].mean()
        .unstack("dia_semana") / 1_000_000
    )
    fig = px.imshow(
        matriz, text_auto=".2f", aspect="auto", color_continuous_scale=ESCALA_AZUL,
        labels={"x": "", "y": "", "color": "Millones"},
    )
    fig.update_layout(separators=",.")
    st.plotly_chart(fig)

# 9. Tablas ---------------------------------------------------------------------
with tab_datos:
    st.caption(f"{len(filtro):,} filas con los filtros actuales")
    columnas = ["fecha", "sede", "producto", "categoria", "precio_unitario", "cantidad", "ingresos"]
    st.dataframe(
        filtro[columnas],
        hide_index=True,
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "precio_unitario": st.column_config.NumberColumn("Precio", format="$ %d"),
            "ingresos": st.column_config.NumberColumn("Ingresos", format="$ %d"),
        },
    )
    # NUEVO: botón para descargar exactamente lo que se está viendo
    st.download_button(
        "Descargar CSV filtrado",
        data=filtro[columnas].to_csv(index=False).encode("utf-8"),
        file_name="ventas_filtradas.csv",
        mime="text/csv",
    )

# NUEVO: st.session_state + st.form ----------------------------------------------
# Una lista normal (hallazgos = []) se borraría en cada repetición del script.
# st.session_state es un diccionario que SOBREVIVE a las repeticiones.
with tab_bitacora:
    st.write("Anota lo que vas descubriendo en el dashboard. Se guarda mientras la pestaña del navegador siga abierta.")

    if "hallazgos" not in st.session_state:
        st.session_state.hallazgos = []

    # Un formulario agrupa widgets: el script NO se repite mientras escribes,
    # solo cuando presionas el botón de enviar.
    with st.form("nuevo_hallazgo", clear_on_submit=True):
        texto = st.text_input("Hallazgo")
        enviado = st.form_submit_button("Guardar")

    if enviado and texto.strip():
        st.session_state.hallazgos.append(texto.strip())

    if st.session_state.hallazgos:
        for i, h in enumerate(st.session_state.hallazgos, start=1):
            st.markdown(f"{i}. {h}")
        if st.button("Borrar todo"):
            st.session_state.hallazgos = []
            st.rerun()  # vuelve a ejecutar ya mismo para que la lista desaparezca
    else:
        st.caption("Todavía no hay hallazgos.")
