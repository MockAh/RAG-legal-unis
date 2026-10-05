# 01 · Contratos de datos — Acervo

> **El documento más importante del Proyecto.** Las conversaciones no se ven entre sí;
> estos esquemas son su única frontera común. Cualquier cambio aquí debe propagarse
> a todas las conversaciones activas y anotarse en el changelog de abajo.
> Estado: **v2.7** · esquemas en pseudocódigo Pydantic v2. **La v2.0 fue la primera versión que
> rompió compatibilidad** (ver §"Qué rompe la v2.0 y cómo se migra"). Desde ahí vuelve a regir la
> regla de siempre: las specs refinan sin romper; los cambios aditivos son libres; renombrar o
> quitar campos exige actualizar aquí primero.

---

## Qué cambia en la v2.0 (leer primero)

El sistema deja de tener un solo uso. Se llama **Acervo** y tiene dos modos que comparten el
mismo Descargador: el **modo jurídico** (lo que hasta la v1.4 era todo el proyecto, y que
conserva el nombre **LegisUni**) y el **modo académico** (descargar y verificar artículos
científicos a partir de una lista).

| Cambio | Tipo | Dónde |
|---|---|---|
| Vocabularios nuevos: `Modo`, `TipoPuerta`, `Relacion`; `MotivoFallo` extraído y ampliado | aditivo | Vocabularios |
| `CatalogEntry.entry_id` incorpora la dirección de origen — **resuelve C20** con la salida B | **rompe** | N2 |
| Contrato común nuevo `Encargo`: lo único que recibe el Descargador | aditivo | N10 |
| `DownloadResult.entry_id` → `encargo_id`; campos nuevos `modo`, `puerta_usada`, `intentos`, `duplicado_de` | **rompe** (renombre) + aditivo | N5 |
| `NormativeRecord.entry_id` nuevo | aditivo | N7 |
| Modo académico: `ArticleRef`, `ArticleBatch`, `ArticleVerdict`, `BatchReport` | aditivo | N11–N14 |
| Parámetros: ruta en disco generalizada, puertas múltiples, cruce de vestíbulo, muros, alias por hash, revisión académica, confiabilidad académica, idioma por modo | mixto | Parámetros |

**Decisiones tomadas en la conversación «Acervo: modo académico» (2026-09-10):** orden de
recogida mínima (quién la pide, puertas en orden, cajón, etiqueta); identidad de la foto por
dirección de origen (C20, salida B) con alias por hash; ficha del artículo; extras y
correcciones como sobres independientes; recibo con puerta usada y motivo por puerta; sellos
del notario académico; confiabilidad académica por DOI y título; nombres **Acervo** y
**Encargo**.

### Nombres de trabajo

La conversación de diseño usó una metáfora. Se deja aquí para que el vocabulario no se pierda:

| Nombre de trabajo | Pieza | Modo |
|---|---|---|
| Recepcionista | Lector de Índice (spec `03`) · Lector de Lista (spec nueva) | jurídico · académico |
| Mensajero | Descargador (spec `05`) | **común** |
| Notario | Verificador Documental (spec `06`) · Verificador Académico (spec nueva) | jurídico · académico |
| Auditor | Corroborador (spec `04`) · Auditor de Lote (spec nueva) | jurídico · académico |
| Orden de recogida | `Encargo` (N10) | común |
| Puerta | `Puerta` (N10): una dirección donde puede estar el documento | común |
| Vestíbulo | Página HTML intermedia que enlaza al archivo (PMC, repositorios, editoriales) | común |
| Sobre | El archivo descargado | común |
| Archivero | `Store` y persistencia (spec `07`) | común |

### Mapa de contratos

```
MODO JURÍDICO (LegisUni)
  InstitutionRef N0 ─► Localizador ─► SourceCandidate N1 ─► Lector de Índice ─► CatalogEntry N2 / Catalog N3
                                                                              └► Corroborador ─► CoverageReport N4
  CatalogEntry N2 ──(selección temática N15, opcional)──► Encargo N10 ─► Descargador ─► DownloadResult N5
                                   ─► Verificador Documental ─► DocumentVerdict N6 ─► NormativeRecord N7
                                   (ManualQueueItem N8 · HarvestStats N9)

MODO ACADÉMICO
  lista (.docx) ─► Lector de Lista ─► ArticleRef N11 / ArticleBatch N12
  ArticleRef N11 ──traducción──► Encargo N10 ─► Descargador ─► DownloadResult N5
                                   ─► Verificador Académico ─► ArticleVerdict N13
                                   ─► Auditor de Lote ─► BatchReport N14
```

**Regla de reparto entre modos:** el Descargador no sabe en qué modo trabaja más allá de lo que
el `Encargo` le dice. Toda la diferencia entre modos vive en quien llena el `Encargo` y en
quien revisa lo descargado.

---

## Vocabularios controlados (usados por varios contratos)

```python
Modo = Literal["juridico", "academico"]   # v2.0

TipoNorma = Literal[
    "ley_organica",        # acto del Congreso que crea la universidad
    "estatuto",            # estatuto general / reglamento orgánico
    "reglamento",
    "lineamientos",
    "politicas",
    "criterios",
    "codigo",              # código de ética, de conducta
    "protocolo",
    "acuerdo",             # acuerdos rectorales / del Consejo
    "manual",
    "contrato_colectivo",
    "tabulador",
    "anexo",               # formatos y anexos de un instrumento mayor
    "otro",
]

# Jerarquía normativa. Menor número = mayor rango. Sirve para ordenar y para
# detectar huecos (no puede haber reglamentos sin estatuto).
JERARQUIA: dict[TipoNorma, int] = {
    "ley_organica": 1,
    "estatuto": 2,
    "reglamento": 3,
    "contrato_colectivo": 3,
    "lineamientos": 4, "politicas": 4, "criterios": 4,
    "codigo": 4, "protocolo": 4, "acuerdo": 4, "manual": 4, "tabulador": 4,
    "anexo": 5, "otro": 5,
}

EstadoVigencia = Literal[
    "vigente",     # versión actual
    "historico",   # versión anterior de un instrumento aún vigente
    "abrogado",    # instrumento derogado por completo
    "desconocido", # el índice no lo declara y no se pudo inferir
]

OrigenFuente = Literal[          # solo modo jurídico
    "sitio_institucional",   # eslabón 1 de D1
    "pnt_70i",               # eslabón 2
    "periodico_oficial",     # eslabón 3 (incluye DOF)
    "manual",                # cargado a mano por el usuario
]

Regimen = Literal["federal", "estatal", "autonoma_estatal", "tecnologico", "otro"]

TipoPuerta = Literal[            # v2.0
    "enlace_indice",   # jurídico: el enlace publicado en el índice institucional
    "copia_libre",     # académico: PDF de autor, PMC, repositorio institucional
    "oficial",         # académico: página de la editorial
    "resolutor_doi",   # académico: enlace doi.org, literal o construido desde un DOI literal (excepción a D3)
]

Relacion = Literal[              # v2.0 · solo modo académico
    "extra_recomendado",  # otro artículo que la lista sugiere junto a uno pedido
    "correccion",         # corrección / fe de erratas de un artículo pedido
]

MotivoFallo = Literal[           # extraído de N5 en v2.0; valores v1.x intactos
    "http_error", "no_es_pdf", "timeout", "robots_prohibido",
    "url_muerta", "demasiado_grande", "visor_de_terceros",
    # --- v2.0 ---
    "vestibulo_sin_pdf",   # la puerta dio HTML y no se halló en él un enlace a archivo aceptado
    "muro_de_pago",        # la puerta exige pago, suscripción o sesión
    "puertas_agotadas",    # el Encargo traía más de una puerta y todas fallaron
]
```

**Nota sobre `resolutor_doi` y D3 — excepción acotada (v2.0).** D3 prohíbe fabricar URLs. Se
admite **una sola excepción**: construir `https://doi.org/<doi>` cuando el DOI **aparece escrito**
en la lista. No es una dirección inventada: el identificador es literal y `doi.org` es el
resolutor oficial del sistema DOI. **Nada más se construye:** ni otros resolutores, ni rutas de
editorial deducidas, ni DOI adivinados. La puerta construida lleva `construida=True` (D5).
Sin esta excepción, una lista de DOIs sin enlaces no descargaría nada.

**Nota sobre `muro_de_pago`.** Solo se usa cuando la respuesta lo declara sin ambigüedad. En la
duda, el motivo es `vestibulo_sin_pdf`: un muro mal diagnosticado desanima a buscar una copia
que quizá existe. **El Descargador nunca intenta pasar un muro.**

**Nota sobre `puertas_agotadas`.** Con una sola puerta, el motivo del resultado es el de esa
puerta. Así el modo jurídico, que siempre lleva una, conserva exactamente sus motivos de v1.x.

---

## N0 · InstitutionRef — entrada del modo jurídico

*Sin cambios en v2.0. **Sin cambios en v2.7**: ver la nota al final.*

Lo único que el usuario debe proporcionar. **Regla de diseño: tres datos obligatorios, el
resto opcional y auto-completable por el Localizador.**

```python
class InstitutionRef(BaseModel):
    inst_id: str              # slug estable, minúsculas, sin acentos: "uam", "unam", "uanl"
    nombre_oficial: str       # "Universidad Autónoma Metropolitana"
    entidad_federativa: str   # "Ciudad de México" | "Nuevo León" | ...  (o "Federal")
    # --- opcionales: el Localizador los completa si faltan ---
    siglas: str | None = None
    regimen: Regimen | None = None
    dominio_raiz: str | None = None       # "uam.mx" — ancla de autenticidad (D9)
    sujeto_obligado_pnt: str | None = None
    notas: str | None = None              # p. ej. "su Ley Orgánica es federal, DOF 1973"
```

**Nota sobre `inst_id`:** es la raíz de todos los identificadores del modo jurídico y de sus
rutas en disco (`data/norm/<inst_id>/`). Se fija una vez y no cambia nunca.

**Nota sobre `dominio_raiz`:** es el ancla de D9. Si el Localizador no logra fijarlo con
certeza, ese solo hecho manda la institución a la cola manual: sin dominio verificado no hay
autenticidad posible.

**Nota sobre el filtro temático (v2.7).** Se consideró añadir aquí un campo `temas` y **se
descartó**. El tema pertenece a la **corrida**, no a la institución: la UNAM no «es de
deportes»; una petición concreta pide deportes. Un campo aquí lo volvería propiedad permanente
de un `InstitutionRef`, que es identidad estable. El filtro vive en `SeleccionTematica` (N15).

---

## N1 · SourceCandidate — salida del Localizador (spec 02)

*Sin cambios en v2.0.*

Una fuente propuesta. El Localizador devuelve **varias**, ordenadas por confianza.

```python
class SourceCandidate(BaseModel):
    inst_id: str
    url: str                  # DEBE haber aparecido en una búsqueda o como enlace (D3)
    origen: OrigenFuente
    titulo_pagina: str        # tal como lo devolvió la fuente
    dominio: str              # extraído de url; se compara contra dominio_raiz (D9)
    es_dominio_institucional: bool
    confianza: Literal["alta", "media", "baja"]
    razon: str                # por qué el agente cree que esta es la página de legislación
    descubierta_en: datetime
    evidencia_url: str        # la búsqueda o página desde la que se llegó a esta URL (D3)
```

**Regla dura (D3):** si el agente no puede llenar `evidencia_url` con algo que realmente
visitó, la candidata se descarta. No existe la URL "deducida por convención".

---

## N2 · CatalogEntry — una entrada del catálogo (spec 03)

*Cambia en v2.0: formato de `entry_id`. En v2.3: campo `titulo_derivado` (aditivo).
**Sin cambios en v2.7:** el filtro temático NO toca este contrato (ver N15).*

Lo que el Lector de Índice extrae de la página. **Es una promesa, no un documento**: describe
algo que debería existir en esa URL. Todavía no se ha descargado ni verificado nada.

```python
class CatalogEntry(BaseModel):
    entry_id: str             # f"{inst_id}:{doc_slug}:{url_id}"  — v2.0, ver nota abajo
    inst_id: str
    titulo: str               # literal del índice, sin normalizar
    tipo_norma: TipoNorma
    url_documento: str        # enlace directo al PDF/DOCX, crudo
    formato_declarado: str | None      # "pdf" | "docx" | None
    estado: EstadoVigencia
    vigente_hasta: date | None         # si el índice lo declara ("vigente hasta el X")
    fecha_publicacion: date | None
    fecha_ultima_reforma: date | None
    categoria_indice: str | None       # agrupador del propio sitio ("Personal Académico")
    origen: OrigenFuente
    url_indice: str                    # de qué página se extrajo (proveniencia, D5)
    titulo_derivado: bool = False      # v2.3 · True si titulo salió del nombre de archivo (ancla vacía)
    extraido_en: datetime
```

### Nota sobre `entry_id` (v2.0 · resuelve C20 de `08`)

Un `CatalogEntry` describe **una publicación concreta** de un instrumento: una *foto*, no la
*persona*. `doc_slug` nombra al instrumento a través del tiempo; `url_id` distingue la foto:

```python
url_id = sha256(url_normalizada.encode("utf-8")).hexdigest()[:12]
# url_normalizada: url_documento tras §Normalización de URL (Parámetros)
```

**El problema que resuelve (E11.6 de `08`).** La UAM publica dos versiones históricas del
Reglamento de Estudios Superiores. Con la v1.4 ambas producían `uam:res` y colisionaban. Con la
v2.0 son `uam:res:<12 hex>` y `uam:res:<otros 12 hex>`.

**Por qué la dirección y no la fecha.** Solo 1 de 4 universidades declara vigencia en su índice
(C2 de `08`): en las demás, la fecha de la foto no existe hasta que el Verificador abre el
archivo. Dos fotos publicadas, en cambio, siempre tienen direcciones distintas.

**Por qué la normalizada y no la cruda.** `acuerdos rect 2.pdf` y `acuerdos%20rect%202.pdf` son
la misma dirección (E12.2 de `08`) y deben dar la misma etiqueta. La cruda sigue guardándose
íntegra en `url_documento`.

**La trampa, y su remedio.** Las direcciones de la UAM **mueren en bloque** en cada
reconsolidación (spec `03`). Tras una, todas sus fotos cambian de `entry_id` aunque sean las
mismas. El remedio es el **alias por hash** (Parámetros): antes de dar por nueva una foto, se
compara su SHA-256 con los ya registrados del mismo `inst_id` + `doc_slug`. Si coincide, es la
misma foto con otra dirección: no se guarda otro archivo ni se crea otro registro.

**Límite conocido.** Si la universidad re-exporta el mismo texto, los bytes cambian (basta con
la fecha interna del PDF) y el hash ya no coincide. El alias no lo atrapa. La segunda línea de
defensa es `doc_id` (N7): mismo instrumento y misma fecha de versión leída por el Verificador.
Cómo se concilian dos archivos con el mismo `doc_id` se decide en `06`/`07`. **Nunca se borra
ninguno.**

**Segundo límite, medido (v2.7).** El alias **no cruza `grupo_alias`**, y `grupo_alias` lleva
`doc_slug` dentro. Si el `doc_slug` de un instrumento cambia —porque se corrige una heurística
defectuosa, o porque dos corridas lo nombraron distinto—, los mismos bytes se escriben otra vez
bajo un grupo nuevo. Está medido dos veces: los 9 `encargo_id` de la UAM con una fecha por slug
(E14.5) y los documentos de la UNAM cosechados con slugs escritos a mano (E21.15). **No es un
defecto del alias: es la consecuencia de que el slug sea parte de la identidad.** El remedio es
de procedimiento y vive en `03`: la primera corrida tras corregir slugs se hace sobre `data/`
vacío y base limpia.

**Lo que no cambia.** `doc_slug` sigue sin derivarse de la URL (spec `03`). Re-leer el mismo
índice produce los mismos `entry_id`, porque las direcciones son las mismas: el criterio de
idempotencia de `03` se mantiene.

### Nota sobre `doc_slug`

Identificador estable del instrumento *a través del tiempo*, no de la versión. **Cada sitio
tiene su propio mecanismo y no hay uno universal** (C4 de `08`): la UAM usa sufijos de archivo
(`-lo`, `-res`), la UNAM un prefijo numérico (`2-LeyOrganicaUNAM`,
`29-ReglamentoGeneralExamenes`), la UJAT ninguno. Estrategia: intentar el mecanismo del sitio;
si no hay, **fallback al título normalizado** (minúsculas, sin acentos, sin fechas). **Nunca de
la posición en la lista ni de la URL completa**, porque las URLs mueren en bloque en cada
consolidación.

### Nota sobre `estado`

El Lector lo llena solo con lo que el índice *declara*. Si dice "vigente hasta el 16 de marzo
de 2026", eso es `historico` + `vigente_hasta`. Si no declara nada, es `desconocido` — **nunca
se asume `vigente` por omisión**.

> **Medido (C2 de `08`): `desconocido` será el caso mayoritario.** Solo 1 de 4 universidades
> declara vigencia en su índice. En las otras tres, la fecha real solo existe dentro del PDF y
> la produce el Verificador Documental (N6), no el Lector.

### Nota sobre `titulo_derivado` (v2.3)

Medido en **2 de 4** instituciones (C9, E1.5, E10.3 de `08`): hay enlaces a documentos reales
sin texto de ancla. El Lector no los descarta: deriva `titulo` del nombre de archivo
(decodificado antes, E12.7) y marca `titulo_derivado=True`. **Un título derivado no es literal
del índice:** el Verificador Documental debe confirmarlo contra el propio documento antes de
consolidar. Sin este campo, la marca viviría en una nota libre que nadie filtra.

### Nota sobre `categoria_indice`

Es **pista, no dato** (D11). Medido en la UJAT (E4.1 de `08`): su Ley Orgánica y su Estatuto
General están archivados bajo "Otros documentos", y un Estatuto aparece bajo "Reglamentos". Se
conserva porque a veces es informativa, pero `tipo_norma` **nunca** se deriva de ella sin más:
se deriva del título del instrumento.

---

## N3 · Catalog — el catálogo completo de una institución

*Cambia en v2.3: campos de fecha de corte (aditivo). Cambia en v2.6: contabilidad de la lectura (aditivo).*

```python
class Catalog(BaseModel):
    inst_id: str
    entries: list[CatalogEntry]
    fuentes_usadas: list[SourceCandidate]
    generado_en: datetime
    lector_agotado: bool      # True si el Lector devolvió vacío y hubo que ir al respaldo
    notas: str | None         # "índice servido por rejilla JS; sin filas en el HTML"
    # --- v2.3 · fecha de corte del índice (D12, C13) ---
    fecha_corte_declarada: date | None = None   # la que declara la página
    fecha_corte_texto: str | None = None        # declaración literal: «Fecha de corte: Diciembre del 2016»
    catalogo_caducado: bool = False             # fecha_corte_declarada más vieja que el umbral
    # --- v2.6 · contabilidad de la lectura (C13: no mentir sin errores) ---
    enlaces_vistos: int | None = None          # enlaces únicos (URL normalizada) entregados al agente, tras classify.py; None = no hubo lectura
    enlaces_descartados: list[str] = []        # hrefs que el agente declaró explícitamente no normativos
    enlaces_sin_cuenta: list[str] = []         # vistos − (url_documento de entries) − descartados; lo calcula código, nunca el agente
    lectura_incompleta: bool = False           # enlaces_sin_cuenta no vacío (derivado, como catalogo_caducado)
    fallo_lector: Literal["salida_invalida"] | None = None   # el agente respondió, pero su JSON no validó
```

**Nota sobre la fecha de corte (v2.3).** Medido en la UACAM (E10.1 de `08`): un índice HTML
impecable declara al pie «Fecha de corte: Diciembre del 2016». Nada aguas abajo lo detecta.

- **Precisión de mes o año** («Diciembre del 2016», «2019») → se guarda el **último día** del
  periodo. Es la lectura más generosa con la universidad: si aun así resulta caducado, lo está
  sin discusión.
- **El texto literal se guarda siempre** (D5): la conversión a `date` es una interpretación y
  debe poder auditarse.
- **Sin declaración:** `catalogo_caducado=False` y los dos campos de fecha en `None`. La ausencia
  de fecha de corte no prueba frescura, pero tampoco caducidad.
- **No es `CatalogEntry.estado`.** Un índice caducado puede contener instrumentos vigentes: lo que
  caduca es la afirmación del índice sobre qué existe y qué está al día.
- **Qué se hace con un catálogo caducado** sigue abierto (`00` §8, pregunta 8).

**Nota sobre la contabilidad de la lectura (v2.6).** Hasta la v2.5, tres situaciones muy
distintas caían en `lector_agotado` + `notas`: la página es una rejilla JS y no trae nada; el
agente devolvió JSON inválido; el agente emitió 40 entradas de 47. Solo la primera es
agotamiento. La tercera es C13 otra vez: el sistema miente con confianza y sin errores, y el
Corroborador atribuiría a la universidad huecos que son del Lector.

| Caso | `lector_agotado` | `fallo_lector` | `lectura_incompleta` |
|---|---|---|---|
| Rejilla JS | `True` | `None` | `False` (0 vistos) |
| JSON inválido | `False`: no se salta de eslabón en D1 | `"salida_invalida"` | `True`: todo queda sin cuenta |
| 40 de 47 | `False` | `None` | `True`, y la lista dice cuáles faltan |

- **Vistos contra emitidos no basta.** En la UACAM, 83 enlaces a PDF (E20.5, corregido) contra los
  ~27 instrumentos propios que estima E10, aún sin medir: casi toda la diferencia es descarte
  legítimo. Por eso el agente **declara** lo que descarta (`enlaces_descartados`), y la resta la
  hace código (regla de reparto de `00` §2).
- **`lector_agotado` y `fallo_lector` son excluyentes.** Regla dura en `03`.
- **Listas, no conteos** (D5): el Corroborador necesita saber qué hueco es del Lector.
- **Qué hace la orquestación ante `salida_invalida`** (¿reintentar?) no se decide aquí: queda
  pendiente en `07`.

---

## N4 · CoverageReport — salida del Corroborador (spec 04)

*Sin cambios de esquema en v2.0 ni en v2.7. Solo modo jurídico.*

```python
class CoverageReport(BaseModel):
    inst_id: str
    completo: bool
    faltantes: list[Hueco]
    inesperados: list[str]         # entry_ids que no encajan en ninguna rúbrica esperada
    fuentes_cruzadas: list[OrigenFuente]   # contra qué se cotejó realmente
    confianza: Literal["alta", "media", "baja"]
    generado_en: datetime

class Hueco(BaseModel):
    rubrica: str              # clave del esqueleto esperado, ver spec 04
    tipo_norma_esperado: TipoNorma
    descripcion: str          # "no se halló Ley Orgánica"
    severidad: Literal["critico", "importante", "menor"]
    pista: str | None         # "buscar en Periódico Oficial de Nuevo León, ~1971"
```

**`severidad="critico"`** se reserva para lo que hace inservible al corpus: falta la Ley
Orgánica o falta el estatuto. Un corpus sin su norma fundante no puede sustentar nada.

**Nota sobre el filtro temático (v2.7).** `CoverageReport` se calcula **siempre sobre el catálogo
completo**, nunca sobre `SeleccionTematica.incluidas` (N15). Si se calculara sobre la selección,
`completo=True` no significaría nada: un catálogo de deportes «completo» sin su estatuto
habilitante sigue estando incompleto por construcción, que es justo lo que la comprobación de
jerarquía existe para cazar (C15).

---

## N5 · DownloadResult — salida del Descargador (spec 05)

*Cambia en v2.0: `entry_id` → `encargo_id`; campos nuevos; motivos nuevos. Común a ambos modos.*

```python
class IntentoPuerta(BaseModel):    # v2.0
    orden: int                     # posición de la puerta en Encargo.puertas (desde 0)
    url: str                       # la cruda de la Puerta
    url_pedida: str | None         # tras normalizar
    url_final: str | None          # tras redirecciones y, si hubo, tras cruzar el vestíbulo
    enlace_vestibulo: str | None   # enlace seguido dentro del vestíbulo (literal en la página, D3)
    http_status: int | None
    exito: bool
    motivo_fallo: MotivoFallo | None

class DownloadResult(BaseModel):
    encargo_id: str                # v2.0 · antes entry_id. Jurídico: = entry_id. Académico: = articulo_id
    modo: Modo                     # v2.0
    exito: bool
    ruta_local: Path | None        # data/<cajon>/<etiqueta>.<ext>
    sha256: str | None
    bytes: int | None
    content_type: str | None
    http_status: int | None        # de la puerta que abrió, o de la última intentada
    motivo_fallo: MotivoFallo | None = None
    capturado_en: datetime
    url_final: str | None          # tras redirecciones (proveniencia real, D5)
    puerta_usada: int | None       # v2.0 · orden de la puerta que entregó el archivo
    intentos: list[IntentoPuerta]  # v2.0 · una fila por puerta pedida, en orden
    duplicado_de: str | None       # v2.0 · encargo_id ya registrado con el mismo sha256 (alias por hash)
```

**Nota sobre `intentos`.** Es el recibo del mensajero: qué puerta abrió y por qué fallaron las
anteriores. Las puertas posteriores a la que abrió **no se piden** y no aparecen. Sin este
campo, un «no se pudo» del modo académico no diría si faltó la copia libre, si la editorial
tenía muro o si el repositorio no enlazaba el PDF, y el Auditor no podría sugerir una ruta.

**Nota sobre `duplicado_de`.** Cuando el alias por hash reconoce la foto, el resultado es
`exito=True`, `ruta_local` apunta al archivo que ya existía y `duplicado_de` lleva el
`encargo_id` original. No se escribe un archivo nuevo.

**`no_es_pdf`** cubre el caso medido en el proyecto hermano: la URL apunta a una *landing
page* HTML en vez del archivo. El guardián de los primeros bytes lo atrapa y ya demostró su
valor allá.

> **Aviso de nomenclatura (v1.3):** desde que se aceptan `.docx`, este valor significa
> **"el archivo no es de ningún formato aceptado"**, no literalmente "no es PDF". Un `.docx`
> legítimo ya **no** cae aquí; un `.xlsx`, un `.jpg` o una landing page HTML, sí. **El nombre
> del literal se conserva a propósito**: renombrarlo rompería la compatibilidad que las
> versiones de este documento se han comprometido a mantener, y el costo de un nombre
> ligeramente impreciso es menor que el de una migración. Quien lea un `no_es_pdf` en la cola
> manual debe entenderlo como *formato rechazado por el guardián*.
>
> **v2.0: tampoco se renombra**, aunque esta versión ya rompe compatibilidad. Cada ruptura
> se justifica por lo que resuelve; renombrar este literal no resuelve nada funcional y sí
> obligaría a tocar datos y pruebas del modo jurídico. El razonamiento de v1.3 sigue en pie.
>
> **Relación con `vestibulo_sin_pdf` (v2.0):** si el Encargo permite cruzar vestíbulos y la
> puerta devuelve HTML, el motivo es `vestibulo_sin_pdf` cuando no se halla enlace; si no lo
> permite (modo jurídico por defecto), el motivo sigue siendo `no_es_pdf`, como en v1.4.

**`visor_de_terceros`** (nuevo en v1.2) cubre un caso distinto y más delicado: **el documento
existe y es legítimo, pero el índice institucional enlaza a un visor externo en vez de al
archivo.** Medido en la UACAM (**E10.2 de `08`**, 2026-09-06): **cuatro** enlaces a
`drive.google.com/file/d/<id>/view`, que devuelve HTML con un panel de carga en lugar del
archivo.

Los cuatro son: el Formato ARCO, la Ley de Transparencia estatal, la Ley de Protección de
Datos Personales y —el único que es normativa propia de la universidad— los Lineamientos de
Protección de Datos Personales de la UACAM.

**Alcance honesto del hallazgo.** Aplicando el criterio de `08` §E8.2: el valor es **sólido en
existencia y débil en frecuencia**. Un solo caso obliga a manejarlo; cuatro documentos en una
de cuatro instituciones **no** autorizan a tratarlo como fenómeno extendido. Si futuras
mediciones lo encuentran en más sitios, se anota aquí; mientras tanto, es un modo de fallo
real pero marginal.

**Qué NO dice esta medición.** La Ley Orgánica de la UACAM **no** se sirve por visor: cuelga de
`etzna.uacam.mx`, subdominio institucional legítimo. Y su **Estatuto Orgánico no aparece en el
índice en absoluto** — es el hueco crítico de **E10.5**, el primero detectado en datos reales,
y lo caza la comprobación de jerarquía del Corroborador (spec `04`), no el Descargador.
Conviene tenerlo escrito porque son dos diagnósticos opuestos: un documento presente pero mal
servido se resuelve en un clic; uno ausente hay que ir a buscarlo a otra parte.

**Por qué el valor gana su sitio.** Sin él, esos documentos caerían en `no_es_pdf`, que es
engañoso: sugiere enlace roto o basura cuando lo que hay es un documento bueno tras una
pantalla. La distinción existe para que la cola manual (N8) pueda decir *"está en Google
Drive, ábrelo aquí"* en vez de *"falló: no es PDF"*. El primero se resuelve en segundos; el
segundo se ignora.

**Interacción con D9.** `drive.google.com` no es dominio institucional ni subdominio suyo. Aun
cuando el documento se recupere a mano, entra con autenticidad degradada y verificación
obligatoria: el ancla de autenticidad es el dominio, y aquí el dominio no acredita nada.

**Lo que este valor NO autoriza:** construir la URL de descarga directa a partir del `id`.
D3 sigue vigente. La salida correcta es la cola manual con la URL tal como la publicaba el
sitio. Si más adelante se decide resolver estos enlaces automáticamente, será una decisión
aparte y se anotará aquí.

**v2.0.** La distinción vale igual en modo académico: ahí la recoge `BatchReport.no_obtenidos`
(N14) con la URL del visor en `ruta_sugerida`. La interacción con D9 aplica solo al modo
jurídico; en el académico no hay ancla de dominio (Parámetros).

---

## N6 · DocumentVerdict — salida del Verificador Documental (spec 06)

*Sin cambios de esquema en v2.0. Solo modo jurídico. `entry_id` usa el formato nuevo de N2.*

```python
class DocumentVerdict(BaseModel):
    entry_id: str
    coincide_titulo: bool
    coincide_institucion: bool
    fecha_reforma_declarada: date | None    # la que dice el propio documento
    estado_inferido: EstadoVigencia
    veredicto: Literal["ok", "discrepancia", "documento_erroneo", "ilegible"]
    discrepancias: list[str]
    confianza: Literal["alta", "media", "baja"]
    evidencia: str          # el fragmento de la primera página en que se basó el juicio
```

**`documento_erroneo`** = el enlace apunta a otro instrumento (fallo real y frecuente en
sitios institucionales). **`discrepancia`** = es el documento correcto pero algún dato no
cuadra con el catálogo, típicamente la fecha.

---

## N7 · NormativeRecord — el registro consolidado del modo jurídico

*Cambia en v2.0: campo nuevo `entry_id` (aditivo).*

**Es la salida del modo jurídico y la herencia de la futura fase de chunking.** Un
`NormativeRecord` existe solo cuando el documento fue descargado Y verificado.

```python
class NormativeRecord(BaseModel):
    doc_id: str               # f"{inst_id}:{doc_slug}:{fecha_version}"  — ESTABLE
    entry_id: str             # v2.0 · qué foto del catálogo originó este registro
    inst_id: str
    doc_slug: str             # identidad del instrumento a través de versiones
    titulo: str
    tipo_norma: TipoNorma
    jerarquia: int            # de JERARQUIA[tipo_norma]
    estado: EstadoVigencia
    fecha_publicacion: date | None
    fecha_ultima_reforma: date | None
    vigente_hasta: date | None
    # --- proveniencia (D5) ---
    url_origen: str
    url_indice: str
    dominio: str
    origen: OrigenFuente
    capturado_en: datetime
    sha256: str
    ruta_local: Path
    # --- verificación (D6, D9) ---
    verificado: bool
    veredicto: Literal["ok", "discrepancia"]
    notas_verificacion: str | None
```

**Nota sobre `doc_id` y `entry_id` (v2.0).** Son dos identidades distintas y ambas hacen falta.
`entry_id` es la **foto publicada** (qué dirección, qué catálogo). `doc_id` es la **versión
jurídica** (qué instrumento, de qué fecha). Dos fotos con bytes distintos pueden resultar la
misma versión jurídica: ver "Límite conocido" en N2.

**Nota sobre `doc_id`:** lleva la versión dentro. Reformar un reglamento produce un
`NormativeRecord` **nuevo**, no una sobrescritura del anterior; el viejo pasa a
`estado="historico"`. Esto es deliberado: en derecho, la versión anterior no deja de existir,
deja de estar vigente. Una cita a una versión pasada debe seguir resolviendo.

**Regla de proveniencia (D5):** ninguna afirmación de un sistema aguas abajo puede citar algo
que no apunte a un `doc_id` real, y por él a un archivo con su `sha256`. Se cita el documento
concreto en su versión concreta, nunca "la ley".

---

## N8 · ManualQueueItem — la cola manual (D7)

*Sin cambios de esquema en v2.0. Solo modo jurídico.*

```python
class ManualQueueItem(BaseModel):
    inst_id: str
    que_falta: str            # "Ley Orgánica de la UANL"
    por_que: str              # "no aparece en sitio institucional ni en PNT"
    donde_buscar: str | None  # "Periódico Oficial del Estado de Nuevo León"
    entry_id: str | None      # si existe entrada de catálogo pero falló la descarga
    url_intentada: str | None
    severidad: Literal["critico", "importante", "menor"]
    creado_en: datetime
    resuelto: bool = False
```

**La cola manual es producto, no desecho.** Su calidad se mide: un ítem útil dice *qué*
documento falta por su nombre y *dónde* buscarlo. Un ítem que solo dice "falló la descarga"
no cumple.

**Caso `visor_de_terceros`:** cuando el fallo viene de un visor externo, `donde_buscar` debe
llevar la URL del visor y `por_que` debe decir que el documento existe pero está tras un
visor. Es el ítem de cola manual más barato de resolver que produce el sistema, y por eso
merece estar bien formado.

**Lo que NUNCA entra aquí (v2.7):** una entrada excluida por `SeleccionTematica` (N15). No es un
fallo del sistema, es una decisión del usuario. Mezclarlas vaciaría de sentido a esta cola, que
es producto.

**Modo académico (v2.0):** no usa esta cola. Ahí no hay institución ni severidad jurídica, y la
ruta de solución es otra (biblioteca, autor). Lo que falta vive en `BatchReport.no_obtenidos`
(N14).

---

## N9 · HarvestStats — telemetría de una corrida jurídica

*Sin cambios en v2.0. Solo modo jurídico; la telemetría académica vive en N14.*

```python
class HarvestStats(BaseModel):
    inst_id: str
    fuentes_propuestas: int
    fuentes_usadas: int
    entradas_catalogo: int
    descargas_ok: int
    descargas_fallidas: dict[str, int]     # motivo_fallo → conteo
    verificados_ok: int
    verificados_discrepancia: int
    cola_manual: int
    huecos_criticos: int
    duracion_s: float
    llamadas_llm: int
    costo_estimado_usd: float | None
```

**Nota (v2.7):** `entradas_catalogo` cuenta el catálogo **completo**, no la selección temática.
Una entrada excluida por tema no cuenta como descarga fallida en `descargas_fallidas`.

---

## N10 · Encargo — la orden de recogida (común) · v2.0

**Lo único que recibe el Descargador.** No lee `CatalogEntry` ni `ArticleRef`: cada modo
traduce su ficha a un `Encargo`. En código: `DownloadRequest`.

```python
class Puerta(BaseModel):
    url: str                  # cruda, tal como apareció (D3). Única excepción: resolutor DOI
    tipo: TipoPuerta
    url_base: str | None      # para resolver relativas. Jurídico: url_indice
    evidencia: str            # dónde apareció: url_indice | f"lista:{lote_id}#{posicion}"
    construida: bool = False  # v2.0 · True solo para la puerta doi.org armada desde un DOI literal

class Encargo(BaseModel):
    encargo_id: str           # jurídico: entry_id · académico: articulo_id
    modo: Modo
    solicitante: str          # quién lo pide. Jurídico: inst_id · académico: lote_id
    puertas: list[Puerta]     # en orden de preferencia; al menos una
    cajon: str                # relativo a data/. Jurídico: f"norm/{inst_id}" · académico: "papers"
    etiqueta: str             # nombre de archivo sin extensión; la extensión la deciden los bytes
    cruzar_vestibulos: bool   # jurídico: False · académico: True (ver Parámetros)
    grupo_alias: str          # v2.1 · ámbito del alias por hash. Jurídico: f"{inst_id}:{doc_slug}" · académico: articulo_id
    creado_en: datetime
```

### Traducción jurídica

```python
Encargo(
    encargo_id=entry.entry_id,
    modo="juridico",
    solicitante=entry.inst_id,
    puertas=[Puerta(url=entry.url_documento, tipo="enlace_indice",
                    url_base=entry.url_indice, evidencia=entry.url_indice)],
    cajon=f"norm/{entry.inst_id}",
    etiqueta=f"{doc_slug}__{fecha:%Y-%m-%d}",
    # fecha = fecha_ultima_reforma, o fecha_publicacion, o la fecha de creación del Encargo
    cruzar_vestibulos=False,
    grupo_alias=f"{entry.inst_id}:{doc_slug}",
    creado_en=ahora,
)
```

**Con esta traducción, el modo jurídico se comporta exactamente como en v1.4:** una puerta,
los mismos motivos de fallo, la misma ruta en disco. Esa es la prueba de que la migración no
rompió nada (§Migración).

**v2.7 · qué entradas se traducen.** Sin `SeleccionTematica`, **todas** las del catálogo, como
hasta la v2.6. Con una selección, solo las de `incluidas` (N15). La traducción en sí no cambia.

### Traducción académica

```python
Encargo(
    encargo_id=ficha.articulo_id,
    modo="academico",
    solicitante=ficha.lote_id,
    puertas=ficha.puertas,    # ya ordenadas por el Lector de Lista (ver N11)
    cajon="papers",
    etiqueta=f"{slug(ficha.primer_autor)}-{ficha.anio}__{sha256(ficha.articulo_id)[:8]}",
    cruzar_vestibulos=True,
    grupo_alias=ficha.articulo_id,
    creado_en=ahora,
)
```

**Por qué `cajon="papers"` sin lote.** Un mismo artículo pedido en dos listas es un solo
archivo. El lote dice quién lo pidió, no dónde vive.

**Por qué la etiqueta lleva autor y año.** Para que una persona reconozca el archivo en la
carpeta (`raup-1982__3f9a…pdf`). El hash corto es lo que lo hace único. En una corrección, sin
autor ni año propios, la etiqueta usa los del artículo corregido con el prefijo `corr-`.

---

## Modo académico

### Evidencia de partida

Todo lo que sigue se diseñó contra **una lista real**: `Geologia_dois_.docx`, recibida el
2026-09-10. Quince artículos pedidos, numerados con huecos entre 1 y 58, más un artículo extra
recomendado y una corrección. Tres hallazgos de esa lista moldearon los contratos:

1. **Ninguno de los 15 artículos pedidos trae título.** Cada renglón es del tipo
   *«Raup & Sepkoski (1982) — Science 215: 1501»*. Solo el extra (Marshall, 2025) lo trae.
2. **13 de 15 traen un DOI escrito**, suelto o dentro de un enlace. Los otros dos (Dal Corso
   2022, Wang & Marshall 2016) solo tienen enlaces de editorial sin DOI literal.
3. **La lista trae su propio balance y no cuadra.** Declara 12 de 15 con copia libre y nombra
   tres sin ella (31, 37, 44). Pero la 45 también declara no tener copia libre: son 11.

> **Nota (v2.5, 2026-09-25) — historia de diseño, no evidencia verificable.**
> `Geologia_dois_.docx` **nunca llegó al repositorio** (M30 de `PLAN-MIGRACION.md`). Los tres
> hallazgos de arriba no se pueden comprobar: se conservan porque explican de dónde salieron
> los contratos, no como medición. La primera corrida académica (E15 de `08`, 2026-09-25) usó
> `datos/lotes/bloque-a.txt`: 8 fichas del Bloque A, ya estructuradas.

---

## N11 · ArticleRef — la ficha del artículo (Lector de Lista) · v2.0

Lo que el Lector de Lista extrae de un renglón. Como `CatalogEntry`, **es una promesa, no un
documento**.

```python
class ArticleRef(BaseModel):
    articulo_id: str               # ver nota
    lote_id: str
    posicion_en_lista: str | None  # el número que traía la lista ("27"). Solo para el informe; nunca identidad
    referencia_literal: str        # el renglón tal cual venía, sin corregir
    primer_autor: str | None       # apellido, con su ortografía
    anio: int | None
    titulo: str | None
    doi: str | None                # normalizado (Parámetros), y solo si aparece literal en la lista
    autores: list[str] = []
    revista: str | None
    volumen: str | None
    pagina_inicial: str | None     # "1501", "e1700906", "eaat1327"
    puertas: list[Puerta]
    relacion: Relacion | None = None
    relacionado_con: str | None = None   # articulo_id del artículo al que acompaña
    extraido_en: datetime
```

### Identificación mínima

> **Ajuste a la decisión 3 — ratificado (2026-09-10).** La propuesta inicial fue «título, primer autor y
> año obligatorios». Contra la lista real, eso deja fuera **16 de 17** fichas: ningún
> artículo pedido trae título (hallazgo 1), y la corrección tampoco. Se adoptó en su lugar:

Una ficha es válida si trae **primer autor + año + al menos uno** de estos:

- **título**, o
- **DOI**, o
- **cita**: revista + volumen + página inicial.

Con esta regla, las 17 fichas de la lista real son válidas. La que no alcanza la identificación
mínima **no se descarga**: va a `ArticleBatch.incompletos` con su renglón literal.

> **Nota (v2.5):** las 17 fichas son las de `Geologia_dois_.docx`, que nunca llegó al repositorio
> (ver la nota de §Evidencia de partida). La afirmación no es verificable. La primera corrida
> académica usó `datos/lotes/bloque-a.txt` (8 fichas).

**Excepción para correcciones.** Una ficha con `relacion="correccion"` se identifica por lo que
corrige: basta `relacionado_con` + una puerta. `primer_autor` y `anio` pueden ir vacíos. En la
lista real, la corrección de Burgess et al. (2014) solo trae un enlace; exigirle autor y año
obligaría a inventarlos.

### Fichas sin puertas

Una ficha válida sin ninguna puerta (sin enlaces y sin DOI) **no genera `Encargo`**: va
directo a `BatchReport.no_obtenidos` con motivo `sin_puertas` y ruta sugerida «buscar por
título o cita». Con la excepción del resolutor, toda ficha con DOI tiene al menos una puerta.

### Nota sobre `articulo_id`

```python
articulo_id = f"doi:{doi}"                                 # si hay DOI
articulo_id = f"ref:{slug(primer_autor)}-{anio}-{h8}"      # si no
# h8 = sha256 del título normalizado, o de la cita normalizada si no hay título, [:8]
articulo_id = f"corr:{relacionado_con}:{h8_puerta}"         # corrección sin DOI propio
# h8_puerta = sha256 de la url normalizada de su primera puerta, [:8]
```

**Por qué no basta autor + año.** Dos artículos del mismo autor el mismo año colisionarían: es
el mismo patrón que C20, en otro modo.

**Por qué nunca la posición.** Los números de la lista (1, 4, 15… 58) son de quien la escribió.
Otra lista numerará distinto el mismo artículo.

### Nota sobre `doi` y D3

El DOI solo se toma si **aparece escrito** en la lista, suelto o dentro de un enlace
(`science.org/doi/10.1126/science.215.4539.1501` lo trae; `doi.org/10.1016/…` también).
**No se deduce por convenciones de URL:** `nature.com/articles/s43017-021-00259-4` no trae DOI
literal, y esa ficha queda sin DOI aunque uno sospeche cuál es. Por lo mismo, no recibe puerta
`resolutor_doi` construida.

### Nota sobre `puertas` y su orden

El Lector de Lista ordena: **copias libres primero**, en el orden en que aparecen en la lista;
**luego la oficial**; **al final el resolutor DOI**. Si la ficha trae DOI y la lista no incluye
un enlace `doi.org`, el Lector de Lista agrega esa puerta construida al final. Razón: la copia libre suele ser un PDF
directo; la oficial suele ser un vestíbulo con muro.

**Primera medición (E15 de `08`, 2026-09-25).** *A favor:* las tres oficiales que se pidieron
no entregaron. Nature (A.6) fue un vestíbulo cuya cadena de redirecciones pasó por
`idp.nature.com`, que se lee como muro (lectura del log, no comprobación, E15.3). Annual
Reviews (A.2) y ScienceDirect (A.4) respondieron `403`, que E15.4 lee como bloqueo al cliente,
**no** como muro: apoyan poner la oficial detrás, pero no la segunda mitad de la razón. *En
contra:* en A.7 la oficial es un PDF abierto de Cambridge (M30). No se pidió, porque la copia
libre entregó antes (E15.2).

**Costo aceptado:** a veces la copia libre es un manuscrito aceptado y la versión publicada
también estaba abierta. El Verificador Académico anota la edición (N13) y el informe lo señala,
para que el usuario decida si busca la publicada (pregunta abierta 5).

### Nota sobre `relacion`

Extras y correcciones son **sobres independientes**: fichas propias, encargos propios,
veredictos propios. `relacionado_con` solo sirve para que el informe los muestre juntos; no los
engrapa. Si el artículo principal falla, el extra se intenta igual.

---

## N12 · ArticleBatch — el lote (una lista recibida) · v2.0

```python
class ArticleBatch(BaseModel):
    lote_id: str                   # f"{slug(nombre_archivo)}-{sha256_archivo[:8]}"
    archivo_origen: str            # nombre del archivo recibido, tal cual
    sha256_archivo: str
    articulos: list[ArticleRef]
    incompletos: list[str]         # renglones literales que no alcanzaron la identificación mínima
    balance_declarado: str | None  # si la lista trae su propio balance, literal
    generado_en: datetime
    notas: str | None
```

**Nota sobre `lote_id`.** Lleva el hash del archivo: la misma lista da el mismo lote, y
re-correrla no duplica nada. Una lista editada es un lote nuevo, pero sus artículos ya
descargados se reconocen por `articulo_id` y no se vuelven a pedir.

---

## N13 · ArticleVerdict — el sello del Verificador Académico · v2.0

```python
class ArticleVerdict(BaseModel):
    articulo_id: str
    veredicto: Literal["correcto", "discrepancia", "otra_edicion", "otro_articulo", "ilegible"]
    via: Literal["doi", "titulo_autor_anio"]   # qué ruta de revisión decidió
    dois_candidatos: list[str]     # hallados en metadatos y primera página, normalizados
    doi_coincide: bool | None      # None si la ficha no trae DOI o el archivo no trae ninguno
    coincide_titulo: bool | None   # None si la ficha no trae título
    coincide_primer_autor: bool | None
    coincide_anio: bool | None
    coincide_cita: bool | None     # revista/volumen/página; None si no aplica
    edicion: Literal["publicada", "manuscrito_aceptado", "preprint", "desconocida"]
    paginas: int | None
    tiene_texto: bool              # False → escaneo; hizo falta OCR
    discrepancias: list[str]
    confianza: Literal["alta", "media", "baja"]
    evidencia: str                 # fragmento de la primera página en que se basó el juicio
```

### Cómo revisa (orden fijo)

**Paso 0 · ¿Se puede leer?** Archivo sin páginas, corrupto, o sin texto aun tras OCR →
`ilegible`. Aquí se cumple «confirmar que el sobre no está vacío».

**Paso 1 · Juntar candidatos.** Se buscan DOI **solo** en los metadatos del archivo y en la
primera página, cortando si ya empiezan las referencias. **Los DOI de la bibliografía nunca
entran:** un artículo cita decenas de DOI ajenos.

**Paso 2 · Decidir.** El *control* es el título si la ficha lo trae; si no, primer autor + año
+ cita.

| Situación | Control | Veredicto | `via` |
|---|---|---|---|
| El DOI de la ficha está entre los candidatos | coincide | `correcto` | `doi` |
| El DOI de la ficha está entre los candidatos | no coincide | `discrepancia` | `doi` |
| La ficha trae DOI; hay candidatos, pero ninguno es el suyo | coincide | `otra_edicion` | `doi` |
| La ficha trae DOI; hay candidatos, pero ninguno es el suyo | no coincide | `otro_articulo` | `doi` |
| No hay DOI utilizable (la ficha no lo trae o el archivo no trae ninguno) | título (si hay) + primer autor + año coinciden | `correcto`, confianza máxima `media` | `titulo_autor_anio` |
| Ídem | no coinciden | `otro_articulo` | `titulo_autor_anio` |

**Regla corta: el DOI es evidencia; el título desempata.**

**Por qué el control corre siempre, aun con DOI coincidente.** Una corrección cita en su primera
página el DOI del artículo que corrige. Con el DOI solo, se confundiría con el artículo. Con
control, su título (o su página en la revista) no cuadra y sale `discrepancia`.

**Cuando el control no se puede evaluar.** Si la ficha no trae título y el archivo no trae cita
(típico de manuscritos aceptados), se decide con primer autor + año y la confianza es `baja`.
Heredado de `06`: un veredicto seguro de baja calidad es peor que un «no sé» explícito.

**Correcciones.** Una ficha con `relacion="correccion"` es `correcto` si el documento se declara
corrección y cita el DOI de `relacionado_con`. Si no, `otro_articulo`.

**`edicion` no es veredicto.** Un manuscrito aceptado que imprime el DOI de la versión publicada
es `correcto` con `edicion="manuscrito_aceptado"`. El informe lo señala porque importa para
citar páginas.

---

## N14 · BatchReport — el informe del Auditor de Lote · v2.0

```python
class Observado(BaseModel):
    articulo_id: str
    referencia_literal: str
    veredicto: Literal["correcto", "discrepancia", "otra_edicion"] | None   # v2.2 · None = descargado, sin verificar
    nota: str                      # "manuscrito aceptado, no versión publicada"

class Faltante(BaseModel):
    articulo_id: str | None        # None si la ficha fue incompleta
    referencia_literal: str
    motivo: MotivoFallo | Literal["ficha_incompleta", "sin_puertas", "otro_articulo", "ilegible"]
    intentos: int                  # puertas pedidas
    ruta_sugerida: str             # "biblioteca", "pedir el PDF al autor", "abrir visor: <url>"

class BatchReport(BaseModel):
    lote_id: str
    total_fichas: int
    verificados: list[str]         # articulo_id con veredicto correcto, edición publicada, confianza ≥ media
    con_observaciones: list[Observado]   # llegaron, pero algo merece mirarse
    no_obtenidos: list[Faltante]
    balance_declarado: str | None  # copiado de ArticleBatch
    balance_medido: str            # "11 de 15 con copia libre declarada · N verificados"
    cuadra_balance: bool | None    # None si la lista no declaraba balance
    duracion_s: float
    llamadas_llm: int
    generado_en: datetime
```

**Tres grupos, sin solaparse.** Todo artículo pedido cae en exactamente uno.
`otro_articulo` e `ilegible` cuentan como **no obtenidos**: llegó un sobre, pero no se pudo
confirmar que fuera el pedido. Coincide con el parámetro de confiabilidad académica.

**`cuadra_balance` existe por el hallazgo 3.** La lista real se equivocaba en su propio conteo.
Un auditor que no compara lo declarado con lo medido repite el error.

**Se espera código, no agente.** A diferencia del Corroborador, este auditor no adivina qué
debería existir: la lista es el esqueleto. Se confirma en su spec.

---

## N15 · SeleccionTematica — qué se descarga de un catálogo (v2.7) · solo modo jurídico

**El filtro temático NO es una entrada del sistema: es una decisión posterior al catálogo.**
El Lector de Índice levanta siempre el catálogo **completo**, haya tema o no, y el Corroborador
juzga siempre sobre el catálogo **completo**. Lo único que el tema decide es **qué
`CatalogEntry` se traduce a `Encargo`** (N10).

```python
class Excluida(BaseModel):
    entry_id: str
    razon: str                # por qué queda fuera del tema pedido; frase corta, auditable

class SeleccionTematica(BaseModel):
    seleccion_id: str         # f"{inst_id}:{sha256('|'.join(sorted(temas)))[:8]}"
    inst_id: str
    temas: list[str]          # literal, como los escribió el usuario: ["deportes"]
    catalogo_generado_en: datetime   # qué lectura del catálogo se filtró (D5)
    incluidas: list[str]      # entry_id
    excluidas: list[Excluida]
    confianza: Literal["alta", "media", "baja"]
    generado_en: datetime
```

**Regla dura de cobertura.** `incluidas` + `excluidas` debe cubrir **exactamente** las entradas
del catálogo filtrado, sin solaparse y sin faltar ninguna. **Lo comprueba código, no el agente**,
igual que `enlaces_sin_cuenta` (N3). Si no cuadra, la selección es inválida y **no se traduce
ningún `Encargo`**: una entrada que desaparece en silencio es el fallo de C13 otra vez.

**Por qué tabla aparte y no un campo en `CatalogEntry`.** El tema pertenece a quien pide, no al
documento. Un mismo catálogo puede filtrarse hoy por deportes y mañana por personal académico, y
el catálogo no debe reescribirse por eso. `entry_id` no cambia entre selecciones: las dos
conviven apuntando a las mismas entradas. Por la misma razón tampoco va en `InstitutionRef`
(N0): el tema es de la corrida, no de la institución.

**`excluido` no es `fallido`.** Una entrada excluida por tema **no** va a la cola manual (N8),
no cuenta como descarga fallida en `HarvestStats` (N9) y no reduce `entradas_catalogo`. Es una
decisión del usuario, no un problema del sistema. Confundirlas vaciaría de sentido a la cola
manual, que es producto (D7).

**Sin `temas` no hay `SeleccionTematica`:** toda entrada del catálogo se traduce a `Encargo`,
exactamente como hasta la v2.6. **El comportamiento por defecto no cambia.**

**El filtro es juicio de agente y hoy no tiene oráculo.** Decidir si un reglamento «es de
deportes» no se resuelve con una lista de palabras: un Reglamento de Alumnado puede regular la
participación deportiva sin llamarse así. Mientras no exista ese oráculo (pregunta abierta 6),
la `confianza` baja y las excluidas se muestran al usuario **antes** de descargar.

**Qué no resuelve.** Una selección temática no hace más barata la lectura: el Lector gasta la
misma llamada al LLM, porque extrae todo igual. Lo que ahorra son descargas, no razonamiento.

---

## Parámetros globales congelados

| Parámetro | Valor v2.0 |
|---|---|
| **Identificadores** | Jurídico: `entry_id = f"{inst_id}:{doc_slug}:{url_id}"` (v2.0) y `doc_id = f"{inst_id}:{doc_slug}:{fecha_version}"`. Académico: `articulo_id` según N11. Común: `encargo_id` = el identificador de su modo. **Jamás posicional**, tampoco el número de una lista |
| **Ruta en disco** | `data/<cajon>/<etiqueta>.<ext>`. Jurídico: `data/norm/<inst_id>/<doc_slug>__<AAAA-MM-DD>.<ext>` (**idéntica a v1.4**). Académico: `data/papers/<autor>-<año>__<h8>.<ext>`. `<ext>` sale de la **firma de bytes**, nunca de la URL ni de `formato_declarado` (v2.0) |
| Hash de integridad | SHA-256 sobre los bytes crudos del archivo |
| **Guardián de formato** | Los primeros bytes deben coincidir con una firma aceptada: `%PDF-` → `.pdf`; `PK\x03\x04` → `.docx`. Cualquier otra cosa → `no_es_pdf` y **el archivo no se guarda**. La firma manda sobre lo que anuncia el sitio. Aplica a ambos modos y también al archivo alcanzado tras cruzar un vestíbulo (v1.3, v2.0) |
| **Formatos aceptados** | `.pdf` y `.docx`, en ambos modos. El `.docx` entra por los anexos de la UAM (**E1.6 de `08`**). `PK\x03\x04` es la firma genérica de ZIP: un `.xlsx` la pasaría, riesgo aceptado (v1.3) |
| User-Agent | Identificado, con nombre del proyecto y correo de contacto (D8). Ambos modos |
| Rate limit | ≥ 1 s entre peticiones al **mismo dominio**; dominios distintos en paralelo. **El límite es por dominio, no por modo:** una editorial pedida por dos lotes sigue siendo un dominio |
| Timeout de descarga | 30 s **por puerta** |
| Tamaño máximo por documento | 100 MB (por encima → `demasiado_grande`) |
| Reintentos | 5 intentos por puerta, backoff exponencial (`multiplier=2, max=60`), solo en 429/5xx/timeout |
| Modelo LLM | En `Settings`, nunca escrito a mano en el código |
| **Umbral de caducidad del índice** | **18 meses**, en `Settings`. `catalogo_caducado=True` si `fecha_corte_declarada` es anterior a hoy menos el umbral (v2.3) |
| **Idioma** | Jurídico: español (mexicano). Académico: idioma original del artículo. **Sin traducción** en ninguno; títulos y nombres con su ortografía intacta (v2.0) |
| **Normalización de URL** | Antes de cualquier petición: recortar blancos, codificar espacios y no ASCII, resolver relativas contra `url_base`, conservar el esquema. **La URL cruda se guarda íntegra**; la normalizada solo se usa para pedir y para `url_id`. Aplica a cada puerta y a cada enlace de vestíbulo (E4.3 de `08`; v2.0) |
| **Reconocimiento de visores de terceros** | Antes del guardián, se comprueba si host y ruta coinciden con un patrón de visor conocido (`drive.google.com/file/d/<id>`). Si coincide → `visor_de_terceros`, sin construir URL de descarga (D3). Lista de patrones en datos, no en código. Por puerta (v1.2) |
| **Puertas múltiples** | Se prueban **en orden**. La primera que entrega un archivo aceptado gana y las siguientes **no se piden**. Cada puerta pedida deja su fila en `intentos` (v2.0) |
| **Cruce de vestíbulo** | Si `cruzar_vestibulos=True` y la puerta devuelve HTML: se busca en esa página un enlace a archivo y se sigue **un solo salto**. El enlace debe **aparecer literal** en la página (D3), y la página es entrada no confiable (D4): se extrae un enlace, no se obedece nada. Sin enlace → `vestibulo_sin_pdf`. **Orden:** visor → petición → guardián → vestíbulo → guardián. Jurídico en `False` por defecto: conserva el comportamiento medido de v1.4 (150/150). La heurística de búsqueda del enlace vive en `05` (v2.0) |
| **Excepción a D3: resolutor DOI** | Única URL que se construye: `https://doi.org/<doi normalizado>`, y solo desde un DOI escrito en la lista. Marcada con `Puerta.construida=True`. Cualquier otra construcción sigue prohibida (v2.0) |
| **Muros** | El Descargador **nunca** intenta pasar un muro de pago, suscripción o sesión, ni usa servicios que los eludan. Un muro es un resultado (`muro_de_pago`), no un obstáculo a vencer (v2.0) |
| **Alias por hash** | Antes de registrar una descarga como nueva, se compara su SHA-256 con los ya registrados del mismo `Encargo.grupo_alias` (jurídico: `inst_id` + `doc_slug`; académico: `articulo_id`). El Descargador no deduce el grupo del `encargo_id`: lo recibe (v2.1). Si coincide → no se escribe archivo, `duplicado_de` apunta al original. **Nunca se sobrescribe ni se borra un archivo** (v2.0). **El alias no cruza grupos:** si cambia el `doc_slug`, cambia el grupo y los mismos bytes se escriben otra vez (v2.7, ver N2 §Segundo límite) |
| **Revisión académica** | Candidatos DOI solo de metadatos y primera página, cortando en referencias. Normalización de DOI: minúsculas; quitar prefijos `doi:`, `https://doi.org/`, `http://dx.doi.org/`; quitar puntuación final `.,;)]`. Patrón de referencia: `10\.\d{4,9}/\S+`. Decisión según la tabla de N13 (v2.0) |
| **Confiabilidad académica** | En modo académico **no hay ancla de dominio**: una copia legítima puede vivir en GitHub, en un repositorio o en la página de un autor. La confianza la da el Verificador Académico. Un artículo cuenta como obtenido solo con veredicto `correcto` u `otra_edicion`. **D9 sigue rigiendo el modo jurídico sin cambios** (v2.0) |
| **Filtro temático** | Opcional y **posterior al catálogo** (v2.7). El Lector extrae siempre todo; el Corroborador juzga siempre sobre todo; solo la traducción a `Encargo` se limita a `SeleccionTematica.incluidas` (N15). Sin temas, se traducen todas las entradas, como en v2.6. Una entrada excluida **no** es un fallo, no va a cola manual y no cuenta en `descargas_fallidas` |

---

## Qué rompe la v2.0 y cómo se migra

### Lo que rompe

1. **Formato de `CatalogEntry.entry_id`** (N2): pasa de `inst_id:doc_slug` a
   `inst_id:doc_slug:url_id`.
2. **Renombre en `DownloadResult`** (N5): `entry_id` → `encargo_id`.
3. **Entrada del Descargador**: `descargar()` recibe `Encargo` en lugar de `CatalogEntry`.
4. **Idioma del corpus**: deja de ser único.

La ruta en disco se generaliza, pero **la ruta jurídica resultante no cambia**.

### Cómo se migra

**Código.** `descargar()` recibe `Encargo`. La traducción jurídica (N10) vive en un solo sitio.
Los tests que construían `CatalogEntry` para el Descargador pasan por la traducción; los que
leían `entry_id` de un resultado leen `encargo_id`. **Ninguna aserción de comportamiento
cambia.**

**Datos.** Los 150 documentos en disco **no se tocan**: nunca se sobrescribe. Sus nombres ya
estaban declarados desechables (E11.6 de `08`), porque usaron slugs de una heurística
provisional. **No se traducen filas viejas:** se rehace la corrida en una base limpia cuando el
Lector de Índice produzca slugs correctos. Son minutos.

### Criterios de migración

1. La suite completa del Descargador pasa con solo los cambios mecánicos descritos arriba.
2. UAM y UJAT se vuelven a descargar en base limpia: **cada enlace a documento publicado en el
   índice produce un encargo y una descarga exitosa**, con rutas jurídicas de la misma forma que
   en v1.4. **N se mide, no se presupone.** Con los índices capturados el 2026-09-06, N = **156**
   (UAM 47, UJAT 109). **Cero pérdidas por colisión de identificador.**

   > **Por qué el «150/150» de la v2.0 desapareció (v2.4).** Era un artefacto de medición, no una
   > propiedad de los sitios. Los scripts de cosecha de v1 derivaban el identificador de *«lo que
   > va tras el último guion»* y **descartaban en silencio** toda dirección que colisionara con
   > otra ya vista. Medido el 2026-09-11 sobre las fixtures: la UAM perdía **2** —una de ellas el
   > ancla vacía de E1.5, el caso adversarial que `08` llama el más interesante del corpus— y la
   > UJAT ignoraba **4** enlaces porque su `href` termina en salto de línea y el filtro por
   > extensión corría sobre el crudo. Las dos corridas reportaron 100 % sobre un denominador que
   > ellas mismas habían recortado. El formato nuevo de `entry_id` (N2) elimina las colisiones por
   > construcción; el salto de línea lo resuelve la normalización de URL, que ya existía pero se
   > aplicaba después del filtro.
3. Un `Encargo` jurídico que falla produce los mismos motivos que en v1.4, **con la excepción de
   los muros**: nunca `puertas_agotadas`, nunca `vestibulo_sin_pdf`. **`muro_de_pago` sí puede
   aparecer en modo jurídico** (v2.4): el reconocimiento de muros es de `05` v3 y no distingue
   modo, igual que D8. Ninguna aserción de v1.4 lo contradice — medido el 2026-09-11: ningún test
   de la suite afirma que un `401` o un `402` produzcan `http_error`.
4. Los dos históricos del Reglamento de Estudios Superiores de la UAM (E11.6) producen **dos
   `entry_id` distintos**.

---

## Propagación pendiente

*Este documento no modifica los demás. Queda por hacer, en este orden sugerido:*

| Documento | Qué cambia |
|---|---|
| `00` | Nombre **Acervo**; D10 amplía el alcance al modo académico; decisión nueva sobre confiabilidad académica (contenido, no dominio); excepción acotada a D3 para el resolutor DOI; la pregunta de C20 en §8 queda resuelta por esta versión |
| `03` | Formato nuevo de `entry_id`; C20 sale de su agenda |
| `05` | Recibe `Encargo`; puertas múltiples; cruce de vestíbulo; motivos nuevos; alias por hash |
| `06` | Nota de C20: se resolvió en N2 (salida B), no en N7; conciliación de dos archivos con el mismo `doc_id` |
| `07` | CLI `acervo juridico <ficha.docx>` y `acervo academico <lista.docx>`; tablas `encargos`, `lotes`, `articulos`; el modo académico no usa `cola_manual` |
| README | Nombre y versiones |
| Specs nuevas | **Lector de Lista**, **Verificador Académico**, **Auditor de Lote**. Y la ya pendiente de **extracción de texto con OCR**, que ahora comparten ambos verificadores |

**v2.6 · contabilidad de la lectura (N3):**

| Documento | Qué cambia |
|---|---|
| `03` | El agente declara sus descartes; código calcula `enlaces_sin_cuenta` y `lectura_incompleta`; **regla dura: `lector_agotado` y `fallo_lector` son excluyentes**, y un JSON inválido marca `fallo_lector="salida_invalida"`, nunca `lector_agotado`; criterio de aceptación nuevo con salida truncada |
| `04` | No tratar `lectura_incompleta` como hueco de la institución. **Pendiente: `04` sigue en v2 y no lo recoge** |
| `07` | Pregunta abierta: qué hace la orquestación ante `salida_invalida` (¿reintento?). **Pendiente: `07` sigue en v2 y no lo recoge** |

**v2.7 · filtro temático (N15):**

| Documento | Qué cambia |
|---|---|
| `03` | **Nada funcional:** el Lector extrae siempre el catálogo completo. Se anota explícitamente que el filtro **no es suyo**, para que nadie lo implemente ahí |
| `04` | `CoverageReport` se calcula sobre el catálogo completo, nunca sobre la selección (nota ya en N4) |
| `07` | Tabla `selecciones` (espejo de N15); `acervo juridico --inst X --tema deportes`; la última selección por institución se recuerda; una entrada excluida **no** entra a `cola_manual` ni a `descargas_fallidas` |
| `05` | **Sin cambios:** recibe `Encargo` y no sabe de temas (D14) |

---

## Preguntas abiertas (no bloquean este contrato)

1. ~~**Ratificar la identificación mínima** (N11)~~ **Ratificada.**
2. ~~**¿Se permite construir `https://doi.org/<doi>`?**~~ **Resuelta: sí**, como excepción
   acotada a D3 (ver Vocabularios y Parámetros). Pasa a `00`.
3. ~~**`robots.txt` en modo académico.**~~ **Resuelta en `05` v3: misma política que el modo jurídico.** El fail-open de D8 se justificó con sitios institucionales
   que publican por ley. Las editoriales no lo son. Se decide en `05`.
4. ~~**Dos archivos con el mismo `doc_id`**~~ **Resuelta en `06` v4: se conservan ambos; el registro apunta al primero aprobado.** y bytes distintos (límite conocido de N2). Se decide
   en `06`/`07`.
5. **Orden de puertas académicas.** Copia libre primero trae a veces un manuscrito cuando la
   versión publicada también estaba abierta. Medir con la primera corrida antes de cambiarlo.
6. **¿Cómo se evalúa el filtro temático (N15)?** Decidir si un instrumento «es de deportes» es
   juicio de agente y hoy **no tiene oráculo**. Hace falta escribir uno —como el de la UACAM para
   el criterio 4 de `03`— antes de poder medir si sirve. Mientras tanto, la `confianza` baja y las
   excluidas se muestran al usuario antes de descargar. **No bloquea la implementación de N15,
   pero sí bloquea cualquier afirmación sobre su calidad.**

---

## Changelog

| Versión | Fecha | Cambio |
|---|---|---|
| v1.0 | 2026-08-29 | Contratos iniciales N0–N9. |
| v1.1 | 2026-08-29 | Tras medir UNAM-OAG y UJAT (`08` v2): `doc_slug` con estrategia por sitio + fallback; nota de que `estado="desconocido"` será mayoritario; `categoria_indice` degradada a pista (D11); nuevo parámetro global de normalización de URL. **Compatible con v1.0.** |
| v1.2 | — | Nuevo literal `visor_de_terceros` en `motivo_fallo` de N5 (aditivo). Nuevo parámetro "Reconocimiento de visores de terceros", con su nota de orden respecto del guardián. Nota en N8 sobre `donde_buscar`. **Compatible con v1.1.** *(Fila reconstruida en v1.4.)* |
| v1.3 | 2026-09-03 | Se aceptan `.docx` de cualquier institución: guardián de dos firmas (`%PDF-`, `PK\x03\x04`); extensión en disco derivada de los bytes; parámetro "Formatos aceptados"; aviso de nomenclatura en `no_es_pdf`. **Compatible con v1.2.** |
| v1.4 | 2026-09-06 | **Corrección de evidencia** en la nota de `visor_de_terceros` (E10.2: 4 documentos, no 23; Ley Orgánica en subdominio institucional; Estatuto ausente, E10.5). Reconstruida la fila v1.2. Anclas corregidas: anexos `.docx` = E1.6; C2 = 1 de 4. **Compatible con v1.3.** |
| **v2.0** | **2026-09-10** | **El sistema pasa a llamarse Acervo y gana un modo académico.** Decisiones de la conversación «Acervo: modo académico». **Rompe:** `CatalogEntry.entry_id` incorpora `url_id` (**resuelve C20**, salida B, con alias por hash y límite conocido anotado); `DownloadResult.entry_id` → `encargo_id`; el Descargador recibe `Encargo`. **Aditivo:** vocabularios `Modo`, `TipoPuerta`, `Relacion`; `MotivoFallo` extraído a vocabulario con `vestibulo_sin_pdf`, `muro_de_pago`, `puertas_agotadas`; N5 gana `modo`, `puerta_usada`, `intentos`, `duplicado_de`; N7 gana `entry_id`; contratos nuevos N10 `Encargo`, N11 `ArticleRef`, N12 `ArticleBatch`, N13 `ArticleVerdict`, N14 `BatchReport`; parámetros nuevos (puertas múltiples, cruce de vestíbulo, muros, alias por hash, revisión académica, confiabilidad académica) y parámetros generalizados (identificadores, ruta en disco, idioma). Diseñado contra una lista real (`Geologia_dois_.docx`). **Revisión posterior el mismo día:** excepción acotada a D3 para `doi.org` (`Puerta.construida`); fichas sin puertas → `sin_puertas`; `ilegible` pasa a no obtenido; restaurados literal los matices de v1.4 perdidos al condensar (N5, N7, N8). **Ratificado:** identificación mínima de N11 en lugar de título obligatorio. Plan y criterios de migración incluidos. |
| v2.1 | 2026-09-10 | Campo nuevo `Encargo.grupo_alias` (N10): el Descargador necesita saber contra qué grupo aplicar el alias por hash sin conocer `doc_slug` ni `articulo_id` (D14). Surgió al redactar `05` v3. **Compatible con v2.0.** |
| v2.2 | 2026-09-10 | `Observado.veredicto` admite `None` (N14): un artículo descargado cuyo Verificador Académico falló va a `con_observaciones` con nota «sin verificar», en vez de perderse. Surgió al redactar la regla de continuidad de `07` v2. **Compatible con v2.1.** |
| v2.3 | 2026-09-10 | Propagación de `03` v3, ratificada: `Catalog` (N3) gana `fecha_corte_declarada`, `fecha_corte_texto` y `catalogo_caducado` (D12, C13); `CatalogEntry` (N2) gana `titulo_derivado` (C9); parámetro nuevo "Umbral de caducidad del índice" (18 meses). Cierra la propagación de la v2.0. **Compatible con v2.2.** |
| **v2.4** | **2026-09-11** | **Criterios de migración, corregidos contra medición.** El criterio 2 deja de pedir «150/150» y pasa a «todo enlace publicado produce descarga», con **N medido = 156** (UAM 47, UJAT 109): el 150 venía de una heurística de slug que perdía 2 documentos en la UAM y de un filtro por extensión que ignoraba 4 enlaces de la UJAT con salto de línea. El criterio 3 admite `muro_de_pago` en modo jurídico, porque el reconocimiento de muros de `05` v3 no distingue modo (D8) y ninguna aserción de v1.4 lo contradice. **Sin cambios de esquema: ningún contrato N0–N14 se toca. Compatible con v2.3.** |
| **v2.5** | **2026-09-25** | **Aclaración sobre la lista de origen, sin cambios de esquema.** `Geologia_dois_.docx`, la lista contra la que se diseñó §Modo académico, **nunca llegó al repositorio**: sus tres hallazgos (§Evidencia de partida) y las «17 fichas» (N11) se conservan como historia de diseño, con nota de que no son verificables. La primera corrida académica usó `datos/lotes/bloque-a.txt` (E15 de `08`). La razón del orden de puertas (§Nota sobre `puertas` y su orden) cita E15, con datos a favor y en contra. El registro de v2.0 no se toca. **Ningún contrato N0–N14 se toca. Compatible con v2.4.** |
| **v2.6** | **2026-10-01** | **Contabilidad de la lectura, aditivo.** `Catalog` (N3) gana `enlaces_vistos`, `enlaces_descartados`, `enlaces_sin_cuenta`, `lectura_incompleta` y `fallo_lector`: distingue rejilla vacía, salida inválida del agente y lectura truncada, que antes caían todas en `lector_agotado` + `notas`. `lector_agotado` y `fallo_lector` son excluyentes. Propaga a `03`, `04` y `07`. **Ningún campo existente cambia. Compatible con v2.5.** |
| **v2.7** | **2026-10-04** | **Filtro temático, aditivo.** Contrato nuevo **N15 `SeleccionTematica`**: el tema vive en una selección aparte, no en `CatalogEntry` (N2), porque pertenece a quien pide y no al documento; **y tampoco en `InstitutionRef` (N0)**, que es identidad estable: el tema es de la corrida, no de la institución. Se consideraron las dos alternativas y se descartaron, con su razón escrita. Reglas: el Lector extrae siempre el catálogo completo; el Corroborador juzga siempre sobre el completo (nota en N4); `incluidas` + `excluidas` cubren el catálogo exactamente, comprobado por **código**; una entrada excluida no es un fallo, no va a cola manual (N8) ni a `descargas_fallidas` (N9). Sin `temas`, el comportamiento es idéntico al de v2.6. **Además, sin cambio de esquema:** N2 gana el «segundo límite» del alias por hash —el alias no cruza `grupo_alias`, y cambiar un `doc_slug` reescribe los mismos bytes bajo otro grupo—, medido dos veces (E14.5, E21.15), con el remedio de procedimiento en `03`. Pregunta abierta 6: el filtro no tiene oráculo. **Ningún contrato N0–N14 se toca. Compatible con v2.6.** |
