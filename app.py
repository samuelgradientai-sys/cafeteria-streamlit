"""Dashboard de ventas · Cafetería (versión final, la que se despliega).

Ejecutar local:   python -m streamlit run app.py
Streamlit Cloud:  Main file path = app.py

Orden del archivo (s2a, sección 13.1):
  1 configuración · 2 funciones · 3 datos · 4 filtros · 5 indicadores
  6 pestañas con gráficas · 7 tablas y descarga
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ════════════════════════════════════════════════════════════════════════════
# 1. CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Cafetería · Dashboard de ventas", page_icon="☕", layout="wide")

ARCHIVO = Path(__file__).parent / "ventas_cafeteria.csv"

# Colores fijos por entidad: no cambian aunque el usuario filtre.
COLORES_SEDE = {"Centro": "#2a78d6", "Norte": "#eb6834", "Universidad": "#1baf7a"}
COLORES_CATEGORIA = {
    "Bebidas calientes": "#eda100",
    "Bebidas frías": "#6250d6",
    "Comidas": "#008300",
    "Panadería": "#e87ba4",
}
COLOR_ACTUAL = "#eb6834"  # naranja: el periodo que estás mirando
COLOR_REFERENCIA = "#bdb5aa"  # gris cálido para "periodo anterior"
FONDO = "#fffaf5"  # igual al tema: separa los segmentos de las barras apiladas
ESCALA_NARANJA = ["#ffd6be", "#ff924a", "#d16300", "#944302", "#5b2602"]  # claro → oscuro
DEGRADADO_ENCABEZADO = "linear-gradient(115deg, #c84a0f 0%, #b93f0b 55%, #9a3412 100%)"
SIN_BARRA = {"displayModeBar": False}

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
DIAS_LARGOS = dict(zip(DIAS, ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]))
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
PERIODOS = ["Último mes", "Últimos 3 meses", "Todo", "Personalizado"]


# ════════════════════════════════════════════════════════════════════════════
# 2. FUNCIONES
# ════════════════════════════════════════════════════════════════════════════
# --- Formatos (estilo colombiano) ---------------------------------------------
def pesos(v: float) -> str:
    return f"$ {v:,.0f}".replace(",", ".")


def millones(v: float) -> str:
    return f"$ {v / 1e6:.1f} M".replace(".", ",")


def entero(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def pct(v: float, signo: bool = True) -> str:
    return (f"{v:+.1%}" if signo else f"{v:.1%}").replace(".", ",")


def fecha_txt(d) -> str:
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def variacion(actual: float, anterior: float | None):
    if anterior is None or anterior == 0:
        return None
    return actual / anterior - 1


# --- Datos ----------------------------------------------------------------------
@st.cache_data
def cargar_datos(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, parse_dates=["fecha"])
    df["mes"] = df["fecha"].dt.to_period("M").dt.to_timestamp()
    df["mes_txt"] = df["mes"].apply(lambda m: f"{MESES[m.month - 1]} {m.year}")
    df["dia_semana"] = pd.Categorical(
        df["fecha"].dt.day_of_week.map(dict(enumerate(DIAS))), categories=DIAS, ordered=True
    )
    return df


def calcular_periodo(opcion, fecha_min, fecha_max, rango_manual=None):
    """Devuelve (inicio, fin, inicio_anterior, fin_anterior).
    El periodo anterior tiene la misma duración y va justo antes; es None si no hay datos para él."""
    if opcion == "Todo":
        return fecha_min, fecha_max, None, None
    if opcion == "Personalizado":
        inicio, fin = (pd.Timestamp(f) for f in rango_manual)
        dias = (fin - inicio).days + 1
        fin_ant = inicio - pd.Timedelta(days=1)
        inicio_ant = fin_ant - pd.Timedelta(days=dias - 1)
    else:
        meses = 1 if opcion == "Último mes" else 3
        fin = fecha_max
        inicio = (fin.to_period("M") - (meses - 1)).to_timestamp()
        inicio_ant = (inicio.to_period("M") - meses).to_timestamp()
        fin_ant = inicio - pd.Timedelta(days=1)
    if inicio_ant < fecha_min:
        return inicio, fin, None, None
    return inicio, fin, inicio_ant, fin_ant


def filtrar(df, sedes, categorias, inicio, fin) -> pd.DataFrame:
    return df[
        df["sede"].isin(sedes)
        & df["categoria"].isin(categorias)
        & df["fecha"].between(inicio, fin)
    ]


def promedio_diario_semanal(d: pd.DataFrame, columna="ingresos", por=None) -> pd.DataFrame:
    """Promedio diario de cada semana. Se usa el promedio (no la suma) para que
    las semanas incompletas del inicio y del final no parezcan caídas."""
    claves = ["fecha"] + ([por] if por else [])
    diario = d.groupby(claves)[columna].sum().reset_index()
    semana = pd.Grouper(key="fecha", freq="W-MON", label="left", closed="left")
    return diario.groupby([semana] + ([por] if por else []))[columna].mean().reset_index()


def chispa(valores) -> list | None:
    """Datos para la mini gráfica de st.metric (necesita al menos 2 puntos)."""
    valores = [float(v) for v in valores if pd.notna(v)]
    return valores if len(valores) >= 2 else None


def generar_hallazgos(actual: pd.DataFrame, anterior: pd.DataFrame | None) -> list[str]:
    ideas = []

    sedes = actual.groupby("sede")["ingresos"].sum().sort_values(ascending=False)
    if len(sedes) > 1:
        ideas.append(
            f"**{sedes.index[0]}** lidera con el **{pct(sedes.iloc[0] / sedes.sum(), False)}** de los ingresos."
        )

    productos = actual.groupby("producto")["ingresos"].sum()
    ideas.append(f"**{productos.idxmax()}** es el producto que más factura: **{millones(productos.max())}**.")

    por_dia = (
        actual.groupby(["fecha", "dia_semana"], observed=True)["ingresos"].sum()
        .groupby(level="dia_semana", observed=True).mean()
    )
    if len(por_dia) > 1:
        mejor, peor = por_dia.idxmax(), por_dia.idxmin()
        brecha = 1 - por_dia[peor] / por_dia[mejor]
        ideas.append(
            f"El mejor día es el **{DIAS_LARGOS[mejor]}**; el **{DIAS_LARGOS[peor]}** vende "
            f"**{pct(brecha, False)} menos**."
        )

    if anterior is not None and not anterior.empty:
        act = actual.groupby("producto")["ingresos"].sum()
        ant = anterior.groupby("producto")["ingresos"].sum()
        var = (act / ant - 1).replace([np.inf, -np.inf], np.nan).dropna()
        if len(var) > 1:
            texto = f"**{var.idxmax()}** es el que más creció (**{pct(var.max())}**)"
            if var.min() < 0:
                texto += f" y **{var.idxmin()}** el que más cayó (**{pct(var.min())}**)"
            ideas.append(texto + " frente al periodo anterior.")
    return ideas


# --- Estilo común de las gráficas -----------------------------------------------
def estilo(fig: go.Figure, alto: int = 340) -> go.Figure:
    fig.update_layout(
        height=alto,
        margin=dict(l=0, r=0, t=36, b=0),
        separators=",.",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""),
        barcornerradius=4,
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(showgrid=False, title_text="")
    fig.update_yaxes(gridcolor="rgba(45,27,14,0.08)", zeroline=False, title_text="")
    return fig


def encabezado(titulo: str, detalle: str):
    """Franja naranja con el título. Es HTML, por eso lleva unsafe_allow_html=True."""
    st.markdown(
        f"""
        <div style="background:{DEGRADADO_ENCABEZADO}; color:#ffffff; border-radius:0.9rem;
                    padding:1.3rem 1.6rem; margin-bottom:0.4rem;">
          <div style="font-size:0.8rem; font-weight:600; letter-spacing:0.08em;
                      text-transform:uppercase;">☕ Café Analítica</div>
          <div style="font-family:serif; font-size:2.2rem; font-weight:700; line-height:1.2;">{titulo}</div>
          <div style="font-size:0.95rem; margin-top:0.35rem;">{detalle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta(titulo: str, subtitulo: str | None = None):
    """Caja con borde y título; se usa con `with tarjeta(...):`."""
    caja = st.container(border=True)
    caja.markdown(f"**{titulo}**")
    if subtitulo:
        caja.caption(subtitulo)
    return caja


# ════════════════════════════════════════════════════════════════════════════
# 3. DATOS
# ════════════════════════════════════════════════════════════════════════════
df = cargar_datos(ARCHIVO)
FECHA_MIN, FECHA_MAX = df["fecha"].min(), df["fecha"].max()
TODAS_SEDES = sorted(df["sede"].unique())
TODAS_CATEGORIAS = sorted(df["categoria"].unique())

# ════════════════════════════════════════════════════════════════════════════
# 4. FILTROS (barra lateral)
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ☕ Café Analítica")
    st.caption(f"3 sedes · {fecha_txt(FECHA_MIN)} – {fecha_txt(FECHA_MAX)}")

    opcion = st.segmented_control("Periodo", PERIODOS, default="Últimos 3 meses")
    opcion = opcion or "Últimos 3 meses"  # si el usuario deselecciona, volvemos al valor por defecto

    rango_manual = None
    if opcion == "Personalizado":
        rango_manual = st.date_input(
            "Rango de fechas",
            value=(FECHA_MIN.date(), FECHA_MAX.date()),
            min_value=FECHA_MIN.date(),
            max_value=FECHA_MAX.date(),
        )

    sedes_sel = st.pills("Sedes", TODAS_SEDES, selection_mode="multi", default=TODAS_SEDES)
    categorias_sel = st.pills(
        "Categorías", TODAS_CATEGORIAS, selection_mode="multi", default=TODAS_CATEGORIAS
    )

    st.divider()
    st.caption("Datos simulados con fines académicos.")

if opcion == "Personalizado" and len(rango_manual) != 2:
    st.info("Selecciona también la fecha final del rango.")
    st.stop()
if not sedes_sel or not categorias_sel:
    st.warning("Selecciona al menos una sede y una categoría.")
    st.stop()

inicio, fin, inicio_ant, fin_ant = calcular_periodo(opcion, FECHA_MIN, FECHA_MAX, rango_manual)
actual = filtrar(df, sedes_sel, categorias_sel, inicio, fin)
anterior = filtrar(df, sedes_sel, categorias_sel, inicio_ant, fin_ant) if inicio_ant is not None else None
hay_comparacion = anterior is not None and not anterior.empty

if actual.empty:
    st.warning("No hay ventas con esos filtros.")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# 5. ENCABEZADO E INDICADORES
# ════════════════════════════════════════════════════════════════════════════
comparacion_txt = (
    f"comparado con {fecha_txt(inicio_ant)} – {fecha_txt(fin_ant)}"
    if hay_comparacion
    else "sin periodo anterior para comparar"
)
encabezado("Dashboard de ventas", f"<b>{fecha_txt(inicio)} – {fecha_txt(fin)}</b> · {comparacion_txt}")


def delta_txt(v_actual, v_anterior):
    v = variacion(v_actual, v_anterior) if hay_comparacion else None
    return None if v is None else f"{pct(v)} vs anterior"


ingresos = actual["ingresos"].sum()
unidades = actual["cantidad"].sum()
precio_prom = ingresos / unidades
ing_ant = anterior["ingresos"].sum() if hay_comparacion else None
uni_ant = anterior["cantidad"].sum() if hay_comparacion else None
precio_ant = ing_ant / uni_ant if hay_comparacion and uni_ant else None

por_producto = actual.groupby("producto")["ingresos"].sum()
estrella = por_producto.idxmax()
estrella_ant = (
    anterior.loc[anterior["producto"] == estrella, "ingresos"].sum() if hay_comparacion else None
)

diario = actual.groupby("fecha")[["ingresos", "cantidad"]].sum()
semanal = diario.resample("W-MON", label="left", closed="left").mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Ingresos", millones(ingresos), delta=delta_txt(ingresos, ing_ant), border=True,
    chart_data=chispa(semanal["ingresos"]), chart_type="area",
    help=f"Total exacto: {pesos(ingresos)}. La mini gráfica es el ingreso diario promedio de cada semana.",
)
k2.metric(
    "Unidades vendidas", entero(unidades), delta=delta_txt(unidades, uni_ant), border=True,
    chart_data=chispa(semanal["cantidad"]), chart_type="area",
)
k3.metric(
    "Precio promedio por unidad", pesos(precio_prom), delta=delta_txt(precio_prom, precio_ant),
    border=True, chart_data=chispa(semanal["ingresos"] / semanal["cantidad"]), chart_type="line",
    help="Ingresos ÷ unidades. Sube si se venden más productos caros.",
)
k4.metric(
    "Producto estrella", estrella, delta=delta_txt(por_producto[estrella], estrella_ant), border=True,
    help=f"El que más ingresos generó: {pesos(por_producto[estrella])}.",
)

# ════════════════════════════════════════════════════════════════════════════
# 6. PESTAÑAS
# ════════════════════════════════════════════════════════════════════════════
tab_resumen, tab_productos, tab_sedes, tab_simulador, tab_datos = st.tabs([
    ":material/insights: Resumen",
    ":material/bakery_dining: Productos",
    ":material/storefront: Sedes",
    ":material/tune: Simulador de precios",
    ":material/table_view: Datos",
])

# ── Resumen ─────────────────────────────────────────────────────────────────
with tab_resumen:
    izq, der = st.columns([2, 1])

    with izq:
        dias_periodo = (fin - inicio).days + 1
        if dias_periodo <= 45:
            serie = actual.groupby(["fecha", "sede"])["ingresos"].sum().reset_index()
            titulo, sub = "Ingresos diarios por sede", "Cada punto es un día."
        else:
            serie = promedio_diario_semanal(actual, por="sede")
            titulo, sub = "Ingreso diario promedio por sede", "Promedio de cada semana, para suavizar el ruido diario."
        with tarjeta(titulo, sub):
            fig = px.line(serie, x="fecha", y="ingresos", color="sede", color_discrete_map=COLORES_SEDE,
                          markers=dias_periodo > 45)
            fig.update_traces(line_width=2, marker_size=8,
                              hovertemplate="%{fullData.name}: $ %{y:,.0f}<extra></extra>")
            fig.update_layout(hovermode="x unified")
            fig.update_yaxes(tickprefix="$ ", tickformat="~s")
            st.plotly_chart(estilo(fig, 330), config=SIN_BARRA)

    with der:
        with tarjeta("Lo que dicen los datos", "Hallazgos calculados automáticamente."):
            for idea in generar_hallazgos(actual, anterior if hay_comparacion else None):
                st.markdown(f"- {idea}")

    izq, der = st.columns(2)

    with izq:
        with tarjeta("Mix de categorías por mes", "Participación de cada categoría en los ingresos del mes."):
            mix = actual.groupby(["mes", "mes_txt", "categoria"])["ingresos"].sum().reset_index()
            fig = px.bar(
                mix, x="mes_txt", y="ingresos", color="categoria",
                color_discrete_map=COLORES_CATEGORIA,
                category_orders={"mes_txt": mix.sort_values("mes")["mes_txt"].unique().tolist(),
                                 "categoria": TODAS_CATEGORIAS},
            )
            fig.update_traces(marker_line_width=2, marker_line_color=FONDO,
                              hovertemplate="%{fullData.name}: %{y:.1f} %<extra></extra>")
            fig.update_layout(barnorm="percent", bargap=0.35)
            fig.update_yaxes(ticksuffix=" %")
            st.plotly_chart(estilo(fig), config=SIN_BARRA)

    with der:
        cat_act = actual.groupby("categoria")["ingresos"].sum()
        if hay_comparacion:
            cat_ant = anterior.groupby("categoria")["ingresos"].sum().reindex(cat_act.index, fill_value=0)
            orden = cat_act.sort_values().index
            with tarjeta("Ingresos por categoría", "Periodo actual frente al anterior; el número es la variación."):
                fig = go.Figure()
                fig.add_bar(y=orden, x=cat_ant[orden], name="Periodo anterior", orientation="h",
                            marker_color=COLOR_REFERENCIA,
                            hovertemplate="Anterior: $ %{x:,.0f}<extra></extra>")
                fig.add_bar(y=orden, x=cat_act[orden], name="Periodo actual", orientation="h",
                            marker_color=COLOR_ACTUAL,
                            text=[pct(variacion(cat_act[c], cat_ant[c])) if cat_ant[c] else "" for c in orden],
                            textposition="outside", cliponaxis=False,
                            hovertemplate="Actual: $ %{x:,.0f}<extra></extra>")
                fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
                fig.update_xaxes(tickprefix="$ ", tickformat="~s",
                                 range=[0, max(cat_act.max(), cat_ant.max()) * 1.2])
                st.plotly_chart(estilo(fig), config=SIN_BARRA)
        else:
            with tarjeta("Ingresos por categoría", "Elige «Último mes» o «Últimos 3 meses» para comparar."):
                datos = cat_act.sort_values().reset_index()
                fig = px.bar(datos, x="ingresos", y="categoria", orientation="h", color="categoria",
                             color_discrete_map=COLORES_CATEGORIA)
                fig.update_traces(hovertemplate="$ %{x:,.0f}<extra></extra>")
                fig.update_layout(showlegend=False, bargap=0.35)
                fig.update_xaxes(tickprefix="$ ", tickformat="~s")
                st.plotly_chart(estilo(fig), config=SIN_BARRA)

# ── Productos ───────────────────────────────────────────────────────────────
with tab_productos:
    resumen = (
        actual.groupby(["producto", "categoria"], as_index=False)
        .agg(precio=("precio_unitario", "first"), unidades=("cantidad", "sum"), ingresos=("ingresos", "sum"))
        .sort_values("ingresos", ascending=False)
    )
    resumen["participacion"] = resumen["ingresos"] / resumen["ingresos"].sum() * 100
    if hay_comparacion:
        ant_prod = anterior.groupby("producto")["ingresos"].sum()
        resumen["variacion"] = (resumen["ingresos"] / resumen["producto"].map(ant_prod) - 1) * 100
    tendencias = promedio_diario_semanal(actual, por="producto").groupby("producto")["ingresos"].agg(list)
    resumen["tendencia"] = resumen["producto"].map(tendencias)

    izq, der = st.columns([3, 1])
    with izq:
        with tarjeta("Ranking de productos por ingresos", "El color indica la categoría."):
            fig = px.bar(resumen, x="ingresos", y="producto", orientation="h", color="categoria",
                         color_discrete_map=COLORES_CATEGORIA,
                         category_orders={"categoria": TODAS_CATEGORIAS})
            fig.update_traces(hovertemplate="%{y}: $ %{x:,.0f}<extra></extra>")
            fig.update_layout(bargap=0.3)
            fig.update_yaxes(categoryorder="total ascending")
            fig.update_xaxes(tickprefix="$ ", tickformat="~s")
            st.plotly_chart(estilo(fig, 420), config=SIN_BARRA)
    with der:
        st.markdown("**Top 3**")
        for fila in resumen.head(3).itertuples():
            delta = f"{pct(fila.variacion / 100)} vs anterior" if hay_comparacion and pd.notna(fila.variacion) else None
            st.metric(fila.producto, millones(fila.ingresos), delta=delta, border=True,
                      chart_data=chispa(fila.tendencia or []), chart_type="area")

    columnas = ["producto", "categoria", "precio", "unidades", "ingresos", "participacion"]
    columnas += (["variacion"] if hay_comparacion else []) + ["tendencia"]
    st.dataframe(
        resumen[columnas],
        hide_index=True,
        column_config={
            "producto": "Producto",
            "categoria": "Categoría",
            "precio": st.column_config.NumberColumn("Precio", format="$ %d"),
            "unidades": st.column_config.NumberColumn("Unidades", format="%d"),
            "ingresos": st.column_config.NumberColumn("Ingresos", format="$ %d"),
            "participacion": st.column_config.ProgressColumn(
                "Participación", format="%.1f %%", min_value=0, max_value=float(resumen["participacion"].max())
            ),
            "variacion": st.column_config.NumberColumn("Var. vs anterior", format="%+.1f %%"),
            "tendencia": st.column_config.LineChartColumn("Tendencia semanal", y_min=0),
        },
    )

# ── Sedes ───────────────────────────────────────────────────────────────────
with tab_sedes:
    total = actual["ingresos"].sum()
    columnas_sede = st.columns(len(sedes_sel))
    for col, sede in zip(columnas_sede, sorted(sedes_sel)):
        d = actual[actual["sede"] == sede]
        if d.empty:
            continue
        d_ant = anterior[anterior["sede"] == sede] if hay_comparacion else None
        ing_sede = d["ingresos"].sum()
        top = d.groupby("producto")["ingresos"].sum().idxmax()
        dia = (d.groupby(["fecha", "dia_semana"], observed=True)["ingresos"].sum()
               .groupby(level="dia_semana", observed=True).mean().idxmax())
        with col.container(border=True):
            st.markdown(
                f"<span style='color:{COLORES_SEDE[sede]};font-size:1.3rem'>●</span> "
                f"<span style='font-size:1.15rem;font-weight:600'>{sede}</span>",
                unsafe_allow_html=True,
            )
            st.metric(
                "Ingresos", millones(ing_sede),
                delta=delta_txt(ing_sede, d_ant["ingresos"].sum() if d_ant is not None else None),
                chart_data=chispa(promedio_diario_semanal(d)["ingresos"]), chart_type="area",
            )
            st.markdown(
                f"Participación: **{pct(ing_sede / total, False)}**  \n"
                f"Producto top: **{top}**  \n"
                f"Mejor día: **{DIAS_LARGOS[dia]}**"
            )

    izq, der = st.columns(2)
    with izq:
        with tarjeta("Ingreso diario promedio según el día", "En millones de pesos. Más oscuro = vende más."):
            diario_sede = actual.groupby(["fecha", "dia_semana", "sede"], observed=True)["ingresos"].sum().reset_index()
            matriz = (diario_sede.groupby(["sede", "dia_semana"], observed=True)["ingresos"].mean()
                      .unstack("dia_semana") / 1e6)
            fig = px.imshow(matriz, aspect="auto", color_continuous_scale=ESCALA_NARANJA)
            # Número de cada celda: blanco sobre las oscuras y café sobre las claras, para que siempre se lea
            minimo, maximo = np.nanmin(matriz.values), np.nanmax(matriz.values)
            for sede in matriz.index:
                for dia in matriz.columns:
                    valor = matriz.loc[sede, dia]
                    if pd.isna(valor):
                        continue
                    oscura = (valor - minimo) / ((maximo - minimo) or 1) > 0.45
                    fig.add_annotation(x=dia, y=sede, text=f"{valor:.2f}".replace(".", ","), showarrow=False,
                                       font=dict(size=13, color="#ffffff" if oscura else "#2d1b0e"))
            fig.update_traces(hovertemplate="%{y} · %{x}: $ %{z:.2f} M<extra></extra>")
            fig.update_layout(coloraxis_colorbar=dict(title="M$", thickness=12))
            st.plotly_chart(estilo(fig, 300), config=SIN_BARRA)
    with der:
        with tarjeta("Mix de categorías por sede", "Participación de cada categoría en los ingresos de la sede."):
            mix_sede = actual.groupby(["sede", "categoria"])["ingresos"].sum().reset_index()
            fig = px.bar(mix_sede, x="ingresos", y="sede", color="categoria", orientation="h",
                         color_discrete_map=COLORES_CATEGORIA,
                         category_orders={"categoria": TODAS_CATEGORIAS,
                                          "sede": sorted(sedes_sel, reverse=True)})
            fig.update_traces(marker_line_width=2, marker_line_color=FONDO,
                              hovertemplate="%{fullData.name}: %{x:.1f} %<extra></extra>")
            fig.update_layout(barnorm="percent", bargap=0.35)
            fig.update_xaxes(ticksuffix=" %")
            st.plotly_chart(estilo(fig, 300), config=SIN_BARRA)

# ── Simulador ───────────────────────────────────────────────────────────────
with tab_simulador:
    st.markdown("#### ¿Qué pasa con los ingresos si cambio los precios?")
    st.caption("Simulación sobre las ventas del periodo y los filtros elegidos. Es un modelo simple, para explorar escenarios.")

    c1, c2, c3 = st.columns(3)
    cat_sim = c1.selectbox("Categoría a modificar", ["Todas"] + TODAS_CATEGORIAS)
    cambio = c2.slider("Cambio de precio", -20, 30, 10, step=1, format="%d %%") / 100
    sensibilidad = c3.slider(
        "Sensibilidad de los clientes", 0.0, 2.0, 0.5, step=0.1,
        help="Por cada 1 % que sube el precio, la demanda cae este número de %. "
             "Ej.: 0,5 → si el precio sube 10 %, se venden 5 % menos unidades.",
    )

    afectado = np.ones(len(actual), dtype=bool) if cat_sim == "Todas" else (actual["categoria"] == cat_sim).to_numpy()
    factor_precio = np.where(afectado, 1 + cambio, 1.0)
    factor_cantidad = np.where(afectado, max(0.0, 1 - sensibilidad * cambio), 1.0)
    sim = actual.assign(
        cantidad_sim=actual["cantidad"] * factor_cantidad,
        ingresos_sim=actual["precio_unitario"] * factor_precio * actual["cantidad"] * factor_cantidad,
    )
    ing_sim = sim["ingresos_sim"].sum()
    uni_sim = sim["cantidad_sim"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Ingresos actuales", millones(ingresos), border=True)
    m2.metric("Ingresos simulados", millones(ing_sim), delta=pct(ing_sim / ingresos - 1), border=True)
    m3.metric("Unidades simuladas", entero(uni_sim), delta=pct(uni_sim / unidades - 1), border=True)

    izq, der = st.columns([3, 2])
    with izq:
        with tarjeta("Ingresos por categoría: actual vs simulado"):
            comp = sim.groupby("categoria")[["ingresos", "ingresos_sim"]].sum()
            orden = comp["ingresos"].sort_values().index
            fig = go.Figure()
            fig.add_bar(y=orden, x=comp.loc[orden, "ingresos"], name="Actual", orientation="h",
                        marker_color=COLOR_REFERENCIA, hovertemplate="Actual: $ %{x:,.0f}<extra></extra>")
            fig.add_bar(y=orden, x=comp.loc[orden, "ingresos_sim"], name="Simulado", orientation="h",
                        marker_color=COLOR_ACTUAL, hovertemplate="Simulado: $ %{x:,.0f}<extra></extra>")
            fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
            fig.update_xaxes(tickprefix="$ ", tickformat="~s")
            st.plotly_chart(estilo(fig, 300), config=SIN_BARRA)
    with der:
        with tarjeta("Cómo leer el resultado"):
            st.markdown(
                f"- El precio cambia **{pct(cambio)}** y las unidades **{pct(-sensibilidad * cambio)}** "
                f"en {'todas las categorías' if cat_sim == 'Todas' else f'**{cat_sim}**'}.\n"
                f"- Con sensibilidad **menor que 1**, subir precios **aumenta** los ingresos: "
                f"se pierden pocas ventas.\n"
                f"- Con sensibilidad **mayor que 1**, subir precios **reduce** los ingresos: "
                f"los clientes se van más rápido de lo que sube el precio."
            )
            if ing_sim >= ingresos:
                st.success(f"Este escenario suma **{millones(ing_sim - ingresos)}** en el periodo.")
            else:
                st.error(f"Este escenario resta **{millones(ingresos - ing_sim)}** en el periodo.")

# ════════════════════════════════════════════════════════════════════════════
# 7. TABLA Y DESCARGA
# ════════════════════════════════════════════════════════════════════════════
with tab_datos:
    columnas = ["fecha", "sede", "producto", "categoria", "precio_unitario", "cantidad", "ingresos"]
    st.caption(f"{entero(len(actual))} filas con los filtros actuales.")
    st.dataframe(
        actual[columnas].sort_values(["fecha", "sede"]),
        hide_index=True,
        column_config={
            "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "sede": "Sede",
            "producto": "Producto",
            "categoria": "Categoría",
            "precio_unitario": st.column_config.NumberColumn("Precio", format="$ %d"),
            "cantidad": st.column_config.NumberColumn("Unidades", format="%d"),
            "ingresos": st.column_config.NumberColumn("Ingresos", format="$ %d"),
        },
    )
    st.download_button(
        "Descargar CSV filtrado",
        data=actual[columnas].to_csv(index=False).encode("utf-8"),
        file_name=f"ventas_{inicio:%Y%m%d}_{fin:%Y%m%d}.csv",
        mime="text/csv",
        icon=":material/download:",
    )
