# 06 · Spec — Verificador Documental (pieza ⑤)

> Conversación: "Fase Verificador". Leer antes `00` v2.0, `01` v2.2 (contratos N2, N5, N6, N7) y **`08` v7**.
> Estado: **v4** · agente LLM · **pieza del modo jurídico** (LegisUni).
> **Dos cambios grandes desde la v2, ambos por datos:** E6.6 (¿cuántos PDF son escaneos?) está
> medida y **refutó la hipótesis de esta spec**; y el corpus ya no es solo PDF: hay `.docx`.
> **v4 (2026-09-10), por la llegada del modo académico:** C20 quedó resuelto en `01` y no aquí;
> esta pieza gana la conciliación de copias con el mismo `doc_id`; lee de `descargas` y escribe
> en `documentos` (`07` v2); y comparte la extracción de texto con el Verificador Académico, que
> es **otra pieza con otra spec**.

---

## Qué cambia en la v4 (leer primero)

| Cambio | Sección |
|---|---|
| **Orden de construcción:** dentro de la ruta jurídica sigue siendo prioritaria, pero la ruta académica va antes (`00` §6, pregunta 10) | Por qué esta pieza subió de prioridad |
| C20 resuelto en `01` v2.0 (D15): esta pieza **no** gana la tercera función que la v3 anticipaba | Versiones e identidad |
| Nueva tarea: conciliar dos archivos distintos con el mismo `doc_id` | Versiones e identidad |
| Los duplicados por hash ya llegan marcados (`duplicado_de`): no cuestan llamada al LLM | Versiones e identidad |
| Frontera explícita con el Verificador Académico; `extract.py` pasa a ser compartido | Frontera con el Verificador Académico |
| `consolidate.py` llena `NormativeRecord.entry_id` | Diseño |
| Criterios 13–15; criterio 8 ajustado | Criterios |

---

## Objetivo

Para cada documento descargado, abrir sus primeras páginas y responder dos preguntas:

1. **¿Es lo que el catálogo dice que es?** (identidad)
2. **¿De cuándo es?** (fecha real de la versión)

Producir un `DocumentVerdict` (N6) y, si pasa, consolidar el `NormativeRecord` (N7).

---

## Por qué esta pieza subió de prioridad (cambio de v1 a v2)

En el diseño original era la última rueda: un control de calidad al final del flujo. **La
medición la convirtió en pieza esencial.**

De las **cuatro** universidades medidas (C2 de `08`), **solo la UAM declara vigencia en su
índice**:

| | Vigencia en el índice | ¿De dónde sale la fecha? |
|---|---|---|
| UAM | *"vigente hasta el 16 de marzo de 2026"* | Del índice |
| UNAM | Nada visible | Solo del PDF |
| UJAT | Nada, ni consistente en nombres | Solo del PDF |
| UACAM | Nada. Y el índice entero caducó en 2016 | Solo del PDF |

Es decir: **en tres de cuatro casos, el eje temporal del corpus no existe hasta que esta pieza
corre.** Y sin eje temporal, un corpus jurídico es peligroso: citar un reglamento derogado no
es un error de forma.

De ahí que la fechación deje de ser un subproducto del juicio y pase a ser **la segunda
función declarada** de la pieza.

> **v4 · orden de construcción.** Todo lo anterior sigue valiendo **dentro del modo jurídico**:
> sin esta pieza, tres de cuatro corpus no tienen eje temporal. Pero desde `00` v2.0 el modo
> académico se completa primero (`00` §6, pregunta 10). Esta pieza se construye con la ruta
> jurídica, después. Lo que no espera es la spec de extracción de texto, que ambas rutas
> necesitan.

**La UACAM añade un nivel más.** Su índice declara «Fecha de corte: Diciembre del 2016»
(D12 de `00`). Ahí el Verificador no solo aporta la fecha que el índice no da: es el único
componente capaz de decir **si los documentos son tan viejos como el índice o no**. Un
instrumento de 2019 en un índice congelado en 2016 significa que el índice se actualizó
parcialmente; uno de 2015 confirma la congelación. Ese dato no existe en ninguna otra parte
del sistema.

---

## "Verídico" son tres cosas distintas

Separarlas sigue siendo la decisión de diseño central:

| | Qué pregunta | Quién la responde |
|---|---|---|
| **Autenticidad** | ¿Viene de una fuente oficial? | El **dominio** (D9), fijado por el Localizador. No este agente. *(En modo académico no hay ancla de dominio: rige D13, y eso es trabajo del Verificador Académico.)* |
| **Integridad** | ¿El archivo llegó completo y sin corromper? | El **hash y el guardián de formato** (spec 05). Código, no agente. |
| **Identidad y vigencia** | ¿Es el instrumento correcto, en su versión correcta? | **Este agente.** |

El Verificador Documental **no juzga si la fuente es confiable** — eso ya se decidió antes y
por otro criterio.

---

## Alcance

### Qué lee

Las **primeras 2–3 páginas** del PDF, extraídas como texto. Es donde vive todo lo que importa:
el título del instrumento, la institución emisora, el órgano que lo aprobó, la fecha de
aprobación y la leyenda de última reforma.

**No lee el documento completo.** Es caro, innecesario y no mejora el juicio.

### La fechación: tres fuentes que hay que reconciliar

Para un mismo documento pueden coexistir tres fechas distintas, y no siempre coinciden:

1. **La del índice** (`CatalogEntry.fecha_ultima_reforma`) — a veces no existe.
2. **La del nombre de archivo** — `_rem38_021220`, `...11072024.pdf`,
   `REFORMADO-25032026.pdf`. Formatos heterogéneos: `DDMMYY`, `DDMMAAAA`, con marcas de
   remisión. **Ambigua por sí sola** y por eso el Lector no la interpreta (spec `03`).
3. **La declarada dentro del documento** — típicamente una leyenda como *"Última reforma
   publicada en la Gaceta …"* en las primeras páginas.

**Regla de precedencia: (3) manda sobre (2) manda sobre (1).** El documento es la fuente
autoritativa sobre sí mismo; el nombre de archivo es una pista fuerte que además ayuda a
desambiguar el formato de fecha; el índice es la más débil.

Cuando (3) y (1) discrepan, el veredicto es `discrepancia` y ambas fechas quedan registradas.
No se elige en silencio.

### Qué compara

1. **Título:** ¿el del documento corresponde al del `CatalogEntry`? Tolerante a variantes de
   redacción y mayúsculas; intolerante a que sea otro instrumento.
2. **Institución:** ¿el documento es de esta universidad? Atrapa el enlace que apunta a la
   normativa de otra institución — riesgo real, porque la UNAM aloja legislación de terceros
   en su propio dominio (E3.6 de `08`).
3. **Fecha**, según la precedencia de arriba.
4. **Estado inferido:** si el texto dice "abrogado", "deja de tener vigencia" o similar, eso
   pesa más que cualquier cosa que diga el índice.

### Caso especial: la Ley Orgánica y su doble versión

Medido en la UJAT (E4.4 de `08`): la universidad publica su Ley Orgánica desde una carpeta de
2012, mientras el Congreso del Estado publica la suya por separado. **D2 exige bajar ambas.**

El Verificador compara las dos y determina cuál es la vigente. Si la del sitio universitario
es más vieja, la del Congreso gana y la otra queda como `historico`. **Es el único punto del
sistema donde se comparan dos documentos entre sí**, y merece prompt propio.

### Caso especial: cinco candidatos para el mismo instrumento

Medido en la UACAM (E10.4 de `08`): su Ley Orgánica está enlazada desde **cinco lugares** de la
misma página, y **no todos apuntan a la misma versión**.

El Lector conserva los cinco candidatos sin elegir (spec `03`), y el Corroborador tampoco puede
elegir porque no abre documentos (pregunta 9 de `04`). **La elección cae aquí**, y es la misma
mecánica que el caso de la doble Ley Orgánica de arriba, escalada a *n* versiones: se comparan,
gana la más reciente por fecha declarada dentro del documento, y las demás quedan `historico`.

**Ninguna se descarta.** Que una universidad publique cinco versiones divergentes de su norma
fundante es un hallazgo sobre esa universidad, no un estorbo a limpiar.

### Versiones e identidad (v4 · C20 resuelto fuera de aquí)

**La v3 anticipaba que esta pieza podía ganar una tercera función:** resolver en N7 la colisión
de `entry_id` entre versiones (C20 de `08`). **No la gana.** `01` v2.0 eligió la salida B
(D15): cada publicación tiene su propio `entry_id`, porque incorpora su dirección de origen. Los
dos históricos del Reglamento de Estudios Superiores de la UAM ya llegan aquí como dos entradas
distintas. El prompt de juicio no cambia por C20.

**Lo que sí cambia para esta pieza son tres cosas:**

1. **Hay dos identidades y hay que llenar ambas.** `entry_id` es la *foto publicada*; `doc_id`
   es la *versión jurídica* (`01` N7). `consolidate.py` escribe las dos en el `NormativeRecord`.
2. **Los duplicados exactos ya no llegan como archivos.** Si dos publicaciones tienen los
   mismos bytes, el Descargador lo resolvió con el alias por hash (`05` v3) y el
   `DownloadResult` trae `duplicado_de`. Esta pieza **no llama al LLM** para ellos: los reporta
   como duplicado del original y hereda su veredicto.
3. **Nueva tarea: conciliar copias con el mismo `doc_id` y bytes distintos.** Es el límite
   conocido de la salida B (`01` N2): una universidad re-exporta el mismo texto, cambian los
   bytes, el hash no coincide, y esta pieza lee dos veces el mismo instrumento con la misma fecha
   declarada. **Decisión (ratificada 2026-09-10; misma en `07` y `01`):** ambos archivos se conservan en
   `descargas`; el `NormativeRecord` apunta al primero con veredicto `ok`; el otro se anota como
   copia equivalente. **Nunca se borra ninguno.** Pregunta abierta 10.

### Los tres fallos que debe atrapar

Fallos **reales y frecuentes** en sitios institucionales, no hipótesis:

- **Enlace cruzado:** el vínculo del Reglamento de Estudios apunta al Reglamento del Alumnado.
- **Versión vieja:** el índice dice "vigente" pero el PDF declara una reforma anterior.
- **Documento de otra institución:** más raro pero letal, porque pasa desapercibido para todo
  lo demás.

### Regla de honestidad

El agente **no reescribe ni corrige**: juzga y reporta. Si no puede decidir, `confianza="baja"`
y a revisión humana. Un veredicto `ok` de baja confianza es peor que un `no sé` explícito.

> Replica la separación Redactor/Verificador del proyecto hermano, y por la misma razón: quien
> produce no debe ser quien juzga, o el juicio se vuelve auto-complaciente. Aquí el productor
> es el Lector de Índice.

### Documentos escaneados — E6.6 medida, y la hipótesis era falsa

**Este es el cambio grande de la v3.** La v2 decía: *"Propuesta: no OCR en v1; medir primero
cuántos son. Si son 2 de 60, la cola manual es más barata. La sospecha es que se concentran en
las leyes orgánicas estatales viejas."*

**Ya está medido (C21, C22, E12.5 de `08`), y las dos partes de esa frase eran falsas:**

| | UJAT | UAM |
|---|---|---|
| Documentos sin texto extraíble | **24 de 105** (23 %) | **0 de 42** |
| Peso de esos documentos | **179 MB** de 285 (63 %) | — |

- **No son 2 de 60: son 24 de 105.** La cola manual para 24 documentos no es más barata que
  el OCR; es media jornada de trabajo humano por universidad.
- **No son leyes orgánicas viejas: son documentos firmados.** Acuerdos rectorales, el contrato
  colectivo (28 MB), acuerdos de género y de firma electrónica. Se escanean **porque llevan
  firma**, no por antigüedad. La Ley Orgánica de la UJAT, en cambio, tiene texto.

**Consecuencia directa para esta pieza:** el Verificador **no puede juzgar el 23 % del corpus
de la UJAT**. No es que le cueste: no hay texto que leer. Esos 24 documentos irían a
`ilegible` + cola manual, y con ellos se va el contrato colectivo entero.

**Qué se decide aquí y qué no:**

- **Aquí:** el veredicto de un documento sin texto extraíble es `ilegible`, con
  `confianza="baja"`, y **nunca un juicio inventado**. Eso no cambia.
- **Aquí también:** el Verificador **detecta y reporta** que un documento es imagen, porque es
  quien lo abre. Ese dato alimenta la fase de extracción.
- **No aquí:** si se hace OCR, con qué motor y con qué umbral de calidad. Eso es la **spec de
  extracción de texto** (paso 6 de `00` §6), que no existe todavía y que nació justamente de
  esta medición. Decidirlo en esta conversación sería resolver el problema de otro.
  **v4:** esa spec ahora la necesitan **los dos verificadores**, y por eso sube al paso 6 de
  `00` §6: bloquea a ambos modos.

**Y ojo con el criterio de aceptación:** pedirle al Verificador un 80 % de fechación sobre el
corpus de la UJAT es **imposible** mientras el 23 % sea ilegible. El techo real es 77 %. El
criterio 3 se recalibró por eso.

### El corpus no es solo PDF: hay `.docx`

`01` v1.3 aceptó `.docx`, y hay tres en el corpus de la UAM (anexos del protocolo de violencia
de género). **`extract.py` tiene que manejarlos**, no solo PDF.

No es complicado —`python-docx` o `mammoth`— pero es un caso que la v2 no contemplaba y que
haría fallar la extracción en silencio: un `.docx` abierto con `pdfplumber` lanza excepción, y
si esa excepción se traduce a `ilegible`, tres documentos legítimos y con texto perfecto se
irían a cola manual sin razón.

### Frontera con el Verificador Académico (v4)

Los dos abren un archivo y juzgan si es lo pedido. **No son la misma pieza** y no deben
fusionarse:

| | Verificador Documental (esta spec) | Verificador Académico (spec nueva) |
|---|---|---|
| Modo | jurídico | académico |
| Compara contra | `CatalogEntry` (N2) | `ArticleRef` (N11) |
| Evidencia principal | título, institución, **fecha declarada** | **DOI**, título, primer autor, año |
| Confiabilidad | dominio (D9), fijado antes | contenido (D13), la decide él |
| Produce | `DocumentVerdict` (N6) → `NormativeRecord` (N7) | `ArticleVerdict` (N13) |
| Fechación | **función central** | no fecha nada; anota la edición |
| Compara versiones entre sí | sí (Ley Orgánica doble, cinco candidatos) | no |

**Comparten solo la apertura del sobre:** `extract.py` (primeras páginas → texto, PDF y
`.docx`, detección de documentos sin capa de texto) y, cuando exista, el OCR. Por eso
`extract.py` sale de `verificador/` a un paquete común (ver Diseño). **Los prompts no se
comparten:** cada uno juzga con criterios distintos, y un prompt que sirviera para ambos
juzgaría mal los dos.

---

## No-alcance

- NO verifica artículos científicos (Verificador Académico).
- NO extrae el articulado ni trocea (fase de chunking, futura).
- NO juzga contenido jurídico.
- NO decide autenticidad de la fuente.
- NO repara documentos.

---

## Diseño

```
extraccion/                 # común a ambos verificadores (v4)
  extract.py      # primeras N páginas -> texto. PDF (pdfplumber) Y .docx (python-docx).
                  # Detecta y reporta cuando no hay capa de texto: dato para la fase
                  # de extracción, no solo un fallo local.

verificador/                # modo jurídico
  fechas.py       # parseo de fechas heterogéneas: texto libre, DDMMYY, DDMMAAAA
  agent.py        # prompt de juicio; salida JSON estricta
  compara.py      # n versiones del mismo instrumento frente a frente
  concilia.py     # copias con el mismo doc_id y bytes distintos (v4)
  consolidate.py  # DocumentVerdict + CatalogEntry + DownloadResult -> NormativeRecord
                  # (llena entry_id y doc_id, v4). Lee de `descargas`, escribe en `documentos`
  models.py
```

**Sobre la ubicación de `extraccion/`:** la spec de extracción de texto puede reorganizarla. Lo
que esta spec fija es que **no viva dentro de ninguno de los dos verificadores**.

**`extract.py` distingue tres resultados, no dos:** texto extraído, **documento sin capa de
texto** (imagen), y error de lectura. Los dos últimos producen `ilegible`, pero por razones
distintas y hay que poder contarlas por separado — el primero es candidato a OCR, el segundo
es un archivo roto.

**Sobre `evidencia`:** el `DocumentVerdict` guarda el fragmento concreto del documento en que
se basó el juicio. Sin eso, el veredicto no es auditable y no sirve de nada revisarlo después.
Es el principio de proveniencia de D5 aplicado al juicio en vez de al dato.

`fechas.py` es código, no LLM. El parseo de `021220` a `2020-12-02` es determinista una vez
elegido el formato, y un agente que lo haga a ojo introducirá errores silenciosos en el eje
temporal del corpus entero.

---

## Criterios de aceptación

**Los corpus ya existen.** UAM (45 documentos) y UJAT (105) están descargados y en disco desde
las corridas E11 y E12 de `08`. No hay que conseguir material: hay que abrirlo.

1. **Corpus UAM completo:** sobre los **45 documentos** descargados (42 PDF + 3 `.docx`),
   ≥ 95 % con veredicto `ok`. **Los tres `.docx` deben producir veredicto real, no `ilegible`**
   — tienen texto perfecto y fallarían solo por no manejar el formato.
2. **Fechación UNAM — el criterio que justifica la subida de prioridad.** Sobre los ~60
   documentos de la UNAM, cuyo índice **no declara vigencia alguna**, el Verificador produce
   `fecha_reforma_declarada` para ≥ 80 %. Si falla aquí, el corpus de la UNAM queda sin eje
   temporal y el sistema no cumple D6.
3. **Fechación UJAT — recalibrado por medición.** Sobre sus 105 documentos, **24 son escaneos
   sin texto** (C21 de `08`), así que el techo teórico es 77 %. El criterio es:
   **`fecha_reforma_declarada` para ≥ 90 % de los 81 documentos legibles**, y los 24 restantes
   clasificados como `ilegible` **por ausencia de capa de texto**, no por error de lectura.
   *La v2 pedía ≥ 80 % del corpus completo, que es imposible; el criterio se corrigió cuando la
   medición lo demostró.*
4. **Detección de escaneos:** el Verificador identifica los 24 documentos-imagen de la UJAT con
   ≥ 95 % de acierto contra la lista medida, y **cero falsos positivos** entre los 81 legibles.
   Ese conteo es el insumo de la spec de extracción.
5. **Prueba adversarial de enlace cruzado:** se altera a mano una entrada del catálogo para
   que apunte a otro reglamento; el Verificador emite `documento_erroneo`.
6. **Prueba de institución:** se inyecta un PDF de normativa de otra universidad — hay
   material real disponible en el repositorio de terceros de la UNAM (E3.6 de `08`) — y se
   detecta.
7. **Caso Ley Orgánica doble (UJAT):** con las dos versiones bajadas (sitio universitario de
   2012 y Congreso de Tabasco), el Verificador identifica cuál es la vigente y marca la otra
   `historico`. Ningún documento se descarta.
8. **Caso cinco candidatos (UACAM, E10.4):** las cinco versiones de la Ley Orgánica se comparan
   entre sí; gana una por fecha declarada y las otras quedan `historico`. **Si dos resultan
   idénticas por hash, llegan ya marcadas con `duplicado_de` (`05` v3): se reportan como
   duplicado, no como versiones distintas, y no entran a la comparación.**
9. **Prueba de fecha discrepante:** un documento cuya reforma declarada no coincide con la del
   catálogo produce `discrepancia`, no `ok` silencioso.
10. **Índice caducado (UACAM, D12):** sobre su corpus, el Verificador reporta la distribución
    de fechas reales. **Si algún documento es posterior a diciembre de 2016**, es evidencia de
    que el índice se actualizó parcialmente pese a su declaración — hallazgo que ninguna otra
    pieza puede producir.
11. **Falso positivo bajo:** revisión humana de 10 veredictos `discrepancia`; ≥ 8 deben ser
    discrepancias reales. Un verificador que se queja de todo no se usa.
12. **Coste:** ≤ 1 llamada al LLM por documento (los casos de comparación de versiones pueden
    usar más, y se registran aparte). **Ojo:** 150 documentos ya en disco son 150 llamadas por
    corrida completa; conviene medir el coste real antes de escalar a 40 universidades.

### v4 — identidad y frontera

13. **C20 en consolidación:** los dos históricos del Reglamento de Estudios Superiores de la UAM
    (E11.6 de `08`) producen **dos `NormativeRecord`**, cada uno con su propio `entry_id` y su
    `doc_id` según la fecha declarada dentro del documento.
14. **Duplicado sin costo:** un `DownloadResult` con `duplicado_de` produce su reporte de
    duplicado con **cero llamadas al LLM**.
15. **Conciliación:** dos archivos con bytes distintos y la misma fecha declarada del mismo
    instrumento producen **un** `NormativeRecord`, apuntando al primero aprobado, y ambos
    archivos siguen en disco y en `descargas`. Se prueba con una re-exportación simulada (mismo
    texto, metadatos distintos).

> **Criterio común con la spec de extracción:** `extraccion/extract.py` se usa desde ambos
> verificadores sin duplicarse. Lo verifica esa spec, no esta.

---

## Preguntas abiertas (agenda de esta conversación)

1. ~~**¿OCR para los escaneados?**~~ **E6.6 medida (C21 de `08`), y la hipótesis era falsa.**
   No son "2 de 60": son **24 de 105** en la UJAT y 0 de 42 en la UAM. No se concentran en
   leyes orgánicas viejas sino en **documentos firmados** (acuerdos rectorales, contrato
   colectivo). La cola manual **no** es más barata que el OCR a esa escala.
   **Pero la decisión no se toma aquí:** el OCR es la spec de extracción de texto (paso 6 de
   `00` §6). Lo que sí le toca a esta pieza es **detectar y contar** los documentos-imagen, que
   es el criterio 4. Sigue abierto solo un flanco: **¿el Verificador debe intentar juzgar un
   documento con OCR de baja calidad, o rechazarlo?** Propuesta: rechazarlo. Un juicio sobre
   texto corrupto es peor que un `ilegible` honesto.
2. **¿Cuántas páginas leer?** 2–3 es la propuesta. Medir si alguna Ley Orgánica pone la
   leyenda de reforma más adelante. **Hay material para medirlo ya:** 150 documentos en disco.
3. **¿Modelo distinto al del Lector?** El proyecto hermano decidió que el Verificador usara
   otro prompt —idealmente otra "personalidad"— que el productor. Vale la pena replicarlo.
4. **¿Qué hacer con `discrepancia`?** ¿Entra al corpus marcado o se queda fuera? Propuesta:
   entra, marcado, porque un documento correcto con fecha dudosa sigue siendo más útil que
   ningún documento — pero la fase de chunking debe poder filtrarlo.
5. **¿Y con `estado="desconocido"` que sigue desconocido tras verificar?** Será el caso de los
   documentos sin leyenda de reforma. Propuesta: entra al corpus con la fecha de captura como
   límite inferior conocido, marcado explícitamente como no fechado.
6. **Ciclo de corrección.** Si el veredicto es `documento_erroneo`, ¿se re-dispara el Lector
   sobre ese índice? Propuesta: sí, una vez, y si vuelve a fallar → cola manual.
7. ~~**¿Esta pieza resuelve la identidad de las versiones (C20)?**~~ **Resuelta en `01` v2.0
   (D15, salida B): no.** El prompt de juicio no cambia por C20. Ver §Versiones e identidad.
8. **¿Cuánto cuesta de verdad?** 150 documentos ya en disco permiten medir el coste por
   universidad **antes** de escalar. Es el tipo de número que allá se estimó a ojo y salió mal.
9. **Prompts exactos:** el de juicio y el de comparación de versiones. Redactarlos y probarlos
   aquí con los casos 5–8.
10. ~~**Conciliación de copias con el mismo `doc_id` (v4).**~~ **Ratificada (2026-09-10).** Compartida con la pregunta 7 de `07`
    y la 4 de `01`. Propuesta en §Versiones e identidad. **Quien llegue primero la ratifica y
    actualiza las otras dos.**

---

## Registro de consideraciones diferidas

*(Se llena durante la implementación.)*
