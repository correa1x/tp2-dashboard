"""Todos los callbacks del dashboard.

1. render_pagina        → navegación entre páginas (URL → layout)
2. opciones_estado      → filtro encadenado: la región limita los estados disponibles
3. clic_en_estado       → cross-filtering: clic en una burbuja selecciona ese estado
4. limpiar_filtros      → botón que devuelve todos los filtros a su valor inicial
5. texto_periodo        → muestra el rango de meses elegido en el slider
6. actualizar_inicio    → KPIs + 4 gráficos + textos de hallazgos de la página principal
7. actualizar_detalle   → 4 gráficos + textos de la página de detalle
"""

from dash import Input, Output, State, ctx, html, no_update

from layouts import detail, home
from utils import graficos as g
from utils.datos import cargar_datos, comparar_a_tiempo_vs_tarde, filtrar, kpis, meses_disponibles, nombre_mes

FILTROS = [
    Input("filtro-region", "value"),
    Input("filtro-estado", "value"),
    Input("filtro-meses", "value"),
    Input("filtro-pago", "value"),
    Input("filtro-categoria", "value"),
]


def _fmt(numero, decimales=1, sufijo=""):
    return "—" if numero is None else f"{numero:,.{decimales}f}{sufijo}".replace(",", "X").replace(".", ",").replace("X", ".")


def _datos_filtrados(region, estado, meses, pago, categoria):
    return filtrar(cargar_datos(), regiones=region, estados=estado, rango_meses=meses,
                   metodos=pago, categorias=categoria)


def calcular_inicio(region, estado, meses, pago, categoria):
    """Lógica pura del callback de inicio (se prueba en tests/ sin levantar el servidor)."""
    df = _datos_filtrados(region, estado, meses, pago, categoria)
    k = kpis(df)
    comp = comparar_a_tiempo_vs_tarde(df)

    # Textos de hallazgo que cambian con los filtros
    if df.empty:
        insight_dias = insight_tarde = insight_estados = "No hay pedidos con estos filtros."
    else:
        rapido = df.loc[df["dias_entrega"] <= 7, "nota"].mean()
        lento = df.loc[df["dias_entrega"] > 21, "nota"].mean()
        insight_dias = [html.B("Hallazgo: "),
                        f"entregados en una semana o menos: {_fmt(rapido, 2)} ★; "
                        f"en más de 3 semanas: {_fmt(lento, 2)} ★."]
        if comp["nota_tarde"] is not None and comp["nota_a_tiempo"] is not None:
            insight_tarde = [html.B("Hallazgo: "),
                             f"{_fmt(comp['neg_tarde'], 0)}% de los pedidos tarde reciben 1–2 ★, "
                             f"contra {_fmt(comp['neg_a_tiempo'], 0)}% de los que llegan a tiempo."]
        else:
            insight_tarde = "Esta selección no tiene pedidos de ambos tipos para comparar."
        por_estado = df.groupby("estado", observed=True).agg(dias=("dias_entrega", "mean"),
                                                             n=("nota", "size"))
        por_estado = por_estado[por_estado["n"] >= 30]
        if len(por_estado) >= 2:
            lento_e, rapido_e = por_estado["dias"].idxmax(), por_estado["dias"].idxmin()
            insight_estados = [html.B("Hallazgo: "),
                               f"{lento_e} es el estado más lento ({_fmt(por_estado.loc[lento_e, 'dias'])} días) y "
                               f"{rapido_e} el más rápido ({_fmt(por_estado.loc[rapido_e, 'dias'])} días)."]
        else:
            insight_estados = "Selecciona más estados para comparar."

    return (
        _fmt(k["pedidos"], 0),
        _fmt(k["nota"], 2, " ★"),
        _fmt(k["pct_tarde"], 1, "%"),
        _fmt(k["pct_negativas"], 1, "%"),
        g.nota_por_dias_entrega(df),
        g.distribucion_notas_tarde(df),
        g.mapa_estados(df, estados_sel=estado),
        g.tendencia_mensual(df),
        insight_dias, insight_tarde, insight_estados,
    )


def calcular_detalle(region, estado, meses, pago, categoria):
    df = _datos_filtrados(region, estado, meses, pago, categoria)
    if df.empty:
        vacio = "No hay pedidos con estos filtros."
        return (g.treemap_categorias(df), g.boxplot_ticket_pago(df), g.flete_por_valor(df),
                g.dona_recompra(df), vacio, vacio, vacio)

    cat = df.groupby("categoria", observed=True)["nota"].agg(["mean", "size"])
    cat = cat[cat["size"] >= 100]
    if len(cat) >= 2:
        insight_cat = [html.B("Hallazgo: "),
                       f"entre categorías con 100+ pedidos, la nota va de {_fmt(cat['mean'].min(), 2)} "
                       f"({cat['mean'].idxmin()}) a {_fmt(cat['mean'].max(), 2)} ({cat['mean'].idxmax()}): "
                       f"una diferencia de {_fmt(cat['mean'].max() - cat['mean'].min(), 2)} ★."]
    else:
        insight_cat = "Muy pocas categorías con 100+ pedidos en esta selección."

    pago_g = df.groupby("metodo_pago", observed=True).agg(nota=("nota", "mean"),
                                                         ticket=("valor_total", "median"))
    insight_pago = [html.B("Hallazgo: "), "nota por método: " + " · ".join(
        f"{m}: {_fmt(r['nota'], 2)} ★" for m, r in pago_g.iterrows())]

    chicos = df[df["valor_productos"] < 50]["flete_pct"].median()
    grandes = df[df["valor_productos"] >= 200]["flete_pct"].median()
    insight_flete = [html.B("Hallazgo: "),
                     f"en carritos de menos de R$50 el envío equivale al {_fmt(chicos, 0)}% del valor; "
                     f"desde R$200 baja al {_fmt(grandes, 0)}%."]

    return (g.treemap_categorias(df), g.boxplot_ticket_pago(df), g.flete_por_valor(df),
            g.dona_recompra(df), insight_cat, insight_pago, insight_flete)


def registrar_callbacks(app):

    @app.callback(Output("contenido-pagina", "children"), Input("url", "pathname"))
    def render_pagina(pathname):
        return detail.layout() if pathname == "/detalle" else home.layout()

    @app.callback(
        Output("filtro-estado", "options"),
        Output("filtro-estado", "value", allow_duplicate=True),
        Input("filtro-region", "value"),
        State("filtro-estado", "value"),
        prevent_initial_call="initial_duplicate",
    )
    def opciones_estado(regiones, estados_actuales):
        df = cargar_datos()
        if regiones:
            df = df[df["region"].isin(regiones)]
        disponibles = sorted(df["estado"].unique().tolist())
        # Si cambian las regiones, se quitan los estados que ya no aplican
        estados = [e for e in (estados_actuales or []) if e in disponibles]
        return disponibles, estados

    @app.callback(
        Output("filtro-estado", "value", allow_duplicate=True),
        Input("graf-estados", "clickData"),
        State("filtro-estado", "value"),
        prevent_initial_call=True,
    )
    def clic_en_estado(click, estados_actuales):
        if not click:
            return no_update
        estado = click["points"][0]["customdata"][0]
        actuales = list(estados_actuales or [])
        # Clic en un estado ya seleccionado lo quita (toggle)
        return [e for e in actuales if e != estado] if estado in actuales else actuales + [estado]

    @app.callback(
        Output("filtro-region", "value"),
        Output("filtro-estado", "value", allow_duplicate=True),
        Output("filtro-meses", "value"),
        Output("filtro-pago", "value"),
        Output("filtro-categoria", "value"),
        Input("btn-limpiar", "n_clicks"),
        prevent_initial_call=True,
    )
    def limpiar_filtros(_):
        df = cargar_datos()
        return [], [], [0, len(meses_disponibles()) - 1], sorted(df["metodo_pago"].cat.categories), []

    @app.callback(Output("texto-periodo", "children"), Input("filtro-meses", "value"))
    def texto_periodo(rango):
        meses = meses_disponibles()
        return f"{nombre_mes(meses[rango[0]], False)} – {nombre_mes(meses[rango[1]], False)}"

    @app.callback(
        Output("kpi-pedidos", "children"),
        Output("kpi-nota", "children"),
        Output("kpi-tarde", "children"),
        Output("kpi-negativas", "children"),
        Output("graf-dias", "figure"),
        Output("graf-tarde", "figure"),
        Output("graf-estados", "figure"),
        Output("graf-tendencia", "figure"),
        Output("insight-dias", "children"),
        Output("insight-tarde", "children"),
        Output("insight-estados", "children"),
        *FILTROS,
        Input("url", "pathname"),
    )
    def actualizar_inicio(region, estado, meses, pago, categoria, pathname):
        if pathname == "/detalle":
            return [no_update] * 11
        return calcular_inicio(region, estado, meses, pago, categoria)

    @app.callback(
        Output("graf-treemap", "figure"),
        Output("graf-pago", "figure"),
        Output("graf-flete", "figure"),
        Output("graf-recompra", "figure"),
        Output("insight-categorias", "children"),
        Output("insight-pago", "children"),
        Output("insight-flete", "children"),
        *FILTROS,
        Input("url", "pathname"),
    )
    def actualizar_detalle(region, estado, meses, pago, categoria, pathname):
        if pathname != "/detalle":
            return [no_update] * 7
        return calcular_detalle(region, estado, meses, pago, categoria)
