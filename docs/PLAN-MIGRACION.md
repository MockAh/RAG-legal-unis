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
- La ruta se arma desde `cajon` + `etiqueta` + extensión de los bytes.
- Validación anti-traversal.
- Unificar `data_root` y `data_dir` en uno solo.
- Criterio: `grep -rn CatalogEntry legisuni/descargador/` vacío.
- Commit: `M17: rutas desde cajón y etiqueta, con validación`

## M18 · Encargo valida cajon y etiqueta
- `ValueError` al construir con `..`, `/`, ruta absoluta o caracteres fuera
  del conjunto. Criterio 17 de `docs/05`.
- Commit: `M18: Encargo rechaza cajones y etiquetas peligrosos`

## M19 · descargar(encargo)
- `descargar()` recibe `Encargo`, usa una puerta (`puertas[0]`), emite el
  recibo de un `IntentoPuerta`. **Sin cambio de comportamiento.**
- Criterios 11 y 12. `pytest -q` verde.
- Commit: `M19: descargar recibe Encargo`