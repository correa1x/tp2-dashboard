"""Carga y filtrado de datos. Todo lo que toca el DataFrame vive aquí."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

RUTA_DATOS = Path(__file__).resolve().parent.parent / "data" / "pedidos_limpios.csv.gz"

# Rangos de días de entrega usados en los gráficos
RANGOS_DIAS = [0, 3, 7, 14, 21, 30, 90]
ETIQUETAS_DIAS = ["0–3", "4–7", "8–14", "15–21", "22–30", "31+"]


@lru_cache(maxsize=1)
def cargar_datos() -> pd.DataFrame:
    """Lee el CSV limpio una sola vez (queda en memoria para todos los callbacks)."""
    df = pd.read_csv(RUTA_DATOS, parse_dates=["fecha_compra", "mes"])
    df["rango_dias"] = pd.cut(df["dias_entrega"], bins=RANGOS_DIAS, labels=ETIQUETAS_DIAS)
    # Tipos categóricos: menos memoria y groupby más rápido
    for c in ["estado", "region", "categoria", "metodo_pago"]:
        df[c] = df[c].astype("category")
    return df


MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def nombre_mes(fecha: pd.Timestamp, corto: bool = True) -> str:
    """'ene 18' / 'ene 2018' sin depender del idioma del sistema."""
    anio = f"{fecha:%y}" if corto else f"{fecha:%Y}"
    return f"{MESES_ES[fecha.month - 1]} {anio}"


def meses_disponibles() -> list[pd.Timestamp]:
    return sorted(cargar_datos()["mes"].unique())


def filtrar(df: pd.DataFrame, regiones=None, estados=None, rango_meses=None,
            metodos=None, categorias=None) -> pd.DataFrame:
    """Aplica los filtros del dashboard. Un filtro vacío/None significa 'todos'."""
    mascara = pd.Series(True, index=df.index)
    if regiones:
        mascara &= df["region"].isin(regiones)
    if estados:
        mascara &= df["estado"].isin(estados)
    if rango_meses:
        meses = meses_disponibles()
        inicio, fin = meses[rango_meses[0]], meses[rango_meses[1]]
        mascara &= df["mes"].between(inicio, fin)
    if metodos is not None:  # checklist: lista vacía = ningún método seleccionado
        mascara &= df["metodo_pago"].isin(metodos)
    if categorias:
        mascara &= df["categoria"].isin(categorias)
    return df[mascara]


def kpis(df: pd.DataFrame) -> dict:
    """Indicadores principales de la selección."""
    if df.empty:
        return {"pedidos": 0, "nota": None, "pct_tarde": None, "pct_negativas": None, "dias": None}
    return {
        "pedidos": len(df),
        "nota": df["nota"].mean(),
        "pct_tarde": df["llego_tarde"].mean() * 100,
        "pct_negativas": df["resena_negativa"].mean() * 100,
        "dias": df["dias_entrega"].median(),
    }


def comparar_a_tiempo_vs_tarde(df: pd.DataFrame) -> dict:
    """Nota promedio y % de reseñas negativas según si el pedido llegó tarde."""
    g = df.groupby("llego_tarde").agg(nota=("nota", "mean"), negativas=("resena_negativa", "mean"))
    return {
        "nota_a_tiempo": g.loc[False, "nota"] if False in g.index else None,
        "nota_tarde": g.loc[True, "nota"] if True in g.index else None,
        "neg_a_tiempo": g.loc[False, "negativas"] * 100 if False in g.index else None,
        "neg_tarde": g.loc[True, "negativas"] * 100 if True in g.index else None,
    }
