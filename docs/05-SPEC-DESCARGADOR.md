# 05 · Spec — Descargador (pieza ④)

> Conversación: "Fase Descargador". Leer antes `00` y `01` v2.1 (contratos N5, N10).
> Estado: **v3** · **código convencional, sin LLM.** Pieza común a los dos modos de Acervo (D14).
> **Fase v1 cerrada el 2026-09-06:** diez de diez criterios, 150/150 documentos de UAM y UJAT
> (E11 y E12 de `08`, cierre en `08` v7).
> **La v3 abre una fase nueva:** migrar la entrada a `Encargo` y enseñar al Descargador a probar
> varias puertas, cruzar vestíbulos y reconocer muros. Criterios 11 a 18.

---

## Qué cambia en la v3 (leer primero)

| Cambio | Sección |
|---|---|
| La entrada deja de ser `CatalogEntry`: es `Encargo` (N10). El paquete no importa fichas de ningún modo | Entrada |
| Varias puertas por encargo, probadas en orden, con recibo por puerta | Puertas múltiples |
| Cruce de vestíbulo: seguir un enlace a archivo desde una página HTML, un solo salto | Cruce de vestíbulo |
| Reconocimiento conservador de muros; nunca se intentan pasar | Muros |
| Ruta en disco desde `cajon` + `etiqueta`, validados contra rutas peligrosas | Nombres de archivo |
| Alias por hash dentro de `grupo_alias` | Idempotencia |
| `robots.txt`: misma política en ambos modos, aplicada también al enlace del vestíbulo (**ratificada**, pregunta 7) | Cortesía de red |

---

## Objetivo

Dada una lista de `Encargo` (N10), bajar cada documento probando sus puertas en orden,
guardarlo con nombre estable, calcular su hash y reportar `DownloadResult` (N5) por cada uno,
con el recibo de cada puerta intentada. Idempotente y re-ejecutable.

**No sabe en qué modo trabaja** más allá de lo que el `Encargo` dice (D14).

**Sin agentes.** Aquí no hay nada que razonar: hay bytes que pedir y verificar.

---

## Por qué va primero

No depende de ninguna otra pieza. Se puede probar el primer día con una lista de URLs
escritas a mano — y ya tenemos ~30 URLs reales de la UAM en `08`. Da resultado visible de
inmediato y deja el terreno listo para que las piezas con agentes tengan dónde escribir.

**v3:** sigue siendo la base, ahora de dos modos. Por eso su migración va antes que cualquier
pieza nueva (`00` §6, paso 4).

---

## Alcance

### Entrada: el `Encargo` (v3)

```python
def descargar(encargo: Encargo) -> DownloadResult: ...
```

**El paquete `descargador/` no importa `CatalogEntry` ni `ArticleRef`.** Cada modo traduce su
ficha a `Encargo` en su propio paquete (la traducción jurídica, en `juridico/`; la académica, en
`academico/`), según `01` N10. Si el Descargador llegara a leer una ficha, la frontera entre
modos dejaría de existir sin que ningún test lo notara: por eso es criterio de aceptación (12).

**Validación del `Encargo` antes de pedir nada.** `cajon` y `etiqueta` llegan, en el modo
académico, de un agente que leyó un documento del usuario, y terminan siendo una ruta en disco.
Se rechazan: rutas absolutas, `..`, separadores dentro de `etiqueta`, y cualquier carácter fuera
de `[a-z0-9._-]` (más `/` solo en `cajon`). Un `Encargo` inválido no llega al bucle: produce
`ValueError` al construirse y la orquestación lo registra y sigue (criterio 17). Es D4 aplicado
a nombres de archivo.

### Normalización de URLs (requisito nuevo, por evidencia)

Las URLs de los índices reales **no son limpias**. Medido en la UJAT (E4.3 de `08`):

```
/abogado_gral/legislacion_univ2012/REGLAMENTO DE LA HONORABLE JUNTA DE GOBIERNO ….pdf
   ↑ espacios sin codificar en el nombre
/2015/abogado general/nuevos/A_DISTANCIA.pdf
   ↑ espacio en el nombre de carpeta
http://archivos.ujat.mx/…    y    https://archivos.ujat.mx/…
   ↑ ambos esquemas en la misma página
<https://…-20032024.pdf >
   ↑ espacio final dentro del propio enlace
```

Antes de cualquier petición: recortar blancos, codificar espacios y no-ASCII, resolver
relativas contra `Puerta.url_base` (en modo jurídico, `url_indice`). **La URL cruda se conserva
íntegra** en `Puerta.url` y en `IntentoPuerta.url`; la normalizada solo se usa para pedir. Si se guarda la
normalizada, se pierde la capacidad de reproducir exactamente lo que publicaba el sitio.

**v3 · una sola normalización para dos usos.** `urlnorm.py` expone también
`url_id(url, base)` (`01` N2: primeros 12 hex del SHA-256 de la URL normalizada). El Lector de
Índice debe llamar a esta función y no reimplementarla: dos normalizaciones distintas darían
dos `entry_id` para la misma dirección y romperían C20 en silencio.

**Advertencia sobre `http`:** no promover a `https` automáticamente. Algunos servidores
institucionales tienen el certificado mal configurado y la promoción convierte una descarga
que funcionaba en un fallo silencioso. Se pide tal como viene.

### El guardián de formato

**Los primeros bytes del archivo deben coincidir con una firma aceptada:**

| Firma | Formato | Extensión en disco |
|---|---|---|
| `%PDF-` | PDF | `.pdf` |
| `PK\x03\x04` | ZIP → `.docx` | `.docx` |

Si no coincide con ninguna, el resultado es `motivo_fallo="no_es_pdf"` y **el archivo no se
guarda**. El literal conserva ese nombre por compatibilidad (ver aviso de nomenclatura en N5
de `01` v1.3); su significado real es *formato no aceptado*.

Esto no es paranoia: el proyecto hermano midió que una fracción grande de sus fallos venía de
URLs "de PDF" que en realidad servían *landing pages* HTML, y que el guardián atrapó incluso
un dominio secuestrado por un casino. La misma trampa existe aquí, agravada por que los
sitios institucionales redirigen a portales de autenticación con frecuencia.

**La firma manda sobre lo que anuncia el sitio.** La extensión de la URL y
`CatalogEntry.formato_declarado` son declaraciones del índice, no hechos; un sitio que enlaza
`.pdf` y sirve otra cosa es un caso real. La extensión con que se guarda el archivo sale de
los bytes recibidos.

**Sobre `PK\x03\x04`:** es la firma genérica de ZIP, así que un `.xlsx` o un `.odt` la
pasarían. Se acepta a sabiendas: el guardián existe para atrapar landing pages y basura, no
para vigilar que una universidad no publique una hoja de cálculo. Si eso ocurre, es dato del
corpus y lo resolverá el Verificador Documental.

### Puertas múltiples (v3)

```
para cada puerta, en orden:
    visor de terceros? ─sí─► intento fallido (visor_de_terceros), siguiente puerta
    robots prohíbe?    ─sí─► intento fallido (robots_prohibido), siguiente puerta
    pedir (retry, rate limit por dominio)
    guardián acepta?   ─sí─► ÉXITO: guardar, alias por hash, fin del encargo
    ¿HTML y cruzar_vestibulos? ─sí─► cruce de vestíbulo (un salto) ─► guardián
    si no ─► intento fallido con su motivo, siguiente puerta
sin éxito: motivo = el de la única puerta, o puertas_agotadas si hubo más de una
```

- **La primera puerta que entrega un archivo aceptado gana.** Las siguientes **no se piden**:
  no hay "la mejor copia", hay la primera válida. Elegir entre ediciones es trabajo del
  Verificador Académico, que ve el contenido.
- **Cada puerta pedida deja su `IntentoPuerta`**, también las fallidas. Es el recibo que el
  Auditor de Lote necesita para sugerir una ruta.
- **Reintentos y timeout son por puerta.** Un 503 en la copia libre se reintenta cinco veces
  antes de pasar a la oficial; un 404 pasa de inmediato.
- **Con una sola puerta, el comportamiento es idéntico al de v2.** Es lo que protege al modo
  jurídico (criterio 11).
- **Una puerta `construida=True`** (resolutor DOI, `00` D3) se trata igual que las demás. La
  excepción la aplica el Lector de Lista; el Descargador **no construye nada**.

### Cruce de vestíbulo (v3)

Solo si `Encargo.cruzar_vestibulos=True` y la respuesta es HTML (el guardián la rechazó y los
primeros bytes o el `content-type` son de HTML). En modo jurídico está apagado: una landing page
sigue siendo `no_es_pdf`, como en v2.

**Dónde se busca el enlace, en este orden, y se toma el primero que exista:**

1. `<meta name="citation_pdf_url" content="…">`. Es la etiqueta de metadatos que publican
   editoriales, PubMed Central y la mayoría de repositorios institucionales para los indexadores
   académicos. Es la señal más fiable porque la declara el propio sitio.
2. `<link rel="alternate" type="application/pdf" href="…">`.
3. **Un único** `<a href>` cuyo destino termine en `.pdf`. Si hay dos o más, **no se elige**:
   una página de artículo suele enlazar también material suplementario, y adivinar cuál es el
   artículo es exactamente lo que D3 prohíbe → `vestibulo_sin_pdf`.

**Reglas duras:**

- **Un solo salto.** Si el enlace seguido devuelve otra vez HTML → `vestibulo_sin_pdf`. No hay
  recursión.
- **El enlace debe aparecer en la página** (D3). Relativo → se resuelve contra la `url_final`
  del vestíbulo, con la misma normalización.
- **La página es entrada no confiable** (D4): se parsea con `selectolax`/`lxml` sin ejecutar
  scripts, y de ella solo se extrae un atributo. Ningún texto de la página cambia el
  comportamiento.
- **El enlace pasa por todo lo que pasa una puerta:** visor, robots, rate limit, retry,
  guardián, tope de tamaño.
- **Se registra en `IntentoPuerta.enlace_vestibulo`**, y `url_final` es la del archivo, no la
  del vestíbulo.

**Fuera de alcance:** redirecciones por JavaScript o `meta refresh`, formularios, botones que
generan el PDF al vuelo. Si el sitio no expone un enlace en el HTML, el resultado honesto es
`vestibulo_sin_pdf` y la ruta sugerida la da el Auditor.

### Muros (v3)

**El Descargador nunca intenta pasar un muro** (`00` D8): no envía credenciales, no reutiliza
sesiones de usuario, no usa proxies institucionales ni servicios que eludan el acceso.

**Se reconoce `muro_de_pago` solo cuando la respuesta lo declara sin ambigüedad:**

- status `401` o `402`;
- una redirección cuyo destino coincide con un **patrón de autenticación** conocido (rutas o
  hosts de inicio de sesión, SSO o proveedores de identidad). La lista vive en datos, junto a
  los patrones de visor, no en código.

**Un `403` no es muro:** también lo producen bloqueos anti-bots y servidores mal configurados
(la UAM respondía 403 a su propio `robots.txt`, E11.1). Sigue siendo `http_error`. En la duda,
**no se diagnostica muro** (`01`, nota sobre `muro_de_pago`): un muro mal diagnosticado desanima
a buscar una copia que quizá existe.

### Nombres de archivo

```
data/<cajon>/<etiqueta>.<ext>
  jurídico:  data/norm/<inst_id>/<doc_slug>__<AAAA-MM-DD>.<ext>     (idéntica a v2)
  académico: data/papers/<autor>-<año>__<h8>.<ext>
```

**v3: el Descargador ya no compone `cajon` ni `etiqueta`; los recibe del `Encargo`** y solo
añade `<ext>`. Lo que sigue explica cómo los compone la traducción jurídica (`01` N10).

La fecha es la de **versión** del documento (`fecha_ultima_reforma`, o `fecha_publicacion`, o
en último caso la de captura). Así conviven versiones sucesivas del mismo instrumento sin
pisarse, que es exactamente lo que exige D6.

`<ext>` sale de la **firma de bytes** que reconoció el guardián (`.pdf` o `.docx`), nunca de
la URL. Es lo que permite que la fase de chunking sepa qué extractor necesita mirando solo la
ruta, sin un campo aparte que pueda desincronizarse del archivo real.

**Nunca** se usa la URL como nombre de archivo: las URLs de la UAM codifican la fecha de
consolidación y mueren en bloque cada vez que la universidad reconsolida.

### Idempotencia

1. Si el archivo ya existe **y** su SHA-256 coincide con el registrado → no se re-descarga.
2. Si existe pero el hash difiere → se descarga a un nombre nuevo y **se conservan ambos**.
   Un cambio de bytes sin cambio de fecha declarada es una señal, no un error a silenciar.
3. Nunca se sobrescribe un archivo existente. Jamás.
4. **Alias por hash (v3, `01` v2.1):** tras descargar y antes de escribir, se compara el
   SHA-256 con los ya registrados en el mismo `Encargo.grupo_alias`. Si coincide, **no se
   escribe archivo**: `exito=True`, `ruta_local` apunta al existente y `duplicado_de` lleva el
   `encargo_id` original. Es lo que evita duplicar la UAM entera cada vez que reconsolida y
   cambia todas sus URLs (D15).
5. **Idempotencia de red con varias puertas:** si el `encargo_id` ya tiene una descarga exitosa
   registrada y su archivo existe con el hash registrado, **no se pide ninguna puerta**.

### Cortesía de red (D8)

- User-Agent identificado: nombre del proyecto + URL + correo de contacto.
- **`robots.txt`: se consulta por dominio, se cachea, y su política es FAIL-OPEN.**
  - `200` → se parsea y se obedece. Si prohíbe, `motivo_fallo="robots_prohibido"`, el ítem va
    a cola manual y **no se fuerza**.
  - `404` / `410` → permitido. No hay archivo de política; el estándar dice que todo está
    permitido.
  - **Cualquier otro status, o error de red → permitido, con `logging.warning`.**

  **Medido (E11.1 de `08`, 2026-09-06):** la UAM responde **403 a `/robots.txt`** y **200 a
  sus PDF**, mismo host y misma sesión. Persiste con y sin cabecera de User-Agent, así que no
  es el patrón de servidores que bloquean clientes sin UA. **Con fail-closed, la cosecha de la
  UAM habría terminado en cero documentos sin que existiera prohibición alguna.**

  La asimetría del costo justifica la regla: fail-open sobre un sitio que sí prohibía es un
  error recuperable y registrado en el log; fail-closed sobre un sitio que no prohibía nada es
  un corpus vacío sin diagnóstico. Y son sitios institucionales con documentos públicos por
  ley, no adversarios.

  > **No cambiar esta política a fail-closed sin releer E11.1.** El código ya se comporta así
  > y está cubierto por tests; "endurecerlo" rompe la primera institución del corpus.

  **Lo que todavía NO está probado en campo:** que un `robots.txt` legible se respete de
  verdad. La corrida de la UAM nunca llegó a parsear uno (E6.15 de `08`). Ese camino solo
  está cubierto por tests.

  **v3 · modo académico (ratificada 2026-09-10, pregunta 7):** **la misma política en ambos
  modos**, aplicada a cada puerta **y al enlace del vestíbulo**. El razonamiento: la parte
  delicada del fail-open es solo el `robots.txt` *ilegible*; uno legible que prohíbe **se
  obedece siempre**, en cualquier modo, y eso ya cubre a las editoriales que no quieren
  descargas automáticas. Endurecer a fail-closed castigaría repositorios pequeños con
  servidores mal configurados, justo donde viven muchas copias libres. Una prohibición no es
  un callejón sin salida: es `robots_prohibido` en el recibo y una ruta sugerida en el informe.
- **Rate limit por dominio**, no global: ≥ 1 s entre peticiones al mismo host. Dominios
  distintos pueden ir en paralelo. **v3:** el limitador es uno para todas las puertas, enlaces
  de vestíbulo y modos; dos lotes que piden a la misma editorial comparten su segundo.
- Reintentos: 5 intentos, backoff exponencial (`multiplier=2`, `max=60`), solo en 429/5xx y
  timeouts. Un 404 no se reintenta.

> El envelope de 5 intentos viene de una lección medida allá: 3 intentos con ~3-4 s no cubren
> ni una ráfaga de 503 ni una de 429. Y tras un 429, esperar 20–30 minutos antes de
> relanzar — reintentar de inmediato alimenta el throttling.

### Límites

- Timeout 30 s **por puerta** (v3; con una sola puerta equivale al "por documento" de v2).
- Tamaño máximo 100 MB → `motivo_fallo="demasiado_grande"` + cola manual.
- Errores de red o contenido inesperado → `DownloadResult(exito=False)` + log de warning.
  **Nunca una excepción que tumbe la corrida.**

---

## No-alcance

- NO abre ni lee el contenido del PDF (Verificador Documental o Académico). Del HTML de un
  vestíbulo solo extrae un enlace.
- NO decide si la URL es legítima (en modo jurídico lo fijó el Localizador vía dominio; en el
  académico lo decide el contenido, D13).
- NO decide si lo descargado es el artículo pedido ni cuál edición conviene.
- NO convierte formatos.
- NO busca puertas nuevas: no consulta buscadores, índices de acceso abierto ni resolutores
  por su cuenta. Prueba las que trae el `Encargo`.
- NO construye URLs. La única excepción de D3 la aplica el Lector de Lista, antes.
- NO pasa muros.
- NO sabe de modos: lee `Encargo`, nunca `CatalogEntry` ni `ArticleRef`.

---

## Diseño

```
descargador/
  fetch.py        # httpx.Client compartido, retry, rate limit por dominio
  urlnorm.py      # normalización de URL antes de pedir; url_id() (v3)
  guard.py        # guardián %PDF-, límite de tamaño, content-type
  paths.py        # ruta desde cajon + etiqueta + ext; validación anti-traversal (v3)
  robots.py       # caché de robots.txt por dominio
  puertas.py      # bucle de puertas y recibo IntentoPuerta (v3)
  vestibulo.py    # búsqueda del enlace a archivo en HTML, un salto (v3)
  muros.py        # reconocimiento conservador de muro_de_pago (v3)
  store.py        # SQLite: descargas (antes documentos, ver `07` v2); hash; idempotencia; alias por hash (v3)
  models.py       # importa Encargo y DownloadResult de los contratos; nada de fichas
datos/
  patrones.toml   # patrones de visores de terceros y de autenticación (v3: muros)

juridico/traduccion.py   # CatalogEntry → Encargo   (fuera de descargador/, D14)
academico/traduccion.py  # ArticleRef  → Encargo   (llega con el Lector de Lista)
```

**Dónde viven los patrones.** Si el código actual tiene los patrones de visor en otro sitio, se
respeta su ubicación; lo que importa es que visores y muros vivan juntos y en datos.

**Frontera modelo→persistencia:** todo valor numérico que llegue de una librería externa se
convierte a tipo nativo de Python antes de guardarse. `model_copy(update=...)` **no valida**;
un tipo ajeno puede colarse hasta SQLite como BLOB sin error ni warning, y el fallo aparece
recién al *leer*. Ya pasó allá.

---

## Criterios de aceptación

1. ~~**Corrida real UAM:**~~ **CUMPLIDO (2026-09-06, E11 de `08`): 45 de 45 exitosas (100 %).**
   El criterio pedía ≥ 90 % sobre ~30 URLs; el índice resultó tener **45** documentos
   (31 vigentes + 8 históricos + 1 abrogado + 1 consolidado + 5 anexos, 3 de ellos `.docx`).
   Cero fallos. Corpus de 12.6 MB en ~2 min con el rate limit de 1 s.
2. ~~**Corrida real UJAT — la prueba de suciedad.**~~ **CUMPLIDO (2026-09-06, E12 de `08`): 105 de 105.** Con sus ~60 URLs reales, que incluyen
   espacios sin codificar, `http` y `https` mezclados y rutas de 2012 a 2026. **Dos cosas se
   miden por separado:** cuántas se normalizaron bien (debe ser el 100 %) y cuántas
   respondieron (probablemente menos — las rutas viejas son candidatas a enlace muerto,
   E6.7 de `08`). Un enlace muerto es un dato del corpus, no un fallo del Descargador.
3. **Guardián probado:** una URL que devuelve HTML produce `no_es_pdf` y **no deja archivo**
   en disco.
10. **`.docx` aceptado (cumplido, E11.4):** los tres anexos `.docx` reales de la UAM
    (**E1.6** de `08`) se descargaron, pasaron el guardián por su firma `PK\x03\x04` y quedaron
    en disco **con extensión `.docx`**, derivada de los bytes y no de la URL. Un archivo cuya
    firma no sea `%PDF-` ni `PK\x03\x04` sigue produciendo `no_es_pdf`.
4. **Idempotencia — en dos niveles, y se miden por separado:**
   - **De disco y base (cumplido, E11):** una segunda corrida completa no crea archivos nuevos
     ni filas nuevas. Verificado sobre la UAM.
   - **De red (cumplido según el cierre de `08` v7):** una segunda corrida tampoco debe **pedir** la URL cuando el
     `sha256` ya registrado en `documentos` coincide. Exige que `descargar()` consulte
     `Store.hash_registrado` antes de llamar al `Fetcher`. Sin esto, re-cosechar 40
     universidades son 1 600 peticiones inútiles.
5. **Versión nueva:** ante un documento cuyo hash cambió, quedan dos archivos y dos filas, y
   ninguno se perdió.
6. **URL cruda preservada:** tras normalizar y descargar, `CatalogEntry.url_documento` sigue
   conteniendo la URL tal como la publicaba el sitio, espacios incluidos.
7. **Cortesía verificada** (cumplido según el cierre de `08` v7): el UA enviado es el configurado, y hay ≥ 1 s entre peticiones al
   mismo dominio.
   **Ojo con cómo se mide (E11.7 de `08`):** `httpx` registra al **recibir** la respuesta, no
   al enviar la petición, así que los huecos entre sus líneas de log **no** son los intervalos
   entre peticiones. Este criterio **no se puede verificar leyendo el log de `httpx`**. Exige
   que `RateLimiter.esperar` emita su propia línea con los segundos que durmió.
8. **Robustez:** una lista de 30 entradas con 5 URLs rotas termina la corrida completa y
   reporta los 5 fallos con su motivo. Cero excepciones no capturadas.
9. **Hash reproducible:** el SHA-256 de un archivo bajado dos veces es idéntico.

> **Criterios 1–10 (fase v1):** cumplidos. **Con la v3 se re-verifican con `Encargo`** a través
> del criterio 11; ninguno se relaja.

### Fase v3 — Encargo, puertas y dos modos

11. **Migración sin regresión** (`01`, §Migración):
    - la suite completa pasa con solo cambios mecánicos (construir `Encargo` por la traducción
      jurídica; leer `encargo_id` en vez de `entry_id`) y **ninguna aserción de comportamiento
      cambia**;
    - UAM y UJAT en base limpia: **156/156 medido el 2026-09-18**, rutas jurídicas con la misma forma que en v2;
    - un `Encargo` jurídico que falla produce los mismos motivos que v2: nunca
      `puertas_agotadas`, nunca `vestibulo_sin_pdf`;
    - los dos históricos del Reglamento de Estudios Superiores de la UAM producen dos `entry_id`
      distintos y dos archivos.
12. **Frontera de modos:** ningún módulo de `descargador/` importa `CatalogEntry` ni
    `ArticleRef`. Se verifica con un test que inspecciona los imports, no a ojo.
13. **Puertas múltiples:** con tres puertas, la primera 404 y la segunda PDF → `exito=True`,
    `puerta_usada=1`, dos `intentos`, y **la tercera nunca se pidió** (`pytest-httpx` falla si
    hay peticiones no esperadas). Con todas fallidas → `puertas_agotadas` y un intento por
    puerta con su motivo.
14. **Vestíbulo:** HTML con `citation_pdf_url` → un salto, archivo guardado,
    `enlace_vestibulo` registrado. HTML sin enlace → `vestibulo_sin_pdf`. Enlace que devuelve
    HTML → `vestibulo_sin_pdf` y **ninguna segunda petición**. Dos `<a>` a `.pdf` sin meta →
    `vestibulo_sin_pdf`. El mismo HTML con `cruzar_vestibulos=False` → `no_es_pdf`.
15. **Muros:** `401` y `402` → `muro_de_pago`; redirección a un patrón de autenticación →
    `muro_de_pago`; `403` → `http_error`. Ninguna petición lleva credenciales.
16. **Alias por hash:** los mismos bytes desde otra URL y el mismo `grupo_alias` → sin archivo
    nuevo, `duplicado_de` con el `encargo_id` original. Los mismos bytes con **otro**
    `grupo_alias` → archivo propio (el alias no cruza grupos).
17. **Rutas seguras:** `etiqueta` con `..`, `/` o caracteres fuera del conjunto, y `cajon`
    absoluto o con `..`, se rechazan al construir el `Encargo`; nada se escribe fuera de
    `data/`.
18. **Primera corrida académica real — medición, no umbral.** Con encargos armados desde una
    lista real, como la primera corrida jurídica usó slugs provisionales. `01` §Modo académico
    se diseñó contra `Geologia_dois_.docx`, que nunca llegó al repositorio (`01` v2.5). La
    corrida usó `datos/lotes/bloque-a.txt` (8 fichas, M30). Se miden por separado: cuántas
    puertas `copia_libre` entregaron archivo directo, cuántos vestíbulos se cruzaron con éxito, cuántos `vestibulo_sin_pdf`,
    `muro_de_pago` y `robots_prohibido`. **No hay porcentaje mínimo:** es la primera medición
    de un terreno nuevo. Se registra en `08` como evidencia nueva y alimenta las preguntas 8 y 9.
    **Medido el 2026-09-25 (E15 de `08`), 3/7.** 7 encargos (A.5 sin puertas), 16 puertas
    declaradas y 12 pedidas.
    - `copia_libre` con archivo directo: **3** de 5 pedidas, las tres en la puerta 0 (E15.2);
    - vestíbulos cruzados con éxito: **0**. Hubo dos saltos (A.6, dos veces) y los dos
      volvieron a HTML (E15.6);
    - `vestibulo_sin_pdf`: **3** intentos (A.4 ×1, A.6 ×2);
    - `muro_de_pago`: **0**, aunque A.6 pasó por `idp.nature.com/authorize` en una
      redirección intermedia que `es_muro_de_pago` no ve (E15.3);
    - `robots_prohibido`: **0**, con fail-open en dos hosts (E15.7). Tres hosts se visitaron
      solo por redirección, sin consultar su `robots.txt` (E15.8);
    - además, **6 `http_error`, todos `403`**, en cuatro hosts; son el primer dato de la
      pregunta 8 (E15.4).

---

## Preguntas abiertas (agenda de esta conversación)

1. ~~**`.docx` y otros formatos.**~~ **Resuelta a favor (2026-09-03, `01` v1.3).** Se aceptan
   `.pdf` y `.docx`, de cualquier institución — no solo los anexos de la UAM. Guardián de dos
   firmas (`%PDF-`, `PK\x03\x04`) y extensión en disco derivada de los bytes, no de la URL.
   La fase de chunking distingue por la extensión de `ruta_local`. Ver §"El guardián de
   formato". **Sigue fuera de alcance:** cualquier otro formato (`.xls`, `.odt`, imágenes).
2. ~~**¿Se descarga el PDF consolidado completo?**~~ **Resuelta a favor (2026-09-06, C19 de
   `08`).** Se descarga, con `tipo_norma="otro"`. El de la UAM pesa **4.3 MB**, muy lejos del
   tope de 100 MB, y el corpus entero de una universidad son **12.6 MB** — del orden de 500 MB
   para las ~40 públicas. Es barato, sirve de respaldo y es la base natural para el diff.
3. ~~**Persistir la URL candidata cuando falla.**~~ **Resuelta por diseño en v3:** cada puerta pedida queda en `IntentoPuerta` con su URL cruda, también las fallidas. Lección directa del proyecto hermano: allá no
   se persistieron las URLs de PDF y por eso los fallos **no fueron recuperables después**.
   Aquí la URL ya vive en `CatalogEntry`, así que el problema está resuelto de nacimiento —
   verificar que efectivamente sea así antes de firmar la fase.
4. ~~**¿Verificación de certificado TLS estricta?**~~ **Cerrada: se queda estricta** (E12.3 de `08`, 2026-09-06). *Texto original conservado:* Algunos sitios institucionales
   mexicanos tienen certificados mal configurados. Relajarlo abre un agujero; no relajarlo
   pierde documentos. **La corrida de la UAM no aporta nada aquí** (45/45 con TLS estricto,
   pero es un solo dominio bien configurado). **La UJAT es el caso que decide**, porque mezcla
   `http` y `https` en la misma página y sirve desde `archivos.ujat.mx`. Mantener estricto
   hasta tener ese dato.
5. **¿Se reintenta un enlace muerto con la ruta actual?** La UJAT sirve documentos desde
   carpetas de 2012 que pueden haber desaparecido. Tentación: adivinar la ruta nueva. **D3 lo
   prohíbe** — construir URLs está vedado. La salida correcta es la cola manual con el nombre
   exacto del documento.
6. **Paralelismo:** ¿cuántos dominios en vuelo a la vez? Propuesta de partida: 4. Sin medir:
   la corrida de la UAM fue de un solo dominio, en serie. **v3:** el modo académico es el
   primer caso con muchos dominios distintos por lote; el criterio 18 da el primer dato.
7. ~~**`robots.txt` en modo académico**~~ **Ratificada (2026-09-10): la misma política que el
   modo jurídico**, aplicada también al enlace del vestíbulo (§Cortesía de red). Gatillo de
   revisión: el criterio 18.
8. **Protecciones anti-bots en repositorios.** Algunos sitios sirven una página de desafío en
   lugar del PDF. Hoy caería en `vestibulo_sin_pdf` o `http_error`, que es honesto pero no
   distingue la causa. ¿Merece un motivo propio? **No se decide sin medir** (criterio 18).
9. **¿Cruzar vestíbulos en modo jurídico?** Apagado por defecto para conservar el 150/150
   medido. Gatillo de revisión: un `no_es_pdf` sobre una página institucional que enlaza el PDF
   correcto.
10. **La regla del `<a>` único** (§Cruce de vestíbulo) puede ser demasiado estricta o demasiado
    laxa. Medir en el criterio 18 cuántos vestíbulos se perdieron por tener dos enlaces y
    cuántos enlaces únicos resultaron no ser el artículo (lo dirá el Verificador Académico).

---

## Registro de consideraciones diferidas

*(Se llena durante la implementación. Todo lo que se decida anotar en vez de resolver, con su
gatillo de revisión.)*

---

### CD-05-1 · `%` literal en rutas de URL

**Anotado en:** M3 (normalización de URL) · 2026-09-02
**Estado:** aceptado a sabiendas, sin resolver.

`urlnorm.py` codifica ruta y query con `quote(..., safe=_SAFE)`, donde:

```python
_SAFE = "/:@!$&'()*+,;=%"
```

El `%` está en el conjunto seguro **a propósito**: es lo que hace que la normalización sea
idempotente. Sin él, una URL que el sitio ya publica codificada (`REGLAMENTO%20DE%20LA…pdf`,
caso real de la UJAT) se convertiría en `%2520` en la segunda pasada y la petición fallaría.
El criterio de aceptación de idempotencia lo exige.

**El costo:** un `%` **literal** en un nombre de archivo publicado —del tipo
`DESCUENTO 50%.pdf` o `INCREMENTO 3.5% SALARIAL.pdf`— tampoco se codifica, y la URL resultante
es inválida. La petición fallará con un error que **no dirá que la causa es la codificación**.

Se acepta porque el caso es raro en sitios institucionales mexicanos (nombres de archivo con
`%` literal), y porque la alternativa —distinguir `%XX` válido de `%` suelto— añade una regex
y un modo de fallo nuevo para cubrir un caso aún no observado en las mediciones de `08`.

**Gatillo de revisión:** un `motivo_fallo="http_error"` o `"url_muerta"` sobre una URL cuya
ruta contenga un `%` **no seguido de dos dígitos hexadecimales**. Basta con un caso.

**Solución cuando se dispare:** codificar solo los `%` sueltos antes de llamar a `quote`,
detectando los escapes válidos con `re.sub(r"%(?![0-9A-Fa-f]{2})", "%25", ruta)`. Es un cambio
de dos líneas y un test; no se hace ahora porque no hay evidencia de que haga falta.

---

### CD-05-2 · El User-Agent hay que acordarse de ponerlo en cada llamador

**Anotado en:** M10 (primera corrida real) · 2026-09-06
**Estado:** ~~aceptado a sabiendas~~ **resuelta en `07` v2** (§Cliente HTTP único, criterio 15).

`RobotsCache` recibe el `user_agent` para **evaluar** las reglas, pero el `fetcher` que hace
el GET de `/robots.txt` es una función inyectada, y sus cabeceras son responsabilidad de quien
la escribe. En la primera corrida se olvidó ponerlas: el `Fetcher` mandaba UA y el fetcher de
robots no.

**El síntoma fue engañoso.** Se sospechó del UA porque la UAM devolvía 403 en `/robots.txt` y
200 en los PDF — el patrón exacto de D8. Al añadir la cabecera, **el 403 persistió**: la causa
era otra (E11.1), pero el bug real existía y se habría quedado ahí sin diagnosticar.

**El diseño lo permite:** el UA vive en `Settings`, pero cada llamador tiene que acordarse de
usarlo. Nada lo obliga.

**Gatillo de revisión:** la conversación de la spec `07`. **Solución:** que `RobotsCache`
reciba un `httpx.Client` ya configurado con las cabeceras, en vez de una función suelta. Así
el UA se pone una sola vez, en un solo sitio, y ningún llamador puede olvidarlo.

**v3 agrava el riesgo:** el enlace del vestíbulo es un llamador más de robots y fetch. Si la
solución no llega antes de implementar `vestibulo.py`, ese módulo **debe** usar el mismo
`httpx.Client` configurado, nunca uno propio.

---

### CD-05-3 · `DownloadResult` da defaults que N5 no declara

**Anotado en:** M15 (contratos de la v2.4) · 2026-09-13
**Estado:** aceptado a sabiendas, sin resolver.

N5 declara `ruta_local`, `sha256`, `bytes`, `content_type`, `http_status` y `url_final`
como `X | None` **sin** `= None`, lo que en Pydantic v2 los hace obligatorios. Desde M2, el
código les da `= None`. La divergencia se detectó en M15, al construir `Puerta`.

**Se conserva.** Endurecerlo obligaría a pasar seis campos en cada construcción de un
resultado fallido, donde todos valen `None` por definición, y rompería los 102 tests sin
ganar nada medible.

**Las clases nuevas sí siguen `01` al pie** (`Puerta`, `Encargo`, `IntentoPuerta`): no tienen
convención previa que romper, y el campo obligatorio fuerza a cada llamador a decidir. En
`Puerta.url_base` eso importa: si se pudiera omitir, una puerta con URL relativa fallaría en
silencio contra `None` en vez de resolverse contra su base.

**Gatillo de revisión:** un `DownloadResult` construido sin un campo que sí debía llevar —una
descarga exitosa sin `sha256`, o un fallo de red sin `http_status`— que pase sin error y
llegue a la base. Basta con un caso.

**Solución cuando se dispare:** quitar los defaults de N5 y ajustar los llamadores, o añadir
un validador de modelo que exija los campos de proveniencia cuando `exito=True`. Lo segundo
es más barato y atrapa el caso real; lo primero es más fiel al contrato.