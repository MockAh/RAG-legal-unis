# 00 · Visión y arquitectura

> Documento maestro del Proyecto **Acervo**. Todas las conversaciones deben leerlo primero.
> Estado: **v2.0** · vivo. Actualizado 2026-09-10 tras la conversación «Acervo: modo académico»
> (`01` v2.0). **El sistema tiene ahora dos modos:** el jurídico, que conserva el nombre
> **LegisUni**, y el académico.
> **Cuatro universidades medidas** (UAM, UNAM, UJAT, UACAM) y **dos corridas reales**:
> 150 documentos descargados, 150/150. La spec `05` está cerrada.
> Si una decisión cambia, se actualiza AQUÍ y en el contrato afectado.
> Proyecto hermano: `RAG_publish` (sistema multiagente de escritura científica). Acervo
> hereda su método de trabajo y varias de sus lecciones operativas, pero es un sistema aparte.
>
> **Qué cambió en la v2.0:** §1 y §3 describen dos modos; D3 gana una excepción acotada; D8 y
> D9 precisan su alcance por modo; D10 amplía el alcance; decisiones nuevas D13 (confiabilidad
> académica), D14 (un Descargador para ambos modos) y D15 (identidad de cada publicación, C20);
> §6 reordena el plan; §8 cierra la pregunta 3 y abre la 9 y la 10.

---

## 1. Qué construimos

Un **sistema multiagente de recuperación de legislación universitaria**: dado el nombre de
cualquier universidad pública mexicana y un puñado de datos mínimos, el sistema localiza sus
fuentes oficiales, extrae el catálogo completo de su normativa, corrobora que ese catálogo
esté completo, descarga los documentos y verifica que lo descargado sea auténtico, vigente e
íntegro.

**La salida es un corpus normativo con proveniencia total**, listo para ser troceado e
indexado por un sistema RAG posterior.

Eso es el **modo jurídico (LegisUni)**. Desde la v2.0 existe también el **modo académico**:
dada una lista de artículos científicos (referencias, DOIs o enlaces, en `.docx`), el sistema
descarga las copias de acceso abierto que encuentre, verifica que cada archivo sea el artículo
pedido y entrega un informe de lo que obtuvo y lo que no, con el motivo y una ruta sugerida.

**Los dos modos comparten el Descargador** (D14). Difieren en quién prepara los pedidos y en
quién revisa lo que llega.

**Lo que NO es:** no es un buscador de literatura. En modo académico **la lista la trae el
usuario**: el sistema no decide qué leer, no busca artículos por tema, no pasa muros de pago
(D8) ni indexa nada. No responde preguntas jurídicas. En ambos modos, solo consigue y valida
documentos.

---

## 2. Por qué agentes (y no solo código)

El proyecto hermano fijó en su decisión D6 que filtros, procesadores e indexadores son código
convencional: se usan agentes LLM solo donde hace falta razonamiento agéntico. Aquí sí hace
falta, y por una razón medida, no supuesta:

**Cada universidad publica su normativa de forma distinta.** La evidencia de campo (ver `08`)
muestra dos casos opuestos en la misma ciudad: la UAM sirve su índice en HTML estático,
categorizado y con estado de vigencia explícito; la UNAM lo sirve en una rejilla JavaScript
cuyo HTML llega vacío. Escribir un parser por institución no escala a ~40 universidades
públicas estatales más las federales. Un agente que sepa leer *cualquier* página de índice y
extraer una lista estructurada, sí.

**Y hay un segundo argumento, que apareció midiendo y es más fuerte.** La heterogeneidad
técnica se podría atacar con parsers, con esfuerzo. Lo que no se puede atacar con parsers es
la heterogeneidad **semántica**: la UACAM sirve un índice HTML impecable que declara al pie
«Fecha de corte: Diciembre del 2016» (C13 de `08`). Un parser lo procesa sin un error y
produce un catálogo de hace nueve años con aspecto de vigente. Hace falta algo que **entienda
lo que lee**, no solo que lo extraiga.

**Regla de reparto:** el razonamiento (buscar, interpretar HTML heterogéneo, juzgar
completitud, comparar un PDF contra su entrada de catálogo) es de agentes. La mecánica
(pedir URLs, verificar bytes, guardar, deduplicar, contar) es código. Ningún agente escribe
en disco ni decide idempotencia.

> **Confirmado en campo:** el Descargador es código puro, sin un solo agente, y bajó 150
> documentos de dos universidades con 150/150 de éxito (E11 y E12 de `08`). El reparto
> funciona.

**En modo académico la regla es la misma.** Leer una lista escrita a mano (renglones sin
título, DOIs dentro de enlaces, extras y correcciones mezclados) y juzgar si un PDF es el
artículo pedido son razonamiento: agentes. Llevar las cuentas del lote es mecánica: se espera
código (`01`, N14).

---

## 3. Arquitectura — dos modos, un Descargador

### Modo jurídico (LegisUni) — cinco piezas

```
      InstitutionRef (N0)  ← el usuario da 3–5 datos
              │
              ▼
   ① LOCALIZADOR (agente)          busca y propone fuentes oficiales
              │  SourceCandidate (N1)
              ▼
   ② LECTOR DE ÍNDICE (agente)     lee la página y extrae el catálogo
              │  Catalog (N3) de CatalogEntry (N2)
              ▼
   ③ CORROBORADOR (agente)         ¿está completo? cruza contra esqueleto
              │                     esperado + PNT 70-I + Periódico Oficial
              │  CoverageReport (N4)
              ▼
              │  CatalogEntry → Encargo (N10)
              ▼
   ④ DESCARGADOR (código)          baja los documentos, guardián de firma, hash
              │  DownloadResult (N5)              ✔ IMPLEMENTADO Y MEDIDO (migra a Encargo)
              ▼
   ⑤ VERIFICADOR DOCUMENTAL (agente)  lee la 1ª página: ¿es lo que dice ser?
              │  DocumentVerdict (N6)
              ▼
      NormativeRecord (N7)  →  SQLite + data/norm/   →  fase de chunking (futura)
              │
              └──► ManualQueueItem (N8) para lo que no se resolvió solo
```

### Modo académico — cuatro piezas

```
      lista .docx  ← el usuario da referencias, DOIs o enlaces
              │
              ▼
   Ⓐ LECTOR DE LISTA (agente)      convierte cada renglón en una ficha
              │  ArticleBatch (N12) de ArticleRef (N11) → Encargo (N10)
              ▼
   ④ DESCARGADOR (código)          el mismo: prueba puertas en orden, cruza vestíbulos
              │  DownloadResult (N5)
              ▼
   Ⓑ VERIFICADOR ACADÉMICO (agente) ¿es el artículo pedido? DOI y título
              │  ArticleVerdict (N13)
              ▼
   Ⓒ AUDITOR DE LOTE (código)      obtenidos · con observaciones · no obtenidos
              │
              ▼
      BatchReport (N14)  +  data/papers/
```

**La frontera entre modos es el `Encargo` (N10).** El Descargador no lee fichas de ningún modo:
recibe órdenes de recogida. Todo lo que distingue a un modo vive antes y después de él.

**Memoria compartida:** SQLite (`instituciones`, `fuentes`, `catalogo`, `documentos`,
`cola_manual`; y para el modo académico `lotes`, `articulos`; común a ambos `encargos`) +
carpetas `data/norm/<inst_id>/` y `data/papers/`. El esquema exacto se fija en `07`.

**El ciclo se puede re-ejecutar.** El sistema no "corre una vez": cada corrida es un cotejo
del estado publicado contra el estado en disco. Ese cotejo es también el detector de reformas.

---

## 4. Decisiones ya tomadas (no reabrir sin causa)

| # | Decisión | Razón |
|---|----------|-------|
| **D1** | **Cadena de fuentes: sitio institucional → PNT (art. 70-I) → Periódico Oficial / DOF → cola manual.** En ese orden. | Medido: el sitio institucional dio más y mejor que el 70-I (URLs directas, vigencia, histórico y abrogados). El 70-I es respaldo homologado, no fuente primaria. Ver `08`. |
| **D2** | **La Ley Orgánica se busca SIEMPRE también fuera del sitio de la universidad, y se comparan versiones.** Federales (UNAM, UAM, IPN) → DOF; estatales → Periódico Oficial / Congreso del estado. | *Suavizada tras medir la UJAT (E4.4 de `08`):* a veces sí está en el portal universitario, pero desactualizada — la UJAT publica la suya desde una carpeta de 2012. No basta con hallarla: hay que comparar contra la fuente que la promulgó. |
| **D3** | **Ningún agente inventa URLs.** Solo puede devolver una URL que haya aparecido en un resultado de búsqueda o como enlace en una página que abrió. **Única excepción (v2.0):** construir `https://doi.org/<doi>` cuando el DOI aparece escrito en la lista del modo académico; la puerta queda marcada `construida=True` (`01`, N10). Nada más se construye. | Una URL alucinada que casualmente resuelve es la peor falla posible: documento falso con apariencia de oficial. *La excepción no fabrica una dirección:* el identificador es literal y `doi.org` es el resolutor oficial del sistema DOI. Sin ella, una lista de DOIs sin enlaces no descargaría nada. |
| **D4** | **Todo HTML descargado es entrada NO confiable.** Los agentes extraen datos de él; jamás obedecen instrucciones halladas dentro. | Superficie de inyección de prompt. Un sitio comprometido no debe poder redirigir el sistema. |
| **D5** | **Proveniencia total.** Cada documento guarda: URL de origen, dominio, fecha de captura, hash SHA-256, y de qué eslabón de D1 vino. | Es el requisito para que una cita futura sea auditable, análogo a D5 del proyecto hermano. |
| **D6** | **La vigencia es campo de primera clase, y su valor por defecto es `desconocido`, nunca `vigente`.** | El corpus jurídico sin eje temporal es peligroso: citar un reglamento derogado es un error de fondo, no de forma. *Medido (C2 de `08`): solo **1 de 4** universidades declara vigencia en su índice.* Por eso el default no puede ser optimista. **Y hay un nivel más:** la UACAM demuestra que el índice entero puede estar caducado sin que ninguna entrada lo diga (C13). No basta con fechar los documentos; hay que fechar el catálogo. |
| **D11** | **La categoría que el sitio asigna a un documento es pista, no dato.** | Medido en la UJAT (E4.1 de `08`): su Estatuto General y su Ley Orgánica están archivados bajo "Otros documentos", y un Estatuto aparece bajo "Reglamentos". El esqueleto esperado del Corroborador es más confiable que la taxonomía publicada. |
| **D12** | **Un índice puede estar caducado sin que nada dentro de él lo diga.** Antes de extraer un catálogo, se busca la fecha de corte declarada; si es vieja, el catálogo entero se marca sospechoso. *Campos en `Catalog` (`01` v2.3); umbral de 18 meses en `Settings`.* | *Medido (C13 de `08`, 2026-09-06):* la UACAM sirve un índice HTML impecable con la línea «Fecha de corte: Diciembre del 2016». Técnicamente perfecto, **nueve años desactualizado**, y nada aguas abajo lo detectaría: el Corroborador vería un catálogo completo y el Verificador encontraría los documentos. **Es el modo de fallo más peligroso hallado hasta ahora**, porque el sistema mentiría con confianza y sin errores. |
| **D7** | **La cola manual es una salida legítima del sistema, no un fallo.** | El valor no está en bajar el 100 % solo; está en saber con precisión qué falta. Buscar 5 documentos nombrados es media hora; no saber qué falta es el problema real. |
| **D8** | **Acceso respetuoso: `robots.txt`, rate limit por dominio, User-Agent identificado con correo de contacto.** Solo documentos públicos en sitios oficiales. **La política de `robots.txt` es FAIL-OPEN:** si no se puede leer, se permite y se registra un warning. | El proyecto hermano midió que los 403 venían de servidores que bloquean clientes sin UA (D2 de su registro 02). Además, estos son sitios institucionales, no adversarios. *Medido (C17 de `08`): la UAM responde **403 a `/robots.txt`** y **200 a sus PDF**, con y sin UA; `archivos.ujat.mx` responde 404. Con fail-closed, la cosecha de la UAM habría dado **cero documentos** sin que existiera prohibición alguna.* Si el archivo se lee y prohíbe, se obedece: a cola manual, sin forzar. **v2.0: el Descargador nunca intenta pasar un muro de pago, suscripción o sesión, en ningún modo**; un muro es un resultado, no un obstáculo. **Misma política en modo académico** (`05` v3, §8 pregunta 9): uno legible que prohíbe se obedece siempre; el fail-open solo cubre los ilegibles. |
| **D9** | **Autenticidad se decide por dominio, no por contenido.** Un PDF es oficial si vino de un dominio institucional verificado; el contenido solo confirma identidad y vigencia. **Rige el modo jurídico; el académico se rige por D13.** | Un PDF puede decir cualquier cosa. El dominio es el ancla dura. |
| **D10** | **Alcance v1.** Modo jurídico: **universidades públicas mexicanas**; privadas fuera (no son sujetos obligados; su normativa interna no es necesariamente pública). Modo académico (v2.0): **artículos científicos de una lista dada por el usuario, solo en copias de acceso abierto.** | Frontera de alcance honesta, no limitación técnica. En el académico, la frontera es legal y de diseño: lo que está tras un muro va al informe con una ruta sugerida (biblioteca, autor), no a la carpeta. |
| **D13** | **Modo académico: la confiabilidad se decide por contenido, no por dominio.** El DOI es evidencia; el título desempata. Candidatos DOI solo de metadatos y primera página, nunca de la bibliografía. Sin DOI utilizable, deciden título, primer autor y año. Un artículo cuenta como obtenido solo con veredicto `correcto` u `otra_edicion` (`01`, N13). | Una copia legítima puede vivir en GitHub, en un repositorio o en la página de un autor: no hay dominio que acredite. Lo que sí hay es un identificador impreso en el propio documento. *Diseñado contra la primera lista real (`01`, §Modo académico):* 13 de 15 artículos traían DOI escrito y ninguno traía título, de ahí que el título desempate pero no sea obligatorio. |
| **D14** | **Un solo Descargador para ambos modos. Recibe `Encargo` (N10) y no sabe más.** Cada modo traduce su ficha a un `Encargo`; la traducción jurídica reproduce exactamente el comportamiento de v1.4. | Es la pieza medida y cerrada (150/150). Duplicarla por modo duplicaría también su costo de mantenimiento. La diferencia real entre modos está en leer los pedidos y en juzgar lo recibido, que son trabajo de agentes. |
| **D15** | **Cada publicación de un instrumento tiene identidad propia: `entry_id` incorpora su dirección de origen normalizada.** Antes de dar por nueva una descarga, se compara su hash con lo ya registrado (alias por hash). Nunca se borra un archivo. | Resuelve C20 de `08` (salida B, decidida en `01` v2.0): los dos históricos del Reglamento de Estudios Superiores de la UAM colisionaban. La fecha no sirve de identidad porque 3 de 4 índices no la declaran (C2). **Límite conocido:** una re-exportación con bytes distintos no la atrapa el hash; la segunda defensa es `doc_id`. |

---

## 5. Stack por defecto

- **Lenguaje:** Python 3.12; `httpx` (cliente síncrono en v1), `pydantic` v2 + `pydantic-settings`.
- **Persistencia:** SQLite. *Medido: 150 documentos de 2 universidades pesan 297 MB en disco,
  con varianza de 23× entre instituciones (C19 de `08`). Extrapolado a ~40, varios GB. SQLite y
  disco local siguen bastando.*
- **Agentes:** API de Anthropic. Cada agente = un prompt de sistema + herramientas acotadas,
  no un proceso aparte. El nombre del modelo vive en `Settings`, nunca escrito a mano en el
  código (los identificadores de modelo cambian; verificar el vigente al implementar).
- **Búsqueda web:** herramienta de búsqueda expuesta al Localizador. Sin scraping de buscadores.
- **HTML:** `selectolax` o `lxml` para reducir la página antes de dársela al agente
  (ahorra contexto y elimina scripts, que además es la mitigación de D4).
  **Detectar la codificación declarada, no asumir UTF-8:** medido, la UAM sirve `iso-8859-1`
  y la UJAT `utf-8` (C18 de `08`). Asumir mal no lanza excepción, solo corrompe los acentos.
- **Extracción de texto de PDF:** `pdfplumber` para el caso normal. **Y hace falta OCR:**
  medido, 24 de 105 documentos de la UJAT son escaneos sin texto extraíble, contra 0 de 42 en
  la UAM (C21 de `08`). El motor y el umbral se deciden en la spec de extracción, que aún no
  existe. **Desde la v2.0 esa spec la comparten ambos verificadores**: el académico también
  abre escaneos viejos.
- **Páginas JavaScript:** **pendiente de decidir** — ver §8. No asumir Playwright todavía.
- **Entradas en `.docx`** (ficha de universidad, lista de artículos): `python-docx`. *Propuesta;
  se confirma en `07`.*
- **CLI:** `typer`. Un comando por modo: `acervo juridico <ficha.docx>` y
  `acervo academico <lista.docx>`; sin argumentos, un menú. *Se fija en `07`.*
- **Tests:** `pytest` + `pytest-httpx`. Los agentes se prueban con respuestas grabadas.
  *Referencia medida: la suite del Descargador son 90 tests en 1.3 s, sin red ni disco real.*

---

## 6. Orden de implementación

1. ~~Congelar contratos (`01`)~~ **hecho** — **v2.0** (2026-09-10): dos modos, `Encargo`, C20
   resuelto. Primera versión que rompe compatibilidad, con plan de migración.
2. ~~Descargador + persistencia (`05` + `07`)~~ **HECHO Y CERRADO (2026-09-06).** Diez de diez
   criterios de aceptación. 150 documentos de dos universidades, 150/150. La parte de `07` que
   se implementó es la mínima: `Store` sobre SQLite; la orquestación completa sigue en el
   paso 7.
3. **Propagación de `01` v2.0 ← SIGUIENTE.** `00` ✔ (este documento); faltan `03`, `05`, `06`,
   `07` y el README, según la tabla de propagación de `01`.
4. **Migración del Descargador a `Encargo`** (`05`). Criterios en `01`: suite verde con cambios
   mecánicos, 150/150 en base limpia, motivos jurídicos idénticos, C20 resuelto en datos.
5. **Primer modo completo: el académico** (§8, pregunta 10, resuelta). Las dos rutas, en ese orden:
   - **Jurídica (después):** Lector de índice (`03`) → Verificador documental (`06`) → Corroborador (`04`)
     → Localizador (`02`).
   - **Académica (primero):** Lector de Lista → **extracción de texto** (paso 6, que el
     Verificador necesita) → Verificador Académico → Auditor de Lote (tres specs nuevas más la de
     extracción).
6. **Extracción de texto — spec por escribir, y sube de prioridad.** No existía en el plan
   original. La corrida de la UJAT mostró que el 23 % de su corpus son escaneos sin texto (C21
   de `08`). Desde la v2.0 la necesitan **los dos verificadores**, así que bloquea a ambos modos.
7. El otro modo.
8. Orquestación completa + CLI con menú de modos (`07`).

**Por qué la propagación va antes que cualquier pieza nueva:** las conversaciones no se ven
entre sí. Una spec que todavía hable el idioma de `01` v1.4 produciría código que no encaja.

**Por qué este orden y no el de la figura:** se construye de abajo hacia arriba. El
Descargador no depende de nadie y da resultado visible el primer día — y en efecto lo dio.
El Lector se puede probar en aislamiento porque ya hay cuatro casos reales medidos.

**Por qué el Verificador sube al cuarto lugar** (cambio respecto de v1, por evidencia): la
medición mostró que **solo 1 de 4 universidades declara vigencia en su índice** (C2 de `08`).
En los otros tres casos, la fecha real del documento solo existe dentro del PDF. Eso convierte
al Verificador Documental en el único componente capaz de fechar el corpus — deja de ser el
control de calidad final y pasa a ser fuente de un dato que nadie más produce.

**El Localizador va al final de la ruta jurídica** porque las fuentes de prueba ya se conocen: no
bloquea nada y es el más difícil de evaluar sin puntos de comparación.

Cada fase tiene criterios de aceptación en su spec. No se avanza sin cumplirlos.

---

## 7. Cómo trabajar en este Proyecto

Método heredado del proyecto hermano, que funcionó:

- **Una conversación por spec.** Al abrirla: *"Trabajamos la spec 0X. Lee 00 y 01 primero."*
- **Las "Preguntas abiertas" al final de cada spec son la agenda de esa conversación.**
- Si una conversación toma una decisión que afecta un contrato compartido, el usuario
  actualiza `01-CONTRATOS-DE-DATOS.md` en el conocimiento del Proyecto **antes** de continuar
  en otras conversaciones. Las conversaciones no se ven entre sí; los contratos son su única
  frontera común.
- **Cada spec lleva su registro de consideraciones diferidas.** Todo lo que se decide *anotar
  en vez de resolver ahora* se escribe ahí, con su gatillo de revisión. En el proyecto hermano
  este registro resultó más valioso que la spec misma.
- **Micro-tareas de ~15 min.** En la conversación se pide *"dame el prompt de M_n"* y se
  recibe el prompt para Copilot de esa tarea, nada más.
- **Un commit por tarea firmada**, con mensaje `MN: descripción`.

---

## 8. Preguntas abiertas del proyecto (no de una spec en particular)

1. ~~**Páginas JavaScript.**~~ **Casi resuelta por evidencia.** Los **4** sitios institucionales
   medidos sirven HTML plano (C1 de `08`); lo único que exigió JS fue un formato 70-I. La
   propuesta de partida es **no pagar Playwright**: saltar al siguiente eslabón de D1 cuando
   una rejilla aparezca. La UACAM era la candidata natural a romper el patrón —estatal
   pequeña— y resultó HTML plano también.
2. ~~**¿Cuántas universidades en v1?**~~ **Cuatro medidas** (UAM, UNAM, UJAT, UACAM) y **dos
   descargadas por completo** (UAM 45/45, UJAT 105/105). E6.1 cerrada. Lo que sigue sin
   respuesta es cuántas entran a la v1 del corpus, y eso depende de la fase de orquestación.
3. ~~**Versiones históricas: ¿se descargan o se ignoran?**~~ **Resuelta de hecho: se descargan**,
   con `estado="historico"`. Las 8 de la UAM ya están en el corpus. **Pero destapó un hueco de
   contrato:** dos históricos del mismo instrumento producen el mismo `entry_id` y colisionan
   (C20 de `08`). ~~Se decide en la conversación de la spec `03`.~~ **Resuelto en `01` v2.0**
   (salida B, D15).
4. ~~**Documentos por unidad/facultad.**~~ **Resuelta (2026-09-10): se adopta la propuesta.** Muchas universidades tienen normativa por plantel
   además de la general. ¿Alcance v1 = solo normativa general? Propuesta: sí.
5. ~~**¿Contrato Colectivo cuenta como legislación universitaria?**~~ **Resuelta a favor.**
   Dos de cuatro universidades medidas lo publican en su propio índice de legislación (E3.2,
   E4.1 de `08`). Entra con `tipo_norma="contrato_colectivo"`. *Nota: el de la UJAT es un
   escaneo de 28 MB sin texto extraíble — necesitará OCR.*
6. ~~**Repositorios de terceros oficiales.**~~ **Resuelta (2026-09-10): se adopta la propuesta.** La UNAM aloja legislación de otras universidades
   (E3.6 de `08`). Dominio oficial, pero no el de la institución emisora, y sin garantía de
   estar al día. Propuesta: pista de existencia para el Corroborador, nunca fuente primaria.
7. ~~**¿Se conservan los PDF originales tras extraer el texto?**~~ **Resuelta (2026-09-10): se conservan.** Nueva, y ahora es real: el 63 %
   del peso del corpus son escaneos (C21 de `08`) que tras el OCR se vuelven unos pocos MB de
   texto. Conservarlos es proveniencia dura (D5) y cuesta disco; descartarlos ahorra mucho y
   rompe la auditabilidad. **Propuesta: conservarlos** — D5 pesa más que el disco, que es
   barato. Se decide en la spec de extracción.
8. **¿Qué se hace cuando un índice está caducado (D12)?** Detectarlo es el requisito; qué
   hacer después no está decidido. ¿Se cosecha igual marcando todo como sospechoso? ¿Se salta
   al siguiente eslabón de D1 buscando un índice vivo? ¿Se manda entero a cola manual?
   Afecta al Lector y al Corroborador a la vez.
9. ~~**`robots.txt` en modo académico.**~~ **Resuelta en `05` v3 (2026-09-10): misma política en ambos modos, aplicada también al enlace del vestíbulo.** El fail-open de D8 se justificó con sitios que publican
   por ley y no son adversarios. Las editoriales y los repositorios académicos no son sujetos
   obligados. ¿Fail-open, fail-closed, o por tipo de puerta (copia libre sí, editorial no)?
   Se decide en `05`.
10. ~~**¿Qué modo se completa primero?**~~ **Resuelta (2026-09-10): el académico.** Propuesta adoptada: **el académico.** Tiene tres piezas en vez de
    cinco, su esqueleto es la propia lista (no hay que adivinar qué falta), ya hay una lista real
    para probar y sería la **primera corrida completa de punta a punta** del proyecto. En contra:
    el jurídico es el propósito original y el Lector de índice ya tiene fixtures de cuatro
    universidades. Ambas rutas necesitan la spec de extracción de texto.

---

## 9. Herencia del proyecto hermano (leer antes de escribir código)

Lecciones ya pagadas allá que aplican aquí sin cambios:

- **`.venv` siempre.** Verificar que la cabecera de pytest diga `.venv/bin/python`.
- **`extra="ignore"` en `SettingsConfigDict`.** Sin eso, un `.env` con variables de otro
  proyecto revienta cualquier comando de la CLI. Los tests no lo atrapan porque se aíslan
  con `monkeypatch.chdir(tmp_path)`: **el aislamiento que protege los tests es lo que oculta
  el fallo del entorno real.**
- **Todo módulo con CLI se prueba UNA vez a mano desde la raíz del repo antes de firmarse.**
- **Los tracebacks de pytest imprimen el repr completo de `Settings`, incluidas las API keys.**
  Revisar cualquier log antes de compartirlo. Una key ya se filtró así allá, dos veces.
- **Toda frontera modelo→persistencia convierte a tipos nativos de Python.** Nunca confiar en
  que `model_copy(update=...)` valide: no lo hace.
- **Tras cada corrida cara, respaldo inmediato de la base.** Un corpus de minutos merece una
  copia de un segundo.

### Lecciones propias, pagadas en la fase Descargador (2026-09-06)

- **El asistente de código no tiene el `.venv` activado.** Tres veces reportó
  `ModuleNotFoundError` y lo diagnosticó como dependencia faltante; una vez llegó a **recrear
  el `.venv`** tras un `find -maxdepth 4` que se quedó un nivel corto. Se resolvió con un
  `.github/copilot-instructions.md` que lo dice explícitamente. **Un error de importación es
  del intérprete hasta que se demuestre lo contrario.**
- **Verificar el trabajo del asistente con comandos, no con su resumen.** Reportó "todos los
  tests pasan" corriendo solo el archivo nuevo; reportó un problema de entorno inexistente;
  reportó "no problems found" sobre archivos que no nombró. Los tests pasaban de verdad, pero
  ninguna de esas tres afirmaciones era comprobable como estaba escrita.
- **El log de una librería no mide lo que uno cree.** `httpx` registra al *recibir* la
  respuesta, no al enviar la petición: los huecos entre sus líneas no son los intervalos entre
  peticiones. El criterio de cortesía solo se pudo verificar cuando el propio `RateLimiter`
  emitió su línea (E11.7 de `08`).
- **Medir antes de concluir, incluso cuando la inferencia es razonable.** Se dio por escaneo
  un PDF de 16 MB por su tamaño; al medirlo, tenía texto. El tamaño no predice si un documento
  es imagen (E12.5 de `08`).
- **Una extrapolación con un solo punto se equivoca por órdenes de magnitud.** Con la UAM sola
  se estimó el corpus en ~500 MB; la UJAT lo mandó a varios GB. Varianza medida entre
  instituciones: **23×** (C19 de `08`).
- **Los tests aíslan y por eso esconden.** Se repitió el patrón heredado: el test de
  `extra="ignore"` corría en `tmp_path` y no probaba nada del `.env` real; el guardián de tipos
  de SQLite solo se validó de verdad con un `typeof()` en SQL crudo y un
  `pytest -W error::DeprecationWarning`.
