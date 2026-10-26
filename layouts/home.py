"""Página principal: la pregunta de investigación y la evidencia sobre logística."""

import dash_bootstrap_components as dbc
from dash import html

from layouts.componentes import tarjeta_grafico, tarjeta_kpi


def layout() -> html.Div:
    return html.Div([
        html.Section([
            html.Div("Pregunta de investigación", className="eyebrow"),
            html.H1(["¿Qué hace que un cliente de ecommerce deje una ",
                     html.Em("mala reseña"), "?"], className="titulo-hero"),
            html.P("¿El producto, el precio, el método de pago… o la entrega? Lo respondemos con "
                   "~95.000 pedidos reales de Olist, el mayor marketplace de Brasil (2017–2018).",
                   className="lead-hero"),
        ], className="hero"),

        dbc.Row([
            tarjeta_kpi("kpi-pedidos", "Pedidos analizados"),
            tarjeta_kpi("kpi-nota", "Nota promedio"),
            tarjeta_kpi("kpi-tarde", "Llegaron tarde"),
            tarjeta_kpi("kpi-negativas", "Reseñas de 1–2 ★"),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(tarjeta_grafico(
                "Pasadas 3 semanas, la satisfacción se desploma",
                "Nota promedio y % de reseñas negativas según cuántos días tardó el pedido en llegar.",
                "graf-dias", "insight-dias"), lg=7),
            dbc.Col(tarjeta_grafico(
                "Llegar tarde convierte un 5 en un 1",
                "Reparto de estrellas: pedidos que llegaron antes de la fecha prometida vs. después.",
                "graf-tarde", "insight-tarde"), lg=5),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(tarjeta_grafico(
                "Donde la entrega es lenta, la nota es baja",
                "Cada burbuja es un estado: días promedio de entrega vs. nota. Tamaño = pedidos. "
                "Haz clic en una burbuja para filtrar todo el dashboard por ese estado.",
                "graf-estados", "insight-estados"), lg=7),
            dbc.Col(tarjeta_grafico(
                "Cuando crece la demanda, la logística se rompe",
                "Pedidos por mes y % que llegó tarde. Fíjate en feb–mar 2018 y en Black Friday (nov 2017).",
                "graf-tendencia"), lg=5),
        ], className="g-3 mb-3"),

        dbc.Card(dbc.CardBody([
            html.Div("Caso aplicado", className="eyebrow eyebrow-claro"),
            html.H3("Qué significa esto para una marca nueva como Puuro", className="card-titulo claro"),
            dbc.Row([
                dbc.Col([html.Span("01", className="num"),
                         html.P("Prometer con margen. Lo que castiga la reseña no son los días sino incumplir "
                                "la fecha prometida. Mejor prometer 15 días y entregar en 10.")], md=4),
                dbc.Col([html.Span("02", className="num"),
                         html.P("Proteger el envío fuera de la zona principal. Las regiones lejanas tardan "
                                "casi el doble: ahí conviene transportadora con mejor cobertura o promesa más larga.")], md=4),
                dbc.Col([html.Span("03", className="num"),
                         html.P("Planear los picos. En temporadas fuertes (Black Friday, preventas) el % de "
                                "pedidos tarde se dispara: ajustar la promesa antes, no después.")], md=4),
            ], className="g-3"),
        ]), className="card-caso"),
    ])
