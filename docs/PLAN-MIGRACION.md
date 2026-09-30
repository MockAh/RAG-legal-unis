# Plan de migración — Descargador a Encargo

Base al arrancar: 102 tests verdes, commit de M15.
Referencia: `docs/05` criterios 11–18, `docs/01` §Migración.

## M15.1 · Renombre pendiente de N5
- `DownloadResult.entry_id` → `encargo_id` en `contracts/descarga.py`.
- Todos los llamadores pasan a `encargo_id=`: `descargador/descargar.py`
  (3 sitios), `descargador/store.py`, `tests/test_store.py`,
  `tests/test_descargar.py`, `tests/test_contracts.py`.
- La columna de SQLite NO se toca en esta tarea; `store.py` mapea
  `resultado.encargo_id` a la columna existente.
- Criterio: `grep -n "entry_id" legisuni/contracts/descarga.py` vacío, y
  `grep -rn "entry_id=" legisuni/descargador/ tests/` sin construcciones de
  DownloadResult. `paths.py` queda fuera a propósito: su `entry_id` es N2, no
  N5, y M17 lo elimina de ahí.
- Ninguna aserción de comportamiento cambia. Si alguna tiene que cambiar, DETENTE.
- Commit: `M15.1: renombre de entry_id a encargo_id en DownloadResult`

## M16 · Traducción jurídica a Encargo
- Nuevo `legisuni/juridico/traduccion.py`: `CatalogEntry` → `Encargo`,
  según `docs/01` §Migración (el ejemplo de código está ahí; respétalo).
- `config.py` gana `data_root` en `Settings`.
- Nuevo `tests/test_traduccion_juridica.py`.
- Criterios 11 y 12 de `docs/05`. La ruta resultante es `data/norm/uam/...`.
- Nota: el `entry_id` de tres segmentos de `01` v2.0 aún no está
  implementado en `cosecha.py`; se hace en M23.
- Commit: `M16: traducción jurídica a Encargo y data_root`

## M17 · paths.py sin CatalogEntry
- La ruta se arma desde `cajon` + `etiqueta` + extensión de los bytes:
  `ruta_documento(data_root, cajon, etiqueta, extension, sha256=None)`.
- Validación anti-traversal en `ruta_documento` (cinturón y tirantes: el
  rechazo "de verdad" al construir el `Encargo` es M18; esta es la última
  línea antes de escribir a disco).
- Se unifica dentro de `paths.py`: su parámetro pasa a ser un único
  `data_root` (equivalente a `Settings.data_root`, "data/"), no el viejo
  `data_dir` ("data/norm"). `Settings.data_dir` **no se toca**: solo lo
  consume `descargar.py`, y retirarlo de ahí es M19.
- `doc_slug_de` y `fecha_de_version` se borran de `paths.py`: sin
  llamador fuera de `descargar.py` (que ya queda roto por esta tarea) y
  `traduccion.py` ya calcula la fecha de forma equivalente.
- Criterio: `grep -rn CatalogEntry legisuni/descargador/paths.py` vacío; el
  `grep` sobre todo el paquete (criterio 12 de `docs/05`) se cumple en M19.
- **`descargar.py` y `tests/test_descargar.py` quedan rotos por esta tarea**
  (llaman a la firma vieja de `ruta_documento` y a `paths.fecha_de_version`,
  que ya no existe): la suite queda roja hasta M19. Por eso M19 se adelanta
  a M18 abajo, para cerrar la ventana cuanto antes.
- Commit: `M17: rutas desde cajón y etiqueta, con validación (suite roja hasta M19)`

## M19 · descargar(encargo)
- `descargar()` recibe `Encargo`, usa una puerta (`puertas[0]`), emite el
  recibo de un `IntentoPuerta`. **Sin cambio de comportamiento.**
- Se adelanta a M18 porque M17 deja `descargar.py` sin compilar contra la
  nueva `paths.py`: cuanto antes se cierre esa ventana, mejor.
- Criterios 11 y 12. `pytest -q` verde.
- Commit: `M19: descargar recibe Encargo`

## M18 · Encargo valida cajon y etiqueta
- `ValueError` al construir con `..`, `/`, ruta absoluta o caracteres fuera
  del conjunto. Criterio 17 de `docs/05`.
- Los patrones y `validar_cajon`/`validar_etiqueta` se movieron a
  `contracts/rutas.py`: módulo auxiliar, no un contrato nuevo (no añade ni
  cambia campos de N10). Es la única definición en el paquete; tanto
  `Encargo` como `descargador/paths.py` (cinturón y tirantes de M17) la
  importan de ahí.
- Commit: `M18: Encargo rechaza cajones y etiquetas peligrosos`

## M20 · Tablas descargas e intentos
- `descargas`: espejo de N5, PK `(encargo_id, sha256)`, índice por `grupo_alias`.
- `intentos`: espejo de `IntentoPuerta`, FK `encargo_id`, una fila por puerta pedida.
- Base **limpia**: `legisuni.db` (v1) no se toca ni se migra; la v2 se crea nueva.
- `documentos` no se borra: `docs/07` la divide, no la elimina.
- `grupo_alias` viene del `Encargo`, no de `DownloadResult`. No cambiar N5.
- Criterio 16 de `docs/07`. Verificación: `.schema` sobre base nueva.
- Commit: `M20: tablas descargas e intentos`

## M21 · Idempotencia de red por defecto
- Regla 5 de `docs/05`: no se vuelve a pedir lo ya registrado, sin `--reanudar`.
- Criterios 4 y 11. Test con `httpx_mock` sin respuestas registradas.
- Lee lo ya registrado contra `documentos` (`Store.hash_registrado`/`ruta_registrada`,
  sin cambios): es lo que nombra el criterio 4 literalmente, y `descargas` (M20)
  todavía no tiene lectura ni escritor.
- **Excepción explícita al criterio 11, autorizada por el criterio 4 del mismo
  `docs/05`:** `test_default_no_omite_y_llama_al_fetcher` probaba justo el
  comportamiento que la Regla 5 invierte (sin bandera, se pedía la red). Se
  reemplaza por el test decisivo (misma base, `httpx_mock` sin respuestas
  registradas); no es un renombre cosmético, es la aserción cambiando a
  propósito.
- Commit: `M21: idempotencia de red por defecto`

## M22 · Test de frontera de modos
- `tests/test_frontera_modos.py`: inspección de imports. Criterio 12.
- Commit: `M22: test de frontera entre modos`

## M23a · entry_id de tres segmentos (juridico/)
- Nuevo `legisuni/juridico/identificadores.py`: `entry_id(inst_id, doc_slug,
  url_documento, url_indice) -> str`, formato `f"{inst_id}:{doc_slug}:{url_id}"`
  (`01` N2, nota sobre `entry_id`).
- `url_id(url, base)` vive en `descargador/urlnorm.py`, no en `juridico/`: es
  el criterio de una sola normalización de `docs/05` v3 (línea 89) — dos
  normalizaciones distintas darían dos `url_id` para la misma dirección y
  romperían C20 en silencio. `juridico/identificadores.py` la importa, no la
  reimplementa.
- `doc_slug` sigue sin derivarse de la URL: llega como parámetro; su
  mecanismo (por sitio) no se toca aquí.
- Sin compatibilidad con los `entry_id` de v1: el cambio de formato es
  intencional (M24 corre contra base v2 limpia).
- No toca `scripts/` ni `descargar.py` (eso es M23c).
- Tests: dos históricos de la UAM (mismo `doc_slug`, URLs distintas) →
  `entry_id` distintos (C20 de `docs/08`, E11.6); "acuerdos rect 2.pdf" y
  "acuerdos%20rect%202.pdf" (mismo `url_indice`) → mismo `entry_id`/`url_id`
  (E12.2).
- Commit: `M23a: entry_id de tres segmentos en juridico/`

## M23b · Ningún enlace publicado se pierde en la extracción
- Dos defectos distintos (`01` v2.4, changelog): filtro por extensión que
  ignora 4 enlaces de la UJAT con salto de línea en el `href`; heurística de
  slug que pierde 2 documentos en la UAM por colisión de `entry_id` de dos
  segmentos (uno de ellos, el ancla vacía de E1.5 de `docs/08`).
- Filtro: se recorta el `href` antes de comprobar la extensión, en
  `entradas_desde_html` de `cosecha.py` y `cosecha_uam.py`. `url_documento`
  sigue guardándose crudo (D5); solo cambia la comprobación.
- Colisión de slug: no se toca `_doc_slug_desde_href`. Se ensambla `entry_id`
  con `identificadores.entry_id` de M23a (tres segmentos) en vez de
  `f"{inst_id}:{doc_slug}"`: el `url_id` distingue por construcción los pares
  que compartían slug (`"2026"` y `"rjd"`). Aplicado en `cosecha_uam.py` y
  también en `cosecha.py` (UJAT no lo necesitaba para llegar a 109, pero dos
  formatos de `encargo_id` en la misma base v2 ensuciarían el criterio 11).
- Verificado que el salto de línea no cambia el `url_id` (`normalizar`
  recorta antes de hashear): los 4 enlaces de la UJAT dan el mismo `url_id`
  con o sin `\n`.
- No toca `main()` de ningún script (descarga/escritura), ni ejecuta nada
  contra la red.
- Tests sobre las fixtures reales (`fixtures/uam-index.html`,
  `fixtures/ujat-*.html`): UAM → 47, UJAT → 109, los 156 `entry_id`
  combinados son únicos.
- Commit: `M23b: ningún enlace publicado se pierde en la extracción`

## M23 · cosecha.py arma Encargos
- `scripts/cosecha.py` construye `Encargo` vía `juridico/traduccion.py`.
- ~~Arregla el filtro de extensión (los 4 enlaces con salto de línea, E13 de `08`).~~
  **Hecho en M23b.**
- ~~Implementa el `entry_id` de tres segmentos (`inst_id:doc_slug:url_id`) de `01` v2.0.~~
  **Hecho en M23a/M23b.**
- **Aviso de M21:** `cosecha.py` debe escribir en ambas tablas (`guardar` y
  `guardar_descarga`), o la idempotencia de M21 —que lee `documentos`— dejará
  de funcionar y M24 volvería a descargar los 156 en cada corrida.
  Alternativa a decidir en M23: mudar también la lectura a `descargas`.
- Verificación: `--dry-run` → UAM 47, UJAT 109.
- Commit: `M23: cosecha arma Encargos y no pierde enlaces`

## M23c · main() de cosecha.py y cosecha_uam.py contra Encargo
- Decisión tomada (aviso de M21 arriba): se escribe en **ambas** tablas,
  `store.guardar(resultado)` y `store.guardar_descarga(resultado,
  encargo.grupo_alias)`. Es transitorio.
- **Deuda para después de M24:** la idempotencia de M21 sigue leyendo
  `documentos` (`hash_registrado`/`ruta_registrada`); mudar esa lectura a
  `descargas` no se hizo aquí y queda pendiente.
- `--dry-run` construye el `Encargo` de cada entrada (`traducir` es pura) y
  muestra `encargo_id`, `cajon/etiqueta` y la URL — así las 156 entradas
  pasan por la validación de M18 (criterio 17 de `docs/05`) antes de M24,
  sin tocar la red. Sigue terminando antes de construir el `Fetcher`.
- Commit: `M23c: main() de cosecha.py y cosecha_uam.py contra Encargo`

## M23d · _doc_slug_desde_href sanea en todas sus ramas
- Causa del fallo dejado pendiente por M23c: `_doc_slug_desde_href` de
  `cosecha_uam.py` tenía dos ramas y solo la de respaldo pasaba por
  `paths.sanear`; la rama del sufijo del nombre de archivo devolvía texto
  crudo (`ANEXO1`, `3A`, `3B`, `ANEXO3C`), que M18 rechaza por mayúsculas.
- Auditado `cosecha.py`: una sola rama, siempre pasa por `paths.sanear`
  (que ya hace `.lower()`). No tiene el mismo defecto, no se toca.
- Fix en `cosecha_uam.py`: esa rama también pasa por `paths.sanear`. Da
  `anexo1`, `3a`, `3b`, `anexo3c` — los nombres que v1 dejó en disco
  (criterio 11) — sin mover ningún otro slug (45 únicos antes y después de
  47 entradas UAM).
- Test nuevo en `tests/test_extraccion_indices.py` con los 4 `href` reales.
- Verificación: 47/109/156 sin cambios; `--dry-run` de la UAM ya no lanza
  `ValidationError`.
- Commit: `M23d: _doc_slug_desde_href sanea en todas sus ramas`

## M24 · Corrida real (puerta de control) — la ejecuta el humano
- **La ejecuta el humano, no Claude Code.**
- Prerrequisito: `.env` con `DATA_ROOT`, base v2 limpia. Antes de correrla,
  `data/` debe estar vacío y `legisuni_v2.db` no debe existir todavía
  (E13.6 de `docs/08`).
- Comandos exactos, con las mismas `--url-indice` que usa
  `tests/test_extraccion_indices.py`:

  ```bash
  .venv/bin/python scripts/cosecha_uam.py --html fixtures/uam-index.html \
    --url-indice https://www.uam.mx/legislacion/index.html

  .venv/bin/python scripts/cosecha.py --inst-id ujat \
    --html fixtures/ujat-15763.html --url-indice https://www.ujat.mx/abogado/15763 \
    --html fixtures/ujat-16443.html --url-indice https://www.ujat.mx/abogado/16443 \
    --html fixtures/ujat-17669.html --url-indice https://www.ujat.mx/abogado/17669 \
    --html fixtures/ujat-33794.html --url-indice https://www.ujat.mx/abogado/33794 \
    --html fixtures/ujat-4232.html --url-indice https://www.ujat.mx/abogado/4232
  ```

  **Los `url_id` dependen de estas URLs exactas:** cambiar una base cambia
  los identificadores resultantes y rompe la correspondencia con lo que
  fija `tests/test_extraccion_indices.py`.
- UAM + UJAT: 47 + 109 = 156/156, dos `entry_id` distintos para el RES.
- Si no da 156, no se sigue a M25.
## M25 · Cliente HTTP único
- Referencia: `docs/07` §Cliente HTTP único y su criterio 15; cierra CD-05-2
  de `docs/05`.
- La orquestación construye **un solo** `httpx.Client` (`construir_cliente`,
  en `descargador/fetch.py`): User-Agent, timeout y TLS estricto desde
  `Settings`. Se inyecta a `Fetcher` y a `RobotsCache`. Ningún módulo crea
  su propio cliente ni recibe una función para pedir.
- `RobotsCache(user_agent, cliente)` reemplaza a `RobotsCache(user_agent,
  fetcher)`; `_fetcher_robots` desaparece de ambos scripts.
- `Fetcher.cliente` pasa a **obligatorio**: se quita el respaldo
  `httpx.Client()`. Los helpers de `test_fetch.py` y `test_descargar.py`
  solo cambian en el montaje.
- **El fail-open de robots no cambia** (E11.1 de `docs/08`: la UAM responde
  403 a `/robots.txt` y 200 a sus PDF). Se añade un test de 403 que antes
  no existía; `tests/test_robots.py` cambia solo en el montaje, ninguna
  aserción existente se toca.
- Tests: `tests/test_cliente_http.py`. Criterio 15 — Fetcher y RobotsCache
  reciben el mismo objeto y la petición a `/robots.txt` lleva el User-Agent
  configurado. Un test corre `main` de ambos scripts (con `--limite 0`, sin
  red) y comprueba la identidad del cliente en el cableado real, porque el
  `--dry-run` termina antes de construir nada. El cruce de vestíbulo
  llega en M28: añadirlo al test de identidad es una línea.
- **Deudas detectadas, NO se arreglan en M25:**
  1. `user_agent` duplicado: `RobotsCache` lo recibe como parámetro (para
     `can_fetch`) y el cliente lo lleva en su cabecera. Dos fuentes que
     podrían divergir.
  2. `Fetcher` sigue mandando `User-Agent` y `timeout` en cada petición,
     redundantes con los del cliente.
- Verificación: `--dry-run` → UAM 47, UJAT 109. El `--dry-run` no ejercita
  el cableado; lo cubre el test de `main`.
- Commit: `M25: cliente HTTP único`

## M26 · Bucle de puertas (`puertas.py`)
- Referencia: `docs/05` v3, criterio 13 y la sección "Puertas múltiples"
  (línea 136: "sin éxito: motivo = el de la única puerta, o
  `puertas_agotadas` si hubo más de una"); `docs/01` línea 159 (nota sobre
  `puertas_agotadas`).
- Nuevo `legisuni/descargador/puertas.py`, función `probar_puertas(encargo,
  fetcher, robots, settings)`:
  - Recorre `encargo.puertas` en orden (`orden` = índice).
  - Por puerta: normaliza su URL, chequea `robots.permitido(url)` (si
    prohíbe → intento fallido `robots_prohibido`, sigue), pide con
    `fetcher.pedir(url)` (que ya aplica rate limit y reintentos **por
    llamada**, así que queda "por puerta" sin código nuevo), evalúa con
    `guard.evaluar(...)`.
  - **Un 200 cuyo cuerpo el guardián rechaza (HTML, tamaño) es puerta
    fallida, no error de red:** se registra su intento con el motivo que
    dé `guard.evaluar` (`no_es_pdf`, `demasiado_grande`, etc.) y el bucle
    sigue a la siguiente puerta.
  - Se detiene en la primera puerta que entrega bytes aceptados. Las
    siguientes **no se piden**.
  - Devuelve un `ResultadoPuertas` (dataclass): `exito`, `puerta_usada`,
    `respuesta` cruda, `extension`, `motivo_fallo`, `intentos:
    list[IntentoPuerta]` — uno por cada puerta *pedida*, robots-bloqueadas
    incluidas.
  - Sin éxito: motivo = el de esa única puerta si `len(puertas) == 1`, o
    `"puertas_agotadas"` si hubo más de una. Con una sola puerta,
    `puertas_agotadas` **nunca** aparece (protege criterio 11).
- `descargar.py` se simplifica: conserva la lectura de idempotencia de red
  (antes del bucle) y la escritura a disco + alias por hash (después),
  delegando el bucle entero a `puertas.probar_puertas`. El caso ya
  existente de fallo de escritura (`test_fallo_de_escritura_no_propaga_
  excepcion`) reconstruye el intento de la puerta que tuvo éxito en pedir
  pero falló al escribir, marcándolo `exito=False,
  motivo_fallo="http_error"` — igual que hoy.
- **Fuera de alcance, anotado para M28:** una puerta que da HTML rechazado
  por el guardián y que además tenga `Encargo.cruzar_vestibulos=True`
  debería intentar el cruce de vestíbulo antes de darse por fallida. M26
  no lo hace — la trata como puerta fallida sin más, incluso en modo
  académico. M28 (vestíbulo) inserta ese paso dentro de esta misma puerta,
  antes de registrar el motivo.
- Vestíbulo y muros no entran aquí: quedan para milestones futuros
  (`vestibulo.py`, `muros.py`), tal como los separa el diseño de `docs/05`.
- **Ninguna aserción de `test_descargar.py` cambia** (criterio 11) — solo
  se añaden tests nuevos, ahí mismo:
  - `test_tres_puertas_la_segunda_entrega_pdf`: tres puertas (404, PDF, una
    tercera sin respuesta registrada en `httpx_mock` — si se pide, el test
    falla solo). Verifica `puerta_usada == 1` y `len(intentos) == 2`.
  - `test_primera_puerta_da_html_segunda_da_pdf`: primera puerta 200 con
    HTML (el guardián la rechaza con `no_es_pdf`), segunda con PDF.
    Verifica `puerta_usada == 1` y `len(intentos) == 2` — un 200 rechazado
    por el guardián cuenta como puerta fallida, no corta el bucle.
  - `test_todas_las_puertas_fallan_da_puertas_agotadas`: tres puertas, las
    tres 404. Verifica `motivo_fallo == "puertas_agotadas"`,
    `len(intentos) == 3`, cada una con su propio motivo.
- Criterio de cierre: `.venv/bin/python -m pytest -q` en verde, incluidos
  los tests nuevos.
- Commit: `M26: bucle de puertas en puertas.py`

## M27 · Reconocimiento de muros (`muros.py` + `datos/patrones.toml`)
- Referencia: `docs/05` v3, sección "Muros" y criterio 15; `docs/01` línea
  989-991 (muro_de_pago sí puede aparecer en jurídico, D8 no distingue modo)
  y línea 155 (nota: "en la duda, el motivo es `vestibulo_sin_pdf`", no
  `http_error` ni `muro_de_pago`).
- Nuevo `legisuni/descargador/muros.py`: `es_muro_de_pago(status, url_final)`.
  `401`/`402` → `True`. Si no, compara `url_final` contra los patrones de
  `legisuni/datos/patrones.toml` (path hermano de `descargador/`, según el
  árbol de `docs/05`; `visores.json` se queda donde está, `docs/05` dice que
  se respeta su ubicación actual). `403` **nunca** es muro: cae al
  `http_error` que ya produce `Fetcher`, sin cambio ahí.
- **No distingue modo:** no mira `encargo.modo`. `muro_de_pago` puede salir
  en un `Encargo` jurídico igual que en uno académico (docs/01 989-991).
- **Los casos dudosos no cambian en M27.** `muros.py` documenta en su
  docstring la nota de `docs/01` línea 155: ante la duda el motivo correcto
  es `vestibulo_sin_pdf`, no `http_error` ni `muro_de_pago` mal
  diagnosticado. Hoy no hay vestíbulo, así que un HTML dudoso (que no matchee
  ningún patrón) sigue el camino de siempre: `guard.evaluar` → `no_es_pdf`.
  **Anotado para M28:** el orden final de una puerta será visor → petición →
  guardián → vestíbulo (un salto) → guardián; los HTML dudosos que hoy caen
  en `no_es_pdf` pasarán a intentar el vestíbulo primero, y solo si ese
  cruce falla el motivo será `vestibulo_sin_pdf`.
- **Patrones — sin evidencia medida, mínimos a propósito** (criterio 18, la
  primera corrida académica real, no se ha corrido todavía). Dos
  convenciones de protocolo de identidad federada, no editoriales
  observadas: `Shibboleth SSO` (`^/Shibboleth\.sso/`, sin `host` porque el
  IdP vive en el dominio de cada institución) y `CAS` (`^/cas/login`).
  Deliberadamente sin `accounts.google.com` / `login.microsoftonline.com` /
  Okta: serían proveedores adivinados sin evidencia de que una editorial
  redirija ahí.
- Integración en `puertas.py`: justo tras `fetcher.pedir(url)`, antes de
  mirar `motivo_red`. Es puerta fallida más — el bucle de M26 sigue a la
  siguiente sin cambiar su estructura.
- `datos/patrones.toml` es dato de paquete: se carga una sola vez
  (`lru_cache`, igual que `guard._cargar_visores`), no por petición.
- **Empaquetado — gap preexistente detectado y corregido de paso:**
  `pyproject.toml` no tenía `[tool.setuptools.package-data]` ni
  `MANIFEST.in`; `visores.json` solo "funciona" hoy porque el venv está en
  modo editable. Se añade `[tool.setuptools.package-data]` cubriendo
  `descargador/*.json` **y** `datos/*.toml`, para que ambos sobrevivan una
  instalación real, no solo la editable.
- Tests nuevos en `tests/test_descargar.py` (ninguna aserción existente
  cambia): `401` → `muro_de_pago`; `402` → `muro_de_pago`; `403` →
  `http_error` (control negativo); redirección a `/Shibboleth.sso/Login` →
  `muro_de_pago` aunque el destino final responda `200`; el `_encargo()`
  jurídico de siempre con una puerta `401` → `muro_de_pago` sin
  restricción de modo.
- Test nuevo en `tests/test_muros.py`: carga el `patrones.toml` **real** (no
  un fixture) vía `muros._cargar_patrones()` y confirma que compila sin
  excepción — un `ruta_regex` mal escrito debe romper aquí, no en una
  corrida real.
- Criterio de cierre: `.venv/bin/python -m pytest -q` en verde.
- Commit: `M27: reconocimiento de muros`

## M28 · Cruce de vestíbulo (`vestibulo.py`)
- Referencia: `docs/05` v3, sección "Cruce de vestíbulo" y criterio 14 (sus
  cinco casos); `docs/01` línea 937 (orden: visor → petición → guardián →
  vestíbulo → guardián); D3 y D4 de `docs/00`.
- Nuevo `legisuni/descargador/vestibulo.py`, **puro, sin red** (no importa
  `httpx`): `es_html(primeros_bytes, content_type)` y
  `extraer_enlace(cuerpo) -> str | None`. Parsea con `selectolax` (no
  ejecuta scripts) y solo lee un atributo (D4). Prioridad:
  `<meta name="citation_pdf_url">` → `<link rel="alternate"
  type="application/pdf">` → un **único** `<a href>` cuya ruta termine en
  `.pdf` (literal de `docs/05`; `.docx` no entra). Devuelve el valor
  **literal** de la página (D3): no normaliza ni construye nada.
- **Dos o más `<a>` a `.pdf` sin meta ni link → no se elige**, y se cuentan
  **etiquetas**, no destinos únicos: dos `<a>` al mismo PDF también dan
  `vestibulo_sin_pdf`. Contar destinos únicos se revisará con la evidencia
  real de M31 (pregunta 10 de `docs/05`).
- Integración en `puertas.py`, dentro de la misma puerta: solo si
  `guard.evaluar` da `no_es_pdf`, `encargo.cruzar_vestibulos=True` y la
  respuesta es HTML (bytes o `content-type`). Un solo salto:
  - sin enlace → `vestibulo_sin_pdf`;
  - enlace relativo → se resuelve contra la `url_final` del vestíbulo con
    `urlnorm.normalizar`;
  - el enlace pasa por lo mismo que una puerta: robots → `fetcher.pedir`
    (rate limit, reintentos, tope) → muros → red → tamaño → guardián. Se
    extrajo `_evaluar_respuesta` para que puerta y salto compartan ese
    camino sin duplicarlo;
  - salto que devuelve HTML otra vez → `vestibulo_sin_pdf`, sin recursión
    ni más peticiones;
  - **cualquier otro fallo del salto conserva su motivo propio**
    (`url_muerta`, `robots_prohibido`, `muro_de_pago`, `no_es_pdf`…).
- `IntentoPuerta.enlace_vestibulo` lleva el literal de la página;
  `url_final` y `http_status` son los del archivo; `url_pedida` sigue
  siendo la de la puerta. `construir_intento` gana `enlace_vestibulo=None`;
  la rama de fallo de escritura de `descargar.py` lo conserva.
- **Sin cliente propio.** El vestíbulo no es un receptor de `httpx.Client`:
  el salto solo sale por el `Fetcher`. En `tests/test_cliente_http.py` se
  corrigen los comentarios de M25 que anunciaban una clase `Vestibulo`, y
  en su lugar: `test_el_salto_del_vestibulo_sale_por_el_fetcher` (ambas
  peticiones pasan por `fetcher.pedir` y llevan el UA configurado) y
  `test_vestibulo_no_importa_httpx` (inspección con `ast`). Los scripts no
  cambian.
- Modo jurídico: `cruzar_vestibulos=False`, no entra en la rama nueva.
  Todos los tests previos usan `False`; **ninguna aserción cambia**
  (criterio 11).
- Tests nuevos: en `tests/test_descargar.py`, los cinco casos del criterio
  14 (con dos PDF distintos en el de los dos `<a>`), más enlace relativo,
  fallo del salto con su motivo (`url_muerta`) y robots que prohíbe el
  enlace; `tests/test_vestibulo.py` con la extracción (prioridad, meta
  vacía, dos `<a>` al mismo PDF, D4: `<a>` dentro de `<script>` y texto
  con "instrucciones" no cuentan).
- **Deuda anotada, NO se arregla en M28:** `docs/01` línea 937 dice
  "visor → petición", pero el visor se comprueba **después** de pedir,
  dentro de `guard.evaluar` sobre `url_final`. Pasa igual en las puertas
  (desde v1) y en el salto (que reutiliza el mismo camino a propósito,
  para no tener dos criterios). Adelantar el chequeo antes de pedir es
  tarea aparte.
- Criterio de cierre: `.venv/bin/python -m pytest -q` en verde.
- Commit: `M28: cruce de vestíbulo`

## M29 · Alias por hash
- Referencia: `docs/05` criterio 16 (línea 402) e Idempotencia regla 4;
  `docs/01` línea 940 ("Alias por hash") y línea 417 (nota sobre
  `duplicado_de`); evidencia C24 y E13.4 de `docs/08`.
- **Qué cambia y qué no, en modo jurídico.** C24/E13 midió que dos corridas
  de la UAM en días distintos dejaron los 45 documentos dos veces en disco.
  **Ese caso ya lo cerró M21:** el `encargo_id` (`inst_id:doc_slug:url_id`)
  no depende de la fecha, y tanto los scripts como `descargar()` se saltan
  lo ya registrado, así que la segunda corrida con la misma base no pide
  ni escribe nada. Lo que M29 cambia es otro caso: **un `encargo_id` nuevo
  con bytes idénticos dentro del mismo `grupo_alias`** (una reconsolidación:
  URLs nuevas, mismos bytes). En v1 escribía un segundo archivo; ahora no
  escribe nada y lleva `duplicado_de`. Es excepción al criterio 11,
  autorizada por el criterio 16. Sigue sin medirse en campo (E13.4).
- `Store.alias_por_hash(grupo_alias, sha256, excluir_encargo_id) ->
  (encargo_id, ruta) | None`: lee `descargas` (índice por `grupo_alias` de
  M20). Solo `exito = 1`, solo filas dueñas de su archivo (`duplicado_de IS
  NULL`: un alias nunca apunta a otro alias), nunca el propio `encargo_id`.
  Varias coincidencias → la más antigua (`capturado_en`, `rowid`).
- `descargar.py`: tras calcular el SHA-256 y **antes** de resolver ruta o
  escribir, si hay `store`, consulta `alias_por_hash(encargo.grupo_alias,
  …)`. El grupo se recibe del `Encargo`, nunca se deduce del `encargo_id`
  (v2.1). Con alias: `exito=True`, `ruta_local` = la del original,
  `duplicado_de` = su `encargo_id`, sin escribir archivo; `sha256`,
  `bytes`, `url_final`, `puerta_usada` e `intentos` son los de esta
  descarga (D5). Sin `store`, nada cambia.
- **Si el archivo original falta en disco o su hash ya no coincide, no hay
  alias** y se escribe el propio (`docs/01` línea 417: `ruta_local` apunta
  al archivo que ya existía). Un error al leerlo tampoco hay alias, nunca
  excepción.
- Scripts sin cambios: ya persisten con `guardar_descarga(resultado,
  encargo.grupo_alias)`, que guarda `duplicado_de`.
- **Ninguna aserción existente cambia:** los tests que usan `Store` en
  `test_descargar.py` solo escriben `documentos`, nunca `descargas`.
- Tests nuevos: en `tests/test_descargar.py`, las dos mitades del criterio
  16 (mismo grupo → un solo archivo y `duplicado_de` al primero; otro
  grupo → archivo propio) más el original ausente en disco; en
  `tests/test_store.py`, `alias_por_hash` con otro grupo, fallida, uno
  mismo y alias de alias.
- Commit: `M29: alias por hash`

## M30 · Encargos del Bloque A desde un lote ya estructurado
- **Cambio de fuente.** `Geologia_dois_.docx` (la lista contra la que se
  diseñó `01` §Modo académico y el criterio 18 de `docs/05`) nunca llegó al
  proyecto. La sustituye `datos/lotes/bloque-a.txt` (commit S10): 8 fichas
  del Bloque A, ya estructuradas (campos `CLAVE : valor` y enlaces marcados
  `[PDF]`, `[REG]`, `[DOI]`). `docs/01` y `docs/05` siguen citando la lista
  de geología; no se tocan en esta tarea.
- **No es el Lector de Lista** (`docs/00` §3, pieza Ⓐ, sin spec). El
  conversor `scripts/convertir_bloque_a.py` es desechable, lo dice en su
  encabezado y no tiene tests propios: solo se valida su salida
  (`tests/test_encargos_bloque_a.py`).
- Salida: `datos/encargos_bloque_a.json`, la entrada de la corrida. El `.txt`
  no se vuelve a leer en tiempo de ejecución. Forma:
  `lote_id` (N12: `slug(nombre_archivo)-sha256[:8]`), `archivo_origen`,
  `sha256_archivo`, `encargos` (N10), `no_obtenidos` (forma de `Faltante`,
  N14) y el bloque auxiliar (no es contrato): `vinculos` y `registros`.
- Reglas, todas de `docs/01`:
  - `articulo_id` (N11): `doi:{doi}` si hay DOI; si no,
    `ref:{slug(primer_autor)}-{anio}-{h8}`, con `h8` del título normalizado
    (sin acentos, minúsculas, blancos colapsados). Los `A.n` del archivo son
    `posicion_en_lista`, nunca identidad: viajan en
    `Puerta.evidencia = "lista:{lote_id}#A.n"`.
  - Traducción académica (N10): `cajon="papers"`, `cruzar_vestibulos=True`,
    `grupo_alias=articulo_id`, `etiqueta` según `01` l.668.
  - **A.5 no tiene ninguna puerta** (monografía, sin URL ni DOI): no genera
    `Encargo` (`01` l.745). Van **7**, no 8; A.5 queda en `no_obtenidos` con
    motivo `sin_puertas`, 0 intentos y ruta «buscar por título o cita».
  - **Orden de puertas por tipo, no por marca** (`01` l.776): `copia_libre`
    primero (en el orden de la lista), luego `oficial`, al final
    `resolutor_doi`. En A.7 eso pone Semantic Scholar antes que Cambridge.
  - Puerta DOI: `tipo="resolutor_doi"`, **`construida=False`**. Los seis DOI
    del lote traen su enlace `doi.org` literal: no se construye ninguno. La
    excepción a D3 (`construida=True`) solo aplicaría a una ficha con DOI y
    sin `[DOI]`; el conversor la implementa, pero este lote no la ejercita.
  - Tipo por host: `[PDF]` → `copia_libre`, salvo el de `cambridge.org` en
    A.7, que es el PDF de la editorial → `oficial`. PMC y `hull-repository`
    → `copia_libre` (`01` l.128); editoriales (annualreviews, sciencedirect,
    nature) → `oficial`.
  - **PubMed y ADS no son puerta.** Son registros bibliográficos: ningún
    `TipoPuerta` los describe, y etiquetarlos `oficial` falsearía el tipo y
    la evidencia de M31. Quedan en `registros` del JSON (6: A.1 ×2, A.2,
    A.3, A.6, A.7). A.3 se queda solo con el resolutor DOI, coherente con
    su nota («sin PDF de acceso libre»). Si M31 muestra que los registros
    llevan a PDF, se propondrá un tipo `registro` en una v2.5, con evidencia.
- **Hallazgo para el Lector de Lista:** A.3S es un **suplemento** (material
  suplementario de A.3). No es extra ni corrección, y `Relacion` no lo
  prevé porque la lista de geología no lo traía. A.3S va **sin** `relacion`;
  el vínculo con A.3 vive solo en `vinculos` del JSON. El vocabulario no se
  toca: decidir si «suplemento» entra en `Relacion` es tarea de la spec del
  Lector de Lista.
- **Hallazgo para M31:** la razón que da `01` (l.779) para poner la oficial
  después de las copias libres —«la oficial suele ser un vestíbulo con
  muro»— no se cumple en A.7, donde la oficial es un PDF abierto directo.
  Se conserva el orden del contrato; M31 dirá cuánto pesa (pregunta
  abierta 5 de `01`).
- Nuevo `scripts/lote.py`: lee el JSON, valida cada `Encargo` y descarga con
  el mismo cableado que `cosecha.py` (cliente único, `guardar` +
  `guardar_descarga`). **No se ejecuta sin `--dry-run`.**
- Verificación: `lote.py --dry-run` → 7 encargos, puertas en orden, y la
  línea de A.5 como no descargable.
- Commit: `M30: Encargos del Bloque A y lote.py`

## M31 · Primera corrida académica real — la ejecuta el humano · **cerrada**
- **La ejecutó el humano, no Claude Code**, el 2026-09-25:
  `.venv/bin/python scripts/lote.py`, sin `--dry-run`, sobre
  `datos/encargos_bloque_a.json` y la base `legisuni_v2.db` de E14.
- Criterio 18 de `docs/05`: medición, no umbral. **3/7**, 163 filas en
  `descargas` (156 jurídicas + 7 académicas). Evidencia completa en E15 de
  `docs/08`; resumen medido en el criterio 18.
- Pendientes que M28 y M30 dejaron para esta corrida:
  - **Registros (PubMed, ADS):** `lote.py` no los pide, así que la corrida
    no dice si llevan a PDF. No hay evidencia para proponer un tipo
    `registro`.
  - **Oficial abierta de A.7:** no se pidió; A.7 salió en la puerta 0. Sin
    dato para la pregunta abierta 5 de `docs/01` (E15.2).
  - **Regla del `<a>` único (pregunta 10 de `docs/05`):** sin dato. El único
    vestíbulo sin enlace (A.4) no distingue «ninguno» de «dos» (E15.6).
- Motivos de micro-tareas futuras, **sin arreglo propuesto**:
  - `muros.es_muro_de_pago` solo ve la URL final; en A.6 la señal
    (`idp.nature.com/authorize`) estaba en una redirección intermedia
    (E15.3).
  - Dos puertas del mismo encargo que acaban en el mismo destino se piden
    dos veces, con su vestíbulo cada una (A.6; también A.2) (E15.6).
- Commit: `E15: primera corrida académica, 3/7`

## M32 · Muros sobre la cadena de redirecciones
- Motivo: E15.3 de `docs/08`. En A.6, `muros.es_muro_de_pago(status,
  url_final)` solo veía la URL final (la página del artículo, `200`); los
  saltos intermedios no le llegaban.
- **Solo mecanismo, sin patrones nuevos.** `RespuestaCruda` (dataclass
  interno de `fetch.py`, no contrato) gana `redirecciones: tuple[str, ...] =
  ()`, llenado desde `response.history` de httpx. `es_muro_de_pago` gana un
  argumento opcional `redirecciones` y evalúa los patrones contra cada URL de
  la cadena más `url_final`. Las llamadas existentes no cambian (un `str`
  como segundo argumento posicional sigue siendo `url_final`).
  `puertas._evaluar_respuesta` pasa la cadena, así que cubre puerta y salto.
- **`IntentoPuerta` y `DownloadResult` no se tocan.** La cadena no se
  persiste.
- **Por qué no `idp.nature.com/authorize`:** el mismo log de E15.6 lo
  descarta. La puerta 0 de A.6 pasó por el IdP en la primera visita al host;
  la puerta 1 acabó en la misma página sin pasar por él, y el salto al PDF
  tampoco. Es un intercambio de cookie de sesión: un patrón haría depender el
  diagnóstico de las cookies. Además `/authorize` es ruta genérica de OAuth.
  Queda anotado en `datos/patrones.toml`. En la duda, no es muro.
- Tests nuevos (ninguna aserción existente cambia): Shibboleth en un salto
  intermedio con destino `200` → `muro_de_pago` (falla con la lógica
  anterior); control negativo, `301` → `302` → PDF → éxito; la cadena de A.6
  (`303` → authorize → `302` → transit → `302` → artículo HTML, salto al PDF
  `303` → artículo HTML) → `vestibulo_sin_pdf`, con el porqué escrito. En
  `tests/test_muros.py`: patrón en salto intermedio → muro; authorize
  genérico en la cadena → no muro.
- Criterio 11: los patrones siguen siendo `Shibboleth.sso` y `/cas/login`;
  las redirecciones jurídicas medidas son http→https (E12.3).
- Commit: `M32: muros sobre la cadena de redirecciones`

## M33 · Resumen disjunto y puertas duplicadas por destino
Dos deudas, ambas medidas.

**1. El resumen de los scripts cuenta los omitidos como exitosas** (E16 de
`docs/08`: `total: 47`, `exitosas: 47`, `omitidos: 47`).
- Causa: `descargar()` devuelve `exito=True` también para el omitido por la
  regla 5, y `cosecha.py` / `cosecha_uam.py` lo contaban en las dos
  categorías. `lote.py` ni siquiera tenía `omitidos`.
- Los tres scripts: omitido → `omitidos`; si no, `exito` → `exitosas`; si
  no, su motivo. `exitosas + omitidos + fallos == total`. `lote.py` gana la
  línea `omitidos:`; `sin puertas` sigue aparte, fuera de `total`. Un alias
  por hash (`duplicado_de`) sigue siendo exitosa: sí se pidió.
- Test en `tests/test_cliente_http.py`, parametrizado sobre los tres
  `main()`: dos corridas sobre la misma base → `exitosas: 1, omitidos: 0` y
  luego `exitosas: 0, omitidos: 1`, sin peticiones en la segunda. Falla con
  los scripts anteriores.

**2. Puertas duplicadas por destino** (E15.6: en A.6 la oficial y el
`resolutor_doi` acaban en la misma página y cada una cruzó su vestíbulo).
- **Se detecta después de pedir, por `url_final`, antes del vestíbulo**
  (opción b). No antes de pedir por URL normalizada (a): en A.6 las URLs
  iniciales eran distintas y solo coincidían tras redirigir, así que (a) no
  se activaría y nada medido la pide. No durante la cadena (c): exige
  seguir redirecciones a mano en el `Fetcher` y se cruza con E15.8, abierta.
- `puertas.py` guarda, por encargo, `url_final → (orden, motivo)` de cada
  puerta fallida que tuvo respuesta HTTP (un timeout o `robots_prohibido` no
  dejan destino). Si una puerta posterior acaba en un destino ya visto, no
  se evalúa ni se cruza su vestíbulo: su `IntentoPuerta` lleva el motivo de
  la primera, con su `url_final` y `http_status` reales y sin
  `enlace_vestibulo`. El recibo sigue con una fila por puerta.
- **Qué ahorra en A.6:** el salto al PDF de la puerta 1 y su redirección (2
  de 4 respuestas). **Qué no:** la página del artículo se vuelve a pedir,
  porque el `Fetcher` ya siguió la redirección.
- Modo jurídico: una sola puerta, el diccionario nunca tiene entrada previa.
  Criterio 11: ninguna aserción existente cambia. Contratos sin cambios.
- Tests en `tests/test_descargar.py`: A.6 con dos puertas → dos intentos
  `vestibulo_sin_pdf`, `puertas_agotadas`, y la lista exacta de peticiones
  sin el segundo salto (falla con el `puertas.py` anterior); control
  negativo, dos destinos distintos → cada puerta con su vestíbulo.
- Commit: `M33: resumen disjunto y puertas duplicadas por destino`

## M35 · Una omisión no pisa la fila registrada
- Motivo, medido en `legisuni_v2.db` (2026-09-26, E17 de `docs/08`): las
  **47 filas** de la UAM en `descargas` tienen `bytes`, `content_type`,
  `http_status`, `url_final` y `puerta_usada` en NULL y
  `capturado_en = 2026-09-26`. La UJAT está intacta. El daño es solo del modo
  jurídico. **Corrección (E17.1):** este punto atribuía el daño a E16, que es
  del 2026-09-23. El daño empezó con E16, porque el código de entonces ya
  pisaba las filas, y la corrida de verificación del 26 lo repitió. Esa es la
  que dejó el `capturado_en` medido.
- Causa: el resultado de una omisión (regla 5) solo trae `sha256` y
  `ruta_local`. Los scripts lo persistían igual, y el upsert sobre
  `(encargo_id, sha256)` pisaba la fila buena. `documentos` recibía el mismo
  resultado por `guardar`.
- **Decisión (opción A): al omitir no se escribe.** `cosecha.py`,
  `cosecha_uam.py` y `lote.py` solo llaman a `guardar` y `guardar_descarga`
  si el encargo no se omitió. Una omisión no es una observación nueva, así que
  `capturado_en` conserva el momento real de la captura (D5). Cubre las dos
  tablas.
  - Descartada B (COALESCE en el `ON CONFLICT`): no protege `capturado_en`
    (NOT NULL) y, en `documentos` (PK solo `entry_id`), dejaría `sha256` y
    `ruta_local` de un éxito en una fila con `exito = 0`.
  - Descartada C (`Store` ignora resultados con `exito` e `intentos == []`):
    deduce la omisión de la forma del resultado.
- **La regla vive, por ahora, en los tres scripts.** Un llamador nuevo que
  persista una omisión volvería a pisar. M34 la centraliza en `descargar()`.
- **Riesgo que no llegó a materializarse:** el resultado de una omisión trae
  `duplicado_de = None`, así que omitir un alias le habría borrado el
  `duplicado_de` y lo habría convertido en dueño de su archivo. Medido: la
  base tiene cero alias (E14 es anterior a M29).
- **Pérdida medida, no reparable: `content_type`** de las 47 filas de la UAM.
  `intentos` no lo guarda, y deducirlo de la extensión sería inventar la
  cabecera del servidor. Se queda en NULL.
- **`documentos` no se repara:** sus 47 filas de la UAM sufrieron el mismo
  daño y quedan así. M34 la congela y deja de leerse.
- La reparación de las 47 filas de `descargas` (`url_final` y `http_status`
  desde `intentos`, `bytes` del archivo en disco, `puerta_usada = 0`,
  `capturado_en` de la fecha de modificación del archivo) queda para **M35b**,
  aparte, y la ejecuta el humano. **`capturado_en` no es reparable con
  certeza** (E17): la fecha de modificación es cuándo se escribió el archivo,
  no cuándo se capturó la respuesta. Sirve como estimación, y M35b tiene que
  declararla como tal.
- Test en `tests/test_cliente_http.py`, parametrizado sobre los tres `main()`:
  dos corridas sobre la misma base, y las filas de `descargas` y `documentos`
  quedan idénticas tras la segunda, `capturado_en` incluido. Falla con los
  scripts anteriores.
- Criterio 11: ninguna aserción existente cambia. Contratos sin cambios.
- Commit: `M35: una omisión no pisa la fila registrada`

## M35b · Reparación de las 47 filas (la aplica el humano)
- Es un script de reparación de datos, no una corrección de código. Motivo:
  E17 de `docs/08`. Nuevo `scripts/reparar_omisiones.py`, con `--db`
  obligatorio; no lee `Settings` ni `.env`.
- Por defecto solo muestra, y abre la base en solo lectura (`mode=ro`).
  Escribe únicamente con `--aplicar`, en una transacción (`BEGIN IMMEDIATE`).
  **Aborta sin escribir** si las filas afectadas no son exactamente 47
  (constante `FILAS_ESPERADAS`, no argumento). Afectadas: `descargas` con
  `encargo_id LIKE 'uam:%'`, `exito = 1` y `bytes`, `http_status`,
  `url_final` y `puerta_usada` en NULL.
- Fuentes, y ninguna otra:
  - `url_final` y `http_status`: del **único** intento con `exito = 1` del
    encargo, al que después se exige `orden = 0`. Filtrar por `orden = 0` y
    comprobarlo luego no comprobaría nada.
  - `puerta_usada = 0`: el `orden` de ese intento.
  - `bytes`: tamaño del archivo en `ruta_local`, solo si su SHA-256 coincide
    con el `sha256` de la fila.
  - `capturado_en`: **estimación**, la fecha de modificación del archivo, que
    indica cuándo se escribió el archivo y no cuándo se capturó la respuesta.
    Se declara así en el docstring, en la cabecera de la salida y en cada fila.
  - `content_type`: no se toca. Pérdida definitiva.
- **Una fila se repara entera o no se toca:** una fila medio reparada parece
  buena y no lo es. La que no cumple una condición (cero o varios intentos
  exitosos, `orden` distinto de 0, intento sin `url_final` o sin
  `http_status`, archivo ausente o ilegible, hash distinto) queda intacta y se
  reporta con su motivo. Nada se rellena por analogía. El recuento de fechas
  estimadas por día es solo informativo: no filtra.
- El `UPDATE` repite la firma de fila dañada en su `WHERE` y exige tocar
  exactamente una fila. Una segunda aplicación aborta (0 afectadas).
- `documentos` e `intentos` no se tocan.
- Se ejecuta desde la raíz del repo (`ruta_local` es relativa). **La copia de
  seguridad va fuera del repo**, nunca en la raíz del proyecto:
  `cp legisuni_v2.db ~/respaldo-acervo/legisuni_v2.antes-M35b.db`.
- Tests en `tests/test_reparar_omisiones.py`, con filas dañadas por el mismo
  camino que en campo (descarga buena y, encima, su omisión): la vista previa
  deja la base idéntica byte a byte; si las afectadas no son las esperadas,
  aborta sin escribir; `--aplicar` repara la fila entera y deja
  `content_type` en NULL y `documentos` igual; hash distinto, archivo
  ausente, cero o dos intentos exitosos y `orden = 1` quedan intactas y
  reportadas; una segunda aplicación aborta.
- Criterio 11: ninguna aserción existente cambia. Contratos sin cambios.
- Commit: `M35b: script de reparación de las 47 filas`

## M34 · La idempotencia lee de `descargas`
- Deuda anotada en M21 y M23c: la idempotencia leía `documentos`, mientras la
  escritura iba a `documentos` y a `descargas`. Ahora lee `descargas` y nadie
  escribe en `documentos`.
- **Qué fila se elige (opción A).** `descargas` tiene PK `(encargo_id,
  sha256)`, y un encargo puede tener varias filas: versiones distintas, o filas
  con `sha256` NULL de intentos fallidos (en SQLite los NULL de la PK son
  distintos, así que cada fallo añade una fila). Se toma **la última fila del
  encargo** (`capturado_en DESC, rowid DESC`). Si tiene `exito = 1`, se
  devuelven su `sha256` y su `ruta_local`; si no, `None`. Es lo que hacía
  `documentos`: la última escritura gana. Por eso es lo fiel al criterio 11.
  Un fallo nunca se devuelve como descarga buena. `capturado_en` va antes que
  `rowid` porque el upsert de un hash ya registrado conserva el `rowid` viejo.
- `hash_registrado` y `ruta_registrada` leen **la misma fila**, elegida por
  una única función privada (`Store._fila_vigente`). Antes no filtraban igual y
  podían devolver el hash de una versión y la ruta de otra.
- **Un solo camino de escritura: `descargar()`.** Con `store`, persiste con
  `guardar_descarga(resultado, encargo.grupo_alias)` todo lo que no es una
  omisión: éxito, fallo o alias. **La regla de M35 (no escribir al omitir) pasa
  de los tres scripts a `descargar()`.** `cosecha.py`, `cosecha_uam.py` y
  `lote.py` ya no llaman a `guardar` ni a `guardar_descarga`; conservan
  `hash_registrado` para el resumen de M33. Sin `store`, nada cambia.
- **`documentos` no se borra** (`docs/07` la divide, no la elimina): queda como
  tabla de la fase v1, **sin escritores, congelada en sus 156 filas**.
  `Store.guardar` y `Store.contar` se conservan con sus tests. **Su esquema no
  es el `documentos` de `docs/07` §Persistencia** (N6 + N7, PK `doc_id`): es el
  de v1 (PK `entry_id`, forma de N5). La tabla jurídica de `docs/07` sigue
  pendiente. `docs/07` no se toca.
- Criterio 4 de `docs/05`: el texto pasa de «registrado en `documentos`» a
  «registrado en `descargas` (desde M34)». Se alinea el texto con el código; no
  es un criterio nuevo. `Store.hash_registrado` conserva su papel.
- **Criterio 11: los cambios de preparación son mecánicos.** Cambia la tabla,
  no el comportamiento medido. Ocho tests registraban con `guardar` y leían con
  `hash_registrado` o `ruta_registrada`: cinco en `tests/test_store.py` (en
  `test_guardar_mismo_entry_id_con_datos_distintos_actualiza` se añade
  `guardar_descarga` junto a `guardar`, porque su `contar()` mide
  `documentos`) y tres en `tests/test_descargar.py`. Además se quitan las tres
  llamadas a `guardar_descarga(resultado1, …)` de los tests de alias de M29:
  con `descargar()` escribiendo, duplicaban en silencio las filas de
  `intentos`. **Cero `assert` eliminados en el diff.**
- Tests nuevos:
  - `tests/test_store.py`: fallo viejo y éxito posterior → el éxito; éxito y
    fallo posterior → `None`; solo fallos NULL → `None`; dos versiones → hash
    y ruta de la misma fila; `capturado_en` decide antes que `rowid`; una fila
    solo en `documentos` ya no cuenta.
  - `tests/test_descargar.py`: con `store`, `descargar()` escribe en
    `descargas` y no en `documentos`; un fallo también se escribe; una omisión
    no escribe nada.
  - `tests/test_cliente_http.py`, sobre los tres `main()`: `documentos` queda
    vacía.
- Efecto en campo: la base v2 tiene las 47 filas de la UAM en `descargas`
  (reparadas en E18), así que la idempotencia sigue viendo las 47. Lo
  comprueba el humano, sin red, leyendo la base con `Store.hash_registrado`.
- Commit: `M34: la idempotencia lee de descargas`

## M36 · Encargos del Bloque B
- Entrada: `datos/lotes/bloque-b.txt` (commit S12): 32 fichas (31 obras + 1
  corrección), mismo formato que el Bloque A. Salida:
  `datos/encargos_bloque_b.json`, con la misma forma que la de M30.
- **Conversor generalizado.** `scripts/convertir_bloque_a.py` pasa a
  `scripts/convertir_bloque.py --entrada … --salida …`. Sigue siendo desechable y
  sigue sin ser el Lector de Lista. Se comprobó regenerando el Bloque A en un
  directorio temporal: sale idéntico a `datos/encargos_bloque_a.json` salvo por
  `creado_en` y la clave nueva `vinculos[].relacion`. El JSON de A no se
  regenera en el repositorio.
- Reglas de M30 sin cambios: `articulo_id` (`docs/01` l.761–769), orden de
  puertas por tipo (l.785), `cajon="papers"`, `cruzar_vestibulos=True`,
  `grupo_alias=articulo_id`.
- **B.11 y B.22** son monografías sin URL ni DOI: `sin_puertas`, como A.5. Van
  **30** encargos, no 32.
- **ResearchGate (B.7, B.9) y DOAJ no son puerta.** Van a `registros`, como
  PubMed y ADS en M30. B.7 y B.9 se quedan con su oficial y el resolutor.
- **Suplemento de B.10 (figshare).** Sale de las puertas y queda en `registros`
  con `"nota": "material suplementario"`. **Por qué:** un suplemento descargado
  como artículo sería un **falso éxito**. Eso es peor que un fallo porque no se
  nota: el Descargador lo daría por bueno, y solo lo detectaría el Verificador
  Académico, que todavía no existe.
- **B.29: el DOI trae `<` y `>` sin codificar.** Medido:
  `urlnorm.normalizar` devuelve `…019%3C0867:CCAPCT%3E2.3.CO;2`, codifica solo
  `<>` y es idempotente. El conversor no codifica nada: `Puerta.url` guarda el
  enlace crudo (D3, `docs/05` §Normalización) y la normalización ocurre al
  pedir (`puertas.py`).
- **B.15C, corrección de B.15.** `articulo_id` = `corr:{articulo_id de B.15}:{h8}`
  (`docs/01` l.767), con `h8` sacado de la URL normalizada de su primera puerta.
  Etiqueta `corr-burgess-2014__…` (N10). `relacion` pertenece a `ArticleRef`
  (N11), no a `Encargo`: vive en `vinculos`, que gana la clave `relacion`
  (`"correccion"`; `null` si el literal no está en `Relacion`). Es un cambio
  aditivo en el bloque auxiliar, que no es contrato.
- **B.33 y B.33B, «publicado en paralelo».** No está en `Relacion`: como A.3S,
  van sin `relacion` y el vínculo, en los dos sentidos, vive en `vinculos`.
  Hallazgo para la spec del Lector de Lista, junto con «suplemento». El
  vínculo se toma ahora con una expresión regular sobre el ID, no con la
  última palabra; con la última palabra, B.15C daba `"3)"`.
- **Tipo por host (21 hosts `[REG]` nuevos).** Se clasifican por lo que son,
  no por su marca:
  - PMC en sus dos hosts (`www.ncbi…/pmc`, `pmc.ncbi…`) → `copia_libre`. Los
    `[PDF]` de B.13, B.15, B.15C, B.16 y B.34 son páginas intermedias, no
    archivos: los cruza la corrida.
  - Repositorios institucionales (`eprints.*`, `dspace`, `repository.cam`,
    `archive-ouverte.unige`, `nora.nerc`, `discovery.ucl`, `pure-oai.bham`,
    `pure.ed`) y páginas de autor o de curso → `copia_libre`.
  - Editoriales (`science.org`, `pnas.org`, `nature.com`,
    `pubs.geoscienceworld.org`) → `oficial`. Esto incluye los `[PDF]` de B.8 y
    B.36, que son PDF del propio editor, como Cambridge en A.7.
  - **Nueve portales CRIS clasificados `copia_libre` sin evidencia; revisar
    con M37.** Son `research.ed.ac.uk`, `research.birmingham`,
    `researchwithrutgers`, `experts.arizona`, `pure.psu`, `research.vu.nl`,
    `research-information.bris`, `research-portal.st-andrews` y
    `profiles.wustl`. Es la clasificación menos segura de las tres: muchos solo
    muestran la ficha del artículo, sin archivo. La corrida debe poder
    auditarla.
- **Efecto del orden que la corrida debe mirar:** en B.8 el portal CRIS de
  WUSTL (`copia_libre`) va antes que el PDF aceptado en `science.org`
  (`oficial`), que es el único enlace directo verificado de la ficha. Es el
  mismo caso que A.7 (pregunta abierta 5 de `docs/01`).
- Verificación: `lote.py --dry-run --encargos datos/encargos_bloque_b.json` da
  30 encargos, 85 puertas, ninguna construida, y B.11 y B.22 como no
  descargables. Test de la salida: `tests/test_encargos_bloque_b.py`.
- Commit: `M36: Encargos del Bloque B y conversor generalizado`

## M36.1 · El informe registra los parámetros de la corrida
- Pendiente de E18.1 de `docs/08`: la anomalía de los 43 s no es medible sin
  `rate_limit_s` ni los hosts de la corrida.
- El resumen de `cosecha.py`, `cosecha_uam.py` y `lote.py` imprime al final
  `rate_limit_s`, `user_agent` y `hosts distintos pedidos`.
- **Qué cuenta como host pedido:** el host de `IntentoPuerta.url_pedida` de
  cada puerta que llegó a pedirse, incluidas las que terminan en `http_error`,
  `timeout` o visor. No cuentan las puertas con `robots_prohibido` (no se
  piden) ni los encargos omitidos por idempotencia (no piden nada).
- **Salvedad:** el conteo **no incluye** los hosts que solo aparecen en la
  cadena de redirecciones (E15.8) ni el del enlace seguido en un vestíbulo.
  Para E18.1 no importa: es jurídica, con una sola puerta y sin vestíbulos. En
  una corrida académica el número es un mínimo.
- Test nuevo en `tests/test_cliente_http.py`, sobre los tres `main()`: un
  host en la primera corrida y cero en la segunda (omitido). Ningún `assert`
  existente cambia.
- Commit: `M36.1: el informe registra los parámetros de la corrida`

## M38 · Un `200` que no parece `robots.txt`
- Motivo: E19.12 de `docs/08`. `www.pure.ed.ac.uk/robots.txt` siguió cuatro
  `302` hasta un login SAML en `login.microsoftonline.com`, que respondió
  `200`. `RobotsCache._cargar` pasó ese HTML a `RobotFileParser` como si fuera
  un `robots.txt` legible, sin warning. Toca D8.
- **Criterio negativo:** no se exige que parezca un `robots.txt`; se rechaza lo
  que claramente es otra cosa. Un `200` no se acepta si su `Content-Type`
  declarado es de marcado (`text/html`, `application/xhtml+xml`, `*xml`) **o**
  si su cuerpo, sin BOM ni espacios iniciales, empieza por `<`. Todo lo demás
  se acepta como hoy: cuerpo vacío, solo comentarios, `text/plain`,
  `application/octet-stream` o sin `Content-Type`.
- **Descartados:** exigir al menos una directiva rechazaría un `robots.txt`
  vacío, que es legítimo (todo permitido). Exigir que la URL final termine en
  `/robots.txt` sería una regla sin medir, y el de `www3.nd.edu` ya redirigió
  con query. Tampoco sirve el cambio de host: `doi.org`,
  `pdfs.semanticscholar.org` y `www3.nd.edu` redirigieron su `robots.txt` a
  otro host (todos acabaron en `404`).
- **Qué se hace cuando no lo parece:** permitido, con un warning propio
  («no parece robots.txt … fail-open (permitido)»), y `None` en caché. Es el
  caso literal de D8: «si no se puede leer, se permite y se registra un
  warning». Una página de login es una política ilegible, no una prohibición.
  `robots_prohibido` afirmaría algo que nadie declaró, y un motivo nuevo sería
  cambiar N5.
- **M38 corrige la clasificación, no el acceso.** `RobotFileParser` sobre HTML
  casi siempre da cero reglas: sobre Pure la decisión práctica habría sido la
  misma. Lo que cambia es que ahora queda registrada como fail-open.
- **Modo jurídico y criterio 11:** UAM y UJAT sirvieron **`403` y `404`**, nunca
  `200` (`m24-uam.log`, `m24-ujat.log`; E14). El modo jurídico no entra en la
  rama que toca M38, así que E14 no puede cambiar. (Se había dado por hecho lo
  contrario al plantear la tarea.)
- **Riesgo residual, no cerrable con los logs:** los logs guardan solo la línea
  de estado, no `Content-Type` ni cuerpo. En E15 y E19, 24 hosts distintos
  respondieron `200` a `robots.txt`. Si alguno sirvió HTML con `200`, su
  clasificación cambia; sería el mismo fallo de E19.12, no un `robots.txt`
  legítimo. No se sondean hoy: medirían el día de hoy, no el de la corrida.
- Tests nuevos en `tests/test_robots.py` (ninguna aserción existente cambia;
  `FetcherFalso` no se toca): HTML `text/html` → permitido con el warning
  nuevo; HTML servido como `text/plain` → ídem; la cadena de E19.12 (`302` ×4
  a otro host, `200` HTML) → ídem, una sola carga por host. Controles sin
  warning: `200` vacío; solo comentarios sin `Content-Type`; `Disallow` como
  `application/octet-stream`, que se sigue obedeciendo.
- Documentación: viñeta en `docs/05` §Cortesía de red; nota en E19.12 de
  `docs/08`. `docs/01` no se toca; D8 en `docs/00` ya lo cubre.
- Commit: `M38: un 200 que no parece robots.txt no se obedece`

## ~~Deuda · La idempotencia no mira el disco (regla 5 de `docs/05`)~~ · **cerrada por M40**
- La regla 5 exige, para no pedir ninguna puerta, una descarga exitosa
  registrada **y que su archivo exista con el hash registrado**.
  `Store.hash_registrado` solo mira la base, no el disco: **si alguien borra un
  archivo, la idempotencia lo dará por descargado** y no se vuelve a pedir.
- **Precede a M34:** ya pasaba cuando la lectura era contra `documentos`. M34
  no la introduce y no la arregla. Queda para una micro-tarea propia.

## M39 · Un fallo repetido no añade fila
- Motivo: E19.11 de `docs/08`, medido en campo. `descargas` tiene 41 filas
  académicas para 37 encargos: B.7–B.10 fallaron en la parcial y otra vez en
  la completa. Con `sha256` NULL, la PK `(encargo_id, sha256)` no deduplica,
  porque en SQLite dos NULL de una PK son distintos (anotado en M34 como
  comportamiento).
- **Mecanismo: borrar e insertar, sin cambiar el esquema.** En
  `Store.guardar_descarga`, solo si `resultado.sha256 is None`, y en la misma
  transacción: `DELETE FROM descargas WHERE encargo_id = ? AND sha256 IS
  NULL` y después el `INSERT` de siempre. Las filas con hash siguen entrando
  por el upsert sobre `(encargo_id, sha256)`: **dos versiones con hashes
  distintos siguen conviviendo** (criterio 5 de `docs/05`, M20). Un éxito
  posterior a un fallo añade su fila y deja la del fallo, como antes.
- **Por qué no `UPDATE`:** el fallo actualizado conservaría su `rowid` viejo.
  Con un empate exacto de `capturado_en` entre ese fallo y un éxito escrito en
  medio, `_fila_vigente` (`capturado_en DESC, rowid DESC`) elegiría el éxito,
  y hoy elige el fallo. Parece improbable, pero los tests usan `ahora` fijo y
  el reloj de WSL retrocede (E19.7). **Borrar e insertar da un `rowid` nuevo:
  la fila vigente de M34 es la misma en todos los casos.** Lo único que
  desaparece son otras filas NULL del mismo encargo; si la vigente era una de
  ellas, la nueva gana igual que hoy, porque se escribe después.
- **Por qué no un índice único parcial** (`UNIQUE (encargo_id) WHERE sha256 IS
  NULL`): `Store()` ejecuta el esquema al abrir. Sobre `legisuni_v2.db`, con
  los 4 pares duplicados, `CREATE UNIQUE INDEX` fallaría y ningún script
  podría abrir la base hasta limpiarla: el código quedaría atado al estado de
  los datos. Además es un índice que `docs/07` no declara.
- **Qué se pierde:** la fila del fallo anterior desaparece de `descargas`, con
  su `capturado_en` y su `motivo_fallo`. Es inherente a no añadir fila.
- **Límites, escritos a propósito:**
  - Tras M39, `descargas` guarda **una fila de fallo por encargo**, mientras
    `intentos` sigue acumulando **una por corrida**, porque esos intentos
    ocurrieron. La asimetría es correcta, pero **un conteo de `intentos`
    mezcla corridas y no se puede separar por fecha**: `intentos` no tiene
    fecha (E19.1).
  - Unir `intentos` con `descargas` por `encargo_id` sigue duplicando en
    cuanto un encargo tiene a la vez fila de fallo y de éxito, o dos
    versiones. Es un problema de la consulta, no de la tabla; M39 no lo toca.
- **Las 4 filas existentes** se limpian aparte, con M39b (script que ejecuta el
  humano). Sin eso solo se corregirían si B.7–B.10 vuelven a fallar; si
  alguna tiene éxito, un éxito no borra fallos, y sus dos filas quedarían para
  siempre.
- Criterio 11: **ninguna aserción existente cambia** (la suite pasó con el
  cambio antes de añadir tests). Contratos sin cambios; `docs/07` sin cambios.
- Tests nuevos en `tests/test_store.py`: dos fallos → una fila con los datos
  del segundo; fallo, éxito, fallo → dos filas y la vigente es el último
  fallo; empate de `capturado_en` → gana el fallo escrito después (protege
  contra un `UPDATE`); dos versiones más dos fallos → tres filas; con dos NULL
  preexistentes, un fallo nuevo deja una; el fallo de otro encargo no se toca;
  `intentos` acumula una fila por corrida. Seis de siete fallan con la lógica
  anterior; el del empate pasa en ambas, como se espera.
- Nota en E19.11 de `docs/08`.
- Commit: `M39: un fallo repetido no añade fila`

## M40 · La idempotencia comprueba el archivo en disco
- Motivo: la deuda anterior, anotada en M34. La regla 5 de `docs/05` exige,
  para no pedir ninguna puerta, una descarga exitosa registrada **y su archivo
  en disco con el hash registrado**. `Store.hash_registrado` solo consulta la
  base: un PDF borrado se daba por descargado y no se volvía a pedir nunca.
- **M39 queda reservada** para la deduplicación de fallos; no se numera aquí.
- **Dónde: en `descargar.py`, no en `Store`.** `ya_descargado(store,
  encargo_id) -> (sha256, ruta) | None` toma la fila vigente de M34
  (`hash_registrado` + `ruta_registrada`) y comprueba que el archivo exista y
  que su SHA-256 coincida; un `OSError` da `None`, nunca excepción. Razones:
  `Store` es persistencia SQLite y no conoce `data_root`; `tests/test_store.py`
  afirma `hash_registrado(...) == …` con rutas inventadas (`/datos/b.pdf`) en
  al menos cinco sitios, que cambiarían si la comprobación viviera en `Store`;
  y `descargar.py` ya verifica archivos contra un hash (regla 1 y
  `_original_por_hash` de M29).
- **Una sola decisión para omitir y para contar.** `cosecha.py`,
  `cosecha_uam.py` y `lote.py` calculan `omitido` con `ya_descargado`, no con
  `hash_registrado`. Si no, con un PDF borrado el resumen diría «omitidos: 1»
  mientras `descargar()` lo pide de nuevo.
- **Coste: hash completo, con `hashlib.file_digest`** (lee por bloques; los
  escaneos de la UJAT llegan a 33.7 MB). **Corrección de cifras:** la UAM son
  **12.6 MB** (E11), no 297; 297 MB es el total jurídico, UAM 12.6 + UJAT 285
  (E12.6). **Medido, no supuesto:** SHA-256 en memoria en esta máquina, ~483
  MB/s → 297 MB en ~0,6 s, la UAM en ~26 ms. Como scripts y `descargar()`
  llaman ambos a `ya_descargado`, cada archivo se hashea dos veces: ~1,2 s por
  corrida jurídica completa, contra ~2 min de red por universidad solo por el
  rate limit. La lectura de disco en frío será algo más lenta; sigue siendo
  segundos contra minutos. Solo el tamaño no basta: reescribiría la regla 5
  («con el hash registrado») y no detecta un archivo sustituido por otro del
  mismo peso. Un hash que no coincide no se pierde: se piden las puertas y la
  regla 2 escribe con sufijo `__sha8`, conservando ambos (regla 3).
- **Alias por hash (M29).** La fila vigente de un alias lleva la `ruta_local`
  del original. Si falta ese archivo, **ninguno de los dos está descargado** y
  se piden ambos. No se pierde nada; el orden decide los papeles:
  - original antes que alias (el orden en que se crearon): el original
    reescribe su archivo y el alias se omite. Todo queda como estaba;
  - alias antes que original: por la regla de M29 (original ausente → no hay
    alias) el alias escribe su propio archivo y el upsert sobre `(encargo_id,
    sha256)` le pone `duplicado_de = NULL`; luego el original encuentra esos
    bytes y queda como su alias. Una sola copia en disco, **papeles
    invertidos**, y el upsert pisa la marca anterior. **Limitación conocida,
    heredada de M29, aceptada y no corregida aquí.**
- **Ruta relativa:** `data_root` por defecto es `Path("data")`; la comprobación
  depende de ejecutar desde la raíz del repo, igual que `_original_por_hash`.
  No es nuevo.
- **Excepción al criterio 11, autorizada por la regla 5** (como M21 con el
  criterio 4). Dos tests de `tests/test_descargar.py`
  (`test_omite_encargo_id_ya_registrado_con_exito` y
  `test_ya_registrado_no_toca_la_red_sin_ninguna_respuesta_mockeada`)
  registraban un archivo **inexistente** con un hash **inventado**
  (`"abc123"`) y afirmaban que se omitía: codificaban el hueco. **Cambia su
  preparación** (escriben el archivo y registran su SHA-256 real); **ningún
  `assert` cambia.** No es un cambio mecánico: el comportamiento que
  documentaban deja de existir.
- Tests nuevos: en `tests/test_descargar.py`, `ya_descargado` sin fila, con
  archivo y hash, con archivo ausente y con bytes distintos; archivo borrado →
  se pide y se reescribe; archivo con otros bytes → se pide y conviven ambos;
  alias con original borrado en los dos órdenes, afirmando los papeles. En
  `tests/test_cliente_http.py`, sobre los tres `main()`: archivo borrado →
  «exitosas: 1, omitidos: 0» y hay peticiones nuevas (falla con la lógica
  anterior).
- **Efecto en campo, medido antes del commit** (2026-09-30, por el humano, sin
  red): un comando de solo lectura abrió `legisuni_v2.db` con `mode=ro`, sin
  `Store.__init__`, y aplicó `ya_descargado` a cada `encargo_id` de
  `descargas`:
  ```
  {'sin descarga vigente': 25, 'ya descargado': 168}
  ```
  **Cero `VIGENTE SIN ARCHIVO VÁLIDO`.** Los 168 son 156 jurídicos + 12
  académicos (3 del Bloque A y 9 del B); los 25 son fichas académicas cuya fila
  vigente es un fallo, que M40 no toca. 168 + 25 = 193 = 156 + 37 encargos
  académicos. **Una corrida repetida da el mismo resultado que antes de M40.**
  (La estimación previa de «9 académicos» olvidaba los 3 del Bloque A.)
- `docs/05`: sin cambios; la regla 5 ya dice esto.
- Commit: `M40: la idempotencia comprueba el archivo en disco`
