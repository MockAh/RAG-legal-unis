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
