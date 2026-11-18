# Caso de estudio 1 - Olist

**Equipo:** Santiago Alba, Domingo Leiva, Facundo Diaz y Marcos Devincenzi.

Estudiamos la calidad de nueve tablas de Olist y construimos una tabla con una fila
por pedido. Las preguntas son:

1. ¿Qué proporción de los pedidos entregados llegó después del día prometido y cómo cambia por mes de compra?
2. ¿La calificación media es diferente entre los pedidos entregados a tiempo y los entregados tarde?

## Entrega

- [Guía de estudio y defensa del Caso 1](docs/GUIA_CASO_1.md): recorrido de todas las etapas, fórmulas, código explicado, decisiones, controles, resultados y preguntas para practicar.
- [informe.pdf](informe.pdf): informe de cinco páginas con preguntas, hallazgos, decisiones, controles y conclusiones.
- [notebook.ipynb](notebook.ipynb): análisis, curación, controles y tres pruebas con errores intencionales.
- `data/curated/orders_curated.csv`: 99.441 pedidos, con `order_id` único.
- `data/source_manifest.json`: versión, procedencia, fecha de descarga y hashes de los nueve originales.
- `results/`: perfiles de calidad, resultados, comparación antes/después y trazabilidad por pedido.
- `figures/`: los dos gráficos del análisis.
- `download_data.py` y `requirements.txt`: descarga y dependencias para reproducir el trabajo.

## Cómo entender el trabajo, paso a paso

1. **Definimos el problema y el grano.** Estudiamos atraso y calificaciones con el pedido como unidad. Son datos históricos de 2016-2018; el análisis es descriptivo y no entrena un modelo.
2. **Verificamos las fuentes.** El script descarga Olist v2 y comprueba los nueve SHA-256 del manifiesto. El notebook vuelve a validarlos y lee identificadores y prefijos postales como texto para conservar ceros iniciales.
3. **Perfilamos las nueve tablas.** Revisamos dimensiones, tipos, faltantes, duplicados exactos, claves, multiplicidad y rangos de fechas. Un pedido repetido en ítems o pagos no es necesariamente un duplicado erróneo.
4. **Aplicamos reglas de calidad.** Las claves, referencias obligatorias, conversiones de fechas y rangos inválidos detienen la integración. Las anomalías que no podemos corregir con evidencia quedan señaladas.
5. **Agrupamos antes de unir.** Resumimos ítems, pagos y reseñas por `order_id`. Después hacemos uniones izquierdas validadas desde `orders`, evitando multiplicar filas e importes y conservando los 99.441 pedidos.
6. **Definimos el atraso.** Un pedido apto debe estar entregado y tener compra, entrega y promesa presentes y coherentes. Comparamos días calendario: el mismo día prometido cuenta a tiempo. En los no aptos dejamos el atraso desconocido.
7. **Validamos y probamos.** `validar_curado` comprueba el contrato de salida. Probamos copias con una clave duplicada, una nota de 9 y una fecha necesaria ausente. Los tres errores se detectan.
8. **Respondemos con poblaciones explícitas.** Calculamos tasas por mes de compra y notas por pedido. Exportamos curado, resultados, trazabilidad y gráficos, y explicamos las limitaciones en el informe.

La [guía completa](docs/GUIA_CASO_1.md) indica las celdas concretas, explica operaciones de Pandas y ofrece preguntas de defensa. No hay división entrenamiento/prueba porque no construimos un predictor: los filtros de aptitud y reseñas definen poblaciones descriptivas.

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

En Windows, activar el entorno con `.venv\Scripts\activate`; se puede usar `py -3.12` para crear el entorno si Python está instalado con ese lanzador.

Al terminar deben aparecer `OK: contrato de pedidos validado`, tres pruebas detectadas y un curado de 99.441 filas y 23 columnas. `results/resumen.json` debe informar 96.470 pedidos aptos y 6.534 tardíos. Ejecutar todo desde un kernel reiniciado evita depender de variables de una sesión anterior.

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

## Preparar la defensa

Cada integrante debe poder explicar el notebook entero, incluso el código que preparó otro compañero. Usar la [guía](docs/GUIA_CASO_1.md) para practicar entradas, operaciones, salidas, decisiones y límites de cada fragmento. Las pruebas con errores intencionales no son errores accidentales del trabajo: son comprobaciones deliberadas de los controles.

Un error propio verificable del avance original fue cargar códigos postales sin fijar el tipo: `09790` apareció como `9790`. La lectura actual usa texto y conserva el cero inicial. El [extracto de evidencia](docs/EVIDENCIA_PREFIJOS_POSTALES.md) conserva la carga y salida históricas, la fila fuente, la corrección y los hashes, sin requerir el notebook viejo completo. La guía explica el alcance de esa corrección.

## Uso de IA

Durante la realización del trabajo utilizamos ChatGPT como herramienta de apoyo, principalmente para ayudarnos con la estructura del código en Python, resolver dudas sobre algunas funciones de Pandas y mejorar la organización del análisis.

A partir de las ideas iniciales del grupo, fuimos consultando a la IA y adaptando las sugerencias a nuestro dataset y a los objetivos del proyecto. También la utilizamos para entender errores y pensar distintas formas de validar los datos.

Para comprobar los resultados, ejecutamos el código, revisamos las tablas y los gráficos obtenidos, y realizamos pruebas introduciendo errores intencionales para verificar que nuestros controles los detectaran.
