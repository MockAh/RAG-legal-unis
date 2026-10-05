# 04 · Spec — Corroborador (pieza ③)

> Conversación: "Fase Corroborador". Leer antes `00` v2.0, `01` **v2.7** (contratos N3, N4, N8,
> N15) y **`08` v18**.
> Estado: **v3** (2026-10-04) · agente LLM. Depende de un `Catalog` funcional (spec `03` v5).
> **La medición de la UACAM cambió esta spec más que ninguna otra.** Aportó el primer hueco
> crítico real del proyecto —una universidad a la que le falta su Estatuto Orgánico— y con él
> la primera oportunidad de validar que esta pieza sirve. También destapó dos problemas que la
> v1 no contemplaba: un índice puede estar caducado, y "presente en el catálogo" no es binario.
> **La v3 recoge dos propagaciones de `01` que la v2 no tenía, y las dos tocan el mismo nervio:**
> esta pieza puede atribuir a una universidad un hueco que no es suyo. Si el Lector leyó a medias,
> o si el usuario pidió solo un tema, el catálogo que llega está incompleto **por nuestra causa**,
> y declararlo hueco manda a alguien a buscar al Periódico Oficial un documento que sí estaba
> publicado.

---

## Qué cambia en la v3 (leer primero)

| Cambio | Sección |
|---|---|
| **Un hueco del Lector no es un hueco de la universidad** (`01` v2.6, N3) | §Lo que no es un hueco · criterio 13 |
| **`completo` se calcula sobre el catálogo completo, nunca sobre la selección temática** (`01` v2.7, N15) | §Lo que no es un hueco · criterio 14 |
| Números corregidos: UAM **47** enlaces (no 45); UACAM **87** (no ~82) | criterios 1, 12 |
| **El «27 propios» de la UACAM sigue sin medir y no se puede medir con `grep`** | §Qué hace con lo inesperado |
| **El abogado del Auditor:** qué es, qué lo haría examinable, y qué no | pregunta 10 |
| El esqueleto por régimen, con el dato que falta: **el tecnológico no está medido** (E6.2) | pregunta 1 |
| **Unificar `doc_slug` entre un catálogo a mano y un índice institucional** (E21.15, E6.25) | pregunta 11 |
| El estado real del Lector: su núcleo determinista está construido; su agente, no | §Dependencias |

---

## Objetivo

Responder una sola pregunta con evidencia: **¿este catálogo está completo?**

No "¿existe este documento?" (eso lo sabe el Lector), sino "¿qué debería haber aquí que no
está?". Produce un `CoverageReport` (N4) y alimenta la cola manual (N8).

---

## Dependencias, al 2026-10-04

Esta pieza depende de un `Catalog` funcional. Estado real de la spec `03`:

- **Construido y medido (M41–M46):** el núcleo determinista del Lector —reducción, filtrado,
  fecha de corte, `doc_slug`, contabilidad—. Los conteos 47 / 109 / 156 se reproducen desde
  `lector/`, y **ningún `doc_slug` de la UAM es ya una fecha** (E13.5 cerrada).
- **Falta:** el agente del Lector y su evaluación. Sin él no hay `tipo_norma` ni `estado`, que es
  justo lo que esta pieza coteja.

**Consecuencia práctica:** el Corroborador se puede diseñar y discutir ya, pero sus criterios 1,
3, 4 y 8 no se pueden puntuar hasta que el Lector clasifique. Lo que **sí** se puede construir hoy
es todo lo determinista: `jerarquia.py`, `esqueleto.py` y las reglas de §Lo que no es un hueco.

---

## El principio: contra un esqueleto, no contra Wikipedia

La tentación es cotejar contra fuentes enciclopédicas. **Es la fuente equivocada:** Wikipedia
puede decirte que una universidad existe y cuándo se fundó, pero no qué reglamentos tiene
vigentes hoy ni cuál se abrogó el mes pasado.

El cotejo correcto es contra un **esqueleto normativo esperado**: toda universidad pública
autónoma mexicana tiene, por la estructura misma de su régimen jurídico, un conjunto de
instrumentos previsibles. Lo que falte de ese esqueleto es un hueco real.

### La medición subió el peso de esta pieza

En el diseño v1 el Corroborador era una comprobación de cortesía. Dejó de serlo cuando la
UJAT mostró que **la taxonomía del sitio puede estar rota** (E4.1 de `08`): su Ley Orgánica y
su Estatuto General están archivados bajo "Otros documentos", junto a un tabulador de sueldos.
La UNAM, en cambio, publica su índice ordenado por jerarquía normativa real.

Consecuencia: **el esqueleto esperado es más confiable que la clasificación publicada** (D11).
El Corroborador no está verificando el trabajo del Lector: está aportando la única estructura
en la que se puede confiar.

### El primer hueco crítico real: la UACAM no publica su Estatuto Orgánico

**Medido (E10.5 de `08`).** En el índice de legislación de la UACAM está la Ley Orgánica —varias
veces, incluso— y no está el Estatuto Orgánico. No es un problema de clasificación ni de
nombre distinto: **el documento no aparece.**

Esto importa por dos razones:

1. **Es la validación de esta pieza.** Hasta ahora el Corroborador se justificaba con un
   argumento: "podría haber huecos". Ahora hay uno medido, en la segunda universidad estatal
   que se miró. Un sistema sin Corroborador entregaría el corpus de la UACAM como si estuviera
   completo.
2. **Es el caso de prueba que faltaba.** Los criterios de la v1 solo probaban que el
   Corroborador **no** inventara huecos falsos. Ninguno probaba que **encontrara** uno real.

### Un índice puede estar caducado (D12)

**Medido (C13 de `08`).** La UACAM declara al pie: «Fecha de corte: Diciembre del 2016». El
índice es HTML impecable y sus documentos existen y responden.

Para el Corroborador esto es un modo de fallo nuevo y grave: **un catálogo caducado puede
verse completo.** Si la universidad emitió tres reglamentos desde 2017, no faltan del índice
por descuido — el índice simplemente dejó de contarlos. Cotejar contra el esqueleto no lo
detecta, porque el esqueleto de 2016 y el de hoy se parecen.

**Requisito:** cuando `Catalog` venga marcado como caducado, el `CoverageReport` **no puede
declarar `completo=True`**, por bien que cubra el esqueleto. La antigüedad del índice es una
razón independiente de incompletitud.

> **Nota de la v3:** desde M43, la detección es **determinista y no depende del agente**. El
> `corte.py` del Lector encuentra «Fecha de corte:&nbsp;Diciembre del 2016» con el agente
> desconectado y marca `catalogo_caducado`. Para esta pieza eso significa que el campo llega
> fiable: **si viene `True`, es un hecho medido, no un juicio.**

### "Presente en el catálogo" no es binario

**Medido (E10.4 de `08`).** La UACAM enlaza su Ley Orgánica desde varios lugares distintos de la
misma página, y **no todos apuntan a la misma versión**.

Para el Corroborador, la rúbrica `ley_organica` está cubierta — pero decir `completo=True` sin
más sería engañoso: hay una discrepancia sin resolver. Un instrumento presente varias veces con
versiones divergentes es un hallazgo, no una tranquilidad.

**Requisito:** el `CoverageReport` distingue entre *cubierto sin ambigüedad* y *cubierto con
candidatos en conflicto*. Lo segundo va al reporte aunque no sea un hueco.

---

## Lo que NO es un hueco de la universidad (v3)

**Es la sección nueva de esta versión, y su nervio es uno solo: no atribuir a la institución un
hueco que es nuestro.** Un `ManualQueueItem` que manda a alguien al Periódico Oficial de Campeche
a buscar un documento que sí estaba publicado en el índice no es un ítem mediocre: es trabajo
humano desperdiciado por una afirmación falsa.

### 1 · El Lector leyó a medias (`01` v2.6)

`Catalog` (N3) distingue desde la v2.6 tres situaciones que antes caían todas en
`lector_agotado` + `notas`:

| Lo que trae el `Catalog` | Qué significa | Qué hace el Corroborador |
|---|---|---|
| `lector_agotado=True` | la página es una rejilla JS y no traía nada | **no coteja**: no hay catálogo que juzgar. `confianza="baja"`, y el hueco es del eslabón de D1, no de la universidad |
| `fallo_lector="salida_invalida"` | el agente respondió y su JSON no validó | **no coteja.** La página podía ser perfectamente legible |
| `lectura_incompleta=True` | el agente emitió 40 entradas de 47 vistas | **coteja, pero no puede declarar `completo=True`**, y ninguna rúbrica descubierta se marca `critico` sin advertencia |

**Reglas duras:**

1. **`completo=True` exige `lectura_incompleta=False`.** Una lectura truncada no prueba ausencia:
   prueba que no miramos todo.
2. **Un hueco hallado sobre una lectura incompleta lleva su procedencia.** El `Hueco` dice en
   `descripcion` que la lectura fue parcial, y `CoverageReport.confianza` baja a `media` o
   `baja`. Sin eso, el reporte afirma con la misma voz «la UACAM no publica su Estatuto» y «no
   vimos 7 de 47 enlaces».
3. **`enlaces_sin_cuenta` se copia al reporte.** Es la lista de lo que el Lector vio y no explicó.
   El Corroborador no la investiga —no es su trabajo— pero sí la pasa, porque es la diferencia
   entre un hueco de la universidad y un hueco nuestro.
4. **Esto no se puede inferir del conteo.** Un catálogo de 40 entradas es indistinguible de uno
   de 47 si no se mira la contabilidad. Por eso los campos existen.

> **Es la misma clase de fallo que C13**, un eslabón más abajo: el sistema afirmaría con
> confianza y sin errores que a una universidad le faltan documentos que sí publica.

### 2 · El usuario pidió solo un tema (`01` v2.7)

`SeleccionTematica` (N15) permite descargar solo parte de un catálogo. **No cambia nada de lo que
esta pieza hace, y por eso hay que escribirlo:**

- **`CoverageReport` se calcula siempre sobre el catálogo completo**, nunca sobre
  `SeleccionTematica.incluidas`. Un catálogo de deportes «completo» sin su estatuto habilitante
  sigue estando incompleto por construcción, que es justo lo que la comprobación de jerarquía
  existe para cazar.
- **Una entrada excluida por tema no es un hueco**, no genera `ManualQueueItem` y no cuenta en
  `inesperados`.
- **El Corroborador no lee `SeleccionTematica`.** Recibe el `Catalog` y nada más. Si alguna vez
  necesitara saber qué se descargó, eso es otra pregunta y otra pieza.

---

## Esqueleto esperado (v1 — refinar en esta conversación)

| Rúbrica | `tipo_norma` | Severidad si falta | Nota |
|---|---|---|---|
| `ley_organica` | `ley_organica` | **crítico** | Casi nunca en el sitio universitario (D2) |
| `estatuto_general` | `estatuto` | **crítico** | "Estatuto General", "Estatuto Orgánico" o "Reglamento Orgánico". **Hueco real medido: la UACAM no lo publica** (E10.5 de `08`) |
| `organos_colegiados` | `reglamento` | importante | Consejo/Colegio, Junta de Gobierno |
| `personal_academico` | `reglamento` | importante | Ingreso, promoción y permanencia |
| `alumnado` | `reglamento` | importante | Inscripción, estudios, exámenes |
| `estudios_posgrado` | `reglamento` | menor | A veces dentro del de estudios |
| `transparencia_datos` | `reglamento` | importante | Obligatorio por LGTAIP |
| `responsabilidades_etica` | `codigo` | importante | Código de ética / de conducta |
| `violencia_genero` | `protocolo` | importante | Prácticamente universal desde ~2020 |
| `defensoria_derechos` | `reglamento` | menor | No todas la tienen |
| `presupuesto_adquisiciones` | `reglamento` | menor | |
| `personal_administrativo` | `contrato_colectivo` | menor | **Confirmado con datos:** UNAM y UJAT lo publican en su propio índice de legislación |

**Regla de jerarquía:** un catálogo con reglamentos pero sin estatuto, o con estatuto pero sin
Ley Orgánica, está incompleto por construcción. La pirámide normativa no tiene huecos en el
medio. Esta comprobación es puro código, no necesita LLM.

---

## Alcance

### Tres cotejos, en orden de coste

1. **Contra el esqueleto** (código + LLM para mapear títulos a rúbricas). Barato, siempre.
2. **Contra el 70-I de la PNT** (agente). Si el catálogo del sitio institucional trae 30
   instrumentos y el 70-I trae 45, hay 15 que investigar — y viceversa.
3. **Contra el Periódico Oficial / DOF** (agente), solo para la Ley Orgánica y sus reformas.
   Es el único documento que casi con certeza NO está en el sitio de la universidad.

### El mapeo título → rúbrica es el trabajo real del LLM

Las universidades nombran lo mismo de formas distintas: "Estatuto General", "Reglamento
Orgánico", "Ley Orgánica y Estatuto"; "Reglamento de Ingreso, Promoción y Permanencia del
Personal Académico" vs. "Estatuto del Personal Académico". El agente debe reconocer **la
función del instrumento, no su nombre**. Eso es lo que ningún diccionario fijo resuelve.

### Qué hace con lo inesperado

Los instrumentos que no encajan en ninguna rúbrica **no son error**: van a
`CoverageReport.inesperados` y se conservan íntegros en el catálogo. El esqueleto es un piso,
no un techo. Una universidad con un reglamento de radiodifusión propio simplemente lo tiene.

**Pero cuidado con el denominador.** Medido en la UACAM: su índice tiene **87 enlaces únicos a
documento** (83 PDF + 4 de visor, M42 de `PLAN-MIGRACION.md`; E20.5 decía 81 porque su `grep` no
distinguía mayúsculas). De ellos, **~27 serían normativa propia según la estimación de E10** — el
resto son contratos y convenios por ejercicio, formularios y documentos de otras instituciones.
**Dos de cada tres enlaces del índice no son instrumentos normativos.**

> **El «27» sigue sin medir, y no se puede medir con `grep`** (E20.5). Separar la normativa propia
> de la ajena exige **leer los títulos**, que es exactamente lo que esta pieza y el Lector hacen.
> Escribir ese oráculo a mano es trabajo humano pendiente, y sirve a la vez al criterio 4 de `03`
> y al criterio 12 de aquí.

Si el Corroborador razona sobre el conteo bruto del catálogo —"esta universidad tiene 87
documentos, seguro está completa"— concluye mal. El descarte lo hace el Lector, pero el
Corroborador no debe apoyarse en volumen como señal de completitud.

### Cuándo se declara completo

`completo=True` exige **las seis** condiciones:

1. Cero huecos críticos.
2. ≤ 2 huecos importantes, cada uno con pista concreta de dónde buscarlo.
3. **El catálogo no viene marcado como caducado** (D12). Un índice con fecha de corte vieja
   nunca se declara completo, cubra lo que cubra.
4. Ninguna rúbrica crítica cubierta por candidatos en conflicto sin resolver.
5. **`lectura_incompleta=False`** (v3). Una lectura truncada no prueba ausencia.
6. **`lector_agotado=False` y `fallo_lector=None`** (v3). Sin lectura no hay nada que declarar.

Nunca se declara completo por ausencia de evidencia en contra.

---

## No-alcance

- NO descarga (pieza ④) ni abre documentos (pieza ⑤).
- NO juzga la *calidad* jurídica ni interpreta contenido.
- NO decide si un instrumento está vigente leyéndolo — eso es la pieza ⑤.
- **NO lee `SeleccionTematica`** ni ajusta su juicio al tema pedido (v3, N15).
- **NO investiga los `enlaces_sin_cuenta`** que el Lector no supo explicar: los pasa al reporte.

---

## Diseño

```
corroborador/
  esqueleto.py    # la tabla de rúbricas, versionada y editable sin tocar código
  jerarquia.py    # comprobación de pirámide (código puro, sin LLM)
  lectura.py      # v3 · reglas de §Lo que no es un hueco; código puro, sin LLM
  agent.py        # mapeo título -> rúbrica + cotejo con PNT y Periódico Oficial
  models.py
```

El esqueleto vive en un **archivo de datos** (YAML o JSON), no incrustado en el prompt. Va a
cambiar conforme se conozcan más universidades, y debe poder cambiar sin tocar código ni
re-probar el agente.

**`lectura.py` es nuevo y es deliberadamente determinista.** Decidir si un catálogo es apto para
cotejarse no es juicio: son tres campos de `Catalog` y una tabla de verdad. Delegarlo al agente
sería delegar la honestidad del sistema a un componente estocástico.

---

## Criterios de aceptación

1. **Caso UAM:** sobre su catálogo real (**47 enlaces**), el Corroborador detecta que **la Ley
   Orgánica sí está** y que el esqueleto se cubre casi entero. `completo=True`.
   **No debe contar como cobertura** los 8 históricos, el abrogado, los **5 anexos** ni el
   **consolidado**: la cobertura la dan los **31 instrumentos vigentes**.
   *(Corregido en v3: la v2 decía «45 enlaces» y solo excluía históricos y abrogado.)*
2. **Prueba de hueco crítico inducido:** se retira artificialmente la Ley Orgánica del
   catálogo de la UAM; el Corroborador la marca `critico` y produce un `ManualQueueItem` con
   `donde_buscar` apuntando al DOF (porque la de la UAM es federal, 1973).
3. **Caso UJAT (estatal, medido) — el criterio que prueba D11:** el catálogo trae la Ley
   Orgánica y el Estatuto General **archivados bajo "Otros documentos"**. El Corroborador debe
   declarar `completo=True` y **no** reportar huecos críticos falsos. Un Corroborador que se
   fíe de `categoria_indice` fallará aquí.
4. **Caso UACAM — el hueco crítico REAL (E10.5). El criterio más importante de esta spec.**
   Sobre el catálogo real de la UACAM, el Corroborador debe:
   - marcar `estatuto_general` como **hueco crítico**, porque el documento no existe en el
     índice;
   - declarar `completo=False`;
   - producir un `ManualQueueItem` que **nombre el Estatuto Orgánico de la UACAM** y apunte a
     dónde buscarlo (Periódico Oficial del Estado de Campeche, o el propio portal fuera del
     índice de legislación).
   **Un Corroborador que declare completa a la UACAM falla la spec entera**, por bien que haga
   todo lo demás: sería exactamente el fallo silencioso que justifica su existencia.
5. **Caso UACAM — índice caducado (D12):** el mismo catálogo viene marcado con fecha de corte
   de diciembre de 2016. **Aunque cubriera el esqueleto completo, `completo` debe ser `False`**
   y el reporte debe decir por qué. Se prueba con un catálogo sintético al que se le añaden a
   mano los instrumentos faltantes: sigue sin ser completo.
   *(v3: el campo llega del piso determinista de `corte.py`, no del agente del Lector.)*
6. **Caso UACAM — candidatos en conflicto (E10.4):** la Ley Orgánica aparece en varios enlaces
   con versiones divergentes. La rúbrica se marca cubierta, **pero con conflicto declarado en
   el reporte**. Un Corroborador que se quede con el primer enlace y calle falla.
7. **Régimen correcto:** para la UJAT, la pista de contraste de la Ley Orgánica apunta al
   **Congreso del Estado de Tabasco**; para la UACAM, al de Campeche; para la UAM y la UNAM, al
   **DOF**. Es la prueba de que el agente entendió el régimen en vez de memorizar un patrón.
8. **Prueba de sinonimia (con datos reales):** las cuatro universidades medidas nombran
   distinto lo mismo — "Reglamento Orgánico" (UAM), "Estatuto General" (UNAM y UJAT),
   "Estatuto Orgánico" (UACAM, el que falta) — y todas deben mapear a `estatuto_general`. Igual
   con el personal académico: "Reglamento de Ingreso, Promoción y Permanencia" (UAM) vs.
   "Estatuto del Personal Académico" (UNAM y UJAT).
9. **Prueba de jerarquía:** un catálogo con 20 reglamentos y sin estatuto se marca incompleto
   por la comprobación de código, sin necesidad de LLM. *(La UACAM es este caso en la vida
   real, no en un test sintético.)*
10. **Calidad de la cola manual:** revisión humana de 10 `ManualQueueItem`; ≥ 9 deben nombrar
    el documento faltante y decir dónde buscarlo. Un ítem que solo dice "falta algo" no cuenta.
11. **No sobre-reporta:** **tres de las cuatro** universidades medidas (UAM, UNAM, UJAT) tienen
    catálogo completo y ninguna debe generar huecos críticos falsos. **La cuarta, la UACAM, sí
    tiene un hueco real** y debe reportarlo — ver criterio 4.
12. **No confunde volumen con completitud:** el catálogo de la UACAM sale de **87 enlaces** de
    los que solo ~27 serían normativa propia. El Corroborador debe llegar a la misma conclusión
    trabajando sobre los 27 que sobre los 87: el hueco del Estatuto Orgánico está en ambos.
    *(v3: 87, no ~82. El «27» sigue sin medir y su oráculo está pendiente.)*

### v3 — lo que no es un hueco de la universidad

13. **Un hueco del Lector no se atribuye a la institución** (`01` v2.6). Tres sub-casos, los tres
    deterministas y verificables sin agente:
    - **Rejilla JS:** `Catalog(entries=[], lector_agotado=True)` → `completo=False`,
      `confianza="baja"`, **cero `Hueco` de rúbrica** y **cero `ManualQueueItem` que nombren
      instrumentos**. Un reporte que liste doce huecos críticos sobre un catálogo vacío falla.
    - **Salida inválida:** `fallo_lector="salida_invalida"` → mismo comportamiento. **Y no se
      marca como agotamiento**: la página era legible.
    - **Lectura truncada:** `lectura_incompleta=True` con `enlaces_sin_cuenta` de 7 elementos →
      `completo=False` **aunque el esqueleto esté cubierto**; cada `Hueco` dice en su
      `descripcion` que la lectura fue parcial; `confianza` no puede ser `"alta"`; y los 7
      `enlaces_sin_cuenta` aparecen en el reporte.
    **Control negativo, y es la mitad que importa:** el mismo catálogo con
    `lectura_incompleta=False` produce el reporte normal. La regla no debe volver tímido al
    Corroborador cuando el Lector sí leyó todo.
14. **El filtro temático no cambia el juicio** (`01` v2.7, N15). Con un `Catalog` de la UAM
    completo y una `SeleccionTematica` que solo incluye 3 entradas, el `CoverageReport` es
    **idéntico** al que se produce sin selección: mismas rúbricas cubiertas, mismos huecos, mismo
    `completo`. **Cero `ManualQueueItem` por entradas excluidas.** Se verifica llamando al
    Corroborador dos veces y comparando los dos reportes campo a campo.

---

## Preguntas abiertas (agenda de esta conversación)

1. **¿El esqueleto es único o por régimen?** Una universidad tecnológica federal y una
   autónoma estatal tienen estructuras distintas. Propuesta: un esqueleto base + variantes
   por `Regimen`.
   **Dato de la v3:** de los cuatro regímenes, el **tecnológico es el único sin una sola
   medición** (E6.2). Y es el que más se aparta: en una autónoma, la normativa de la SEP es casi
   toda ajena; en un tecnológico, no. **Antes de escribir su variante hay que medir uno.**
2. **¿Cómo se accede al 70-I de la PNT programáticamente?** Sigue sin resolverse (E6.5) y ahora
   importa más: es el respaldo del que depende toda universidad cuyo sitio no sirva. Mismo
   problema de rejilla JS de la spec `03` — **y medido otra vez el 2026-10-01: la rejilla sigue
   vacía** (E20.3).
3. **¿Se usa el repositorio de terceros de la UNAM?** Aloja legislación de otras universidades
   (E3.6). Propuesta: **pista de existencia únicamente** — si la UNAM tiene copia de un
   reglamento de la UJAT que no aparece en el índice de la UJAT, eso es señal de hueco, pero
   el documento se busca en su emisor, no se toma de ahí. **Es exactamente el mecanismo que
   podría confirmar si el Estatuto Orgánico de la UACAM existe** y simplemente no está publicado.
4. **Reformas a la Ley Orgánica.** ¿Se persiguen todos los decretos de reforma o basta el texto
   vigente consolidado? Propuesta: texto vigente consolidado; las reformas históricas son alcance
   futuro.
5. **Umbral de `completo`:** ¿cero huecos críticos y ≤ 2 importantes es el corte correcto?
   Calibrar con las **cuatro** universidades reales: **con datos, no a ojo**. El dato duro es que,
   sea cual sea el umbral, **la UACAM debe salir incompleta y las otras tres completas**.
6. **Prompt exacto del agente de mapeo.** Redactarlo y probarlo aquí.
7. **¿Qué hace el Corroborador con un índice caducado, además de no declararlo completo?**
   (Pregunta 8 de `00`, versión local.) ¿Busca un índice alternativo? ¿Manda el catálogo entero
   a cola manual? ¿Cotejar contra el 70-I basta para saber qué se emitió desde 2016? Afecta
   también a `03`. **E6.10** —la rama vigente de la UACAM, `/view/paginas/49`— es la medición más
   barata que lo informa.
8. **¿Un documento en visor de terceros cuenta como "presente"?** La UACAM sirve cuatro
   instrumentos desde Google Drive (C14), uno de ellos normativa propia. Están en el catálogo,
   pero el Descargador los manda a cola manual. Propuesta: **sí para cobertura**, con nota de que
   su obtención está pendiente — cobertura y obtención son cosas distintas.
9. **¿Cómo se resuelve un conflicto entre candidatos?** Cuando un instrumento aparece en varios
   enlaces con versiones distintas (E10.4), alguien tiene que elegir. El Corroborador no puede
   —no abre documentos—, así que probablemente es trabajo del Verificador (`06`). **Confirmar
   que la frontera queda ahí y no en el aire.**
10. **El abogado del Auditor: ¿un agente especializado en el régimen jurídico mexicano?** (nueva
    en v3.) La idea es que esta pieza no solo mapee títulos a rúbricas, sino que **entienda el
    régimen**: qué obliga a quién, dónde se promulga cada ley fundacional, qué cambia entre una
    autónoma y un tecnológico. Es, de hecho, lo que el criterio 7 ya le exige.
    **Lo que la hace construible, y hay que decirlo con precisión:** no es «saber derecho», es que
    **sus respuestas tienen hoja de respuestas**, y ya está escrita en `08`:

    | Pregunta | Respuesta correcta | Fuente |
    |---|---|---|
    | ¿Dónde se promulgó la ley fundacional de la UJAT? | Congreso de Tabasco | E4.4 |
    | ¿Y la de la UACAM? | Congreso de Campeche | E10.4 |
    | ¿Y las de UAM y UNAM? | DOF | D2 |
    | ¿Está completo el catálogo de la UACAM? | **No**: falta el Estatuto Orgánico | E10.5 |
    | ¿Y los de UAM, UNAM, UJAT? | Sí | criterio 11 |
    | «Reglamento Orgánico» / «Estatuto General» / «Estatuto Orgánico» | los tres → `estatuto_general` | criterio 8 |

    **Lo que se descarta, y por qué:** una cadena de agentes —un «núcleo» que entiende el Estado
    mexicano, un intermedio de la SEP, y luego esta pieza—. Dos razones concretas. **(a) Un hecho
    verificable una vez se guarda; no se vuelve a preguntar:** si la respuesta es la misma para la
    UAM y para las 40 que faltan, es un archivo de datos, no un agente (`00` §2). **(b) En cadena,
    el error pierde dueño:** si una rúbrica se mapea mal, no se sabe a cuál de los tres corregir.
    **Y «SEP» es el marco equivocado para las autónomas**, que se rigen por su ley orgánica y por
    sus propios órganos (art. 3º, fr. VII).
    **Lo que queda por decidir aquí:** si este saber vive como **archivo de datos** que alimenta el
    prompt del agente de mapeo, o como **una llamada propia** con su pregunta acotada. Las hojas
    de arriba sirven igual para las dos; lo que cambia es el coste por institución.
11. **¿Cómo se unifica el `doc_slug` entre un catálogo escrito a mano y un índice institucional?**
    (nueva en v3; deuda **E6.25**.) Medido en E21.15: cinco documentos de la UNAM cosechados desde
    un catálogo escrito a mano tienen grupos `unam:ley-organica`, mientras que el Lector producirá
    `unam:n2`, `unam:n29`… desde el prefijo numérico del OAG (E3.4). **Dos grupos distintos → el
    alias por hash no actúa → los mismos bytes se bajan otra vez.**
    Para esta pieza el problema no es el disco sino el juicio: **si el mismo instrumento aparece
    con dos identidades, ¿la rúbrica está cubierta una vez o dos?** Afecta al Lector y al
    Corroborador a la vez, y por eso está en las dos agendas (`03`, pregunta 14).
12. **¿Cuál es el denominador de la UNAM?** (nueva en v3.) E21.16 lo dice sin rodeos: las corridas
    de octubre salieron de un catálogo escrito a mano sobre la economía de una facultad, así que
    «22 de 26» **no dice nada** sobre qué fracción de la normativa de la UNAM está en el corpus.
    El índice del OAG —**84 enlaces**, E20.5— es el que daría ese denominador, y **no se ha
    cosechado**. Es **E6.8**, y sigue abierta.

---

## Registro de consideraciones diferidas

### CD-04-1 · El Corroborador recibe la contabilidad, pero no puede recalcularla

**Anotado en:** v3 (2026-10-04). **Estado:** aceptado a sabiendas.

`Catalog.enlaces_vistos` es un `int` y `enlaces_sin_cuenta` una lista ya calculada por el Lector
(`cuenta.py`). El Corroborador **confía** en esa resta: no tiene la tabla de enlaces original para
rehacerla. Es la contraparte de CD-03-1.

**El costo:** si `cuenta.py` tuviera un error, el Corroborador lo propagaría sin poder detectarlo.
**Lo que lo mitiga:** la resta es determinista y está cubierta por tests (M46), y el caso
«40 de 47» tiene test propio.

**Gatillo:** la primera vez que un hueco reportado resulte ser un error de contabilidad y no de la
universidad. **Solución:** persistir la tabla de enlaces reducida y pasarla al Corroborador, que es
la misma solución que CD-03-1.
