"""
TP2 — Dashboard interactivo con Dash
¿Qué hace que un cliente de ecommerce deje una mala reseña?

Ejecutar en local:   python app.py   → http://127.0.0.1:8050
En la nube (Render):  gunicorn app:server
"""

import os

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from callbacks.filtros import registrar_callbacks
from layouts.componentes import navbar, panel_filtros
from utils.datos import cargar_datos

# Cargar los datos al arrancar (queda en caché para todos los usuarios)
cargar_datos()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,  # los gráficos de cada página no existen al mismo tiempo
    title="Entregas y reseñas · TP2",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # lo usa gunicorn en el despliegue

app.layout = html.Div([
    dcc.Location(id="url"),
    navbar(),
    dbc.Container([
        dbc.Row([
            dbc.Col(panel_filtros(), lg=3, className="col-filtros"),
            dbc.Col(html.Div(id="contenido-pagina"), lg=9),
        ], className="g-4"),
        html.Footer([
            "Datos: ", html.A("Brazilian E-Commerce Public Dataset by Olist",
                              href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce", target="_blank"),
            " · Valores en reales brasileños (R$) · TP2 Visualización de Datos con Python, 2026-2",
        ], className="footer"),
    ], fluid=True, className="contenedor"),
])

registrar_callbacks(app)

if __name__ == "__main__":
    app.run(debug=os.environ.get("DEBUG", "1") == "1", host="0.0.0.0",
            port=int(os.environ.get("PORT", 8050)))
