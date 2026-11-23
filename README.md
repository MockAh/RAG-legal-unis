# Acervo

**Español** · [English](README.en.md)

Sistema para **conseguir y validar documentos con proveniencia total**. Tiene dos modos que
comparten un mismo Descargador:

- **Modo jurídico (LegisUni):** dado el nombre de una universidad pública mexicana, localiza sus
  fuentes oficiales, extrae el catálogo completo de su normativa, corrobora que esté completo,
  descarga los documentos y verifica que sean auténticos, vigentes e íntegros. La salida es un
  corpus normativo listo para un sistema RAG posterior.
- **Modo académico:** dada una lista de artículos científicos (referencias, DOIs o enlaces, en
  `.docx`), descarga las copias de acceso abierto que encuentre, verifica que cada archivo sea el
  artículo pedido e informa qué obtuvo, qué no y por qué.

**Lo que no es:** no es un buscador de literatura (la lista la trae el usuario), no pasa muros de
pago, no indexa ni responde preguntas jurídicas. Solo consigue y valida documentos.

> El paquete de Python se llama `legisuni` por razones históricas. El nombre del sistema es
> **Acervo**.

---

## Estado

*Al 2026-11-23, micro-tarea M50.*

| Pieza | Modo | Estado |
|---|---|---|
| ④ Descargador | común | **Hecho.** Migrado a `Encargo`; dos corridas jurídicas reales y una académica. Tags `descargador-v1-cerrado` → `descargador-v2-reparado`. |
| ② Lector de índice | jurídico | **En curso.** Núcleo determinista hecho (M41–M48); `Catalog`, salida del agente y agente maniquí (M49); grabadora de artefactos de evaluación (M50). Falta el agente real. |
| ⑤ Verificador documental | jurídico | Especificado, sin código. |
| ③ Corroborador | jurídico | Especificado, sin código. |
| ① Localizador | jurídico | Especificado, sin código. |
| Orquestación, persistencia y CLI `acervo` | ambos | Especificado, sin código. Hoy se opera con los scripts de `scripts/`. |
| Lector de Lista, Extracción de texto (OCR), Verificador Académico, Auditor de Lote | académico / común | Sin spec todavía. |

El detalle vivo está en [`docs/PLAN-MIGRACION.md`](docs/PLAN-MIGRACION.md) y en las cabeceras de
versión de cada documento de `docs/`.

---

## Documentación

La especificación está en [`docs/`](docs/). Se lee en este orden:

| Archivo | Qué es |
|---|---|
| [`00-VISION-Y-ARQUITECTURA.md`](docs/00-VISION-Y-ARQUITECTURA.md) | Documento maestro: qué se construye, por qué con agentes, decisiones (D1–D15). |
| [`01-CONTRATOS-DE-DATOS.md`](docs/01-CONTRATOS-DE-DATOS.md) | Esquemas N0–N15. **Es ley:** la única frontera entre piezas. |
| [`02-SPEC-LOCALIZADOR.md`](docs/02-SPEC-LOCALIZADOR.md) | ① Localizador (jurídico). |
| [`03-SPEC-LECTOR-DE-INDICE.md`](docs/03-SPEC-LECTOR-DE-INDICE.md) | ② Lector de índice (jurídico). |
| [`04-SPEC-CORROBORADOR.md`](docs/04-SPEC-CORROBORADOR.md) | ③ Corroborador (jurídico). |
| [`05-SPEC-DESCARGADOR.md`](docs/05-SPEC-DESCARGADOR.md) | ④ Descargador (común). |
| [`06-SPEC-VERIFICADOR-DOCUMENTAL.md`](docs/06-SPEC-VERIFICADOR-DOCUMENTAL.md) | ⑤ Verificador documental (jurídico). |
| [`07-SPEC-ORQUESTACION-PERSISTENCIA-Y-CLI.md`](docs/07-SPEC-ORQUESTACION-PERSISTENCIA-Y-CLI.md) | Flujos, base única y CLI `acervo`. |
| [`08-EVIDENCIA-DE-CAMPO.md`](docs/08-EVIDENCIA-DE-CAMPO.md) | Lo medido en campo (UAM, UNAM, UJAT, UACAM) y en las corridas reales. |
| [`PLAN-MIGRACION.md`](docs/PLAN-MIGRACION.md) | Micro-tareas, una por commit. |

Toda la documentación está en español.

---

## Estructura del repositorio

```
legisuni/
  contracts/     Esquemas Pydantic de docs/01 (N0–N15)
  descargador/   Pieza ④: cliente HTTP, robots.txt, muros, vestíbulos, almacén SQLite
  lector/        Pieza ②: extracción determinista de índices, ensamblado del Catalog
  juridico/      Traducción CatalogEntry → Encargo
  datos/         Patrones y tablas de configuración empaquetadas
  config.py      Settings (variables LEGISUNI_*)
scripts/         Scripts de corrida y de reparación; no forman parte del paquete
tests/           Pruebas sin red ni disco real
datos/           Lotes de encargos de entrada
fixtures/        HTML real capturado de los índices institucionales
docs/            Especificación
```

---

## Instalación

Requiere Python 3.12 o superior.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env   # y rellena los valores
```

La configuración se lee de variables `LEGISUNI_*` (ver [`.env.example`](.env.example)): clave de
API del LLM, modelo, User-Agent, raíz de datos, ruta de la base, límites de tiempo, tamaño y ritmo.

## Pruebas

```bash
.venv/bin/python -m pytest -q
```

Las pruebas no tocan la red ni el disco real.

## Uso

Hasta que exista la CLI `acervo`, se opera con scripts:

```bash
# Modo jurídico: extraer un índice guardado, sin red ni base
.venv/bin/python scripts/cosechar_indice.py \
  --html fixtures/uam-index.html \
  --url-indice https://www.uam.mx/legislacion/index.html \
  --inst-id uam --solo-extraer

# Modo académico: ver qué se descargaría de un lote de encargos, sin descargar
.venv/bin/python scripts/lote.py --encargos datos/encargos_bloque_a.json --dry-run
```

> ⚠️ **Sin `--solo-extraer` o `--dry-run`, estos scripts hacen peticiones reales a servidores
> universitarios.** Respetan `robots.txt` y un ritmo por dominio, pero úsalos con criterio.

---

## Método de trabajo

- Los contratos de `docs/01` no se cambian sin decisión explícita.
- El trabajo avanza en micro-tareas pequeñas definidas en `docs/PLAN-MIGRACION.md`, una por
  commit (`MN: descripción`).
- Ninguna migración cambia una aserción de comportamiento existente.
- Lo medido se distingue de lo supuesto: si no está en `docs/08`, es suposición.

## Proyecto hermano

Acervo es un sistema aparte de `RAG_publish`: no comparte código, contratos ni base. Comparte el
método de trabajo y un destino: el corpus del modo jurídico será la entrada de un sistema RAG
jurídico que se especificará en otro lugar.
