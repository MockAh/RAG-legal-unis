# 07 · Spec — Orquestación, persistencia y CLI

> Conversación: "Fase Orquestación". Leer antes `00` v2.0 y `01` v2.2 (todos los contratos).
> Estado: **v2** · **código convencional.** Parte se construye al principio (persistencia, junto
> con la spec 05) y parte al final (orquestación completa).
> **v2 (2026-09-10):** Acervo tiene dos modos (`00` §3). Esta spec cose los dos, les da una
> sola base y una sola CLI, y resuelve la deuda CD-05-2 de `05`.

---

## Qué cambia en la v2 (leer primero)

| Cambio | Sección |
|---|---|
| Flujo académico `procesar_lote` junto al jurídico `cosechar` | El flujo |
| Traducción a `Encargo` como paso explícito de ambos flujos | El flujo |
| Ficha jurídica en `.docx` leída por código, con plantilla | Entradas en `.docx` |
| Tablas nuevas; `documentos` de v1 se divide en `descargas` (común) y `documentos` (jurídico) | Persistencia |
| CLI `acervo` con un comando por modo y un menú que no hace nada que los comandos no hagan | CLI |
| Un solo `httpx.Client` para fetch, robots y vestíbulo (CD-05-2) | Cliente HTTP único |
| Criterios 9–16 | Criterios |

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
    # 1. Localizar (agente) — se salta si ya hay fuentes válidas en DB
    # 2. Leer índice (agente) sobre las candidatas, en orden de confianza,
    #    hasta obtener un Catalog no vacío
    # 3. Corroborar (agente) — puede disparar búsquedas extra (Ley Orgánica)
    # 4. Traducir cada CatalogEntry pendiente a Encargo (juridico/traduccion.py)   ← v2
    # 5. Descargar (código) todo lo que falte o haya cambiado
    # 6. Verificar (agente) lo recién descargado
    # 7. Consolidar NormativeRecord + poblar cola manual
```

### Modo académico (v2)

```python
def procesar_lote(lista: Path, settings: Settings) -> BatchReport:
    # 1. Hash del archivo → lote_id. Si el lote ya fue leído, se reutiliza su ArticleBatch
    # 2. Leer lista (agente Lector de Lista) → ArticleBatch; incompletos quedan anotados
    # 3. Para cada ficha válida:
    #      - articulo_id con veredicto correcto ya registrado (de este u otro lote) → no se pide
    #      - sin puertas → no obtenido, motivo sin_puertas
    #      - si no → traducir a Encargo (academico/traduccion.py) y descargar (código)
    # 4. Verificar (agente Verificador Académico) lo recién descargado → ArticleVerdict
    # 5. Auditar (código Auditor de Lote) → BatchReport; guardar y mostrar
```

**Los dos flujos comparten el paso de descarga, y nada más.** Ninguno llama piezas del otro
modo.

**Regla de continuidad:** el fallo de una pieza no aborta la corrida. Un catálogo sin
corroborar sigue siendo un catálogo útil. Cada paso que falla deja rastro en `HarvestStats` y
en la cola manual, y el flujo continúa hasta donde pueda.

**Regla de economía:** los pasos con LLM se saltan si su entrada no cambió. Re-cosechar una
universidad cuyo índice es idéntico al de la semana pasada debe costar **cero llamadas al
modelo** — solo un GET y un diff. Esto es lo que hace viable la vigilancia periódica.

**En modo académico, las mismas dos reglas (v2):**
- *Continuidad:* si el Verificador Académico falla, el lote termina igual; lo descargado va a
  `con_observaciones` con `veredicto=None` y nota «sin verificar» (`01` v2.2). Si falla el
  Lector de Lista, no hay fichas: el informe lo dice y la corrida termina sin excepción.
- *Economía:* re-procesar la misma lista cuesta **cero llamadas al modelo y cero peticiones**:
  el hash del archivo reutiliza el lote, y cada artículo ya verificado se salta. Un artículo
  verificado en un lote no se vuelve a pedir ni a verificar en otro.

---

## Entradas en `.docx` (v2)

**Ficha jurídica → `InstitutionRef` (N0): la lee código, no un agente.** Es un formulario, no
un texto libre: una tabla de dos columnas (campo, valor) o renglones `campo: valor`. Claves
aceptadas: `inst_id`, `nombre_oficial`, `entidad_federativa` (obligatorias) y `siglas`,
`regimen`, `dominio_raiz`, `sujeto_obligado_pnt`, `notas` (opcionales). Si falta una
obligatoria, **no hay corrida**: el error nombra exactamente qué campo falta. `acervo plantilla
juridico` genera la ficha vacía para llenarla.

**Lista académica → `ArticleBatch` (N12): la lee un agente.** Es texto libre escrito por
personas (medido: renglones sin título, DOIs dentro de enlaces, extras y correcciones mezclados;
`01` §Modo académico). Por eso no tiene plantilla: se acepta como venga.

Lectura de `.docx` con `python-docx`. Se extrae texto **y enlaces**: en una lista, la URL real
de un hipervínculo puede no coincidir con el texto visible, y la puerta es la URL real (D3).

---

## Persistencia

```
— comunes —
encargos           espejo de N10, PK encargo_id; incluye modo, grupo_alias
descargas          espejo de N5, PK (encargo_id, sha256); índice por grupo_alias (alias por hash)
intentos           espejo de IntentoPuerta, FK encargo_id, una fila por puerta pedida

— modo jurídico —
instituciones      espejo de N0
fuentes            espejo de N1, con validez y último uso
catalogo           espejo de N2, PK entry_id (formato v2.0: inst_id:doc_slug:url_id)
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

**Por qué `documentos` se divide (v2).** En v1 mezclaba la descarga (N5) con el consolidado
jurídico (N6 + N7). Una descarga académica no es un `NormativeRecord`, y no puede vivir en una
tabla cuya clave es `doc_id`. La parte de descarga pasa a `descargas`, común; `documentos`
conserva solo lo jurídico. **Es un paso de la migración de `05`:** el `Store` ya implementado
escribe hoy en `documentos`, y se renombra al rehacer la base limpia (`01` §Migración). No se
migran filas viejas.

**Por qué `lote_articulos` es tabla aparte.** Un mismo artículo puede pedirse en varias listas
con distinto número y distinta redacción. El artículo es uno; sus apariciones son muchas.

**Por qué `veredictos` lleva `sha256` en la clave.** El veredicto es sobre un archivo concreto.
Si otra puerta trae otra edición del mismo artículo, merece su propio sello.

**`indices_capturados` es la pieza no obvia y la más importante.** Guardar el hash del índice
(y opcionalmente el HTML reducido) convierte la detección de reformas en una operación de un
GET: si el hash cambió, algo pasó; si no, no hay nada que hacer. Sin esta tabla, cada corrida
periódica cuesta un LLM por universidad.

**Reglas heredadas del proyecto hermano:**
- `upsert` por clave primaria; re-ejecutar no duplica.
- Textos en UTF-8 intactos, con acentos y eñes. Solo las *claves* se normalizan; los títulos
  almacenados conservan su ortografía.
- Toda frontera modelo→persistencia convierte a tipos nativos de Python.
- Tras cada corrida cara, respaldo inmediato de la base.

---

## Cliente HTTP único (v2 · resuelve CD-05-2)

La orquestación construye **un solo `httpx.Client`** con User-Agent, timeouts y TLS estricto
desde `Settings`, y lo inyecta a `Fetcher`, `RobotsCache` y al cruce de vestíbulo. Ningún
módulo crea su propio cliente ni recibe una función suelta para pedir.

Es la solución anotada en CD-05-2: allá se olvidó el UA en el fetcher de robots, y la v3 de `05`
añade un tercer llamador (el enlace del vestíbulo). Con un cliente único, el UA se pone una vez
y ningún llamador puede olvidarlo.

---

## CLI

**v2: el comando se llama `acervo`** (entrada de script en `pyproject.toml`; `python -m acervo`
equivale). Renombrar el paquete interno de Python **no es obligatorio**: el nombre visible es el
comando.

```bash
acervo                                      # menú interactivo (ver abajo)

# --- modo jurídico ---
acervo juridico ficha.docx                  # alta desde la ficha + cosecha
acervo juridico --inst uam                  # cosechar una institución ya dada de alta
acervo juridico --inst uam --desde-cero
acervo juridico --todas --regimen autonoma_estatal
acervo plantilla juridico                   # genera ficha.docx vacía
acervo cola                                 # cola manual pendiente, ordenada por severidad
acervo vigilar                              # diff de índices; reporta qué cambió
acervo resolver <id_cola>                   # marcar un ítem de cola manual como resuelto
acervo instituciones add ...                # alta manual de un InstitutionRef

# --- modo académico ---
acervo academico lista.docx                 # procesa un lote de principio a fin
acervo academico --lote <lote_id>           # re-ejecuta un lote (idempotente)
acervo informe --lote <lote_id>             # muestra el BatchReport en tabla

# --- comunes ---
acervo estado --inst uam | --lote <lote_id>
acervo exportar --inst uam                  # NormativeRecord como JSONL para la fase RAG
acervo exportar --lote <lote_id>            # BatchReport JSON + informe legible
```

### El menú

`acervo` sin argumentos abre un menú de terminal:

1. **¿Qué modo?** Jurídico (ficha de universidad) o académico (lista de artículos).
2. **¿Qué archivo?** Pide la ruta del `.docx`, comprueba que existe y que es `.docx`.
3. **Confirmación.** Jurídico: muestra la institución leída de la ficha. Académico: muestra
   cuántas fichas detectó el Lector y cuántas quedaron incompletas, antes de descargar nada.
4. **Avance.** Una línea por encargo con su resultado (descargado, vestíbulo, muro, fallo).
5. **Cierre.** Jurídico: resumen de `HarvestStats`. Académico: el informe en tres grupos, con
   el aviso si el balance declarado por la lista no cuadra.

**Regla del menú: no hace nada que los comandos no hagan.** Cada opción llama a la misma función
que su comando. El menú es para quien no recuerda los comandos; los comandos, para scripts y
tests. Con `typer` y su dependencia `rich` basta: sin librerías nuevas.

**`vigilar` es el comando que justifica el proyecto a largo plazo.** Corre semanal, compara
hashes de índice, y reporta: *"la UAM consolidó de nuevo el 12 de octubre; 3 reglamentos
cambiaron de fecha; 1 nuevo; 1 abrogado."* Barato porque no llama al LLM salvo donde detectó
cambio. **Solo modo jurídico:** el académico no vigila; una lista se procesa cuando el usuario
la trae.

---

## Criterios de aceptación

### Modo jurídico (v1)

1. **Extremo a extremo con UAM:** `cosechar --inst uam` desde cero produce un corpus completo
   con ≥ 28 `NormativeRecord` verificados, en una sola invocación.
2. **Idempotencia:** segunda corrida idéntica no descarga nada, no crea filas, y hace **cero
   llamadas al LLM**. Se verifica en `HarvestStats.llamadas_llm == 0`.
3. **Continuidad ante fallo:** con el Corroborador deliberadamente roto, la corrida termina,
   entrega catálogo y descargas, y reporta el fallo. No lanza excepción.
4. **Detección de cambio:** se altera a mano el HTML del índice guardado; `vigilar` detecta la
   diferencia y solo entonces dispara el Lector.
5. **Tres universidades medidas:** el flujo completo corre sobre UAM, UNAM (sitio OAG) y
   UJAT, y **ninguna tumba el proceso**. Las tres deben terminar con catálogo poblado. Una
   cuarta universidad estatal pequeña, sin medir, puede terminar con catálogo vacío y cola
   manual poblada: eso también es éxito, no fallo (D7).
6. **Exportación:** el JSONL exportado valida contra N7 y basta para que un sistema aguas
   abajo trocee sin volver a tocar la red.
7. **Coste medido:** `HarvestStats` reporta llamadas y coste estimado por universidad. Se fija
   un tope y se verifica que no se rebase.
8. **Prueba desde la raíz del repo:** la CLI se ejecuta a mano una vez desde la raíz, con el
   `.env` real presente, antes de firmar la fase. (Lección A11 del proyecto hermano: los tests
   se aíslan con `chdir(tmp_path)` y por eso **nunca ven el `.env` real**; el aislamiento que
   protege los tests es lo que oculta el fallo del entorno. Se necesita `extra="ignore"` en el
   `SettingsConfigDict`.) **v2: aplica igual al comando `acervo` y al menú.**

### Modo académico y comunes (v2)

9. **Extremo a extremo académico:** `acervo academico Geologia_dois_.docx`, en una sola
   invocación, produce un `BatchReport` donde **las 17 fichas** aparecen cada una en
   exactamente uno de los tres grupos, y `cuadra_balance=False` (la lista declara 12 de 15 con
   copia libre; son 11).
10. **Idempotencia académica:** la segunda corrida con el mismo archivo hace **cero llamadas al
    LLM, cero peticiones de red** y no crea archivos ni filas. Se verifica en el informe y con
    `pytest-httpx` sin respuestas registradas.
11. **Un artículo, varios lotes:** una segunda lista que repite un artículo ya verificado no lo
    pide ni lo verifica otra vez, y su informe lo muestra como verificado.
12. **Continuidad académica:** con el Verificador Académico deliberadamente roto, el lote
    termina, los descargados aparecen en `con_observaciones` con «sin verificar», y no se lanza
    excepción.
13. **Ficha jurídica:** una ficha sin `entidad_federativa` produce un error que nombra ese campo
    y **cero peticiones**. La plantilla generada por `acervo plantilla juridico`, llenada con los
    datos de la UAM, se lee como un `InstitutionRef` válido.
14. **Menú = comandos:** para cada modo, recorrer el menú con entradas simuladas llama a la misma
    función, con los mismos argumentos, que el comando equivalente.
15. **Cliente HTTP único:** un test verifica que `Fetcher`, `RobotsCache` y el cruce de
    vestíbulo reciben el mismo objeto `httpx.Client`, y que la petición a `/robots.txt` lleva el
    User-Agent configurado. Cierra CD-05-2.
16. **Base v2:** en base limpia existen las tablas de §Persistencia; el `Store` escribe descargas
    en `descargas` y el criterio 11 de `05` (migración sin regresión) sigue pasando.

---

## Preguntas abiertas (agenda de esta conversación)

1. **Frecuencia de `vigilar`.** ¿Semanal? Las universidades reforman en bloque tras sesiones
   de sus órganos colegiados, no continuamente. Propuesta: semanal, y a demanda.
2. **¿Paralelismo entre universidades?** Cosechar 40 universidades en serie es lento; en
   paralelo es agresivo con los servidores. El rate limit es por dominio, así que dominios
   distintos no colisionan. Propuesta: 4 universidades en vuelo.
3. **Presupuesto global de LLM por corrida completa.** Fijar tope duro que aborte antes de
   gastar de más.
4. **¿Qué pasa cuando un `doc_slug` desaparece del índice?** ¿Se asume abrogado o se marca
   `desconocido`? Propuesta: `desconocido` + cola manual. Desaparecer de un índice no es un
   acto jurídico.
5. **Formato de exportación hacia la fase RAG.** JSONL de N7 + carpeta de PDFs. Confirmar que
   basta antes de cerrar la fase.
6. **Formato del informe académico para el usuario (v2).** El `BatchReport` se guarda en JSON;
   ¿qué versión legible se entrega? Propuesta: **Markdown** junto al JSON, porque se lee en
   cualquier editor y se versiona. Si el usuario trabaja siempre en Word, un `.docx` es un paso
   más. Se decide con la primera corrida real.
7. ~~**Dos archivos con el mismo `doc_id` y bytes distintos (v2, `01` pregunta 4).**~~
   **Ratificada (2026-09-10, en `06` v4):** ambos quedan en `descargas`; el `NormativeRecord` apunta al primero que
   el Verificador aprobó, y el otro se anota como copia equivalente. **Nunca se borra ninguno.**
8. **Presupuesto de LLM por lote (v2).** La pregunta 3 fija un tope por corrida jurídica; el
   modo académico necesita el suyo. Propuesta: el mismo mecanismo, con tope por lote.

---

## Registro de consideraciones diferidas

*(Se llena durante la implementación.)*
