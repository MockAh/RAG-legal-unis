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

## M23 · cosecha.py arma Encargos
- `scripts/cosecha.py` construye `Encargo` vía `juridico/traduccion.py`.
- Arregla el filtro de extensión (los 4 enlaces con salto de línea, E13 de `08`).
- Implementa el `entry_id` de tres segmentos (`inst_id:doc_slug:url_id`) de `01` v2.0.
- **Aviso de M21:** `cosecha.py` debe escribir en ambas tablas (`guardar` y
  `guardar_descarga`), o la idempotencia de M21 —que lee `documentos`— dejará
  de funcionar y M24 volvería a descargar los 156 en cada corrida.
  Alternativa a decidir en M23: mudar también la lectura a `descargas`.
- Verificación: `--dry-run` → UAM 47, UJAT 109.
- Commit: `M23: cosecha arma Encargos y no pierde enlaces`

## M24 · Corrida real (puerta de control) — la ejecuta el humano
- Prerrequisito: `.env` con `DATA_ROOT`, base v2 limpia.
- UAM + UJAT: 47 + 109 = 156/156, dos `entry_id` distintos para el RES.
- Si no da 156, no se sigue a M25.