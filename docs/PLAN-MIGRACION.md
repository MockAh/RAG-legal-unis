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
- Commit: `M18: Encargo rechaza cajones y etiquetas peligrosos`