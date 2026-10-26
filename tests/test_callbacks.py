"""Tests básicos de los callbacks (punto opcional +0.5).

Se prueban las funciones de lógica que usan los callbacks, sin levantar el servidor.
Ejecutar:  python -m pytest -q
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.graph_objects as go  # noqa: E402

from callbacks.filtros import calcular_detalle, calcular_inicio  # noqa: E402
from utils.datos import cargar_datos, filtrar, meses_disponibles  # noqa: E402

TODOS_LOS_METODOS = sorted(cargar_datos()["metodo_pago"].cat.categories)
RANGO_COMPLETO = [0, len(meses_disponibles()) - 1]


def test_datos_limpios_sin_nulos_y_tamano_adecuado():
    df = cargar_datos()
    assert 1_000 <= len(df) <= 100_000
    assert df[["nota", "dias_entrega", "estado", "metodo_pago"]].isna().sum().sum() == 0
    assert df["nota"].between(1, 5).all()


def test_sin_filtros_devuelve_todo():
    df = cargar_datos()
    assert len(filtrar(df, rango_meses=RANGO_COMPLETO, metodos=TODOS_LOS_METODOS)) == len(df)


def test_filtro_por_region_reduce_y_respeta_region():
    df = filtrar(cargar_datos(), regiones=["Sur"])
    assert 0 < len(df) < len(cargar_datos())
    assert set(df["region"].unique()) == {"Sur"}


def test_checklist_vacio_no_devuelve_pedidos():
    assert filtrar(cargar_datos(), metodos=[]).empty


def test_callback_inicio_devuelve_kpis_y_figuras():
    salida = calcular_inicio(None, None, RANGO_COMPLETO, TODOS_LOS_METODOS, None)
    assert len(salida) == 11
    assert salida[0] == f"{len(cargar_datos()):,}".replace(",", ".")
    assert all(isinstance(f, go.Figure) for f in salida[4:8])


def test_callback_inicio_con_filtro_por_estado():
    total = calcular_inicio(None, None, RANGO_COMPLETO, TODOS_LOS_METODOS, None)[0]
    solo_sp = calcular_inicio(None, ["SP"], RANGO_COMPLETO, TODOS_LOS_METODOS, None)[0]
    assert solo_sp != total


def test_callback_detalle_con_seleccion_vacia_no_falla():
    salida = calcular_detalle(None, None, RANGO_COMPLETO, [], None)
    assert len(salida) == 7
    assert "No hay pedidos" in salida[4]


def test_pedidos_tarde_tienen_peor_nota():
    """El hallazgo central del dashboard debe sostenerse en los datos."""
    df = cargar_datos()
    assert df[df["llego_tarde"]]["nota"].mean() < df[~df["llego_tarde"]]["nota"].mean() - 1
