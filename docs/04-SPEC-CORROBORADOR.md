# 04 · Spec — Corroborador (pieza ③)
 
> Conversación: "Fase Corroborador". Leer antes `00`, `01` (contratos N3, N4, N8) y **`08` v7**.
> Estado: **v2** · agente LLM. Depende de un `Catalog` funcional (spec 03).
> **La medición de la UACAM cambió esta spec más que ninguna otra.** Aportó el primer hueco
> crítico real del proyecto —una universidad a la que le falta su Estatuto Orgánico— y con él
> la primera oportunidad de validar que esta pieza sirve. También destapó dos problemas que la
> v1 no contemplaba: un índice puede estar caducado, y "presente en el catálogo" no es binario.
 
---
 
## Objetivo
 
Responder una sola pregunta con evidencia: **¿este catálogo está completo?**
 
No "¿existe este documento?" (eso lo sabe el Lector), sino "¿qué debería haber aquí que no
está?". Produce un `CoverageReport` (N4) y alimenta la cola manual (N8).
 
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
 
**Medido (E10.5 de `08`).** En el índice de legislación de la UACAM está la Ley Orgánica —cinco
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
 
### "Presente en el catálogo" no es binario
 
**Medido (E10.4 de `08`).** La UACAM enlaza su Ley Orgánica desde cinco lugares distintos de la
misma página, y **no todos apuntan a la misma versión**.
 
Para el Corroborador, la rúbrica `ley_organica` está cubierta — pero decir `completo=True` sin
más sería engañoso: hay una discrepancia sin resolver. Un instrumento presente cinco veces con
versiones divergentes es un hallazgo, no una tranquilidad.
 
**Requisito:** el `CoverageReport` distingue entre *cubierto sin ambigüedad* y *cubierto con
candidatos en conflicto*. Lo segundo va al reporte aunque no sea un hueco.
 
### Esqueleto esperado (v1 — refinar en esta conversación)
 
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
 
**Pero cuidado con el denominador.** Medido en la UACAM (E10 de `08`): de ~82 enlaces a
documento, **solo 27 son normativa propia**. El resto son contratos y convenios por ejercicio
(unos 30), y documentos de otras instituciones. **Dos de cada tres enlaces del índice no son
instrumentos normativos.**
 
Si el Corroborador razona sobre el conteo bruto del catálogo —"esta universidad tiene 82
documentos, seguro está completa"— concluye mal. El descarte lo hace el Lector, pero el
Corroborador no debe apoyarse en volumen como señal de completitud.
 
### Cuándo se declara completo
 
`completo=True` exige **las cuatro** condiciones:
 
1. Cero huecos críticos.
2. ≤ 2 huecos importantes, cada uno con pista concreta de dónde buscarlo.
3. **El catálogo no viene marcado como caducado** (D12). Un índice con fecha de corte vieja
   nunca se declara completo, cubra lo que cubra.
4. Ninguna rúbrica crítica cubierta por candidatos en conflicto sin resolver.
Nunca se declara completo por ausencia de evidencia en contra.
 
---
 
## No-alcance
 
- NO descarga (pieza ④) ni abre documentos (pieza ⑤).
- NO juzga la *calidad* jurídica ni interpreta contenido.
- NO decide si un instrumento está vigente leyéndolo — eso es la pieza ⑤.
---
 
## Diseño
 
```
corroborador/
  esqueleto.py    # la tabla de rúbricas, versionada y editable sin tocar código
  jerarquia.py    # comprobación de pirámide (código puro, sin LLM)
  agent.py        # mapeo título -> rúbrica + cotejo con PNT y Periódico Oficial
  models.py
```
 
El esqueleto vive en un **archivo de datos** (YAML o JSON), no incrustado en el prompt. Va a
cambiar conforme se conozcan más universidades, y debe poder cambiar sin tocar código ni
re-probar el agente.
 
---
 
## Criterios de aceptación
 
1. **Caso UAM:** sobre su catálogo real (**45 enlaces, 31 instrumentos vigentes**), el
   Corroborador detecta que **la Ley Orgánica sí está** y que el esqueleto se cubre casi
   entero. `completo=True`. No debe contar los 8 históricos ni el abrogado como cobertura.
2. **Prueba de hueco crítico inducido:** se retira artificialmente la Ley Orgánica del
   catálogo de la UAM; el Corroborador la marca `critico` y produce un `ManualQueueItem` con
   `donde_buscar` apuntando al DOF (porque la de la UAM es federal, 1973).
3. **Caso UJAT (estatal, medido) — el criterio que prueba D11:** el catálogo trae la Ley
   Orgánica y el Estatuto General **archivados bajo "Otros documentos"**. El Corroborador debe
   declarar `completo=True` y **no** reportar huecos críticos falsos. Un Corroborador que se
   fíe de `categoria_indice` fallará aquí.
4. **Caso UACAM — el hueco crítico REAL (E10.5 de `08`). El criterio más importante de esta
   spec.** Sobre el catálogo real de la UACAM, el Corroborador debe:
   - marcar `estatuto_general` como **hueco crítico**, porque el documento no existe en el
     índice;
   - declarar `completo=False`;
   - producir un `ManualQueueItem` que **nombre el Estatuto Orgánico de la UACAM** y apunte a
     dónde buscarlo (Periódico Oficial del Estado de Campeche, o el propio portal fuera del
     índice de legislación).
   Es la primera oportunidad de demostrar que esta pieza sirve. **Un Corroborador que declare
   completa a la UACAM falla la spec entera**, por bien que haga todo lo demás: sería
   exactamente el fallo silencioso que justifica su existencia.
5. **Caso UACAM — índice caducado (D12):** el mismo catálogo viene marcado con fecha de corte
   de diciembre de 2016. **Aunque cubriera el esqueleto completo, `completo` debe ser `False`**
   y el reporte debe decir por qué. Se prueba con un catálogo sintético al que se le añaden a
   mano los instrumentos faltantes: sigue sin ser completo.
6. **Caso UACAM — candidatos en conflicto (E10.4):** la Ley Orgánica aparece en cinco enlaces
   con versiones divergentes. La rúbrica se marca cubierta, **pero con conflicto declarado en
   el reporte**. Un Corroborador que se quede con el primer enlace y calle falla.
7. **Régimen correcto:** para la UJAT, la pista de contraste de la Ley Orgánica apunta al
   **Congreso del Estado de Tabasco**; para la UACAM, al de Campeche; para la UAM, al DOF. Es
   la prueba de que el agente entendió el régimen en vez de memorizar un patrón.
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
    tiene un hueco real** y debe reportarlo — ver criterio 4. *La v1 de esta spec afirmaba que
    las tres universidades medidas estaban completas y pedía cero huecos; la medición de la
    UACAM refutó esa premisa, y el criterio se corrigió en vez de conservarlo.*
12. **No confunde volumen con completitud:** el catálogo de la UACAM sale de ~82 enlaces de los
    que solo 27 son normativa propia. El Corroborador debe llegar a la misma conclusión
    trabajando sobre los 27 que sobre los 82: el hueco del Estatuto Orgánico está en ambos.
---
 
## Preguntas abiertas (agenda de esta conversación)
 
1. **¿El esqueleto es único o por régimen?** Una universidad tecnológica federal y una
   autónoma estatal tienen estructuras distintas. Propuesta: un esqueleto base + variantes
   por `Regimen`.
2. **¿Cómo se accede al 70-I de la PNT programáticamente?** Sigue sin resolverse (E6.5 de
   `08`) y ahora importa más: es el respaldo del que depende toda universidad cuyo sitio no
   sirva. Mismo problema de rejilla JS de la spec `03`.
3. **¿Se usa el repositorio de terceros de la UNAM?** Aloja legislación de otras universidades
   (E3.6 de `08`). Propuesta: **pista de existencia únicamente** — si la UNAM tiene copia de un
   reglamento de la UJAT que no aparece en el índice de la UJAT, eso es señal de hueco, pero
   el documento se busca en su emisor, no se toma de ahí. **Ahora es más relevante:** es
   exactamente el mecanismo que podría confirmar si el Estatuto Orgánico de la UACAM existe y
   simplemente no está publicado en su índice.
4. **Reformas a la Ley Orgánica.** No basta con la Ley Orgánica original de 1973 o 1986: hay
   decretos de reforma posteriores. ¿Se persiguen todos o basta el texto vigente consolidado?
   Propuesta: texto vigente consolidado; las reformas históricas son alcance futuro.
5. **Umbral de `completo`:** ¿cero huecos críticos y ≤ 2 importantes es el corte correcto?
   Calibrar con las **cuatro** universidades reales, como se calibró el umbral 0.78 allá:
   **con datos, no a ojo**. Hay un dato duro para calibrar: sea cual sea el umbral, la UACAM
   debe salir incompleta y las otras tres completas.
6. **Prompt exacto del agente de mapeo.** Redactarlo y probarlo aquí.
7. **¿Qué hace el Corroborador con un índice caducado, además de no declararlo completo?**
   (Pregunta 8 de `00`, versión local.) ¿Busca un índice alternativo? ¿Manda el catálogo entero
   a cola manual? ¿Cotejar contra el 70-I es suficiente para saber qué se emitió desde 2016?
   Afecta también a la spec `03`.
8. **¿Un documento en visor de terceros cuenta como "presente"?** La UACAM sirve cuatro
   instrumentos desde Google Drive (C14 de `08`). Están en el catálogo, pero el Descargador los
   manda a cola manual. **¿La rúbrica se marca cubierta?** Propuesta: sí para cobertura, con
   nota de que su obtención está pendiente — son cosas distintas y conviene no mezclarlas.
9. **¿Cómo se resuelve un conflicto entre candidatos?** Cuando un instrumento aparece en cinco
   enlaces con versiones distintas (E10.4), alguien tiene que elegir. El Corroborador no puede
   —no abre documentos—, así que probablemente es trabajo del Verificador (`06`). **Confirmar
   que la frontera queda ahí y no en el aire.**
---
 
## Registro de consideraciones diferidas
 
*(Se llena durante la implementación.)*
