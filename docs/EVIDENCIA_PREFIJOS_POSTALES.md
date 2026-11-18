# Evidencia del error de lectura de prefijos postales

Este extracto conserva la evidencia mínima del avance original y la corrección del Caso 1. Se documentó el 18/11/2026 desde los archivos locales del equipo. Permite entender el ejemplo de la defensa sin tener que disponer del notebook histórico completo.

La numeración de celdas empieza en 1 e incluye todas las celdas del notebook.

## 1. Carga del avance original

La celda 4 de `original/CasoEstudio1/notebook.ipynb` contiene esta línea literal, sin un tipo explícito para el prefijo:

```python
customers = pd.read_csv("data/raw/olist_customers_dataset.csv")
```

## 2. Salida guardada del avance original

La celda 7 muestra `df.head(3)` para cada tabla. Este es el bloque literal de su salida `text/plain` correspondiente a clientes:

```text
                        customer_id                customer_unique_id  \
0  06b8999e2fba1a1fbc88172c00ba8bc7  861eff4711a542e4b93843c6dd7febb0   
1  18955e83d337fd6b2def6b18a428ac77  290c77bc529b7ac935b93aa66c333dc3   
2  4e7b3e00288586ebd08712fdd0374a03  060e732b5b29e8181a18229c7b0b2b5e   

   customer_zip_code_prefix          customer_city customer_state  
0                     14409                 franca             SP  
1                      9790  sao bernardo do campo             SP  
2                      1151              sao paulo             SP  
```

La fila de índice 1 identifica al cliente `18955e83d337fd6b2def6b18a428ac77` y muestra su prefijo como `9790`.

## 3. Valor del CSV fuente

En `olist_customers_dataset.csv`, la línea 3 del archivo, contando el encabezado como línea 1, corresponde al mismo cliente. Se reproduce el encabezado y esa fila literal:

```csv
"customer_id","customer_unique_id","customer_zip_code_prefix","customer_city","customer_state"
"18955e83d337fd6b2def6b18a428ac77","290c77bc529b7ac935b93aa66c333dc3","09790",sao bernardo do campo,SP
```

La fuente guarda **`09790`**, con cinco caracteres. La salida histórica muestra **`9790`**, con cuatro. La lectura numérica perdió el cero inicial de la representación de un identificador.

## 4. Lectura corregida

La celda 5 del [notebook actual](../notebook.ipynb) identifica las columnas y declara como texto los IDs y prefijos postales antes de leer:

```python
for nombre, archivo in archivos.items():
    columnas = pd.read_csv(RAW / archivo, nrows=0).columns
    tipos = {c: "string" for c in columnas if c in ids or "zip_code_prefix" in c}
    tablas[nombre] = pd.read_csv(RAW / archivo, dtype=tipos)
```

Así el código postal conserva `09790`. El criterio se basa en su significado: identifica una zona y no es una cantidad para operar aritméticamente.

## 5. Alcance de la evidencia

La comparación demuestra una pérdida de ceros iniciales en la carga del avance original y una regla de lectura actual que los conserva. **No demuestra que haya ocurrido un error concreto en una unión ni que se haya alterado alguna métrica del Caso 1.** La geolocalización no se integró en el Caso 1 corregido. La preservación del código resulta relevante para preparar las claves del Caso 2.

Tampoco son dos pedidos distintos: el identificador del cliente permite comparar el mismo registro en la salida y en el CSV fuente.

## 6. Procedencia histórica y hashes

Las rutas siguientes identifican las copias locales usadas para preparar este extracto. No son rutas que deban existir al clonar el repositorio:

| Evidencia | Ruta de procedencia local |
|---|---|
| Notebook del avance original | `/Users/santiagoalba/Documents/ChatGPT/ING DE DATOS/original/CasoEstudio1/notebook.ipynb` |
| CSV fuente de clientes | `/Users/santiagoalba/Documents/ChatGPT/ING DE DATOS/CasoEstudio1_Corregido/data/raw/olist_customers_dataset.csv` |

SHA-256 del notebook histórico completo al extraer la evidencia:

```text
608a807b5f903f6adfed6c1f63a1b899fa63b6d18da98fedfed0027d38b9ec5a
```

SHA-256 del CSV completo de clientes:

```text
983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2
```

El hash del CSV coincide con el registrado en [el manifiesto de fuentes](../data/source_manifest.json). Ese archivo se obtiene y verifica con `python download_data.py`; los CSV crudos no se versionan en Git. El notebook histórico completo no forma parte de esta entrega: este documento conserva sus fragmentos relevantes y su huella para identificar la copia de origen. Los hashes identifican bytes, no certifican por sí solos la exactitud de los datos.
