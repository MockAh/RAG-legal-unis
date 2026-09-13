# README — Cómo arrancar el Proyecto Acervo

> Este archivo no es parte de la especificación. Es el instructivo para montar el Proyecto en
> Claude y saber en qué punto está. Súbelo al conocimiento del Proyecto junto con los demás.
>
> **Estado al 2026-09-10:** el sistema pasó a llamarse **Acervo** y tiene dos modos: el
> **jurídico** (conserva el nombre **LegisUni**) y el **académico** (descargar y verificar
> artículos científicos desde una lista). Los contratos están en **v2.3** y **la propagación a las
> specs está cerrada**. Lo siguiente es la migración del Descargador.

---

## 1. Qué subir al conocimiento del Proyecto

Los nueve archivos, tal cual. **Las versiones importan**: la v2 de los contratos rompió
compatibilidad y una spec vieja habla un idioma que ya no existe.

| Archivo | Versión | Modo | Qué es |
|---|---|---|---|
| `00-VISION-Y-ARQUITECTURA.md` | **v2.0** | ambos | Documento maestro. Se lee siempre primero. |
| `01-CONTRATOS-DE-DATOS.md` | **v2.3** | ambos | Esquemas N0–N14. La única frontera entre conversaciones. |
| `02-SPEC-LOCALIZADOR.md` | v1 | jurídico | Pieza ① — agente |
| `03-SPEC-LECTOR-DE-INDICE.md` | **v3** | jurídico | Pieza ② — agente. Primera de la ruta jurídica. |
| `04-SPEC-CORROBORADOR.md` | v2 | jurídico | Pieza ③ — agente |
| `05-SPEC-DESCARGADOR.md` | **v3** | **común** | Pieza ④ — código. Fase v1 cerrada (10/10); fase v3 abierta (criterios 11–18). |
| `06-SPEC-VERIFICADOR-DOCUMENTAL.md` | **v4** | jurídico | Pieza ⑤ — agente |
| `07-SPEC-ORQUESTACION-PERSISTENCIA-Y-CLI.md` | **v2** | ambos | Flujos, base única, CLI `acervo` con menú |
| `08-EVIDENCIA-DE-CAMPO.md` | v7 | ambos | Cuatro universidades medidas + dos corridas reales |

**Specs por escribir:**

| Spec | Modo | Por qué |
|---|---|---|
| **Extracción de texto (con OCR)** | común | La necesitan los dos verificadores. 24 de 105 documentos de la UJAT son escaneos (C21 de `08`). |
| **Lector de Lista** | académico | Convierte una lista `.docx` en fichas (N11, N12). |
| **Verificador Académico** | académico | ¿El archivo es el artículo pedido? DOI y título (N13, D13). |
| **Auditor de Lote** | académico | Informe en tres grupos (N14). Se espera código. |

---

## 2. Instrucciones sugeridas del Proyecto

Pégalas en el campo de instrucciones personalizadas:

> Este Proyecto construye **Acervo**, un sistema multiagente con dos modos: **jurídico**
> (LegisUni: recuperar legislación universitaria mexicana) y **académico** (descargar y
> verificar artículos científicos desde una lista). Antes de responder cualquier cosa, lee
> `00-VISION-Y-ARQUITECTURA.md`, `01-CONTRATOS-DE-DATOS.md` y `08-EVIDENCIA-DE-CAMPO.md`.
>
> Reglas de trabajo:
> - Los contratos de `01` son ley. Si una decisión los toca, dilo explícitamente y detente
>   hasta que yo los actualice; no sigas como si nada.
> - Di siempre de qué modo hablamos, o si la pieza es común.
> - Distingue siempre lo medido de lo supuesto. Si algo no está en `08`, es suposición y hay
>   que decirlo.
> - Trabajamos en micro-tareas de ~15 minutos. Cuando pida "el prompt de M_n", devuelve solo
>   el prompt para Copilot de esa tarea.
> - Prefiero que me digas que algo no se puede o que no lo sabes, a que lo rellenes.
> - Cuando revises la salida de Copilot, no te fíes de su resumen: dime qué comandos correr
>   para verificarlo.
> - Español. Conciso.

---

## 3. Orden de las conversaciones

Una conversación por spec. Al abrir cada una, el mensaje inicial es literalmente:

> *"Trabajamos la spec 0X. Lee 00, 01 y 08 primero. Empecemos por sus preguntas abiertas."*

**Orden** (justificado en `00` §6):

1. ~~**`01`** — contratos.~~ **Hecho: v2.3.** Dos modos, `Encargo`, C20 resuelto.
2. ~~**`05` + `07` (persistencia)** — Descargador y base.~~ **Fase v1 cerrada.** Ver §4.
3. **Propagación de `01` v2.** ~~`00`~~, ~~`03`~~, ~~`05`~~, ~~`06`~~, ~~`07`~~, ~~README~~ hechos.
   **Cerrada el 2026-09-10.**
4. **Migración del Descargador a `Encargo` ← AQUÍ ESTAMOS.** — criterios 11–17 de `05` y 15–16 de `07`. Incluye
   la **primera corrida académica real** con encargos armados a mano (criterio 18 de `05`).
5. **Modo académico, de punta a punta:**
   1. Lector de Lista
   2. Extracción de texto (la necesita el Verificador)
   3. Verificador Académico
   4. Auditor de Lote
   5. Orquestación académica + CLI (`07`)
6. **Modo jurídico:** `03` Lector de índice → `06` Verificador → `04` Corroborador → `02`
   Localizador → orquestación jurídica (`07`).

**Por qué el académico primero** (`00` §8, pregunta 10): tres piezas en vez de cinco, la lista
es su propio esqueleto, ya hay una lista real para probar, y sería la primera corrida completa
del proyecto.

---

## 4. Dónde está el trabajo hecho

**Repositorio:** `RAG-legal-unis`. El paquete se llama `legisuni`; **no hace falta renombrarlo**:
el nombre visible será el comando `acervo` (`07` v2). Trece commits, de `M1` a `M13`.

**Fase Descargador v1: cerrada.** Diez de diez criterios de `05`:

| | UAM | UJAT |
|---|---|---|
| Documentos | 45 | 105 |
| Éxitos | **45/45** | **105/105** |
| Peso | 12.6 MB | 285 MB |

- **90 tests** en 1.3 s, sin red ni disco real.
- **Fixtures capturadas:** `fixtures/uam-index.html` y `fixtures/ujat-*.html` (5 páginas).
  Faltan UNAM-OAG, UACAM y la rejilla 70-I — ver `08` §E9 sobre por qué corre prisa.
- **Corpus en disco** (`data/norm/`) y base SQLite con 150 filas, fuera de git.
- **`.github/copilot-instructions.md`** existe y hace falta (`00` §9).

**Lo que la migración cambiará** (`01` §Migración, `07` v2): `descargar()` recibe `Encargo`;
`DownloadResult.entry_id` pasa a `encargo_id`; la tabla `documentos` se divide en `descargas`
(común) y `documentos` (jurídico). **La base se rehace limpia; los 150 archivos en disco no se
tocan.** Sus nombres ya estaban declarados desechables (E11.6 de `08`).

---

## 5. Estado de las mediciones

**Modo jurídico.** Cuatro universidades medidas: UAM, UNAM (70-I y sitio OAG), UJAT y UACAM.
**4 de 4 sitios institucionales sirven HTML plano.** Dos corridas reales del Descargador. Los
hallazgos que más pesaron:

- La UAM responde **403 a `robots.txt`** y 200 a sus PDF: con fail-closed, cero documentos.
- **24 de 105 documentos de la UJAT son escaneos sin texto**: los firmados.
- La UACAM declara «Fecha de corte: Diciembre del 2016»: índice impecable y caducado (D12).

**Modo académico.** Una sola lista real, sin corrida todavía: `Geologia_dois_.docx`
(17 fichas). Tres hallazgos de lectura moldearon los contratos (`01` §Modo académico): ningún
artículo pedido trae título, 13 de 15 traen DOI escrito, y el balance que declara la propia
lista no cuadra (dice 12 de 15 con copia libre; son 11). **Aún no está en `08`:** entra como
evidencia con la primera corrida (criterio 18 de `05`).

**Método probado** (`08` §E7): buscar por **"Abogado General"** o **"Abogacía General"** da
mejores resultados que "legislación" a secas.

---

## 6. Qué NO está decidido todavía

**Sigue abierto:**

- **Qué se hace con un índice caducado**, más allá de detectarlo (`00` §8 pregunta 8).
- **Cómo acceder al 70-I de la PNT programáticamente** (`04`).
- **Orden de puertas académicas:** copia libre primero trae a veces un manuscrito cuando la
  versión publicada estaba abierta (`01`). Se mide en la primera corrida.
- **Protecciones anti-bots en repositorios** y **la regla del enlace único en vestíbulos**
  (`05`, preguntas 8 y 10). Se miden en la primera corrida.
- **Formato del informe académico** (propuesta: Markdown junto al JSON) y **presupuesto de LLM
  por lote** (`07`, preguntas 6 y 8).

**Resuelto el 2026-09-10:**

- ~~`entry_id` no distingue versiones (C20)~~ → **cada publicación tiene identidad propia**
  (dirección normalizada + alias por hash), D15.
- ~~Dos archivos con el mismo `doc_id`~~ → **se conservan ambos**; el registro apunta al primero
  aprobado (`06` v4).
- ~~Qué modo va primero~~ → **el académico.**
- ~~Dónde vive la fecha de corte del índice~~ → **en `Catalog`**, con texto literal y umbral de 18
  meses; ~~marca de título derivado~~ → **`titulo_derivado` en `CatalogEntry`** (`01` v2.3).
- ~~`robots.txt` en modo académico~~ → **misma política que el jurídico** (`05` v3).
- ~~Listas con DOIs sin enlace~~ → **excepción acotada a D3:** se puede construir `doi.org` desde
  un DOI escrito.
- ~~Qué datos mínimos pide una ficha de artículo~~ → **primer autor + año + título, DOI o cita.**
- ~~Documentos por facultad~~ → solo normativa general. ~~Repositorio de terceros de la UNAM~~
  → pista, nunca fuente. ~~¿Se conservan los PDF tras el OCR?~~ → sí (D5).

**Resuelto antes:** versiones históricas se descargan; OCR medido (24 de 105, documentos
firmados); no pagar Playwright (4/4 HTML plano); contratos colectivos entran; `.docx` se aceptan;
TLS estricto se queda; el consolidado se descarga.

---

## 7. Relación con el proyecto hermano

Acervo es **un sistema aparte** de `RAG_publish`, no una fase suya. No comparte código, ni
contratos, ni base de datos.

Sí comparte el método de trabajo (una conversación por spec, contratos congelados, registro de
consideraciones diferidas, micro-tareas), las lecciones operativas ya pagadas (`00` §9) y un
destino: **el corpus normativo del modo jurídico es la entrada de un sistema RAG jurídico**, con
su propio troceado por artículo, que se especificará después y en otro lugar.

El troceado no se diseña aquí. Aquí solo se consigue y se valida el material.

> **El método se validó en la práctica.** La fase Descargador salió en trece micro-tareas, con
> un commit por tarea firmada y verificación manual antes de cada una. Ninguna tarea se dio por
> buena con el resumen del asistente: siempre con comandos.
