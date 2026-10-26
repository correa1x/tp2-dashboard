"""Funciones que construyen cada figura de Plotly a partir de un DataFrame filtrado.

Separarlas de los callbacks permite probarlas sin levantar la app (ver tests/).
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.colors import sample_colorscale

from utils.datos import ETIQUETAS_DIAS, nombre_mes

# Paleta de la marca
AZUL = "#2540D9"
TINTA = "#14161A"
CREMA = "#F4F1E8"
CORAL = "#E8553A"
GRIS = "#8A8C93"
COLORES_REGION = {
    "Sudeste": AZUL, "Sur": "#2BA37A", "Centro-Oeste": "#F2B53A",
    "Nordeste": CORAL, "Norte": "#8E6FE0",
}
# Escala de nota: 1 (coral) → 5 (azul)
ESCALA_NOTA = [[0, CORAL], [0.5, "#E9E3D3"], [1, AZUL]]
COLORES_NOTA = {1: CORAL, 2: "#F09A84", 3: "#D9D3C3", 4: "#8C9BEA", 5: AZUL}

FUENTE = "Outfit, system-ui, sans-serif"


def _estilo(fig: go.Figure, alto: int = 360) -> go.Figure:
    """Estilo común a todos los gráficos."""
    fig.update_layout(
        height=alto,
        margin=dict(l=10, r=10, t=36, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FUENTE, color=TINTA, size=13),
        hoverlabel=dict(font_family=FUENTE, bgcolor="white"),
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, title_text=""),
    )
    fig.update_xaxes(gridcolor="rgba(20,22,26,0.07)", zeroline=False, linecolor="rgba(20,22,26,0.2)")
    fig.update_yaxes(gridcolor="rgba(20,22,26,0.07)", zeroline=False)
    return fig


def figura_vacia(mensaje: str = "Sin datos para esta selección") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=mensaje, showarrow=False, font=dict(size=15, color=GRIS))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _estilo(fig)


# --------------------------------------------------------------------- inicio

def nota_por_dias_entrega(df: pd.DataFrame) -> go.Figure:
    """Barras: nota promedio por rango de días de entrega + línea de % reseñas negativas."""
    if df.empty:
        return figura_vacia()
    g = (df.groupby("rango_dias", observed=False)
           .agg(nota=("nota", "mean"), negativas=("resena_negativa", "mean"), pedidos=("nota", "size"))
           .reindex(ETIQUETAS_DIAS).reset_index())
    g["negativas"] *= 100
    fig = go.Figure()
    fig.add_bar(
        x=g["rango_dias"], y=g["nota"], name="Nota promedio (1–5)",
        marker_color=[AZUL if (n or 0) >= 4 else CORAL for n in g["nota"].fillna(0)],
        text=g["nota"].round(2), textposition="outside", cliponaxis=False,
        customdata=g["pedidos"],
        hovertemplate="<b>%{x} días</b><br>Nota: %{y:.2f}<br>Pedidos: %{customdata:,}<extra></extra>",
    )
    fig.add_scatter(
        x=g["rango_dias"], y=g["negativas"], name="% reseñas de 1–2 ★", yaxis="y2",
        mode="lines+markers", line=dict(color=TINTA, width=2, dash="dot"), marker=dict(size=8),
        hovertemplate="%{y:.1f}% reseñas negativas<extra></extra>",
    )
    fig.update_layout(
        xaxis_title="Días desde la compra hasta la entrega",
        yaxis=dict(title="Nota promedio", range=[0, 5.4]),
        yaxis2=dict(title="% reseñas negativas", overlaying="y", side="right",
                    range=[0, 100], showgrid=False, ticksuffix="%"),
    )
    return _estilo(fig)


def distribucion_notas_tarde(df: pd.DataFrame) -> go.Figure:
    """Barras 100 % apiladas: cómo se reparten las estrellas a tiempo vs tarde."""
    if df.empty:
        return figura_vacia()
    d = df.assign(estrellas=df["nota"].round().astype(int),
                  entrega=df["llego_tarde"].map({False: "A tiempo", True: "Tarde"}))
    tabla = pd.crosstab(d["entrega"], d["estrellas"], normalize="index") * 100
    tabla = tabla.reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
    fig = go.Figure()
    for estrellas in tabla.columns:
        fig.add_bar(
            y=tabla.index, x=tabla[estrellas], name=f"{estrellas} ★", orientation="h",
            marker_color=COLORES_NOTA[estrellas],
            text=[f"{v:.0f}%" if v >= 6 else "" for v in tabla[estrellas]], textposition="inside",
            insidetextfont=dict(color="white" if estrellas in (1, 5) else TINTA),
            hovertemplate=f"{estrellas} ★: %{{x:.1f}}%<extra>%{{y}}</extra>",
        )
    fig.update_layout(barmode="stack", xaxis=dict(ticksuffix="%", range=[0, 100]),
                      legend=dict(traceorder="normal"))
    return _estilo(fig, alto=260)


def mapa_estados(df: pd.DataFrame, estados_sel=None) -> go.Figure:
    """Burbujas por estado: días promedio de entrega vs nota. Tamaño = pedidos. Clic = filtra."""
    if df.empty:
        return figura_vacia()
    g = (df.groupby(["estado", "region"], observed=True)
           .agg(dias=("dias_entrega", "mean"), nota=("nota", "mean"),
                pedidos=("nota", "size"), tarde=("llego_tarde", "mean"))
           .reset_index())
    g = g[g["pedidos"] >= 30]  # estados con muy pocos pedidos dan promedios ruidosos
    if g.empty:
        return figura_vacia("Muy pocos pedidos por estado (mín. 30)")
    g["tarde"] *= 100
    fig = px.scatter(
        g, x="dias", y="nota", size="pedidos", color="region", text="estado",
        color_discrete_map=COLORES_REGION, size_max=55,
        custom_data=["estado", "pedidos", "tarde"],
        labels={"dias": "Días promedio de entrega", "nota": "Nota promedio", "region": "Región"},
    )
    fig.update_traces(
        textposition="middle center", textfont=dict(size=10, color="white"),
        marker=dict(line=dict(width=1, color="white"), opacity=0.85),
        hovertemplate="<b>%{customdata[0]}</b><br>Entrega: %{x:.1f} días<br>Nota: %{y:.2f}"
                      "<br>Pedidos: %{customdata[1]:,}<br>Llegaron tarde: %{customdata[2]:.1f}%<extra></extra>",
    )
    if estados_sel:
        fig.update_traces(selectedpoints=None)
        for tr in fig.data:
            tr.marker.opacity = [0.95 if e in estados_sel else 0.2 for e in tr.customdata[:, 0]]
    return _estilo(fig, alto=400)


def tendencia_mensual(df: pd.DataFrame) -> go.Figure:
    """Líneas: pedidos por mes y % que llegó tarde (doble eje)."""
    if df.empty:
        return figura_vacia()
    g = df.groupby("mes").agg(pedidos=("nota", "size"), tarde=("llego_tarde", "mean"),
                              nota=("nota", "mean")).reset_index()
    g["tarde"] *= 100
    g["etiqueta"] = g["mes"].map(nombre_mes)
    fig = go.Figure()
    fig.add_bar(x=g["mes"], y=g["pedidos"], name="Pedidos", marker_color="rgba(37,64,217,0.25)",
                customdata=g["etiqueta"], hovertemplate="%{customdata}: %{y:,} pedidos<extra></extra>")
    fig.add_scatter(x=g["mes"], y=g["tarde"], name="% llegó tarde", yaxis="y2", mode="lines+markers",
                    line=dict(color=CORAL, width=3),
                    customdata=g["etiqueta"], hovertemplate="%{customdata}: %{y:.1f}% tarde<extra></extra>")
    fig.update_layout(
        yaxis=dict(title="Pedidos"),
        yaxis2=dict(title="% tarde", overlaying="y", side="right", showgrid=False, ticksuffix="%",
                    rangemode="tozero"),
        xaxis=dict(tickvals=g["mes"][::3], ticktext=g["etiqueta"][::3]),
    )
    return _estilo(fig, alto=320)


# -------------------------------------------------------------------- detalle

def treemap_categorias(df: pd.DataFrame, top: int = 20) -> go.Figure:
    """Treemap: ventas por categoría (tamaño) coloreado por nota promedio."""
    if df.empty:
        return figura_vacia()
    g = (df.groupby("categoria", observed=True)
           .agg(ventas=("valor_total", "sum"), nota=("nota", "mean"), pedidos=("nota", "size"))
           .reset_index().sort_values("ventas", ascending=False).head(top))
    # Colores calculados a mano para que el nodo raíz quede blanco (px.treemap lo pinta con la escala)
    colores = sample_colorscale(ESCALA_NOTA, ((g["nota"] - 3.6) / 0.9).clip(0, 1).tolist())
    fig = go.Figure(go.Treemap(
        ids=["raiz"] + g["categoria"].tolist(), labels=[""] + g["categoria"].tolist(),
        parents=[""] + ["raiz"] * len(g), values=[g["ventas"].sum()] + g["ventas"].tolist(),
        branchvalues="total",
        customdata=[[0, 0]] + g[["pedidos", "nota"]].values.tolist(),
        marker=dict(colors=["white"] + colores, line=dict(color="white", width=2)),
        texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}<br>%{customdata[1]:.2f} ★",
        hovertemplate="<b>%{label}</b><br>Ventas: R$ %{value:,.0f}<br>Pedidos: %{customdata[0]:,}"
                      "<br>Nota: %{customdata[1]:.2f}<extra></extra>",
        pathbar=dict(visible=False), tiling=dict(pad=0),
    ))
    # Barra de color de referencia (traza invisible que solo dibuja la escala)
    fig.add_scatter(x=[None], y=[None], mode="markers", showlegend=False, hoverinfo="skip",
                    marker=dict(colorscale=ESCALA_NOTA, cmin=3.6, cmax=4.5, color=[4],
                                colorbar=dict(title="Nota", thickness=12)))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _estilo(fig, alto=430)


def boxplot_ticket_pago(df: pd.DataFrame) -> go.Figure:
    """Boxplot: valor del pedido según método de pago (sin outliers extremos en el eje)."""
    if df.empty:
        return figura_vacia()
    orden = df["metodo_pago"].value_counts().index.tolist()
    fig = px.box(df, x="metodo_pago", y="valor_total", color="metodo_pago", points=False,
                 category_orders={"metodo_pago": orden},
                 color_discrete_sequence=[AZUL, CORAL, "#2BA37A", "#F2B53A"],
                 labels={"metodo_pago": "", "valor_total": "Valor del pedido (R$)"})
    p95 = df["valor_total"].quantile(0.95)
    fig.update_yaxes(range=[0, p95 * 1.1])
    fig.update_layout(showlegend=False)
    return _estilo(fig, alto=340)


def flete_por_valor(df: pd.DataFrame) -> go.Figure:
    """Barras: cuánto pesa el envío sobre el carrito según su valor (referencia para envío gratis)."""
    if df.empty:
        return figura_vacia()
    cortes = [0, 50, 100, 150, 200, 300, 500, float("inf")]
    etiquetas = ["<50", "50–100", "100–150", "150–200", "200–300", "300–500", "500+"]
    d = df.assign(rango=pd.cut(df["valor_productos"], cortes, labels=etiquetas, right=False))
    g = (d.groupby("rango", observed=False)
          .agg(flete_pct=("flete_pct", "median"), pedidos=("nota", "size"))
          .reindex(etiquetas).reset_index())
    g["pct_pedidos"] = g["pedidos"] / g["pedidos"].sum() * 100
    fig = go.Figure()
    fig.add_bar(x=g["rango"], y=g["flete_pct"], name="Envío como % del carrito (mediana)",
                marker_color=[CORAL if (v or 0) > 20 else AZUL for v in g["flete_pct"].fillna(0)],
                text=g["flete_pct"].round(0).astype("Int64").astype(str) + "%", textposition="outside",
                cliponaxis=False, customdata=g["pedidos"],
                hovertemplate="Carrito R$ %{x}<br>Envío = %{y:.1f}% del carrito<br>"
                              "Pedidos: %{customdata:,}<extra></extra>")
    fig.add_scatter(x=g["rango"], y=g["pct_pedidos"], name="% de los pedidos", yaxis="y2",
                    mode="lines+markers", line=dict(color=TINTA, dash="dot"),
                    hovertemplate="%{y:.1f}% de los pedidos<extra></extra>")
    fig.update_layout(
        xaxis_title="Valor del carrito (R$, sin envío)",
        yaxis=dict(title="Envío / carrito", ticksuffix="%"),
        yaxis2=dict(title="% de pedidos", overlaying="y", side="right", showgrid=False,
                    ticksuffix="%", rangemode="tozero"),
    )
    return _estilo(fig, alto=340)


def dona_recompra(df: pd.DataFrame) -> go.Figure:
    """Dona: qué parte de los clientes volvió a comprar."""
    if df.empty:
        return figura_vacia()
    clientes = df.groupby("cliente_id")["pedido_id"].count()
    recurrentes = int((clientes > 1).sum())
    unicos = int((clientes == 1).sum())
    fig = go.Figure(go.Pie(
        labels=["Compró una sola vez", "Volvió a comprar"], values=[unicos, recurrentes], hole=0.62,
        marker=dict(colors=["#E2DDCF", AZUL], line=dict(color="white", width=2)),
        sort=False, textinfo="none", hovertemplate="%{label}: %{value:,} clientes<extra></extra>",
    ))
    pct = recurrentes / max(recurrentes + unicos, 1) * 100
    fig.add_annotation(text=f"<b>{pct:.1f}%</b><br>recompra", showarrow=False, font=dict(size=20))
    return _estilo(fig, alto=340)
