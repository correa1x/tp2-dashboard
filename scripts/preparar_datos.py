"""
Limpieza y preparación de datos — TP2 Dashboard
================================================

Toma las 7 tablas crudas del dataset público de Olist (ecommerce brasileño,
~100k pedidos 2016-2018) y las convierte en UNA sola tabla a nivel de pedido,
lista para el dashboard: data/pedidos_limpios.csv.gz

Uso:
    python scripts/preparar_datos.py

Si las tablas crudas no están en data/raw/, el script las descarga del
repositorio oficial de Olist en GitHub. Todo el proceso es reproducible.

Cada paso de limpieza queda registrado en la consola (y en el README) con
cuántas filas se quitan y por qué.
"""

from pathlib import Path
import urllib.request

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_RAW = RAIZ / "data" / "raw"
SALIDA = RAIZ / "data" / "pedidos_limpios.csv.gz"

URL_BASE = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
TABLAS = {
    "pedidos": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "resenas": "olist_order_reviews_dataset.csv",
    "pagos": "olist_order_payments_dataset.csv",
    "clientes": "olist_customers_dataset.csv",
    "productos": "olist_products_dataset.csv",
    "traduccion": "product_category_name_translation.csv",
}

# Regiones oficiales de Brasil (IBGE) para agrupar los 27 estados
REGIONES = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sur": ["PR", "RS", "SC"],
}
ESTADO_A_REGION = {e: r for r, estados in REGIONES.items() for e in estados}

METODOS_PAGO = {
    "credit_card": "Tarjeta de crédito",
    "boleto": "Boleto (efectivo)",
    "voucher": "Bono / voucher",
    "debit_card": "Tarjeta débito",
}

# Traducción al español de las categorías más frecuentes (el resto queda en inglés legible)
CATEGORIAS_ES = {
    "health_beauty": "Salud y belleza",
    "bed_bath_table": "Cama, mesa y baño",
    "sports_leisure": "Deportes y ocio",
    "furniture_decor": "Muebles y decoración",
    "computers_accessories": "Accesorios de computador",
    "housewares": "Hogar",
    "watches_gifts": "Relojes y regalos",
    "telephony": "Telefonía",
    "garden_tools": "Jardín",
    "auto": "Automotriz",
    "toys": "Juguetes",
    "cool_stuff": "Artículos curiosos",
    "perfumery": "Perfumería",
    "baby": "Bebés",
    "electronics": "Electrónica",
    "stationery": "Papelería",
    "fashion_bags_accessories": "Bolsos y accesorios",
    "pet_shop": "Mascotas",
    "office_furniture": "Muebles de oficina",
    "consoles_games": "Consolas y juegos",
    "luggage_accessories": "Maletas",
    "construction_tools_construction": "Construcción",
    "home_appliances": "Electrodomésticos",
    "musical_instruments": "Instrumentos musicales",
    "small_appliances": "Pequeños electrodomésticos",
    "food": "Alimentos",
    "food_drink": "Alimentos y bebidas",
    "drinks": "Bebidas",
    "books_general_interest": "Libros",
    "fashion_shoes": "Calzado",
    "fashion_male_clothing": "Ropa hombre",
    "fashio_female_clothing": "Ropa mujer",
    "fashion_sport": "Ropa deportiva",
    "diapers_and_hygiene": "Pañales e higiene",
    "computers": "Computadores",
}


def log(paso: str, antes: int, despues: int, motivo: str) -> None:
    """Imprime cuántas filas elimina cada paso de limpieza."""
    print(f"  - {paso}: {antes:,} → {despues:,} filas ({antes - despues:,} quitadas). {motivo}")


def descargar_si_falta() -> None:
    CARPETA_RAW.mkdir(parents=True, exist_ok=True)
    for archivo in TABLAS.values():
        destino = CARPETA_RAW / archivo
        if not destino.exists():
            print(f"Descargando {archivo} ...")
            urllib.request.urlretrieve(URL_BASE + archivo, destino)


def cargar() -> dict[str, pd.DataFrame]:
    return {nombre: pd.read_csv(CARPETA_RAW / archivo) for nombre, archivo in TABLAS.items()}


def preparar() -> pd.DataFrame:
    descargar_si_falta()
    t = cargar()
    print("Tablas crudas:", {k: len(v) for k, v in t.items()})
    print("\nLimpieza:")

    # ---------------------------------------------------------------- pedidos
    ped = t["pedidos"].copy()
    columnas_fecha = [
        "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ]
    for c in columnas_fecha:
        ped[c] = pd.to_datetime(ped[c], errors="coerce")

    n = len(ped)
    ped = ped[ped["order_status"] == "delivered"]
    log("Solo pedidos entregados", n, len(ped),
        "La pregunta es sobre la experiencia de entrega; cancelados/en tránsito no tienen fecha de llegada.")

    n = len(ped)
    ped = ped.dropna(subset=["order_delivered_customer_date", "order_estimated_delivery_date"])
    log("Sin fecha de entrega real", n, len(ped), "Marcados como entregados pero sin fecha: inconsistencia del sistema.")

    n = len(ped)
    ped = ped[ped["order_delivered_customer_date"] >= ped["order_purchase_timestamp"]]
    log("Entrega antes de la compra", n, len(ped), "Fechas imposibles.")

    # Variables de logística (en días)
    ped["dias_entrega"] = (ped["order_delivered_customer_date"] - ped["order_purchase_timestamp"]).dt.total_seconds() / 86400
    ped["dias_promesa"] = (ped["order_estimated_delivery_date"] - ped["order_purchase_timestamp"]).dt.total_seconds() / 86400
    ped["dias_vs_promesa"] = (ped["order_delivered_customer_date"].dt.normalize() - ped["order_estimated_delivery_date"]).dt.days
    ped["llego_tarde"] = ped["dias_vs_promesa"] > 0

    n = len(ped)
    ped = ped[ped["dias_entrega"] <= 90]
    log("Entregas de más de 90 días", n, len(ped), "Outliers extremos (0,1 %): casos de pérdida o reclamo, distorsionan promedios.")

    # ------------------------------------------------------------------ items
    items = t["items"].merge(t["productos"][["product_id", "product_category_name"]], on="product_id", how="left")
    items = items.merge(t["traduccion"], on="product_category_name", how="left")
    items["categoria"] = items["product_category_name_english"].map(CATEGORIAS_ES).fillna(
        items["product_category_name_english"].str.replace("_", " ").str.capitalize()
    ).fillna("Sin categoría")

    # Categoría principal del pedido = la del ítem más caro
    principal = items.sort_values("price", ascending=False).drop_duplicates("order_id")[["order_id", "categoria"]]
    agg_items = items.groupby("order_id").agg(
        n_items=("order_item_id", "count"),
        valor_productos=("price", "sum"),
        flete=("freight_value", "sum"),
        n_vendedores=("seller_id", "nunique"),
    ).reset_index().merge(principal, on="order_id")

    # ------------------------------------------------------------------ pagos
    pagos = t["pagos"]
    n = len(pagos)
    pagos = pagos[pagos["payment_type"] != "not_defined"]
    log("Pagos con método 'not_defined'", n, len(pagos), "Sin método de pago no se pueden analizar.")
    # Método principal = el que pagó la mayor parte del pedido
    metodo = pagos.sort_values("payment_value", ascending=False).drop_duplicates("order_id")
    metodo = metodo[["order_id", "payment_type", "payment_installments"]].rename(
        columns={"payment_type": "metodo_pago", "payment_installments": "cuotas"})
    metodo["metodo_pago"] = metodo["metodo_pago"].map(METODOS_PAGO)

    # ---------------------------------------------------------------- reseñas
    res = t["resenas"].copy()
    res["tiene_comentario"] = res["review_comment_message"].notna()
    # Algunos pedidos tienen más de una reseña: se promedia la nota
    agg_res = res.groupby("order_id").agg(
        nota=("review_score", "mean"), tiene_comentario=("tiene_comentario", "max")).reset_index()

    # --------------------------------------------------------------- clientes
    cli = t["clientes"][["customer_id", "customer_unique_id", "customer_state", "customer_city"]]

    # ------------------------------------------------------------------ unión
    df = (ped.merge(cli, on="customer_id", how="left")
             .merge(agg_items, on="order_id", how="inner")
             .merge(metodo, on="order_id", how="inner")
             .merge(agg_res, on="order_id", how="inner"))
    print(f"  - Tras unir pedidos + ítems + pagos + reseñas (inner join): {len(df):,} pedidos "
          "(se descartan pedidos sin ítems, sin pago válido o sin reseña).")

    # Variables derivadas
    df["valor_total"] = df["valor_productos"] + df["flete"]
    df["flete_pct"] = np.where(df["valor_productos"] > 0, df["flete"] / df["valor_productos"] * 100, np.nan)
    df["region"] = df["customer_state"].map(ESTADO_A_REGION)
    df["mes"] = df["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    df["resena_negativa"] = df["nota"] <= 2

    # Recompra: el mismo cliente real (customer_unique_id) con más de un pedido
    pedidos_por_cliente = df.groupby("customer_unique_id")["order_id"].transform("count")
    df["cliente_recurrente"] = pedidos_por_cliente > 1

    # Meses con muy pocos pedidos (inicio y fin del dataset) sesgan las series de tiempo
    conteo_mes = df["mes"].value_counts()
    meses_validos = conteo_mes[conteo_mes >= 500].index
    n = len(df)
    df = df[df["mes"].isin(meses_validos)]
    log("Meses con < 500 pedidos (bordes del dataset)", n, len(df), "Meses incompletos al inicio/fin de la serie.")

    columnas = [
        "order_id", "customer_unique_id", "customer_state", "region", "customer_city",
        "order_purchase_timestamp", "mes", "categoria", "n_items", "n_vendedores",
        "valor_productos", "flete", "valor_total", "flete_pct", "metodo_pago", "cuotas",
        "dias_entrega", "dias_promesa", "dias_vs_promesa", "llego_tarde",
        "nota", "resena_negativa", "tiene_comentario", "cliente_recurrente",
    ]
    df = df[columnas].rename(columns={
        "customer_unique_id": "cliente_id", "customer_state": "estado", "customer_city": "ciudad",
        "order_purchase_timestamp": "fecha_compra", "order_id": "pedido_id",
    })
    for c in ["dias_entrega", "dias_promesa", "valor_productos", "flete", "valor_total", "flete_pct"]:
        df[c] = df[c].round(2)
    return df


if __name__ == "__main__":
    final = preparar()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(SALIDA, index=False, compression="gzip")
    print(f"\nListo: {len(final):,} pedidos x {final.shape[1]} columnas → {SALIDA.relative_to(RAIZ)}")
    print(f"Nulos por columna:\n{final.isna().sum()[final.isna().sum() > 0]}")
