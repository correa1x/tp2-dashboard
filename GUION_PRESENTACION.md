# Guion de presentación (10 min)

Tengan la app abierta en la URL de Render **5 minutos antes** (el plan gratis "se duerme" y tarda ~1 min en despertar).

## 1. Contexto (1 min)
- "Analizamos ~95.000 pedidos reales de Olist, el marketplace más grande de Brasil. Es un mercado latinoamericano con problemas logísticos parecidos a los de Colombia."
- Por qué es interesante: cualquier marca que venda online vive de sus reseñas, y queríamos saber qué las daña de verdad.

## 2. Pregunta (30 s)
- "¿Qué hace que un cliente deje una mala reseña: el producto, el precio, el pago o la entrega?"

## 3. Demo en vivo (5 min)
1. **KPIs:** nota promedio de 4,16, solo el 6,6 % llega tarde, pero el 12,7 % de las reseñas es negativa.
2. **Barras por días de entrega:** hasta 3 semanas la nota se mantiene sobre 4,1; después se desploma (2,2 con más de 30 días). Señalar la línea de reseñas negativas, que se dispara.
3. **A tiempo vs. tarde:** el 63 % de los pedidos tarde recibe 1–2 ★, contra el 9 % de los que llegan a tiempo. *Este es el hallazgo principal.*
4. **Burbujas por estado:** hacer **clic en SP** (rápido, buena nota) y luego en **MA o AL** (lentos): los KPIs y todos los gráficos cambian. Explicar que es cross-filtering con un callback.
5. **Filtro de región → estado:** elegir "Nordeste" y mostrar que el dropdown de estados solo deja los de esa región (callback encadenado).
6. **Tendencia mensual:** Black Friday (nov 2017) y feb–mar 2018: cuando sube la demanda, el % tarde pasa del ~3 % al 12–19 %.
7. **Página de detalle:** el treemap y el boxplot muestran que categoría y método de pago casi no cambian la nota. El gráfico del envío muestra que en carritos pequeños el envío vale casi la mitad del pedido.
8. Botón **Limpiar filtros**.

## 4. Hallazgos (1,5 min)
- La reseña se gana o se pierde **después** de vender: logística > producto > pago.
- Lo que castiga es **incumplir la promesa**, no solo la demora → prometer con margen.
- Caso aplicado (Puuro): prometer 15 días y entregar en 10, proteger los envíos a regiones lejanas, ajustar la promesa antes de los picos (preventas, Black Friday), usar kits para diluir el costo del envío.

## 5. Lecciones aprendidas (1 min)
- Lo difícil: unir 7 tablas a nivel de pedido sin duplicar filas (pedidos con varios ítems, pagos y reseñas).
- Lo que mejoraríamos: análisis de texto de los comentarios y un mapa coroplético.

## Preguntas probables del jurado
- **¿Por qué ese gráfico?** Barras para comparar rangos ordenados; barras 100 % apiladas para comparar distribuciones entre dos grupos; burbujas porque cruzan 3 variables (días, nota, volumen); treemap para mostrar peso relativo y nota a la vez.
- **¿Limitaciones?** Brasil 2017–2018, un solo marketplace, la reseña se pide justo al recibir el pedido, es correlación y no causalidad.
- **¿Con 1 millón de filas?** Pre-agregar los datos (tablas resumen por mes/estado/categoría) en vez de filtrar filas crudas; guardar en Parquet o en una base de datos (DuckDB/PostgreSQL); cachear resultados de callbacks (`flask-caching`); más workers en gunicorn.
- **¿Qué mejorarían?** NLP de los comentarios, mapa coroplético, comparar con datos de un ecommerce colombiano.
