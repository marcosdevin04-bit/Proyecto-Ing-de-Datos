# Guía para entender y defender el Caso 1

**Equipo:** Santiago Alba, Domingo Leiva, Facundo Diaz y Marcos Devincenzi.

Esta guía explica el trabajo que efectivamente está en `notebook.ipynb`, su informe y sus resultados. Sirve para estudiar entre compañeros y preparar la defensa individual sin IA. No reemplaza leer y ejecutar el notebook. La numeración de celdas cuenta todas las celdas desde la primera, incluidas las de texto.

## 1. El caso en un minuto

Usamos nueve tablas históricas de Olist, un comercio electrónico de Brasil, para responder dos preguntas:

1. ¿Cuántos pedidos entregados llegaron después del día prometido y cómo cambia el porcentaje por mes de compra?
2. ¿Qué diferencia de calificación aparece entre los pedidos a tiempo y los tardíos?

El resultado principal es una tabla de **99.441 pedidos y 23 columnas**, con una fila por `order_id`. Conservamos todos los pedidos, incluso los que no sirven para medir atraso. Para esa métrica usamos 96.470 pedidos aptos: 6.534 llegaron tarde, **6,77%**. Entre los aptos con reseña, la nota media es **4,29/5 a tiempo** y **2,27/5 tarde**.

El uso posible es ayudar a un equipo de logística o atención al cliente a revisar el cumplimiento histórico y su asociación con la satisfacción. No analizamos un usuario real ni desplegamos una herramienta. Tampoco entrenamos un modelo ni demostramos que el atraso cause toda la diferencia de notas.

## 2. Recorrido del notebook

| Celdas | Qué hacemos | Qué hay que poder explicar |
|---|---|---|
| 1-3 | Presentación, preguntas y significado de las nueve tablas | Unidad de análisis y alcance histórico |
| 4 | Rutas, librerías y configuración | Por qué usamos rutas relativas y un entorno reproducible |
| 5 | Verificamos hashes, leemos CSV y armamos inventario | Qué verifica SHA-256 y por qué los códigos postales son texto |
| 6-8 | Perfil, faltantes, duplicados, claves y multiplicidad | Duplicado exacto frente a repetición válida de un pedido |
| 9 | Copias, conversión de fechas y faltantes por estado | Diferencia entre fecha ausente y fecha no interpretable |
| 10-11 | Patrones de reseñas y metadatos faltantes | Qué observamos y qué causas desconocemos |
| 12-14 | Reglas, integridad, rangos y advertencias | Cuáles detienen el flujo y cuáles conservamos marcadas |
| 15-16 | Contrato, agregación e integración | Cómo evitamos multiplicar filas y definimos el atraso |
| 17-18 | `validar_curado` y tres pruebas alteradas | Qué verifica cada control y qué no garantiza |
| 19 | Exportación, comparación antes/después y trazabilidad | Qué guardamos y por qué no rellenamos todos los faltantes |
| 20-23 | Poblaciones, gráficos, métricas e interpretación | Denominador de cada número y límites de la conclusión |
| 24 | Declaración de uso de IA | Qué apoyo usamos y cómo comprobamos lo producido |

## 3. Datos, procedencia y grano

La fuente es **Brazilian E-Commerce Public Dataset by Olist, versión 2**, descargada de Kaggle el 06/11/2026. Las compras van del 04/09/2016 al 17/10/2018. Ese rango describe las compras, no todos los campos de fecha: por ejemplo, algunos límites de despacho llegan a 2020 y quedan señalados.

**Grano** significa qué representa una fila. Importa porque una unión entre tablas de distinto grano puede multiplicar registros.

| Tabla | Filas | Una fila representa | Clave o precaución |
|---|---:|---|---|
| `orders` | 99.441 | Un pedido | `order_id` |
| `customers` | 99.441 | Un registro de cliente asociado a un pedido | `customer_id`; `customer_unique_id` reconoce al comprador |
| `order_items` | 112.650 | Un ítem numerado dentro de un pedido | `order_id` + `order_item_id` |
| `payments` | 103.886 | Un registro o secuencia de pago | `order_id` + `payment_sequential` |
| `reviews` | 99.224 | Una reseña asociada a un pedido | `review_id` + `order_id` |
| `products` | 32.951 | Un producto | `product_id` |
| `sellers` | 3.095 | Un vendedor | `seller_id` |
| `categories` | 71 | Una traducción de categoría | `product_category_name` |
| `geolocation` | 1.000.163 | Una observación de ubicación | El prefijo postal se repite y no es clave única |

El centro es `orders`. Las otras tablas pueden tener varias filas por pedido. En este caso integramos clientes y agregados de ítems, pagos y reseñas. Perfilamos productos, vendedores, categorías y geolocalización, pero no los añadimos porque no hacen falta para estas dos preguntas. La geolocalización sí se usa después en el Caso 2.

Los importes están en reales brasileños, BRL. Los pesos originales de productos están en gramos y sus dimensiones en centímetros, aunque esos campos no entran al curado. Los identificadores y prefijos postales se leen como texto.

### Qué hacen el manifiesto y la descarga

`download_data.py` busca los nueve CSV en `data/raw/`. Si falta alguno, descarga el archivo de Olist v2. Antes de escribir comprueba los hashes esperados. Luego verifica todos los archivos locales y no sobrescribe un original existente que no coincide: informa el problema.

`data/source_manifest.json` guarda fuente, versión, fecha, tamaño y SHA-256 de cada original. El notebook vuelve a comprobar los hashes antes de cargar las tablas.

Un hash coincidente indica que tenemos los mismos bytes que el manifiesto. **No demuestra que los datos de origen sean verdaderos ni que estén libres de errores.**

Fragmento de la celda 5:

```python
for record in manifest["files"]:
    digest = hashlib.sha256((RAW / record["file"]).read_bytes()).hexdigest()
    if digest != record["sha256"]:
        raise ValueError("El original fue modificado: " + record["file"])
```

Después construimos `tipos` y lo pasamos a `pd.read_csv(..., dtype=tipos)`, para impedir que Pandas interprete los códigos postales como números:

```python
tipos = {c: "string" for c in columnas if c in ids or "zip_code_prefix" in c}
tablas[nombre] = pd.read_csv(RAW / archivo, dtype=tipos)
```

## 4. Qué exploramos y qué encontramos

### Faltantes

`isna().sum()` cuenta valores ausentes. `isna().mean() * 100` calcula el porcentaje porque `True` cuenta como 1 y `False` como 0. El denominador es la cantidad de filas de la tabla correspondiente.

| Campo | Faltantes | Porcentaje | Población |
|---|---:|---:|---|
| Fecha real de entrega | 2.965 | 2,98% | 99.441 pedidos |
| Título de reseña | 87.656 | 88,34% | 99.224 reseñas |
| Mensaje de reseña | 58.247 | 58,70% | 99.224 reseñas |
| Categoría del producto | 610 | 1,85% | 32.951 productos |

De las 2.965 fechas de entrega ausentes, 2.957 corresponden a estados distintos de `delivered` y 8 a pedidos entregados. La falta de entrega puede ser compatible con un estado no entregado, pero esos ocho casos requieren revisión. No inventamos sus fechas.

Las notas numéricas de las reseñas están disponibles aunque falte el texto. Descartar toda reseña sin comentario nos haría perder notas utilizables. Antes del 26/04/2018 todas las 68.782 reseñas anteriores a ese día, según fecha de respuesta, carecen de título. Desde ese día falta en 18.874 de 30.442 reseñas, aproximadamente 62%. Esto sugiere un patrón de disponibilidad o captura, sin probar su causa.

Los mismos 610 productos carecen de categoría, longitud del nombre, longitud de descripción y cantidad de fotos. El patrón conjunto no explica por sí mismo por qué ocurrió.

### Duplicados, claves y multiplicidad

Estos conceptos se comprueban por separado:

- **Duplicado exacto:** todas las columnas iguales. `df.duplicated()` detecta copias adicionales.
- **Clave repetida:** coinciden las columnas que deberían identificar una fila. Se evalúa con `df.duplicated(cols)`.
- **Multiplicidad válida:** un pedido tiene varios ítems, pagos o reseñas porque cada tabla registra otro tipo de evento.

Solo `geolocation` tiene duplicados exactos: 261.831 copias adicionales. Se registran y conservan; esa tabla no se integra en el Caso 1. No dijimos que toda la geolocalización quedara depurada.

Hay 9.803 pedidos con varios ítems, 2.961 con varios pagos y 547 con varias reseñas. Por eso no eliminamos filas solo porque repitan `order_id`.

`review_id` solo tiene 814 repeticiones adicionales, correspondientes a 789 identificadores asociados a varios pedidos. La pareja `review_id + order_id` sí es única en esta versión. No podemos asegurar que todas esas opiniones sean independientes.

### Fechas

La celda 9 trabaja sobre `.copy()` para conservar los DataFrames originales. Convierte fechas con formato explícito y `errors="coerce"`:

```python
convertido = pd.to_datetime(original, format="%Y-%m-%d %H:%M:%S", errors="coerce")
```

Una fecha no interpretable pasa a `NaT`. Por eso también contamos `original.notna() & convertido.isna()`: distingue una ausencia que ya existía de un texto presente que falló al convertir. En esta ejecución hubo cero fechas presentes no interpretables.

No asignamos una zona horaria que la fuente no declara.

## 5. Reglas estrictas y advertencias

Una regla estricta detiene la integración ante cualquier incumplimiento. Una advertencia conserva y señala el registro porque no tenemos evidencia suficiente para corregirlo o eliminarlo.

| Comprobación | Resultado | Tratamiento |
|---|---|---|
| Claves elegidas presentes y únicas | Cero incumplimientos | Si falla, detener |
| Seis referencias obligatorias | Cero nulos y cero huérfanos | Si falla, detener |
| Fechas presentes interpretables | Cero fallos de conversión | Si falla, detener |
| Precio, flete y pago presentes y no negativos | Cero incumplimientos | Si falla, detener |
| Notas entre 1 y 5 | Cero incumplimientos | Si falla, detener |
| Categoría ausente | 610 productos | Conservar ausencia |
| Categoría presente sin traducción | 13 productos | Señalar, no inventar traducción |
| Pago de valor cero | 9 registros de pago | Conservar y señalar |
| Cuotas cero | 2 registros de pago | Conservar y señalar |
| Entrega anterior al despacho | 23 pedidos | Marcar para revisión |
| Cancelado con fecha de entrega | 6 pedidos | Marcar para revisión |
| Límite de despacho desde 2019 | 4 filas de ítems, fechadas en 2020 | Señalar cobertura temporal |

Las seis referencias obligatorias son pedidos a clientes, ítems a pedidos, productos y vendedores, pagos a pedidos y reseñas a pedidos. La traducción de categoría se revisa como séptima relación, pero sus faltantes quedan como advertencia.

No detectamos entregas anteriores a la compra ni aprobaciones anteriores a la compra. Eso no demuestra que todos los horarios sean correctos.

Para la comparación contable, calculamos `total_pagado_brl - total_productos_brl - total_flete_brl`. Entre 98.665 pedidos comparables, 260 tienen diferencia absoluta mayor que BRL 0,05. La tolerancia es exploratoria. No conocemos el motivo ni alteramos importes para forzar la igualdad.

## 6. La decisión central: agregar antes de unir

Si un pedido tiene dos ítems y dos pagos, unir ambas tablas crudas por `order_id` produce cuatro combinaciones. Cada ítem y cada pago aparecería repetido. Si después sumamos, podemos inflar los importes. Es un ejemplo conceptual del riesgo, no una cifra observada de pedidos duplicados en nuestro curado.

La solución de la celda 16 es calcular primero un resumen por pedido:

```python
items_pedido = items.groupby("order_id", as_index=False).agg(
    n_items=("order_item_id", "size"), total_productos_brl=("price", "sum"),
    total_flete_brl=("freight_value", "sum"))
pagos_pedido = payments.groupby("order_id", as_index=False).agg(
    n_pagos=("payment_sequential", "size"), total_pagado_brl=("payment_value", "sum"))
resenas_pedido = reviews.groupby("order_id", as_index=False).agg(
    n_resenas=("review_score", "size"), nota_media=("review_score", "mean"))
```

- `groupby("order_id")` reúne las filas de cada pedido.
- `size` cuenta filas de ese grupo.
- `sum` suma importes ya comprobados como presentes y no negativos.
- `mean` obtiene la media de notas dentro de cada pedido.
- `as_index=False` conserva `order_id` como columna para la unión.

Después partimos de `orders` y hacemos uniones izquierdas:

```python
curado = orders.merge(customers[["customer_id", "customer_state"]], on="customer_id",
                      how="left", validate="many_to_one")
for agregado in [items_pedido, pagos_pedido, resenas_pedido]:
    curado = curado.merge(agregado, on="order_id", how="left", validate="one_to_one")
```

`how="left"` conserva los pedidos de la izquierda. `validate="many_to_one"` exige que el lado de clientes tenga clave única. `validate="one_to_one"` exige unicidad en ambos lados de cada unión con agregados. Así la estructura falla explícitamente si cambia lo que esperábamos.

Comprobamos después que quedan **los mismos 99.441 IDs**. No basta comprobar solamente la cantidad: podríamos perder un pedido y agregar otro, manteniendo el mismo número de filas.

### Cero y ausencia significan cosas distintas

En los conteos llenamos las ausencias con cero:

```python
for c in ["n_items", "n_pagos", "n_resenas"]:
    curado[c] = curado[c].fillna(0).astype("Int64")
```

Hay 775 pedidos sin ítems, uno sin registro de pago y 768 sin reseñas. Un conteo cero dice que no encontramos filas hijas. El importe o la nota correspondiente sigue sin dato. Un pago registrado con valor 0 sí queda como 0. No aplicamos `fillna(0)` a todos los campos.

### Por qué promediamos primero por pedido

Un pedido con tres reseñas no debe pesar tres veces más que uno con una reseña en la comparación principal. Primero obtenemos su `nota_media`, después calculamos la media de esas notas por grupo de atraso. Es una media de medias por pedido, con el mismo peso para cada pedido, no una media de todas las reseñas crudas.

## 7. Cómo definimos el atraso

Comparamos **días calendario**. `.dt.normalize()` lleva la hora a las 00:00 conservando el día. Evita clasificar como tardía una entrega a las 18:00 si la promesa del mismo día aparece a las 00:00.

Un pedido es apto si cumple todas estas condiciones:

1. Estado `delivered`.
2. Compra, entrega real y promesa presentes.
3. Día de entrega no anterior al de compra.
4. Día de promesa no anterior al de compra.

Código real de la celda 16:

```python
compra = curado.order_purchase_timestamp.dt.normalize()
entrega = curado.order_delivered_customer_date.dt.normalize()
promesa = curado.order_estimated_delivery_date.dt.normalize()
curado["apto_atraso"] = (curado.order_status.eq("delivered") & compra.notna() &
                          entrega.notna() & promesa.notna() & (entrega >= compra) & (promesa >= compra))
curado["dias_respecto_promesa"] = (entrega - promesa).dt.days.where(curado.apto_atraso).astype("Int64")
curado["entrega_tarde"] = (curado.dias_respecto_promesa > 0).astype("boolean")
```

La fórmula es:

```text
días respecto de la promesa = día de entrega real - día prometido
entrega tarde = días respecto de la promesa > 0
```

- Diferencia negativa: llegó antes del día prometido.
- Cero: llegó el mismo día, cuenta a tiempo.
- Positiva: llegó tarde.
- Pedido no apto: diferencia e indicador quedan desconocidos.

`.where(curado.apto_atraso)` conserva el resultado solamente donde el pedido es apto. `Int64` y `boolean` son tipos de Pandas que permiten valores ausentes. Así un no apto no se convierte accidentalmente en una entrega a tiempo.

Las 23 entregas anteriores al despacho siguen aptas porque la regla de aptitud utiliza compra, entrega y promesa. Es una limitación explícita: las marcamos para revisión sin decidir arbitrariamente qué fecha es falsa.

## 8. Diccionario del curado

| Columna | Significado |
|---|---|
| `order_id` | Identificador único del pedido |
| `customer_id` | Identificador del registro de cliente |
| `order_status` | Estado declarado del pedido |
| `order_purchase_timestamp` | Momento de compra |
| `order_approved_at` | Momento de aprobación |
| `order_delivered_carrier_date` | Momento de despacho/entrega al transportista registrado |
| `order_delivered_customer_date` | Momento real de entrega al cliente |
| `order_estimated_delivery_date` | Fecha prometida de entrega |
| `customer_state` | UF del cliente |
| `n_items` | Cantidad de filas de ítems por pedido |
| `total_productos_brl` | Suma de precios de los ítems |
| `total_flete_brl` | Suma del flete de los ítems |
| `n_pagos` | Cantidad de registros de pago |
| `total_pagado_brl` | Suma de importes de pago |
| `n_resenas` | Cantidad de reseñas vinculadas al pedido |
| `nota_media` | Media de las notas de ese pedido |
| `apto_atraso` | Si cumple las condiciones para medir atraso |
| `dias_respecto_promesa` | Diferencia en días calendario, solo en aptos |
| `entrega_tarde` | `True` tarde, `False` a tiempo, ausente si no apto |
| `entrega_antes_despacho` | Marca de secuencia temporal sospechosa |
| `aprobacion_antes_compra` | Marca de secuencia temporal sospechosa |
| `cancelado_con_entrega` | Estado cancelado con entrega presente |
| `diferencia_pago_brl` | Pago menos precio y flete, redondeado a dos decimales |

Las fechas se trabajan como fechas en memoria. Al exportar CSV se escriben como texto ISO, por lo que otro proceso debe volver a convertirlas al cargarlo.

## 9. Contrato y pruebas con errores intencionales

`validar_curado(df, pedidos_fuente)`, celda 18, comprueba:

1. `order_id` único y no nulo.
2. Misma cantidad y conjunto de pedidos que la fuente.
3. Notas presentes entre 1 y 5.
4. Fechas e indicadores completos en pedidos aptos.
5. Indicador de atraso desconocido en no aptos.
6. Aptitud y atraso recalculados compatibles con estado y fechas.
7. Importes presentes no negativos.

Recalcular desde las fechas evita aceptar un indicador almacenado que contradiga sus entradas. El umbral de estas reglas es cero incumplimientos.

Probamos sobre `.copy()` tres alteraciones, sin modificar los originales ni el curado exportado:

| Alteración intencional | Resultado esperado y observado | Límite del control |
|---|---|---|
| Repetir un `order_id` | `ValueError` por clave no única | No reconoce el mismo negocio con IDs diferentes |
| Asignar nota 9 | `ValueError` por nota fuera de rango | Una nota 4 falsa puede pasar el rango |
| Quitar la entrega de un pedido apto | `ValueError` por fecha necesaria ausente | Una fecha plausible pero incorrecta puede pasar |

Un `try/except ValueError` registra que se detectó el fallo. Si no hay excepción, el código genera `RuntimeError` porque la prueba falló. Los tres casos figuran detectados en `results/pruebas_controles.csv`.

Estas son pruebas deliberadas de los controles. No son evidencia de tres errores accidentales que hayamos cometido durante el trabajo.

## 10. Resultados y denominadores

| Resultado | Numerador / población | Lectura correcta |
|---|---|---|
| Pedidos curados | 99.441 de 99.441 | Conservamos todos los pedidos |
| Entregados | 96.478 de 99.441 | Estado `delivered` |
| Aptos para atraso | 96.470 de 99.441 | Entregados con fechas suficientes y coherentes |
| Excluidos de la métrica | 2.971 de 99.441 | 2.963 no entregados y 8 entregados sin fecha real |
| Tardíos | 6.534 de 96.470 | 6,773%, redondeado 6,77% |
| Meses graficados | 96.468 aptos | Solo meses con al menos 100 pedidos |
| Marzo de 2018 | 1.328 de 7.003 aptos de ese mes | 18,96% de atraso, por mes de compra |
| Aptos con reseña | 95.824 de 96.470 | 646 aptos no tienen reseña |
| Nota a tiempo | Media 4,291/5 en 89.443 pedidos | Cada pedido pesa una vez |
| Nota tarde | Media 2,272/5 en 6.381 pedidos | Cada pedido pesa una vez |

La tasa global sale de `100 * 6534 / 96470`. No usamos 99.441 como denominador ni incluimos cancelados como si hubieran llegado a tiempo.

El gráfico mensual excluye septiembre y diciembre de 2016, con un pedido cada uno, para evitar interpretar porcentajes muy inestables. Esos dos pedidos permanecen en la tabla mensual completa y en el total global. No desaparecen del curado.

La diferencia de notas es aproximadamente **2,02 puntos sobre 5**. Describe asociación en los pedidos observados. Producto, vendedor, período, ausencia de reseña y reutilización de IDs pueden influir. No aislamos el efecto causal del atraso.

### Entrenamiento y prueba

**No hay separación de entrenamiento y prueba en este caso**, porque realizamos perfilado, curación y análisis descriptivo. No ajustamos ni evaluamos un predictor. Las predicciones P1/P2 son expectativas sobre calidad para orientar la exploración, no modelos de machine learning. Además, el notebook reconoce que se formularon para la corrección, no antes del avance original.

Los filtros de aptitud y disponibilidad de reseña definen poblaciones de análisis, no conjuntos de entrenamiento y test. Si después construyéramos un modelo, habría que fijar el momento de predicción, usar variables disponibles en ese momento y reservar datos para evaluar generalización. Eso sería trabajo futuro.

## 11. Un error propio comprobable y su corrección

En la copia local del avance original, `original/CasoEstudio1/notebook.ipynb`, celda 4, leímos los CSV sin especificar tipos. La salida guardada de la celda 7 muestra el prefijo de un cliente como `9790`. El CSV fuente conserva ese valor como **`09790`**. Al inferir un número, Pandas eliminó el cero inicial de la representación. El documento [Evidencia del error de prefijos postales](EVIDENCIA_PREFIJOS_POSTALES.md) incluye los extractos literales, la fila fuente, la corrección y los hashes, para poder revisar el ejemplo sin disponer del notebook histórico completo.

El cliente del ejemplo tiene `customer_id = 18955e83d337fd6b2def6b18a428ac77`. También aparece `1151` en la salida original donde el CSV fuente guarda `01151`.

La lectura actual de la celda 5 declara como `string` los IDs y las columnas con `zip_code_prefix`. Con eso conserva `09790`. El aprendizaje es definir tipos por significado: un código postal identifica una zona y no se usa para hacer cuentas.

No afirmamos que ese error haya producido un cruce fallido observado ni que alterara una cifra del Caso 1: la geolocalización no se integró aquí. La evidencia demuestra la pérdida de representación. Mantener los ceros resulta especialmente relevante al preparar los cruces del Caso 2.

Otra mejora documentada es pasar de mostrar dimensiones y primeras filas a revisar el conjunto completo. Las expectativas P1/P2 no estaban registradas en el primer avance y se añadieron en la corrección. No debemos presentar ese orden como si hubiera sido otro.

## 12. Archivos para comprobar cada afirmación

| Archivo | Qué permite revisar |
|---|---|
| `data/source_manifest.json` | Procedencia, versión y hashes |
| `results/inventario.csv` | Filas y columnas de cada tabla |
| `results/perfil_columnas.csv` | Tipos, faltantes y valores distintos |
| `results/duplicados.csv` | Duplicados exactos |
| `results/claves.csv` | Nulos y repeticiones en claves |
| `results/multiplicidad.csv` | Pedidos con varias filas hijas |
| `results/fechas.csv` | Conversión y rangos temporales |
| `results/faltantes_por_estado.csv` | Ausencias según estado del pedido |
| `results/integridad.csv` | Correspondencia entre tablas |
| `results/calidad_numerica.csv` | Rangos y advertencias numéricas |
| `results/antes_despues.csv` | Qué cambió y qué se conservó |
| `results/trazabilidad_pedidos.csv` | IDs con aptitud, ausencias y marcas |
| `results/pruebas_controles.csv` | Las tres alteraciones detectadas |
| `results/atrasos_por_mes.csv` | Poblaciones y tasas de todos los meses |
| `results/notas_segun_atraso.csv` | Tamaños y notas por grupo |
| `results/resumen.json` | Resumen de cifras principales |
| `figures/` | Los dos gráficos del informe |
| `data/curated/orders_curated.csv` | Salida con una fila por pedido |

## 13. Cómo reproducirlo y reconocer una ejecución correcta

Desde la carpeta `CasoEstudio1_Corregido`, con Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python download_data.py
jupyter notebook notebook.ipynb
```

En Windows, activar el entorno con `.venv\Scripts\activate` en lugar del comando `source`. La forma de invocar Python 3.12 depende de la instalación local, por ejemplo `py -3.12`.

En Jupyter, elegir **Restart Kernel and Run All Cells**. El orden importa: varias celdas usan variables creadas antes. No alcanza con ejecutar solo una celda que parece funcionar gracias a variables viejas en memoria.

Comprobar al terminar:

1. Mensaje `OK: contrato de pedidos validado`.
2. Tres pruebas con `detectado=True`.
3. Curado con 99.441 filas y 23 columnas, `order_id` sin repetidos.
4. 96.470 aptos y 6.534 tardíos.
5. Resultados y gráficos regenerados en `results/` y `figures/`.

Si faltan originales, ejecutar primero `download_data.py`. Si falla un hash, revisar la procedencia del archivo y el manifiesto; no desactivar el control para que pase. Instalar dependencias y descargar los datos exige Internet la primera vez. El notebook puede ejecutarse sin conexión cuando los nueve originales y las dependencias ya están disponibles.

## 14. Preguntas para practicar la defensa individual

Cada integrante debería responderlas y señalar la celda que lo demuestra:

| Pregunta | Respuesta que hay que entender |
|---|---|
| ¿Cuál es la unidad de análisis? | El pedido, una fila por `order_id` |
| ¿Por qué `order_id` puede repetirse en ítems? | Porque un pedido puede contener varios ítems |
| ¿Por qué no unimos todas las tablas crudas? | Las relaciones uno a muchos pueden multiplicar filas e importes |
| ¿Qué hace `validate="one_to_one"`? | Comprueba unicidad de la clave en ambos lados de la unión |
| ¿Por qué una unión izquierda? | Conserva todos los pedidos del punto de partida |
| ¿Qué diferencia hay entre `NaN` y 0? | Ausencia de información frente a valor observado cero |
| ¿Por qué se conserva una reseña sin texto? | Puede tener una nota numérica válida para la pregunta |
| ¿Cómo calculamos `nota_media`? | Primero dentro del pedido y después entre pedidos del grupo |
| ¿Qué significa `errors="coerce"`? | Una conversión fallida pasa a `NaT`, y la contamos por separado |
| ¿Por qué usamos `.normalize()`? | Para comparar días y contar el mismo día prometido como a tiempo |
| ¿Qué hace `.where(apto_atraso)`? | Deja el atraso desconocido fuera de los pedidos aptos |
| ¿Por qué un cancelado no cuenta a tiempo? | No tiene una entrega confirmada válida para esta métrica |
| ¿Qué población da el 6,77%? | 6.534 tardíos entre 96.470 aptos |
| ¿Por qué el gráfico mensual suma 96.468? | Dos meses de un pedido quedan fuera de la visualización |
| ¿Por qué no hay train/test? | No entrenamos un predictor, el análisis es descriptivo |
| ¿Qué comprueba el hash? | Igualdad de bytes respecto del manifiesto, no verdad del dato |
| ¿Qué pasa con las 23 entregas antes del despacho? | Quedan marcadas, y siguen aptas bajo la regla adoptada |
| ¿Detectar los tres errores prueba que todo está bien? | Solo demuestra que esos controles detectan esas alteraciones |
| ¿El atraso causa una nota menor? | Encontramos asociación, no aislamos causalidad |
| ¿Qué error propio podemos mostrar? | La carga inicial infería números y perdía ceros de códigos postales |
| ¿Qué conserva el Caso 2? | La tabla curada del Caso 1 como entrada congelada |
| ¿Qué hizo la IA y qué hicieron ustedes para verificar? | Apoyó código y explicaciones; revisamos ejecución, cifras, tablas, gráficos y pruebas |

Una forma de ensayar un fragmento de código es explicar: **qué entra, qué hace cada operación, qué sale, por qué se eligió y qué podría fallar**. Por ejemplo, para el `groupby` de pagos: entran registros de pago, se agrupan por pedido, se cuentan y suman, sale una fila por pedido y se evita multiplicar importes en el merge.

## 15. Preparación compartida

Para la defensa grupal, todos deben entender ambos casos aunque cada uno presente una parte. Para la individual, estudiar solamente la parte propia deja afuera preguntas que el profesor puede hacer sobre el resto del equipo.

Primero recorran juntos las celdas 5, 8, 9, 13, 16, 18, 21 y 22. Después roten: cada integrante explica una celda que no haya preparado. Practiquen las cifras con su denominador y distingan lo observado, la interpretación y el trabajo futuro. Si una causa no está demostrada, la respuesta correcta es explicar qué evidencia falta y cómo la investigarían.
