"""Genera ventas_cafeteria.csv con datos simulados (no es Streamlit, es solo pandas).

Ejecutar una sola vez:
    ..\\.venv\\Scripts\\python.exe generar_datos.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)  # semilla fija: siempre salen los mismos datos

productos = pd.DataFrame(
    [
        ("Café americano", "Bebidas calientes", 4500, 30),
        ("Capuchino", "Bebidas calientes", 7000, 22),
        ("Latte", "Bebidas calientes", 7500, 18),
        ("Té chai", "Bebidas calientes", 6500, 8),
        ("Frappé", "Bebidas frías", 9500, 12),
        ("Limonada", "Bebidas frías", 6000, 10),
        ("Croissant", "Panadería", 5000, 15),
        ("Pandebono", "Panadería", 3000, 25),
        ("Sándwich", "Comidas", 14000, 9),
        ("Ensalada", "Comidas", 16000, 5),
    ],
    columns=["producto", "categoria", "precio_unitario", "demanda_base"],
)

# Cada sede vende distinto: la de la universidad baja mucho el fin de semana
sedes = {
    "Centro": {"factor": 1.0, "fin_de_semana": 0.8},
    "Norte": {"factor": 0.8, "fin_de_semana": 1.3},
    "Universidad": {"factor": 1.2, "fin_de_semana": 0.4},
}

fechas = pd.date_range("2026-01-01", "2026-06-30", freq="D")

filas = []
for fecha in fechas:
    es_fin_de_semana = fecha.dayofweek >= 5
    tendencia = 1 + 0.002 * (fecha - fechas[0]).days  # el negocio crece poco a poco
    calor = 1 + 0.3 * np.sin((fecha.month - 1) / 12 * 2 * np.pi)  # más bebidas frías a mitad de año
    for sede, cfg in sedes.items():
        ajuste_dia = cfg["fin_de_semana"] if es_fin_de_semana else 1.0
        for p in productos.itertuples():
            media = p.demanda_base * cfg["factor"] * ajuste_dia * tendencia
            if p.categoria == "Bebidas frías":
                media *= calor
            cantidad = int(rng.poisson(media))
            filas.append(
                {
                    "fecha": fecha.date(),
                    "sede": sede,
                    "producto": p.producto,
                    "categoria": p.categoria,
                    "precio_unitario": p.precio_unitario,
                    "cantidad": cantidad,
                    "ingresos": cantidad * p.precio_unitario,
                }
            )

df = pd.DataFrame(filas)
salida = Path(__file__).parent / "ventas_cafeteria.csv"
df.to_csv(salida, index=False, encoding="utf-8")
print(f"Listo: {len(df):,} filas guardadas en {salida.name}")
