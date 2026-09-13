# 03 · Spec — Lector de Índice (pieza ②)

> Conversación: "Fase Lector". Leer antes `00` v2.0, `01` v2.3 (contratos N1, N2, N3) y **`08` v7**.
> Estado: **v3** · agente LLM · **pieza del modo jurídico** (LegisUni). **Es la pieza de mayor valor de ese modo.**
> **La evidencia cambió mucho desde la v1.** Cuatro universidades medidas (no tres) y dos
> corridas reales del Descargador. Esta versión incorpora seis requisitos nuevos que no
> existían en la v1 y que salieron de datos, no de suposiciones: fecha de corte del índice,
> codificación declarada, percent-encoding en los slugs, enlaces sin texto de ancla, el mismo
> instrumento en varios lugares, y la colisión de `entry_id` entre versiones.
> **v3 (2026-09-10), propagación de `01` v2.0:** la colisión de `entry_id` quedó resuelta en los
> contratos (D15); el Lector calcula `url_id` con la función del Descargador; y dos requisitos de
> la v2 que necesitaban campos en `01` quedaron ratificados y ya están en `01` v2.3 (fecha de
> corte y título derivado).

---

## Qué cambia en la v3 (leer primero)

| Cambio | Sección |
|---|---|
| **Orden de construcción:** esta pieza abre la ruta jurídica, que va después del modo académico (`00` §6) | Por qué es la pieza crítica |
| C20 resuelto en `01` v2.0: `entry_id = inst_id:doc_slug:url_id` (salida B, D15) | Identidad de cada publicación |
| `url_id` se calcula con `urlnorm.url_id()` de `05` v3, nunca con una normalización propia | Identidad de cada publicación |
| "Conservar todas las URL candidatas" se traduce a una entrada por dirección distinta | El mismo instrumento en varios lugares |
| Índices paginados: deduplicación entre páginas por dirección normalizada | Identidad de cada publicación |
| **Contrato ratificado (`01` v2.3):** campos de fecha de corte en `Catalog` (N3) | Fecha de corte · pregunta 7 |
| **Contrato ratificado (`01` v2.3):** marca `titulo_derivado` en `CatalogEntry` (N2) | Enlaces sin texto de ancla · pregunta 9 |
| Frontera con el Lector de Lista | No-alcance |
| Criterios 1 y 12 ajustados; criterios 15–16 nuevos | Criterios |

---

## Objetivo

Dada una `SourceCandidate` (N1), abrir esa página y extraer el catálogo completo de
instrumentos normativos que ofrece: título, tipo, URL del documento, estado de vigencia y
fechas. Producir un `Catalog` (N3) de `CatalogEntry` (N2).

**Esta es la pieza que sustituye a los ~40 parsers artesanales.** Si funciona, el sistema
escala a cualquier universidad. Si no funciona, no hay proyecto.

---

## Por qué es la pieza crítica

Evidencia de campo (`08` v7), **cuatro universidades medidas** — **las cuatro sirven HTML
plano, y las cuatro lo hacen de forma distinta**:

| | UAM | UNAM (OAG) | UJAT | UACAM |
|---|---|---|---|---|
| Enlaces a documento | 45 | ~60 | **105** | ~82 |
| De ellos, normativa propia | 45 | ~60 | 105 | **27** (uno de cada tres) |
| Agrupación | Por materia | **Por jerarquía normativa** | Por tipo, **mal aplicada** | Por tema |
| Vigencia declarada | **Sí, en el texto** | No | No | No |
| **Fecha de corte del índice** | No | No | No | **Sí: «Diciembre del 2016»** |
| Fecha | En la ruta | En el nombre de archivo | A veces, inconsistente | A veces |
| Identidad estable | Sufijo (`-lo`, `-res`) | Prefijo numérico (`2-`, `29-`) | Ninguna | Ninguna |
| URLs | Limpias | Limpias | **Sucias** (espacios, http/https) | **Sucias** (espacios y `%20` mezclados) |
| **Codificación** | **`iso-8859-1`** | ? | **`utf-8`** | ? |
| Visor de terceros | No | No | No | **Sí: 4 en Google Drive** |
| Índice paginado | No | No | **Sí: 5 páginas, solo 2 con documentos** | No |

Ningún parser único cubre los cuatro. Un agente que entienda *qué es una lista de normas* los
cubre el primer día — y reconoce cuándo una página no trae nada.

**El caso realmente difícil resultó ser otro:** no la UNAM (su sitio propio funciona), sino
los formatos 70-I servidos por rejilla JavaScript.

**Y el peor caso no es técnico.** El índice de la UACAM es HTML plano, impecable y fácil de
parsear — y está **congelado desde diciembre de 2016**, cosa que declara en una línea al pie.
Un Lector técnicamente perfecto que no lea esa línea produce un catálogo de nueve años de
antigüedad con aspecto de actual (C13 de `08`).

---

> **v3 · orden de construcción.** Sigue siendo la pieza de la que depende que el modo jurídico
> escale. Pero desde `00` v2.0 el modo académico se completa primero, y esta spec abre la ruta
> jurídica después (`00` §6, pregunta 10). Sus fixtures no esperan: E9 de `08` explica por qué
> las que faltan corren prisa aunque el Lector se construya más tarde.

---

## Alcance

### Extracción

De cada enlace de la página, el agente decide: **¿esto es un instrumento normativo?** Si sí,
llena un `CatalogEntry`. Ejemplos de lo que debe reconocer y clasificar:

| Texto del índice | `tipo_norma` | `estado` | `vigente_hasta` |
|---|---|---|---|
| Ley Orgánica | `ley_organica` | `vigente` | — |
| Reglamento Orgánico | `estatuto` | `vigente` | — |
| Reglamento de Estudios Superiores | `reglamento` | `vigente` | — |
| …vigente hasta el 16 de marzo de 2026 | `reglamento` | `historico` | 2026-03-16 |
| …abrogado a partir del 25 de noviembre de 2025 | `reglamento` | `abrogado` | 2025-11-25 |
| Políticas Operacionales de Docencia | `politicas` | `vigente` | — |
| Anexo 2. Evaluaciones de riesgo | `anexo` | `vigente` | — |
| Tabulador para Ingreso y Promoción | `tabulador` | `vigente` | — |

### La categoría del sitio NO determina `tipo_norma` (D11)

Regla dura, y viene de datos: en la UJAT el **Estatuto del Personal Académico** está listado
bajo "REGLAMENTOS", y **la Ley Orgánica y el Estatuto General** bajo "OTROS DOCUMENTOS", junto
a un tabulador de sueldos y un pronunciamiento institucional.

`tipo_norma` se deriva **del título del instrumento**. `categoria_indice` se guarda como pista
y nada más. Un Lector que clasifique por sección del sitio archivará la norma fundante de una
universidad como "otro" — y el Corroborador reportará un hueco crítico que no existe.

### Lo que NO es instrumento normativo (y hay que descartar)

Menús de navegación, enlaces a unidades académicas, logotipos, "Subir", créditos, contacto,
mapa de sitio. La página de la UAM contiene todos ellos mezclados con los reglamentos.

> Es el mismo problema que el proyecto hermano resolvió con una *stoplist* de secciones no
> citables (su decisión P7): la bibliografía puntúa alto en retrieval y no sustenta nada.
> Aquí el equivalente son los enlaces de navegación.

### Fecha de corte del índice — se comprueba ANTES que nada (C13)

**El requisito más importante que salió de campo, y no existía en la v1.**

La UACAM declara al pie de su índice: *«Fecha de corte: Diciembre del 2016»*. El índice es HTML
plano, impecable, con títulos claros y URLs que responden. **Un Lector técnicamente perfecto lo
procesa sin un solo error y produce 27 instrumentos de hace nueve años con aspecto de
vigentes.** Nada aguas abajo lo detectaría: el Corroborador vería un catálogo completo, el
Verificador encontraría los documentos, y el sistema entero estaría mintiendo con confianza.

**Requisito:** antes de extraer nada, el agente busca en la página cualquier declaración de
fecha de corte, última actualización o periodo de referencia. Patrones a reconocer:

- «Fecha de corte: …», «Última actualización: …», «Actualizado al …»
- «Periodo que se informa: …», «Vigente al …»
- Un encabezado o migaja de pan que ubique la página en un archivo histórico

Si la encuentra, va a `Catalog` como campo propio. **Y si es anterior a ~18 meses, el catálogo
entero se marca como sospechoso** y el Corroborador debe tratarlo como tal.

> Esto **no** es lo mismo que `CatalogEntry.estado`. Un índice caducado puede contener
> instrumentos que siguen vigentes; lo que caduca es la *afirmación del índice* sobre qué
> existe y qué está al día. Son cosas distintas y hay que registrarlas por separado.

**Consecuencia de contrato:** `Catalog` (N3) necesita campos para esto. **Ratificado (2026-09-10),
ya en `01` v2.3** (pregunta 7):

```python
# en Catalog (N3), aditivo
fecha_corte_declarada: date | None    # la fecha que declara la página
fecha_corte_texto: str | None         # la declaración literal («Fecha de corte: Diciembre del 2016») — D5
catalogo_caducado: bool = False       # fecha_corte_declarada más vieja que el umbral
```

- **Umbral de 18 meses, en `Settings`**, no en el código.
- **Fechas con precisión de mes o año** («Diciembre del 2016», «2019») se guardan como el
  **último día** del periodo declarado. Es la lectura más generosa con la universidad: si aun
  así el índice resulta caducado, lo está sin discusión.
- **El texto literal se guarda siempre**, porque la conversión a `date` es una interpretación y
  el Corroborador (y un humano) deben poder auditarla.
- **Sin declaración, `catalogo_caducado=False`** y los dos campos de fecha en `None`. Ausencia de
  fecha de corte no es evidencia de frescura, pero tampoco de caducidad; qué hacer con un índice
  caducado sigue siendo la pregunta 8 de `00`.

### Codificación del HTML — detectar, no asumir (C18)

**Medido:** el índice de la UAM se sirve en **`iso-8859-1`**; el de la UJAT, en **`utf-8`**.
Dos universidades, dos codificaciones.

Leer una página `iso-8859-1` asumiendo UTF-8 **no lanza excepción**: produce títulos con
basura en cada acento y cada eñe — o sea, en casi todos. Esa basura viaja después al
`doc_slug` y al nombre del archivo en disco, y nadie se entera hasta que alguien mira el
corpus a ojo.

**Requisito para `reduce.py`:** leer los bytes crudos, detectar la codificación declarada
(`<meta charset>`, cabecera `Content-Type`) y decodificar con ella. UTF-8 es el fallback, no
el default.

### Enlaces sin texto de ancla (C9, dos casos medidos)

La UAM tiene un `<a>` sin texto visible que apunta a un PDF real. La UACAM, otro. **Dos de
cuatro** — dejó de ser anécdota.

Un Lector que sólo mire el texto del enlace pierde documentos en silencio. **Requisito:**
cuando el ancla esté vacía, derivar un título candidato del **nombre del archivo** y marcar la
entrada como necesitada de verificación.

**Consecuencia de contrato (v3):** `CatalogEntry` (N2) no tiene dónde guardar esa marca. **Ratificado
(2026-09-10), ya en `01` v2.3** (pregunta 9): campo aditivo `titulo_derivado: bool = False`. Cuando es
`True`, `titulo` no es literal del índice sino derivado del nombre de archivo (decodificado según
E12.7), y el Verificador Documental debe confirmarlo contra el propio documento antes de
consolidar. Sin el campo, la marca viviría en una nota libre que nadie filtra.

### El mismo instrumento en varios lugares, con versiones distintas (E10.4)

La UACAM enlaza su Ley Orgánica desde **cinco sitios** de la misma página, y **no todos apuntan
a la misma versión**. El Lector no puede quedarse con el primero que encuentre ni asumir que
los cinco son equivalentes.

**Requisito:** deduplicar por `doc_slug`, pero **conservar todas las URL candidatas** cuando
difieran. Elegir cuál es la buena es trabajo del Verificador Documental, que sí puede abrir los
PDF y compararlos.

**v3 · cómo se traduce con `01` v2.0:** cada **dirección distinta** es su propio `CatalogEntry`,
con el mismo `doc_slug` y distinto `entry_id` (porque `url_id` difiere). La deduplicación es por
**dirección normalizada**: si los cinco enlaces de la UACAM apuntan a tres URLs distintas, salen
**tres** entradas, no cinco ni una. Si dos de esas tres resultan tener los mismos bytes, lo
resuelve el Descargador con el alias por hash (`05` v3), no el Lector.

### Enlaces a visores de terceros (C14)

La UACAM sirve cuatro documentos desde `drive.google.com/file/d/<id>/view`, incluida normativa
propia.

**El Lector los registra con normalidad**, con su `url_documento` tal como viene. **No intenta
construir una URL de descarga directa** — D3 lo prohíbe. El Descargador ya sabe reconocerlos y
mandarlos a cola manual con `motivo_fallo="visor_de_terceros"`.



### Detección de esqueleto vacío

Si la página carga por JavaScript, el agente debe reconocerlo y **devolver
`Catalog(entries=[], lector_agotado=True)` con una nota diagnóstica**, no un catálogo
parcial hecho de los encabezados. Señal típica: el texto contiene instrucciones de uso de una
tabla ("dar doble clic sobre el registro", "ordenar los registros") pero ninguna fila.

### Estabilidad del identificador

`doc_slug` se deriva del **título normalizado sin fechas**, o del sufijo de archivo cuando el
sitio usa uno estable. La UAM usa sufijos limpios: `-lo`, `-ro`, `-res`, `-ripppa`. Esos
sufijos sobreviven a las consolidaciones; las rutas completas no.

**Advertencia medida:** las URLs de la UAM codifican la fecha de consolidación
(`legislacion-uam-julio-24-2026/…`). Cuando la universidad consolide de nuevo, **todas las
rutas mueren a la vez**. Por eso el `doc_slug` no puede derivarse de la URL, y por eso el
mecanismo del sistema es el *diff del índice*, no la persistencia de URLs.

**Decodificar antes de normalizar (E12.7).** Cuando el `doc_slug` salga del nombre de archivo,
hay que aplicar `urllib.parse.unquote` **antes** de normalizar. Medido en la UJAT: sin eso,
`Acuerdo%20de%20Genero.pdf` produce el slug `acuerdo-20de-20genero`, y
`ACTUALIZACI%C3%93N.pdf` produce `actualizaci-c3-93n`. El `%` se convierte en guion y los
dígitos del escape quedan como si fueran palabras.

Es un defecto de quien llama al normalizador, no del normalizador: su trabajo es sanear texto,
no decodificar URLs. Pero el Lector es quien llama.

### Identidad de cada publicación (v3 · C20 resuelto)

> **Resuelto en `01` v2.0 (D15).** La decisión no fue ninguna de las tres salidas de abajo, sino
> una cuarta: **`entry_id = f"{inst_id}:{doc_slug}:{url_id}"`**, donde `url_id` son los primeros
> 12 hex del SHA-256 de la URL normalizada. Cada publicación tiene identidad propia desde el
> Lector, sin esperar a que el Verificador lea la fecha. Los dos históricos de la UAM ya no
> colisionan. Se conserva abajo el planteamiento de la v2 porque explica por qué la fecha no
> servía.

**Lo que le toca al Lector:**

1. **Calcular `url_id` con `urlnorm.url_id(url, base)` del Descargador** (`05` v3), pasando
   `url_documento` cruda y `url_indice` como base. **Nunca con una normalización propia:** dos
   normalizaciones distintas darían dos `entry_id` para la misma dirección y reabrirían C20 en
   silencio. Criterio 15.
2. **`doc_slug` sigue sin derivarse de la URL.** `url_id` distingue fotos; `doc_slug` sigue
   nombrando al instrumento a través del tiempo. Las dos cosas conviven en el mismo `entry_id`.
3. **Índices paginados (UJAT, cinco páginas):** un mismo documento enlazado desde dos páginas
   produce **una** entrada, porque su dirección normalizada es la misma. Su `url_indice` es la de
   la primera página donde apareció, en el orden de lectura.
4. **Tras una reconsolidación de la UAM**, todas las entradas cambian de `entry_id` porque cambian
   sus direcciones. Es esperado: el alias por hash del Descargador reconoce las que no cambiaron
   de contenido. El criterio 9 (estabilidad de `doc_slug`) no se ve afectado.

#### Planteamiento original de la v2 (histórico)

**Medido en la UAM.** Publica dos versiones históricas del mismo Reglamento de Estudios
Superiores:

```
legis-univ-uam-res-VIGENTE-HASTA-16.03.2026.pdf
leg-univ-uam-res-VIGENTE-HASTA-04.11.2024.pdf
```

Ambas son el instrumento `res`. Con `doc_slug` derivado correctamente —y derivarlo
correctamente es justo lo que esta spec exige— **ambas producen `entry_id = "uam:res"` y
colisionan**.

`doc_id` (N7) sí lleva la versión dentro, pero `CatalogEntry` (N2) es anterior a la descarga y
no tiene fecha de versión fiable en el momento de construirse: el índice a veces la declara en
el texto (UAM) y a veces no (todas las demás).

**Era un hueco de `01`.** La v2 planteaba tres salidas posibles:

1. Añadir la versión al `entry_id` cuando el índice la declare, y aceptar que sin declaración
   dos históricos colisionan.
2. Permitir varias `url_documento` por `CatalogEntry`, tratando las versiones como variantes
   de un mismo instrumento.
3. Dejar que colisionen en N2 y resolver la identidad en N7, después de descargar, cuando el
   Verificador ya puede leer la fecha dentro del PDF.


---

## No-alcance

- NO descarga los documentos (pieza ④).
- NO juzga completitud (pieza ③).
- NO abre los PDF.
- NO lee listas de artículos: eso es el **Lector de Lista** del modo académico, otra pieza con
  otra spec. Comparten la disciplina (salida JSON estricta, D3, D4), no el código: uno lee HTML
  institucional, el otro `.docx` escritos por personas.
- NO construye `Encargo`s: la traducción `CatalogEntry → Encargo` vive en `juridico/traduccion.py`
  (`05` v3).

---

## Diseño

```
lector/
  agent.py        # prompt de sistema + extracción estructurada
  reduce.py       # HTML -> texto + tabla de enlaces (quita script/style/nav repetida)
  classify.py     # heurísticas baratas ANTES del LLM (ahorro de contexto y de coste)
  slug.py         # doc_slug estable desde título o sufijo de archivo
  corte.py        # búsqueda de fecha de corte antes de extraer (C13)
  identidad.py    # entry_id = inst_id:doc_slug:url_id, usando descargador.urlnorm.url_id (v3)
  models.py
```

**Estrategia de dos pasos (barato primero, caro después):**

1. `reduce.py` reduce la página a una lista de `(texto del enlace, href)`. Barato, sin LLM.
2. `classify.py` descarta con reglas lo obviamente no-normativo (hrefs a `.jpg`, `#`,
   `javascript:`, enlaces de menú repetidos en toda la página).
3. El LLM recibe la lista ya reducida y devuelve JSON estructurado con los `CatalogEntry`.

Esto importa: una página institucional puede traer 200 enlaces de los cuales 40 son normas.
Mandar los 200 crudos al LLM en cada corrida es coste desperdiciado.

### Salida estructurada

El agente responde **solo JSON**, sin preámbulo ni cercas de markdown, y el llamador lo parsea
con manejo de error explícito. Nunca se confía en que venga limpio.

---

## Criterios de aceptación

**Las fixtures de la UAM y la UJAT ya están capturadas** (`fixtures/`, tomadas 2026-09-06 para
las corridas del Descargador). Faltan las de UNAM-OAG, UACAM y la rejilla 70-I. Ver E9.2 de
`08` para la convención de nombres y por qué corre prisa.

1. **Caso UAM (fixture):** de los **45 enlaces a documento**, extrae **31 instrumentos
   vigentes**, clasifica correctamente Ley Orgánica y Reglamento Orgánico, marca como
   `historico` los **8** anteriores y como `abrogado` el Reglamento de Programas de
   Investigación. Reconoce los **5 anexos** (3 de ellos `.docx`) y el consolidado. Cero
   enlaces de navegación. **v3: los 45 `entry_id` son distintos entre sí**; en particular, los
   dos históricos del Reglamento de Estudios Superiores comparten `doc_slug` y difieren en
   `entry_id`.
2. **Caso UNAM-OAG (fixture):** extrae **≥ 55 instrumentos**, respeta la jerarquía que el
   propio sitio declara (Marco General / Estatutos / Reglamentos / Códigos / Lineamientos /
   Normas), y **prefiere el enlace al PDF sobre el enlace de "vista"** que apunta a los
   sub-portales en puertos `:6060` y `:8443` (E3.5 de `08`).
3. **Caso UJAT (fixture) — el criterio que prueba D11:** el índice está **repartido en cinco
   páginas, de las cuales solo dos traen documentos**. Extrae los **105 enlaces únicos**
   deduplicando entre páginas, y clasifica la **Ley Orgánica como `ley_organica`** y el
   **Estatuto General como `estatuto`**, pese a que el sitio los archiva bajo "OTROS
   DOCUMENTOS". Si el Lector los deja en `otro`, falla.
4. **Caso UACAM (fixture) — el criterio de la fecha de corte:** detecta la declaración
   «Fecha de corte: Diciembre del 2016» y **marca el catálogo entero como caducado**. Extrae
   los **27 instrumentos normativos propios** de entre ~82 enlaces, descartando los ~30
   contratos y convenios por ejercicio y los documentos de otras instituciones. Registra los
   **4 enlaces de Google Drive** con su URL tal cual, sin intentar construir una descarga
   directa. **Un Lector que extraiga los 27 correctamente pero no vea la fecha de corte
   FALLA este criterio**, por bien que haya hecho lo demás.
5. **Caso rejilla JS (70-I de la UNAM, fixture):** devuelve `lector_agotado=True` con nota
   diagnóstica. **No debe alucinar entradas** a partir de los encabezados. Sigue siendo el
   criterio de honestidad más importante de la spec.
6. **Codificación:** la fixture de la UAM (`iso-8859-1`) y la de la UJAT (`utf-8`) producen
   **títulos con sus acentos y eñes correctos** en ambos casos, sin configurar nada distinto
   entre una y otra. Un solo carácter corrupto en un título falla el criterio.
7. **Percent-encoding en slugs:** un enlace a `Acuerdo%20de%20Genero.pdf` produce el
   `doc_slug` `acuerdo-de-genero`, **no** `acuerdo-20de-20genero`. Igual con
   `ACTUALIZACI%C3%93N.pdf` → `actualizacion`.
8. **Enlaces sin ancla:** el `<a>` sin texto de la UAM y el de la UACAM producen entrada, con
   título derivado del nombre de archivo y marca de verificación pendiente. **Cero documentos
   perdidos en silencio.**
9. **Estabilidad de `doc_slug`:** dos capturas del mismo índice en fechas distintas producen
   el mismo `doc_slug` para el mismo instrumento, aunque las URLs hayan cambiado por completo.
   Debe funcionar con los **tres mecanismos**: sufijo (UAM), prefijo numérico (UNAM) y
   fallback por título normalizado (UJAT y UACAM).
10. **Fechas:** toda fecha declarada en texto libre español ("16 de marzo de 2026") se
    convierte correctamente a `date`. Incluye meses con acento y formatos abreviados.
    **No se intenta descifrar fechas incrustadas en nombres de archivo** (`_021220`,
    `...11072024.pdf`): son ambiguas y su lectura correcta es trabajo del Verificador
    Documental, que puede cotejarlas contra el propio texto del PDF.
11. **Estado por defecto:** en los casos UNAM, UJAT y UACAM, donde el índice no declara
    vigencia, todo sale con `estado="desconocido"`. **Cero entradas marcadas `vigente` sin
    declaración explícita.**
12. **Idempotencia:** re-leer el mismo índice no crea entradas nuevas ni cambia `entry_id`.
    **v3:** vale con el formato nuevo, porque las direcciones son las mismas. Re-leer la UJAT
    con sus cinco páginas en otro orden tampoco cambia ningún `entry_id`.
13. **Prueba adversarial (D4):** un índice de prueba con una instrucción inyectada en el texto
    de un enlace no altera el comportamiento del agente.
14. **Coste:** ≤ 1 llamada al LLM por página de índice en el caso normal. Si una página exige
    paginación, el número de llamadas se registra y se justifica. **Ojo con la UJAT:** cinco
    páginas de índice son cinco llamadas, y es correcto que lo sean.

### v3 — identidad y contratos

15. **Una sola normalización:** el `url_id` que calcula el Lector para una URL cruda es idéntico
    al que produce `descargador.urlnorm.url_id` para la misma URL y la misma base. Se verifica con
    un test que importa la función del Descargador, y con otro que falla si `lector/` define su
    propia normalización de URLs. Casos obligatorios: la URL con espacios de la UJAT y la ya
    codificada (`%20`) deben dar el **mismo** `url_id`.
16. **Candidatos múltiples (UACAM, E10.4):** los enlaces a la Ley Orgánica producen **una
    entrada por dirección distinta**, todas con el mismo `doc_slug`, y ninguna por enlace
    repetido a la misma dirección.

> **Criterios 4 y 8 (v3):** el 4 se verifica en `Catalog.fecha_corte_declarada`,
> `fecha_corte_texto` y `catalogo_caducado`; el 8, en `CatalogEntry.titulo_derivado` (`01` v2.3).

---

## Preguntas abiertas (agenda de esta conversación)

1. **Páginas JavaScript — ya no es LA pregunta.** Las **cuatro** universidades medidas sirven
   HTML plano en su sitio institucional; lo único que exigió JS fue un 70-I, que es el
   *respaldo*, no la fuente primaria. **Propuesta reforzada: no pagar Playwright.** Cuando
   aparezca una rejilla, `lector_agotado=True` y se salta al siguiente eslabón de D1.
   Reconsiderar solo si E6.3 de `08` muestra que el patrón es frecuente en las estatales
   pequeñas — la UACAM, que era la candidata natural, resultó HTML plano.
2. ~~**¿El catálogo consolidado sustituye a los individuales?**~~ **Resuelta (C19 de `08` y
   pregunta abierta 2 de `05`).** Individuales siempre; el consolidado se descarga aparte como
   respaldo, con `tipo_norma="otro"`. El de la UAM pesa 4.3 MB, es barato y sirve de base para
   el diff. El Lector debe reconocerlo y no confundirlo con un instrumento.
3. ~~**Versiones históricas: ¿se descargan?**~~ **Resuelta de hecho.** La corrida de la UAM ya
   bajó las 8, con `estado="historico"`. Son baratas y su valor diacrónico es alto. **Lo que
   sigue abierto no es si se bajan, sino cómo se identifican** — ver pregunta 6 (resuelta en v3).
4. ~~**¿Qué hacer con `anexo`?**~~ **Resuelta (`01` v1.3).** Se aceptan `.pdf` y `.docx`, de
   cualquier institución. Los tres anexos `.docx` de la UAM ya están en el corpus (E11.4). El
   Lector los clasifica como `anexo` normalmente.
5. **Prompt exacto del agente:** redactarlo y probarlo aquí contra las fixtures de la UAM y la
   UJAT, que ya existen.
6. ~~**`entry_id` y las versiones históricas.**~~ **Resuelta en `01` v2.0 (D15):**
   `entry_id = inst_id:doc_slug:url_id`. Ver §Identidad de cada publicación.
7. ~~**¿Dónde vive la fecha de corte del índice?**~~ **Ratificada (2026-09-10), en `01` v2.3:** `fecha_corte_declarada: date | None`, `fecha_corte_texto: str | None` y
   `catalogo_caducado: bool`, con umbral de 18 meses en `Settings` y fechas de mes o año
   guardadas como el último día del periodo. Detalle en §Fecha de corte. *(La v2 proponía solo
   dos campos; la v3 añade el texto literal para auditar la conversión, D5.)*
8. **¿El Lector marca los documentos que probablemente necesiten OCR?** Medido: 24 de 105
   documentos de la UJAT son escaneos sin texto, y **el patrón es predecible** — son los
   firmados: acuerdos rectorales y el contrato colectivo (C21, C22 de `08`). El Lector podría
   anticiparlo desde el `tipo_norma`, pero **eso sería adivinar antes de abrir el archivo**.
   Propuesta: **no**. Que lo determine quien abra el PDF, con el dato en la mano. Se anota
   aquí sólo para que la spec de extracción sepa que el patrón existe.
9. ~~**¿Dónde vive la marca de título derivado?**~~ **Ratificada (2026-09-10), en `01` v2.3:** `titulo_derivado: bool = False` en `CatalogEntry`. Detalle en §Enlaces sin
   texto de ancla.

---

## Registro de consideraciones diferidas

*(Se llena durante la implementación. Todo lo que se decida anotar en vez de resolver, con su
gatillo de revisión. Ver `05` para el formato: cada entrada lleva qué se aceptó, por qué, qué
lo dispara y cómo se arregla cuando se dispare.)*
