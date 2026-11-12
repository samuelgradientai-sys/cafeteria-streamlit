# ☕ Cafetería · Dashboard de ventas

Dashboard interactivo en **Streamlit** sobre las ventas de una cafetería con 3 sedes (Centro, Norte y Universidad), de enero a junio de 2026.

**App publicada:** _(pega aquí el enlace de Streamlit Cloud)_

## Qué incluye

- **Periodo con comparación automática:** último mes, últimos 3 meses, todo o un rango personalizado. Cada indicador se compara con el periodo anterior de igual duración.
- **Indicadores** con variación y mini gráfica de tendencia: ingresos, unidades, precio promedio y producto estrella.
- **Resumen:** evolución por sede, hallazgos automáticos, mix de categorías por mes e ingresos por categoría frente al periodo anterior.
- **Productos:** ranking, top 3 y tabla con participación, variación y tendencia semanal.
- **Sedes:** ficha de cada sede, mapa de calor por día de la semana y mix de categorías.
- **Simulador de precios:** ¿qué pasa con los ingresos si subo o bajo precios?
- **Datos:** tabla filtrada y descarga en CSV.

## Estructura

```
cafeteria-streamlit/
├── app.py                  ← la app principal (la que se despliega)
├── ventas_cafeteria.csv    ← datos simulados
├── generar_datos.py        ← script que genera el CSV
├── requirements.txt        ← librerías para Streamlit Cloud
├── .streamlit/config.toml  ← tema visual (colores café)
└── paso_1 … paso_5         ← versiones de aprendizaje, de lo simple a lo completo
```

## Ejecución local

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501`.

## Ruta de aprendizaje

Los archivos `paso_*.py` construyen el dashboard poco a poco. Lo nuevo de cada uno está marcado con `# NUEVO`.

| Paso | Qué se aprende |
|---|---|
| `paso_1_hola.py` | Texto, widgets y el ciclo de ejecución |
| `paso_2_datos.py` | `@st.cache_data`, `st.dataframe`, `st.metric`, `st.expander` |
| `paso_3_filtros.py` | Barra lateral, filtros y `st.stop()` |
| `paso_4_graficas.py` | `st.columns` y gráficas con Plotly |
| `paso_5_dashboard.py` | Pestañas, `column_config`, descarga, `st.session_state` y `st.form` |
| `app.py` | Todo junto, más comparación de periodos, tarjetas, hallazgos y simulador |

### Retos

1. **Paso 1:** agrega un `st.number_input` de presupuesto diario y muestra el gasto mensual.
2. **Paso 2:** quita `@st.cache_data`, agrega `time.sleep(2)` en la carga y nota la diferencia.
3. **Paso 3:** agrega un filtro por producto que dependa de las categorías elegidas.
4. **Paso 4:** agrega una gráfica de unidades por categoría.
5. **Paso 5:** agrega una pestaña para comparar dos sedes lado a lado.

## Datos

`ventas_cafeteria.csv` es **simulado** (semilla fija), con fines académicos. Para regenerarlo: `python generar_datos.py`.

---
Maestría en Analítica Aplicada · Visualización e Inteligencia de Negocios
