"""Página de detalle: descarta (o confirma) las otras explicaciones — producto, pago, precio del envío."""

import dash_bootstrap_components as dbc
from dash import html

from layouts.componentes import tarjeta_grafico


def layout() -> html.Div:
    return html.Div([
        html.Section([
            html.Div("Las otras sospechosas", className="eyebrow"),
            html.H1(["¿Y si no es la entrega? Revisamos ", html.Em("producto, pago y precio"), "."],
                    className="titulo-hero"),
            html.P("Si la categoría o el método de pago explicaran las malas reseñas, aquí lo veríamos. "
                   "Spoiler: las diferencias son pequeñas comparadas con llegar tarde.",
                   className="lead-hero"),
        ], className="hero"),

        dbc.Row([
            dbc.Col(tarjeta_grafico(
                "Las categorías venden distinto, pero califican parecido",
                "Top 20 categorías por ventas (tamaño) coloreadas por nota promedio.",
                "graf-treemap", "insight-categorias"), lg=12),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(tarjeta_grafico(
                "El método de pago cambia el ticket, no la nota",
                "Distribución del valor del pedido por método de pago (sin el 5 % más caro).",
                "graf-pago", "insight-pago"), lg=6),
            dbc.Col(tarjeta_grafico(
                "En carritos pequeños, el envío pesa casi la mitad",
                "Envío como % del valor de los productos, según el tamaño del carrito. "
                "Sirve para decidir desde qué monto dar envío gratis.",
                "graf-flete", "insight-flete"), lg=6),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(tarjeta_grafico(
                "Casi nadie vuelve a comprar",
                "Clientes únicos que hicieron un solo pedido vs. más de uno.",
                "graf-recompra"), lg=5),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div("Conclusión", className="eyebrow"),
                html.H3("La reseña se gana (o se pierde) después de vender", className="card-titulo"),
                html.Ul([
                    html.Li([html.B("La entrega es la variable que más mueve la nota: "),
                             "un pedido tarde tiene ~2 estrellas menos que uno a tiempo."]),
                    html.Li([html.B("Categoría y método de pago casi no cambian la satisfacción: "),
                             "las diferencias son de décimas."]),
                    html.Li([html.B("El envío pesa mucho en carritos pequeños: "),
                             "subir el ticket (kits, combos) diluye el costo del envío."]),
                    html.Li([html.B("La recompra es bajísima: "),
                             "retener al cliente (suscripción, email) es una ventaja competitiva."]),
                ], className="lista-conclusiones"),
                html.Div("Limitaciones", className="eyebrow mt-3"),
                html.P("Datos de Brasil 2017–2018 en reales (R$); un solo marketplace; la reseña se pide "
                       "justo después de la entrega, así que mide sobre todo la experiencia de compra y envío, "
                       "no el uso del producto a largo plazo. Es correlación, no causalidad.",
                       className="small text-muted mb-0"),
            ]), className="card-grafico"), lg=7),
        ], className="g-3 mb-3"),
    ])
