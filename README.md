# Caso de estudio 1 - Olist

Estudiamos la calidad de nueve tablas de Olist y construimos una tabla con una fila
por pedido. Las preguntas son:

1. ¿Qué proporción de los pedidos entregados llegó después del día prometido y cómo cambia por mes de compra?
2. ¿La calificación media es diferente entre los pedidos entregados a tiempo y los entregados tarde?

## Entrega

- [informe.pdf](informe.pdf): informe de cinco páginas con preguntas, hallazgos, decisiones, controles y conclusiones.
- [notebook.ipynb](notebook.ipynb): análisis, curación, controles y tres pruebas con errores intencionales.
- `data/curated/orders_curated.csv`: 99.441 pedidos, con `order_id` único.
- `data/source_manifest.json`: versión, procedencia, fecha de descarga y hashes de los nueve originales.
- `results/`: perfiles de calidad, resultados, comparación antes/después y trazabilidad por pedido.
- `figures/`: los dos gráficos del análisis.
- `download_data.py` y `requirements.txt`: descarga y dependencias para reproducir el trabajo.

## Cómo ejecutar

Se necesita Python 3.12. Desde la carpeta del proyecto, en macOS o Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python download_data.py
jupyter notebook notebook.ipynb
```

En Jupyter, seleccionar **Restart Kernel and Run All Cells**. El notebook genera
`data/curated/`, `results/` y `figures/`. Se necesita Internet para instalar dependencias
y descargar los datos la primera vez.

Los CSV originales se descargan en `data/raw/` y no se suben al repositorio. La fuente es
[Brazilian E-Commerce Public Dataset by Olist, versión 2](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
El script verifica los hashes del manifiesto y no sobrescribe originales existentes.
El notebook vuelve a comprobarlos antes de cargar las tablas.

## Decisiones y resultados

Se agrupan ítems, pagos y reseñas antes de unirlos a pedidos, para evitar multiplicar
filas e importes. Si un pedido no tiene registros hijos, la cantidad es cero y el
importe o nota queda sin dato. Los pagos registrados con valor cero se conservan.

El atraso se calcula en días calendario, solo para pedidos entregados con compra,
entrega y promesa presentes y coherentes. Los demás pedidos se conservan con atraso
desconocido. De 96.470 pedidos aptos, 6.534 llegan tarde (6,77%). Entre los aptos con
reseña, la nota media es 4,29/5 a tiempo y 2,27/5 tarde. Es una asociación descriptiva.

Los controles revisan hashes, claves, referencias, fechas, importes, notas, uniones e
identidad de los pedidos. Las pruebas alteran copias con una clave duplicada, una
nota de 9 y una fecha necesaria ausente. Los tres errores deben detectarse.

Las anomalías temporales, reseñas reutilizadas y diferencias entre cobros y precio
más flete quedan señaladas para revisión. No se corrigen sin evidencia. El análisis
permite describir estas entregas históricas; comparar vendedores o categorías exige
revisión adicional. No permite atribuir causalidad ni generalizar al comercio actual.

## Uso de IA

Durante la realización del trabajo utilizamos ChatGPT como herramienta de apoyo, principalmente para ayudarnos con la estructura del código en Python, resolver dudas sobre algunas funciones de Pandas y mejorar la organización del análisis.

A partir de las ideas iniciales del grupo, fuimos consultando a la IA y adaptando las sugerencias a nuestro dataset y a los objetivos del proyecto. También la utilizamos para entender errores y pensar distintas formas de validar los datos.

Para comprobar los resultados, ejecutamos el código, revisamos las tablas y los gráficos obtenidos, y realizamos pruebas introduciendo errores intencionales para verificar que nuestros controles los detectaran.
