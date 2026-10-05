# 07 · Spec — Orquestación, persistencia y CLI

> Conversación: "Fase Orquestación". Leer antes `00` v2.0 y `01` **v2.7** (todos los contratos).
> Estado: **v3** (2026-10-04) · **código convencional.** Parte se construye al principio
> (persistencia, junto con la spec `05`) y parte al final (orquestación completa).
> **v2 (2026-09-10):** Acervo tiene dos modos (`00` §3). Esta spec cose los dos, les da una
> sola base y una sola CLI, y resuelve la deuda CD-05-2 de `05`.
> **v3 (2026-10-04):** recoge lo que `01` v2.6 y v2.7 dejaron pendiente aquí, y **tapa un hueco
> que la v2 no vio: `Catalog` (N3) no tenía tabla.** `catalogo` es espejo de N2 —las entradas—,
> así que la fecha de corte, `catalogo_caducado` y los cinco campos de contabilidad de la v2.6 no
> tenían dónde vivir. Sin eso, el Corroborador no puede aplicar su criterio 13 y el sistema
> vuelve a poder mentir sin errores.

---

## Qué cambia en la v3 (leer primero)

| Cambio | Sección |
|---|---|
| **Tabla `lecturas` nueva: `Catalog` (N3) no tenía dónde persistirse** | Persistencia · criterio 17 |
| **Regla de escritura de E17: una extracción incompleta no escribe** | Persistencia · criterio 18 |
| **Qué hace la orquestación ante `salida_invalida`** (pendiente de `01` v2.6) | El flujo · **propuesta a ratificar** |
| Tabla `selecciones` (N15) y `--tema` en la CLI (`01` v2.7) | Persistencia · CLI · criterio 19 |
| **Guardia de versión de `doc_slug`:** la base se niega a correr si el algoritmo cambió | §Guardia de slug · criterio 20 · **propuesta** |
| **Toda corrida deja su log en disco**, sin que haya que acordarse de `tee` | §Registro de corridas · criterio 21 |
| Criterio 9 corregido: `Geologia_dois_.docx` nunca llegó al repo (`01` v2.5) | criterio 9 |
| Criterio 1: el corpus de la UAM son **47** enlaces y **31 instrumentos vigentes** | criterio 1 |

---

## Objetivo

Coser las piezas de **los dos modos** en flujos re-ejecutables, persistir todo en una sola base
SQLite, y exponer una CLI que permita cosechar una universidad o procesar una lista de
artículos, revisar el estado y detectar cambios.

**El Orquestador no razona.** No es un agente: es una función que llama a las piezas en orden,
maneja fallos y escribe. Toda la inteligencia vive en las piezas.

---

## El flujo

### Modo jurídico

```python
def cosechar(inst: InstitutionRef, settings: Settings) -> HarvestStats:
    # 0. Guardia de slug: si la versión del algoritmo cambió, se detiene aquí   ← v3
    # 1. Localizar (agente) — se salta si ya hay fuentes válidas en DB
    # 2. Leer índice (agente) sobre las candidatas, en orden de confianza,
    #    hasta obtener un Catalog no vacío. Se persiste en `lecturas`.          ← v3
    # 3. Corroborar (agente) — puede disparar búsquedas extra (Ley Orgánica)
    # 4. Seleccionar por tema, si inst.temas lo pide (N15) → `selecciones`      ← v3
    # 5. Traducir cada CatalogEntry pendiente y seleccionada a Encargo
    # 6. Descargar (código) todo lo que falte o haya cambiado
    # 7. Verificar (agente) lo recién descargado
    # 8. Consolidar NormativeRecord + poblar cola manual
```

### Modo académico

```python
def procesar_lote(lista: Path, settings: Settings) -> BatchReport:
    # 1. Hash del archivo → lote_id. Si el lote ya fue leído, se reutiliza su ArticleBatch
    # 2. Leer lista (agente Lector de Lista) → ArticleBatch; incompletos quedan anotados
    # 3. Para cada ficha válida:
    #      - articulo_id con veredicto correcto ya registrado → no se pide
    #      - sin puertas → no obtenido, motivo sin_puertas
    #      - si no → traducir a Encargo y descargar (código)
    # 4. Verificar (agente Verificador Académico) → ArticleVerdict
    # 5. Auditar (código Auditor de Lote) → BatchReport; guardar y mostrar
```

**Los dos flujos comparten el paso de descarga, y nada más.**

**Regla de continuidad:** el fallo de una pieza no aborta la corrida. Un catálogo sin
corroborar sigue siendo un catálogo útil. Cada paso que falla deja rastro en `HarvestStats` y
en la cola manual, y el flujo continúa hasta donde pueda.

**Regla de economía:** los pasos con LLM se saltan si su entrada no cambió. Re-cosechar una
universidad cuyo índice es idéntico al de la semana pasada debe costar **cero llamadas al
modelo** — solo un GET y un diff. Esto es lo que hace viable la vigilancia periódica.

**En modo académico, las mismas dos reglas.** *Continuidad:* si el Verificador Académico falla,
el lote termina igual; lo descargado va a `con_observaciones` con `veredicto=None` (`01` v2.2).
*Economía:* re-procesar la misma lista cuesta cero llamadas y cero peticiones.

### Qué hace la orquestación ante `salida_invalida` (v3 · **propuesta a ratificar**)

`01` v2.6 dejó esta decisión aquí. El caso: el Lector llamó al agente, el agente respondió, y su
JSON **no validó**. `Catalog` llega con `fallo_lector="salida_invalida"` y
`lector_agotado=False`.

**Propuesta, en tres reglas:**

1. **Un reintento, no más.** Misma página reducida, mismo prompt. Un JSON malformado suele ser
   ruido de muestreo y el reintento es barato; dos reintentos ya es confiar en la suerte. El
   contador va a `HarvestStats.llamadas_llm`, que es donde debe doler.
2. **Si el reintento también falla, NO se salta al siguiente eslabón de D1.** Es la regla que más
   importa y la razón de que `lector_agotado` y `fallo_lector` sean excluyentes: **la página era
   legible**. Saltar al 70-I registraría `origen="pnt_70i"` para una universidad cuyo sitio
   institucional funciona, degradando la proveniencia (D5) por un fallo nuestro.
3. **Se escribe la lectura y nada más** (ver §Persistencia): fila en `lecturas` con su
   `fallo_lector`, **cero filas en `catalogo`**, y un `ManualQueueItem` de severidad
   `importante` que diga *«el índice de X no se pudo leer: fallo del Lector, no de la
   universidad»*, con la `url_indice` para abrirlo a mano.

> **Por qué la cola manual y no un error silencioso:** la cola es producto (D7). Un ítem que
> nombra nuestro propio fallo es tan útil como uno que nombra un documento ausente — y es la
> única forma de que alguien se entere.

**Ratificar antes de implementar.** Lo que está en duda es el punto 1: si un reintento es
suficiente o si conviene cero. No hay medición todavía porque el agente no existe.

---

## Entradas en `.docx`

**Ficha jurídica → `InstitutionRef` (N0): la lee código, no un agente.** Es un formulario, no
un texto libre: una tabla de dos columnas (campo, valor) o renglones `campo: valor`. Claves
aceptadas: `inst_id`, `nombre_oficial`, `entidad_federativa` (obligatorias) y `siglas`,
`regimen`, `dominio_raiz`, `sujeto_obligado_pnt`, `notas` (opcionales). Si falta una
obligatoria, **no hay corrida**: el error nombra exactamente qué campo falta. `acervo plantilla
juridico` genera la ficha vacía.

**Lista académica → `ArticleBatch` (N12): la lee un agente.** Es texto libre escrito por
personas, y por eso no tiene plantilla: se acepta como venga.

Lectura de `.docx` con `python-docx`. Se extrae texto **y enlaces**: en una lista, la URL real
de un hipervínculo puede no coincidir con el texto visible, y la puerta es la URL real (D3).

> **Nota (v3):** el tema de `SeleccionTematica` **no** entra por la ficha. Es de la corrida, no de
> la institución (`01` v2.7, N0): va en `--tema` de la CLI.

---

## Persistencia

```
— comunes —
encargos           espejo de N10, PK encargo_id; incluye modo, grupo_alias
descargas          espejo de N5, PK (encargo_id, sha256); índice por grupo_alias (alias por hash)
intentos           espejo de IntentoPuerta, FK encargo_id, una fila por puerta pedida
meta               clave/valor de la base: versión de esquema y slug_version      ← v3

— modo jurídico —
instituciones      espejo de N0
fuentes            espejo de N1, con validez y último uso
lecturas           espejo de N3 SIN entries, PK (inst_id, generado_en)            ← v3
catalogo           espejo de N2, PK entry_id; FK a la lectura que lo produjo      ← v3
selecciones        espejo de N15, PK seleccion_id; + excluidas(entry_id, razon)   ← v3
documentos         espejo de N6 + N7 consolidado, PK doc_id; FK entry_id
cola_manual        espejo de N8
corridas           espejo de N9, una fila por cosecha
indices_capturados hash del HTML del índice por fecha  ← el detector de cambios

— modo académico —
lotes              espejo de N12 sin artículos, PK lote_id; sha256_archivo único
articulos          espejo de N11, PK articulo_id
lote_articulos     lote_id + articulo_id + posicion_en_lista + referencia_literal
veredictos         espejo de N13, PK (articulo_id, sha256)
informes           espejo de N14, PK lote_id, JSON completo + fecha
```

### `lecturas`: el hueco que la v2 no vio (v3)

`catalogo` es espejo de **N2**, las entradas. Pero `Catalog` (**N3**) tiene campos propios que no
pertenecen a ninguna entrada y que la v2 no persistía en ninguna parte:

```
inst_id · generado_en · lector_agotado · notas
fecha_corte_declarada · fecha_corte_texto · catalogo_caducado          (v2.3)
enlaces_vistos · enlaces_descartados · enlaces_sin_cuenta
lectura_incompleta · fallo_lector                                       (v2.6)
```

**Sin esta tabla, el criterio 13 de `04` es inaplicable:** el Corroborador no tendría de dónde
leer `lectura_incompleta`, y volvería a atribuir a la universidad huecos que son nuestros. Y la
fecha de corte de la UACAM —el hallazgo más importante del proyecto— se perdería entre corridas.

`enlaces_descartados` y `enlaces_sin_cuenta` son listas: van como JSON en su columna, o en una
tabla hija si alguna vez hace falta consultarlas por enlace. **Listas, no conteos** (D5).

`catalogo` gana una FK a la lectura que lo produjo, para que dos lecturas de la misma institución
en fechas distintas no se confundan.

### Regla de escritura: una extracción incompleta no escribe (v3 · E17)

**Si `fallo_lector` no es `None` o `lectura_incompleta=True`, se escribe la fila de `lecturas` y
CERO filas de `catalogo`.**

Es el precedente de E17 trasplantado. Allá, un upsert escribió un resultado pobre encima de uno
bueno y pisó **47 filas** de `descargas`; `content_type` quedó como pérdida definitiva, y la
solución (M35) fue la más simple posible: al omitir no se escribe. **Aquí el daño sería peor: de
una fila de catálogo no hay `intentos` de donde repararla.**

La fila de `lecturas` sí se escribe siempre: es el registro de que lo intentamos y de cómo falló.

### Lo demás

**Por qué `documentos` se divide (v2).** En v1 mezclaba la descarga (N5) con el consolidado
jurídico (N6 + N7). Una descarga académica no es un `NormativeRecord`. **Es un paso de la
migración de `05`**; no se migran filas viejas.

**Por qué `lote_articulos` es tabla aparte.** Un mismo artículo puede pedirse en varias listas
con distinto número y distinta redacción. El artículo es uno; sus apariciones son muchas.

**Por qué `veredictos` lleva `sha256` en la clave.** El veredicto es sobre un archivo concreto.

**`indices_capturados` es la pieza no obvia y la más importante.** Guardar el hash del índice
convierte la detección de reformas en una operación de un GET. Sin esta tabla, cada corrida
periódica cuesta un LLM por universidad.

> **Precisión de la v3:** el hash se calcula sobre los **bytes crudos**, no sobre el texto
> decodificado. Es más barato, no depende de la codificación, y detecta cualquier cambio. El
> texto decodificado lo produce `lector/reduce.py` y solo hace falta cuando ya se decidió leer.

**Reglas heredadas del proyecto hermano:** `upsert` por clave primaria; textos en UTF-8 intactos
—solo las *claves* se normalizan—; conversión a tipos nativos en la frontera modelo→persistencia;
respaldo inmediato tras cada corrida cara.

---

## Guardia de versión de `doc_slug` (v3 · **propuesta**)

**El problema, medido dos veces.** `grupo_alias = f"{inst_id}:{doc_slug}"` y el alias por hash
**solo compara dentro de un grupo** (`01` v2.7, N2). Si el algoritmo de `doc_slug` cambia, los
mismos bytes se escriben otra vez bajo otro grupo. Está medido en la UAM —**14 documentos cambian
de slug** al corregir la heurística (`03` v5)— y en la UNAM —**5 documentos** cosechados con slugs
escritos a mano que no casarán con los del Lector (E21.15, deuda E6.25)—.

El remedio ya está escrito como procedimiento en `03`: `data/` vacío y base limpia. **Pero un
procedimiento que depende de que alguien se acuerde no es un remedio.**

**Propuesta:** la tabla `meta` guarda `slug_version`, una cadena corta que `lector/slug.py`
declara. Al arrancar una corrida jurídica, la orquestación compara:

- **coinciden** → sigue;
- **la base está vacía** → escribe la versión actual y sigue;
- **difieren** → **se detiene antes de cualquier petición**, con un mensaje que diga qué versión
  tiene la base, cuál el código, y que hay que vaciar `data/` y empezar con base limpia —con el
  comando de respaldo delante.

**Qué cuesta:** una columna y una comparación. **Qué evita:** la clase de fallo que este proyecto
persigue, porque la duplicación **no lanza ningún error**: la regla de no sobrescribir jamás hace
exactamente lo que debe, y el corpus se infla en silencio.

**Lo que la guardia NO resuelve:** unificar slugs entre un catálogo escrito a mano y un índice
institucional (E6.25). Eso es trabajo del Lector y del Corroborador (`04` pregunta 11).

---

## Registro de corridas (v3)

**Toda corrida escribe su log a disco, sin que nadie tenga que acordarse.**

Viene de un fallo real y reciente: las **nueve corridas de la UNAM** de octubre se lanzaron sin
`tee`, y sus logs no existen. E21 y E22 tuvieron que redactarse sobre la salida pegada en una
conversación y sobre consultas a la base. **Y E19 existe precisamente porque un resumen contrastado
con su log cambió en cinco cosas.** El proyecto ya había pagado esa lección y la volvió a pagar.

**Requisito:** `acervo` escribe `logs/<AAAA-MM-DD>__<comando>__<id>.log` con todo lo que manda a
la terminal, y la ruta se imprime al terminar. `logs/` va al `.gitignore`. Si el directorio no se
puede crear, se avisa y la corrida sigue: un log es importante, no bloqueante.

**No sustituye a los artefactos de evaluación del Lector** (criterio 20 de `03`), que son otra
cosa y viven aparte: la respuesta cruda del agente, el prompt y el modelo con su versión.

---

## Cliente HTTP único (v2 · resuelve CD-05-2)

La orquestación construye **un solo `httpx.Client`** con User-Agent, timeouts y TLS estricto
desde `Settings`, y lo inyecta a `Fetcher`, `RobotsCache` y al cruce de vestíbulo. Ningún
módulo crea su propio cliente ni recibe una función suelta para pedir.

Es la solución anotada en CD-05-2: allá se olvidó el UA en el fetcher de robots, y la v3 de `05`
añade un tercer llamador. Con un cliente único, el UA se pone una vez y nadie puede olvidarlo.

---

## CLI

**El comando se llama `acervo`** (entrada de script en `pyproject.toml`; `python -m acervo`
equivale).

```bash
acervo                                      # menú interactivo

# --- modo jurídico ---
acervo juridico ficha.docx                  # alta desde la ficha + cosecha
acervo juridico --inst uam                  # cosechar una institución ya dada de alta
acervo juridico --inst uam --tema deportes  # selección temática (N15)            ← v3
acervo juridico --inst uam --desde-cero
acervo juridico --todas --regimen autonoma_estatal
acervo plantilla juridico                   # genera ficha.docx vacía
acervo cola                                 # cola manual pendiente, por severidad
acervo vigilar                              # diff de índices; reporta qué cambió
acervo resolver <id_cola>
acervo instituciones add ...

# --- modo académico ---
acervo academico lista.docx
acervo academico --lote <lote_id>
acervo informe --lote <lote_id>

# --- comunes ---
acervo estado --inst uam | --lote <lote_id>
acervo exportar --inst uam                  # NormativeRecord como JSONL para la fase RAG
acervo exportar --lote <lote_id>
```

### `--tema` (v3)

- Acepta varios: `--tema deportes --tema "actividad fisica"`.
- **Muestra las excluidas antes de descargar**, con su razón, y pide confirmación. `01` v2.7 lo
  exige mientras el filtro no tenga oráculo: es juicio de agente sin forma de medirlo.
- **La última selección por institución se recuerda** en `selecciones`, para que
  `acervo estado --inst uam` pueda decir qué se descargó y qué quedó fuera.
- **Sin `--tema`, nada cambia:** se traducen todas las entradas del catálogo, como hasta la v2.
- **Nunca altera el `CoverageReport`** (`04` v3, criterio 14).

### El menú

`acervo` sin argumentos abre un menú de terminal: modo, archivo, confirmación, avance por
encargo, cierre con el resumen.

**Regla del menú: no hace nada que los comandos no hagan.** Cada opción llama a la misma función
que su comando. Con `typer` y `rich` basta: sin librerías nuevas.

**`vigilar` es el comando que justifica el proyecto a largo plazo.** Corre semanal, compara
hashes de índice, y reporta: *"la UAM consolidó de nuevo el 12 de octubre; 3 reglamentos
cambiaron de fecha; 1 nuevo; 1 abrogado."* Barato porque no llama al LLM salvo donde detectó
cambio. **Solo modo jurídico.**

---

## Criterios de aceptación

### Modo jurídico (v1)

1. **Extremo a extremo con UAM:** `acervo juridico --inst uam` desde cero produce un corpus
   completo en una sola invocación. El índice trae **47 enlaces** y **31 instrumentos vigentes**;
   el objetivo es ≥ 28 `NormativeRecord` verificados. *(v3: la v2 decía «45 enlaces».)*
2. **Idempotencia:** segunda corrida idéntica no descarga nada, no crea filas, y hace **cero
   llamadas al LLM**. Se verifica en `HarvestStats.llamadas_llm == 0`.
3. **Continuidad ante fallo:** con el Corroborador deliberadamente roto, la corrida termina,
   entrega catálogo y descargas, y reporta el fallo. No lanza excepción.
4. **Detección de cambio:** se altera a mano el HTML del índice guardado; `vigilar` detecta la
   diferencia y solo entonces dispara el Lector.
5. **Tres universidades medidas:** el flujo corre sobre UAM, UNAM (sitio OAG) y UJAT, y
   **ninguna tumba el proceso**. Una cuarta estatal pequeña puede terminar con catálogo vacío y
   cola manual poblada: eso también es éxito (D7).
6. **Exportación:** el JSONL valida contra N7 y basta para que un sistema aguas abajo trocee sin
   volver a tocar la red.
7. **Coste medido:** `HarvestStats` reporta llamadas y coste por universidad, con tope verificado.
8. **Prueba desde la raíz del repo:** la CLI se ejecuta a mano una vez desde la raíz, con el
   `.env` real presente, antes de firmar la fase. (Lección A11: los tests se aíslan con
   `chdir(tmp_path)` y **nunca ven el `.env` real**.) Aplica al comando y al menú.

### Modo académico y comunes (v2)

9. **Extremo a extremo académico:** en una sola invocación se produce un `BatchReport` donde cada
   ficha aparece en **exactamente uno** de los tres grupos, y `cuadra_balance` se calcula cuando
   la lista declara balance.
   *(v3: la v2 fijaba este criterio sobre `Geologia_dois_.docx` y sus 17 fichas. **Ese archivo
   nunca llegó al repositorio** (`01` v2.5, M30), así que el criterio era inverificable. La
   entrada medida es `datos/lotes/bloque-a.txt`, 8 fichas, E15. El caso de `cuadra_balance=False`
   necesita una lista que declare su propio balance: **queda pendiente de material**.)*
10. **Idempotencia académica:** la segunda corrida con el mismo archivo hace **cero llamadas al
    LLM, cero peticiones** y no crea archivos ni filas. Se verifica con `pytest-httpx` sin
    respuestas registradas.
11. **Un artículo, varios lotes:** una segunda lista que repite un artículo ya verificado no lo
    pide ni lo verifica otra vez.
12. **Continuidad académica:** con el Verificador Académico roto, el lote termina, los
    descargados aparecen en `con_observaciones` con «sin verificar», y no se lanza excepción.
13. **Ficha jurídica:** una ficha sin `entidad_federativa` produce un error que nombra ese campo
    y **cero peticiones**. La plantilla llenada con los datos de la UAM se lee como
    `InstitutionRef` válido.
14. **Menú = comandos:** recorrer el menú con entradas simuladas llama a la misma función, con
    los mismos argumentos, que el comando equivalente.
15. **Cliente HTTP único:** un test verifica que `Fetcher`, `RobotsCache` y el cruce de vestíbulo
    reciben el mismo `httpx.Client`, y que `/robots.txt` lleva el User-Agent configurado.
16. **Base v2:** en base limpia existen las tablas de §Persistencia; el `Store` escribe descargas
    en `descargas` y el criterio 11 de `05` sigue pasando.

### v3 — lectura, escritura, selección y guardias

17. **`Catalog` se persiste entero:** tras una corrida, la fila de `lecturas` trae
    `fecha_corte_declarada`, `fecha_corte_texto`, `catalogo_caducado`, `enlaces_vistos`,
    `enlaces_descartados`, `enlaces_sin_cuenta`, `lectura_incompleta`, `fallo_lector` y
    `lector_agotado`. **Caso obligatorio, el de la UACAM:** se relee la fila y
    `catalogo_caducado=True` con su texto literal, `&nbsp;` ya colapsado. Si cualquiera de los
    nueve campos no sobrevive al viaje, el criterio 13 de `04` queda sin base.
18. **Una extracción incompleta no escribe:** con `fallo_lector="salida_invalida"` o
    `lectura_incompleta=True`, hay **una fila en `lecturas` y cero en `catalogo`**; y una fila
    buena de `catalogo` de una corrida anterior queda **idéntica, `capturado_en` incluido**. Es
    el test de M35 trasplantado, y su motivo es E17.
19. **Selección temática:** `--tema deportes` sobre la UAM produce una fila en `selecciones` cuyas
    `incluidas` + `excluidas` suman **exactamente 47**, sin solaparse; se traducen a `Encargo`
    solo las incluidas; **cero `ManualQueueItem` por las excluidas**; y el `CoverageReport` es
    idéntico al de la corrida sin `--tema`. Sin la bandera, se traducen las 47.
20. **Guardia de slug:** con `meta.slug_version` distinta de la del código, `acervo juridico`
    **se detiene antes de la primera petición de red** y el mensaje nombra las dos versiones y el
    remedio. Con base vacía, escribe la versión y sigue. Con versiones iguales, no estorba. Se
    prueba con `pytest-httpx` sin respuestas registradas: **cero peticiones** en el caso que se
    detiene.
21. **Toda corrida deja log:** tras cualquier comando existe un archivo bajo `logs/` con la
    salida, y su ruta se imprimió al terminar. Con `logs/` no escribible, la corrida **termina
    igual** y avisa. Motivo: las nueve corridas de la UNAM sin `tee`.

---

## Preguntas abiertas (agenda de esta conversación)

1. **Frecuencia de `vigilar`.** Propuesta: semanal, y a demanda. Las universidades reforman en
   bloque tras sesiones de sus órganos colegiados, no continuamente.
2. **¿Paralelismo entre universidades?** El rate limit es por dominio, así que dominios distintos
   no colisionan. Propuesta: 4 universidades en vuelo.
3. **Presupuesto global de LLM por corrida completa.** Tope duro que aborte antes de gastar de
   más.
4. **¿Qué pasa cuando un `doc_slug` desaparece del índice?** Propuesta: `desconocido` + cola
   manual. Desaparecer de un índice no es un acto jurídico.
5. **Formato de exportación hacia la fase RAG.** JSONL de N7 + carpeta de PDFs. Confirmar antes
   de cerrar la fase.
6. **Formato del informe académico para el usuario.** Propuesta: **Markdown** junto al JSON.
7. ~~**Dos archivos con el mismo `doc_id` y bytes distintos.**~~ **Ratificada en `06` v4:** ambos
   quedan en `descargas`; el `NormativeRecord` apunta al primero aprobado; **nunca se borra
   ninguno.**
8. **Presupuesto de LLM por lote.** El mismo mecanismo de la pregunta 3, con tope por lote.
9. **Ratificar la regla de `salida_invalida`** (v3). La propuesta de §El flujo es: un reintento,
   no saltar de eslabón, escribir solo la lectura, y un ítem de cola manual que nombre nuestro
   propio fallo. **Lo que está en duda es el reintento**, y no hay medición porque el agente del
   Lector todavía no existe. **Decidir antes de implementarlo, o quedará decidido por omisión.**
10. **¿La guardia de slug basta, o hace falta `acervo base reiniciar`?** (v3.) La guardia detiene
    la corrida, pero el remedio sigue siendo manual: respaldar, vaciar `data/`, borrar la base.
    ¿Conviene un comando que lo haga con confirmación explícita y respaldo automático? **A favor:**
    es un procedimiento que se va a repetir y que, hecho a medias, duplica el corpus. **En contra:**
    un comando que borra es un comando que alguien correrá por error.
11. **¿Dónde viven los artefactos de evaluación del Lector?** (v3.) El criterio 20 de `03` pide
    persistir la tabla de enlaces reducida, la respuesta cruda del agente, el prompt y el modelo
    con su versión. ¿Tabla, o archivos bajo `logs/`? **Propuesta: archivos**, porque la respuesta
    cruda puede ser grande y no se consulta por columnas. Decidir junto con el bloque del agente.

---

## Registro de consideraciones diferidas

### CD-07-1 · `lecturas` no guarda la tabla de enlaces que se le dio al agente

**Anotado en:** v3 (2026-10-04). **Estado:** aceptado a sabiendas.

`lecturas` guarda `enlaces_vistos` como conteo y `enlaces_sin_cuenta` como lista, pero **no la
tabla de enlaces reducida** que el Lector entregó al agente. Por tanto la contabilidad de una
corrida pasada **no se puede recalcular** sin volver a leer el índice. Es la contraparte de
CD-03-1 y CD-04-1, y las tres se cierran con la misma solución.

**Gatillo:** la primera vez que haga falta auditar una contabilidad vieja — por ejemplo, tras
cambiar `classify.py` y querer saber si el denominador se movió.

**Solución cuando se dispare:** persistir la tabla reducida junto a los artefactos de evaluación
(pregunta 11), y que `lecturas` la referencie por ruta.
