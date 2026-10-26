"""Piezas de layout reutilizadas por las dos páginas: navbar, panel de filtros y tarjetas."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from utils.datos import cargar_datos, meses_disponibles, nombre_mes


def navbar() -> dbc.Navbar:
    return dbc.Navbar(
        dbc.Container([
            html.Div([
                html.Span("TP2", className="pill-logo"),
                html.Span("Entregas y reseñas", className="brand-title"),
            ], className="d-flex align-items-center gap-2"),
            dbc.Nav([
                dbc.NavLink("Entrega y satisfacción", href="/", active="exact"),
                dbc.NavLink("Producto, pago y clientes", href="/detalle", active="exact"),
            ], pills=True, className="nav-paginas"),
        ], fluid=True, className="flex-wrap gap-2"),
        className="navbar-marca", dark=False,
    )


def panel_filtros() -> dbc.Card:
    df = cargar_datos()
    meses = meses_disponibles()
    # Marcas del slider: solo cada 4 meses para que se lea en móvil
    marcas = {i: nombre_mes(m) for i, m in enumerate(meses) if i % 4 == 0 or i == len(meses) - 1}

    return dbc.Card(dbc.CardBody([
        html.Div("Filtros", className="eyebrow"),

        html.Label("Región", className="filtro-label"),
        dcc.Dropdown(id="filtro-region", options=sorted(df["region"].cat.categories), multi=True,
                     placeholder="Todas las regiones"),

        html.Label("Estado", className="filtro-label"),
        dcc.Dropdown(id="filtro-estado", multi=True, placeholder="Todos los estados"),
        html.Small("Tip: también puedes hacer clic en una burbuja del gráfico de estados.",
                   className="text-muted d-block mt-1"),

        html.Label("Periodo de compra", className="filtro-label"),
        dcc.RangeSlider(id="filtro-meses", min=0, max=len(meses) - 1, step=1,
                        value=[0, len(meses) - 1], marks=marcas, allowCross=False,
                        allow_direct_input=False),
        html.Div(id="texto-periodo", className="texto-periodo"),

        html.Label("Método de pago", className="filtro-label"),
        dbc.Checklist(id="filtro-pago", options=sorted(df["metodo_pago"].cat.categories),
                      value=sorted(df["metodo_pago"].cat.categories), switch=True),

        html.Label("Categoría de producto", className="filtro-label"),
        dcc.Dropdown(id="filtro-categoria",
                     options=df["categoria"].value_counts().index.tolist(),
                     multi=True, placeholder="Todas las categorías"),

        dbc.Button("Limpiar filtros", id="btn-limpiar", color="dark", outline=True,
                   size="sm", className="mt-3 w-100"),
    ]), className="card-filtros")


def tarjeta_kpi(id_valor: str, etiqueta: str) -> dbc.Col:
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.Div(etiqueta, className="kpi-label"),
        html.Div("—", id=id_valor, className="kpi-valor"),
    ]), className="card-kpi"), xs=6, lg=3)


def tarjeta_grafico(titulo: str, subtitulo: str, id_grafico: str, id_insight: str | None = None,
                    **graph_kwargs) -> dbc.Card:
    """Tarjeta estándar: título que dice el hallazgo, subtítulo con qué se mide, gráfico, y nota dinámica."""
    cuerpo = [
        html.H3(titulo, className="card-titulo"),
        html.P(subtitulo, className="card-sub"),
        dcc.Loading(dcc.Graph(id=id_grafico, config={"displayModeBar": False, "responsive": True},
                              **graph_kwargs), type="dot", color="#2540D9"),
    ]
    if id_insight:
        cuerpo.append(html.Div(id=id_insight, className="insight"))
    return dbc.Card(dbc.CardBody(cuerpo), className="card-grafico")
