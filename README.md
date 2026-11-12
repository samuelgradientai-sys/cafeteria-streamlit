# Práctica Streamlit · Dashboard de una cafetería

Cinco pasos, cada uno es una app completa que agrega algo nuevo al anterior.
Lo nuevo de cada archivo está marcado con `# NUEVO` en los comentarios.

## Cómo ejecutar

En PowerShell, desde la carpeta `ANALAITICA`:

```powershell
cd PRACTICA_STREAMLIT
..\.venv\Scripts\python.exe -m streamlit run paso_1_hola.py
```

Se abre en `http://localhost:8501`. Para pasar al siguiente: `Ctrl + C` y cambia el nombre del archivo.

Mientras la app está abierta, edita el `.py`, guarda y presiona **Rerun** (o elige **Always rerun**).

Los datos (`ventas_cafeteria.csv`) son simulados. Para regenerarlos:
`..\.venv\Scripts\python.exe generar_datos.py`

## Los pasos

| Paso | Archivo | Qué aprendes |
|---|---|---|
| 1 | `paso_1_hola.py` | `st.title`, `st.write`, widgets (`text_input`, `slider`, `radio`) y **el ciclo de ejecución** |
| 2 | `paso_2_datos.py` | `@st.cache_data`, `st.dataframe`, `st.metric`, `st.expander` |
| 3 | `paso_3_filtros.py` | `st.sidebar`, `multiselect`, `date_input`, filtrar con pandas, `st.stop()` |
| 4 | `paso_4_graficas.py` | `st.columns`, Plotly (`px.line`, `px.bar`), colores fijos por sede |
| 5 | `paso_5_dashboard.py` | `st.tabs`, `column_config`, `download_button`, `st.session_state`, `st.form` |

## Retos (hazlos tú, sin mirar la solución)

**Paso 1**
- Agrega un `st.number_input` para el presupuesto diario en café y muestra cuánto gasta al mes (`presupuesto * 30`).
- Agrega un `st.checkbox("Mostrar secreto")` que, si está marcado, muestre un `st.balloons()`.

**Paso 2**
- Agrega un segundo `st.metric` con las **unidades vendidas** (`df["cantidad"].sum()`).
- Quita el `@st.cache_data`, agrega `import time` y `time.sleep(2)` dentro de `cargar_datos`, y abre/cierra un expander. Después vuelve a poner el caché. ¿Notas la diferencia?

**Paso 3**
- Agrega un filtro por **producto** (`multiselect`) que solo muestre los productos de las categorías elegidas.
- Agrega un `st.slider` de "cantidad mínima" y filtra las filas con `cantidad >=` ese valor.

**Paso 4**
- Agrega una gráfica de **unidades vendidas por categoría** (`px.bar`).
- Cambia la línea semanal a mensual (`freq="MS"`). ¿Cuál se lee mejor?

**Paso 5**
- Agrega una pestaña **"Comparar sedes"** con un `st.selectbox` para elegir dos sedes y muestra sus ingresos lado a lado con `st.columns(2)`.
- En la bitácora, guarda junto a cada hallazgo la hora (`datetime.now()`) y muéstrala.

**Reto final:** haz tu propio dashboard con `CLASE_2/produccion_planta.csv` siguiendo la estructura del paso 5, sin copiar y pegar.

## Chuleta rápida

```python
st.set_page_config(layout="wide")        # siempre primero
x = st.selectbox("Etiqueta", opciones)    # los widgets devuelven el valor elegido
with st.sidebar: ...                      # barra lateral
a, b = st.columns(2)                      # columnas
t1, t2 = st.tabs(["Uno", "Dos"])          # pestañas
@st.cache_data                            # cachear carga de datos
st.session_state["clave"] = valor         # guardar algo entre repeticiones
st.stop()                                 # cortar la ejecución
```
