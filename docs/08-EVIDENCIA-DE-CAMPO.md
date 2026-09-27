# 08 · Evidencia de campo

> Hallazgos **medidos**, no supuestos, obtenidos antes de escribir una línea de código.
> Estado: vivo · **v15** · se amplía con cada universidad nueva que se explore.
> Mediciones: UAM, UNAM-70I, UNAM-OAG, UJAT, **UACAM**.
> **Medido en vivo el 2026-09-06: la UAM (E1) y la UACAM (E10).** Los conteos de UNAM-OAG (E3)
> y UJAT (E4) son de la captura original y **no se han vuelto a comprobar**; trátalos como
> aproximados hasta que se recapturen (E6.8).
> **Descargas reales ejecutadas:** 45/45 documentos de la UAM el **2026-09-06** (E11) y
> **105/105 de la UJAT el 2026-09-08** (E12). **150 de 150.** Tras la migración a `Encargo`,
> **156 de 156 (E14)**, medido el 2026-09-18. **Primera corrida académica: 3 de 7 (E15)**, el
> 2026-09-25. **Segunda: 8 de 30 (E19)**, el 2026-09-27. Es la evidencia que no viene de
> mirar una página, sino de ejercitar código contra servidores reales. Con ella la spec `05`
> queda cerrada.
> **v8 (2026-09-10):** al auditar el disco antes de la migración apareció que la UAM se descargó
> **dos veces** —el 06 y el 08— y que sus 45 documentos están **duplicados en disco** con distinto
> nombre (**E13**). Se corrige además la fecha de la corrida de la UJAT, que la v7 daba como
> 2026-09-06 en todo el documento.
>
> Este documento existe porque el proyecto hermano aprendió que las decisiones tomadas contra
> datos reales sobreviven y las tomadas contra suposiciones se pagan después. Su umbral de
> relevancia estuvo mal calibrado durante toda una fase por asumir una escala en vez de medirla.

---

## Resumen: 4 de 4 sitios institucionales funcionan — y uno de ellos miente sin querer

| Institución | Régimen | Fuente | Resultado | Instrumentos | Vigencia declarada |
|---|---|---|---|---|---|
| UAM | Federal | Sitio institucional | ✅ HTML plano | **31 vigentes + 5 anexos + 8 históricos + 1 abrogado + 1 consolidado** (contado 2026-09-06) | **Sí, explícita** |
| UNAM | Federal | 70-I (PNT/portal propio) | ❌ Rejilla JS, sin filas | 0 | — |
| UNAM | Federal | Sitio OAG | ✅ HTML plano (Drupal) | ~60 | No (fecha en nombre de archivo) |
| UJAT | Estatal (Tabasco) | Sitio institucional | ✅ HTML plano (tablas) | ~60 | **No, nada** |
| UACAM | Estatal (Campeche) | Micrositio de transparencia | ⚠️ HTML plano, **catálogo caducado en 2016** | 27 propios entre ~82 enlaces | No — pero declara **fecha de corte** |

**Lo único que falló técnicamente en todo el proyecto fue un formato 70-I.** Los cuatro sitios
institucionales entregaron su catálogo sin ejecutar JavaScript.

**Pero "funciona" y "sirve" no son lo mismo.** La UACAM entrega un índice impecable —
estructurado, en dominio oficial, con URL directa a cada PDF— **congelado hace nueve años**, y
lo confiesa en una sola línea al pie. Es el hallazgo más importante de las cuatro mediciones
(E10.1) y la razón definitiva de que `estado="desconocido"` sea el valor por defecto.

---

## E1 · UAM — caso fácil, y mejor que el 70-I

**Fuente:** `https://www.uam.mx/legislacion/index.html`
**Resultado: éxito completo.** Consolidación vigente al 2026-09-06: **julio 24 de 2026**.

**Conteo exacto (no aproximado):**

| Qué | Cuántos | Dónde |
|---|---|---|
| Instrumentos vigentes | **31** | `/legislacion-uam-julio-24-2026/` |
| Anexos del Protocolo de Violencia de Género | **5** (2 PDF + **3 `.docx`**) | misma carpeta |
| Versiones históricas | **8** | `/legis-uam-arch/` |
| Reglamentos abrogados | **1** | `/legis-uam-abr/` |
| PDF consolidado con todo | **1** | carpeta de la consolidación |

**Corrección respecto de la v2 de este documento:** decía "~9 históricos"; son **8**. Y decía
"~30 vigentes"; son **31**, más 5 anexos que la v2 contaba aparte de forma inconsistente.

**Agrupación por materia** que hace el propio sitio: Estructura Orgánica · Órganos Colegiados ·
Defensoría · Transparencia · Planeación/Presupuesto/Contratación · Personal Académico ·
Programas Universitarios · Alumnado y Estudios · Políticas · Junta Directiva · Código y
Protocolo · Reglamentos abrogados.

### E1.1 · El estado temporal viene explícito en el texto del enlace

Los ocho históricos declaran su fecha de cese en el propio texto del enlace:

- Defensoría, *vigente hasta el 20 de julio de 2026*
- Transparencia, *vigente hasta el 29 de julio de 2025*
- Adjudicaciones, *vigente hasta el 26 de agosto de 2024*
- Personal Académico, *vigente hasta el 25 de febrero de 2026* **y** *hasta el 5 de enero de 2026*
- Estudios Superiores, *vigente hasta el 16 de marzo de 2026* **y** *hasta el 4 de noviembre de 2024*
- Alumnado, *vigente hasta el 24 de marzo de 2025*
- Y un abrogado: Programas de Investigación, *abrogado a partir del 25 de noviembre de 2025*

**Dos instrumentos tienen DOS versiones históricas cada uno.** Es decir: el mismo `doc_slug`
con tres registros (uno vigente, dos históricos) ordenables por fecha. Confirma que
`doc_id` deba llevar la versión dentro (N7) y que reformar produzca un registro nuevo, no una
sobrescritura.

**Resultó ser la excepción, no la regla** — ver E4. Por eso `estado` es campo de primera
clase en N2, y por eso su valor por defecto es `desconocido`, no `vigente`.

### E1.2 · Las URLs codifican la fecha de consolidación y morirán en bloque

```
/legislacion/legislacion-uam-julio-24-2026/legislacion-uam-julio-24-2026-lo.pdf
                    ↑ fecha de consolidación en la ruta
```

Conviven rutas de al menos tres consolidaciones (julio 2026, enero 2026, y un archivo
histórico en `/legis-uam-arch/`). Cuando la UAM consolide de nuevo, *todas* las URLs vigentes
cambian a la vez. Por eso `doc_slug` **nunca** se deriva de la URL, y por eso el mecanismo del
sistema es el **diff del índice**, no la persistencia de enlaces.

### E1.3 · Los sufijos de archivo SÍ son estables — pero solo el sufijo

`-lo`, `-ro`, `-rioca`, `-reddu`, `-retra`, `-rpl`, `-rpr`, `-repla`, `-ripppa`, `-tippa`,
`-ripac`, `-rbpa`, `-rpu`, `-res`, `-rd`, `-ra`, `-rss`, `-rreae`, `-lgnma`, `-pg`, `-ptevrg`,
`-ptieand`, `-ptcp`, `-pod`, `-poep`, `-poai`, `-pope`, `-pov`, `-rjd`, `-ceuam`, `-pavrg`.
Treinta y un sufijos, uno por instrumento. **Es el `doc_slug` que N2 necesita** para esta
institución.

**Pero el prefijo es un caos**, y esto es nuevo respecto de la v2. En el archivo histórico
conviven cinco patrones distintos para el mismo tipo de archivo:

```
leg-univ-uam-reddu-VIGENTE-HASTA-20.07.2026.pdf
legis-univ-uam-ripppa-VIGENTE-HASTA-25.02.2026.pdf
legis-univ-uam-julio-2025-ripppa-VIGENTE-HASTA-05-ENERO-2026.pdf
legis-univ-uam-noviembre-2024-ra-VIGENTE-HASTA-24.03.2025.pdf
leg-univ-uam-res-VIGENTE-HASTA-04.11.2024.pdf
```

`leg-` vs `legis-`, con y sin fecha de consolidación intercalada, separadores `.` y `-` para
la misma fecha. **Consecuencia:** el `doc_slug` se extrae por el sufijo, nunca por patrón de
ruta completa, y la ruta del archivo histórico **no es derivable** — hay que leerla del índice.

### E1.4 · Las consolidaciones viejas siguen vivas en el servidor, pero desaparecen del índice

Una búsqueda externa devolvió un PDF de `/legislacion-uam-marzo-16-2026/`, carpeta que **ya no
aparece en el índice actual**. El archivo sigue sirviéndose; simplemente dejó de estar listado.

**Consecuencia dura:** un enlace que responde 200 **no prueba que el documento esté vigente**.
La única fuente de verdad sobre qué es actual es el índice, no el servidor de archivos. Refuerza
que el mecanismo del sistema sea el diff del índice (D6, y el comando `vigilar` de la spec `07`).

### E1.5 · Un enlace SIN texto, apuntando a un documento huérfano

Al final de la sección de abrogados, el HTML contiene un ancla vacía:

```html
<a href=".../legislacion-uam-enero-2026/legis-univ-uam-enero-2026-rjd.pdf"></a>
```

Sin texto visible. Es el Reglamento de la Junta Directiva de enero de 2026 — una **versión
histórica real que no está listada en ninguna otra parte de la página**.

**Es el caso adversarial más interesante de todo el corpus medido**, porque rompe el supuesto
central del Lector de Índice: que cada instrumento tiene un título del que derivar `titulo` y
`tipo_norma`. Aquí solo hay una URL.

**Propuesta (decidir en la spec `03`):** un enlace a documento sin texto de ancla no se
descarta en silencio. Se emite como `CatalogEntry` con `titulo` derivado del sufijo (`-rjd` →
Reglamento de la Junta Directiva), `estado="desconocido"` y `confianza` baja, y el
Verificador Documental resuelve su identidad leyendo el PDF. **La alternativa —ignorarlo— borra
un documento real del corpus sin dejar rastro**, que es exactamente el fallo silencioso que
todo el diseño intenta evitar.

### E1.6 · Cinco anexos, tres en `.docx`

Los anexos del Protocolo para Atender la Violencia por Razones de Género: Anexo 1 (PDF),
Anexo 2, 3A y 3B (**`.docx`**) y Anexo 3C (PDF). Son formularios, no normas.

No es hipotético: son archivos reales del primer caso de prueba. Obliga al Descargador a
decidir qué hace con formatos distintos de PDF (pregunta abierta 1 de la spec `05`) y al
Lector a decidir si un formulario en blanco merece entrar al corpus citable. **Propuesta: se
descargan, con `tipo_norma="anexo"`, y la fase de chunking decide si los indexa.**

---

## E2 · UNAM (70-I) — el único fallo

**Fuente:** `https://transparencia.unam.mx/obligaciones/consulta/marco-normativo`
**Resultado: fallo.**

Llega la cáscara: encabezados, migas de pan, el título "Normatividad aplicable", un aviso de
que *"el proceso de descarga podría tardar varios minutos"* y un panel de ayuda completo que
explica cómo ordenar columnas. **Cero filas de datos.**

### E2.1 · La firma diagnóstica de una rejilla vacía

Instrucciones de uso de una tabla —"dar doble clic sobre el registro que se desea consultar",
"dar clic sobre el título de la columna por la que desea ordenar"— **sin que exista tabla
alguna en el HTML**. Esa combinación es la señal que el Lector de Índice debe reconocer para
devolver `lector_agotado=True` en vez de fabricar entradas a partir de los encabezados.

---

## E3 · UNAM (Oficina de la Abogacía General) — el caso difícil no existe

**Fuente:** `https://www.abogadogeneral.unam.mx/legislacion` (Drupal 8)
**Resultado: éxito completo.** Anula la conclusión provisional de E2.

- **~60 instrumentos** con PDF directo.
- Jerarquía explícita en el propio índice: **Marco General → Estatutos → Reglamentos →
  Códigos → Lineamientos → Normas**. Es casi exactamente la pirámide normativa del
  esqueleto esperado de la spec `04`.
- Secciones adicionales: Normatividad de la propia Oficina, Normatividad de Coordinación de
  Oficinas Jurídicas.

### E3.1 · Sección "Legislación Federal" propia

El índice incluye la **Constitución, artículo 3º fracción VII**, alojada además como PDF en
el dominio de la UNAM. La capa federal no es una invención del diseño: la institución misma
la considera parte de su marco normativo.

### E3.2 · Contratos colectivos publicados

`CCT AAPAUNAM` y `CCT STUNAM` aparecen en el menú de Normateca, con PDF directo. Es evidencia
a favor de incluir `contrato_colectivo` en el vocabulario de N1 (pregunta abierta 5 de `00`).

### E3.3 · Sin vigencia declarada; la fecha va en el nombre del archivo

`..._rem38_021220.pdf`, `..._070425.pdf`, `..._210425.pdf`, `..._271125_081225_w.pdf`.
Formato aparente: `DDMMYY`, a veces con marca de remisión (`rem38`) y a veces con dos fechas.
**Nunca en el texto visible del índice.**

### E3.4 · Prefijo numérico estable como `doc_slug`

`2-LeyOrganicaUNAM`, `5-ReglamentoHConsejoUniversitario`, `29-ReglamentoGeneralExamenes`,
`60-CodigoeticaUNAM`. El número precede al nombre y sobrevive a las reformas (el mismo `29`
aparece en versiones de fechas distintas). Segundo caso, segundo mecanismo estable, distinto
del de la UAM: **el `doc_slug` no se deriva igual en todas partes.**

### E3.5 · Sub-portales en puertos no estándar

Los enlaces "ver" apuntan a `abogadogeneral.unam.mx:6060` y `:8443`. Son, presumiblemente, las
rejillas JS de la normateca. **El PDF nunca pasa por ahí**: cuelga del sitio principal en
`/sites/default/files/`. Enseñanza: cuando un índice ofrece "vista" y "PDF", el PDF suele ser
la ruta estática y la vista la dinámica. Preferir siempre el PDF.

### E3.6 · La UNAM aloja legislación de OTRAS universidades

Existe `abogadogeneral.unam.mx/repoTab` y rutas del tipo
`/sites/default/files/archivos/Repositorio/Universidad Juárez Autónoma de Tabasco/…`.

**Atajo tentador y trampa a la vez.** Es un dominio oficial, pero **no el de la institución
emisora**, y no hay garantía de que la copia esté actualizada. Decisión propuesta: **no usarlo
como fuente primaria**; a lo sumo como pista para el Corroborador de que un instrumento
existe. Anotado como pregunta abierta en la spec `04`.

---

## E4 · UJAT — el caso estatal: funciona, pero desordenado

**Fuente:** `https://www.ujat.mx/abogado/15763`
**Resultado: éxito, con tres problemas nuevos.**

**~60 documentos** en tablas HTML, agrupados en: REGLAMENTOS, CÓDIGO, LINEAMIENTOS, ACUERDOS,
OTROS DOCUMENTOS. Todos con PDF directo.

### E4.1 · La taxonomía del sitio está rota

Esto invalida una suposición del diseño original:

- **"Estatuto del Personal Académico"** aparece bajo **REGLAMENTOS**.
- **La Ley Orgánica y el Estatuto General** aparecen bajo **"OTROS DOCUMENTOS"**, junto al
  Modelo Educativo, un tabulador de sueldos y un pronunciamiento institucional.
- Los contratos colectivos y el Manual General de Organización, también en "OTROS".

**Consecuencia dura:** `categoria_indice` es **pista, no dato**. El sistema no puede confiar
en la clasificación del sitio para nada. Esto sube el peso del Corroborador (spec `04`): el
esqueleto esperado es más confiable que la taxonomía publicada.

### E4.2 · Cero información de vigencia

Ni en el índice, ni en el texto de los enlaces, ni de forma consistente en los nombres de
archivo. Algunos traen fecha (`...11072024.pdf`, `...28112023.pdf`, `REFORMADO-25032026.pdf`),
muchos no.

**Consecuencia mayor:** cruzando con E3.3, **la UAM es el único caso de tres que declara
vigencia**. El valor por defecto de `estado` debe ser `desconocido`, y la fecha real hay que
extraerla del PDF. **Esto convierte al Verificador Documental (pieza ⑤) en pieza esencial, no
opcional: es el único componente capaz de fechar el corpus.**

### E4.3 · URLs sucias

Ejemplos reales del índice:

```
/abogado_gral/legislacion_univ2012/REGLAMENTO DE LA HONORABLE JUNTA DE GOBIERNO ….pdf
   ↑ espacios sin codificar
/2015/abogado general/nuevos/A_DISTANCIA.pdf
   ↑ espacio en el nombre de carpeta
http://archivos.ujat.mx/2021/…      https://archivos.ujat.mx/2026/…
   ↑ http y https mezclados en la misma página
<https://…-20032024.pdf >
   ↑ espacio final dentro del propio enlace
```

Conviven rutas de 2012, 2015, 2017, 2019, 2020, 2021, 2022, 2024, 2025 y 2026. Mayúsculas
inconsistentes en nombres y en carpetas (`abogado-gral`, `abogado-general`, `abogado_gral`,
`Oficina-abogado`).

**Requisito nuevo para el Descargador:** normalizar la URL antes de pedirla (codificar
espacios, recortar blancos, resolver relativas). No estaba en la spec `05` original.

### E4.4 · La Ley Orgánica SÍ está en el sitio — pero en una versión sospechosa

El sitio la publica desde `/abogado_gral/legislacion_univ2012/`, es decir, la carpeta de 2012.
El Congreso del Estado de Tabasco publica la suya por separado.

**Consecuencia:** decisión **D2 se suaviza**. No es cierto que la Ley Orgánica "casi nunca
esté en el sitio universitario"; a veces está, pero desactualizada. La regla correcta es
**buscarla en ambos lados y comparar versiones**, que es exactamente el trabajo del
Verificador Documental.

### E4.5 · El propio sitio señala las capas superiores

El menú incluye enlaces salientes a **"Leyes Federales"** (Cámara de Diputados) y **"Leyes
Estatales"** (Congreso de Tabasco). La institución misma marca dónde vive el resto de su
marco jurídico — señal aprovechable por el Localizador.

---

## E5 · Conclusiones que cambian el diseño

| # | Hallazgo | Qué cambia |
|---|---|---|
| **C1** | **4 de 4** sitios institucionales sirven HTML plano | **D1 confirmada.** El navegador headless baja de prioridad drásticamente (pregunta abierta 1 de `00`). Sigue siendo la conclusión más débil: ver E8.2 |
| **C2** | Solo 1 de 4 declara vigencia | `estado` por defecto = `desconocido`. **La pieza ⑤ se vuelve esencial**, no la última rueda |
| **C3** | La taxonomía del sitio puede estar rota (UJAT) | `categoria_indice` es pista, no dato. **Sube el peso del Corroborador** |
| **C4** | Cada sitio tiene su propio mecanismo de identidad estable (sufijo UAM, prefijo numérico UNAM, nada en UJAT) | `doc_slug` necesita estrategia por sitio + fallback por título normalizado |
| **C5** | URLs sucias con espacios y esquemas mezclados | **Requisito nuevo de normalización** en la spec `05` |
| **C6** | La Ley Orgánica a veces sí está, pero vieja | **D2 suavizada**: buscar en ambos lados y comparar |
| **C7** | Dos de cuatro publican contratos colectivos (UNAM y UJAT; la UACAM no) | Incluir `contrato_colectivo` en el vocabulario. Pregunta abierta 5 de `00` **resuelta a favor** |
| **C8** | La UNAM aloja legislación de terceros | No usar como fuente primaria; sí como pista de existencia |
| **C9** | Enlaces a documento **sin texto de ancla**, en **2 de 4** instituciones (E1.5, E10.3) | El Lector no puede asumir que todo instrumento trae título. Regla firme: emitir con título derivado del sufijo y dejar que el Verificador resuelva |
| **C10** | Las consolidaciones retiradas siguen respondiendo 200 (E1.4) | **Un enlace vivo no prueba vigencia.** La verdad está en el índice, no en el servidor |
| **C11** | El prefijo de los archivos históricos es inconsistente (E1.3) | La ruta del histórico no es derivable; se lee del índice o no se tiene |
| **C12** | Un mismo instrumento puede tener 2 versiones históricas (E1.1) | Confirma `doc_id` con versión dentro (N7): reformar crea registro, no sobrescribe |
| **C13** | **Un índice completo y bien servido puede estar caducado y declararlo en una línea al pie** (E10.1) | **La conclusión más consecuente de todas.** Ninguna defensa técnica lo detecta. Requisito nuevo del Lector: buscar marcas de corte temporal y propagarlas a todo el catálogo. Justificación definitiva de D6 y de la prioridad de la pieza ⑤ |
| **C14** | Existen documentos servidos por **visor de terceros** (Google Drive), 4 casos medidos (E10.2) | Confirma en campo el valor `visor_de_terceros` de **`DownloadResult.motivo_fallo`** (N5, no de `OrigenFuente`). El caso **ya está resuelto**: `01` v1.2 fija que el reconocimiento de visores corre **antes** del guardián de formato, precisamente para que un `/view` que devuelve HTML no se registre como `no_es_pdf`. Implementado y probado en el Descargador (E11.4) |
| **C15** | Un catálogo puede tener 11 reglamentos y **faltarle el estatuto que los habilita** (E10.5) | Primer hueco crítico real. Lo caza la comprobación de jerarquía del Corroborador, que es código puro |
| **C16** | Dos de cada tres enlaces de un índice pueden no ser normativa (E10) | El Lector necesita descartar formularios, circulares y contratos, no solo menús de navegación |
| **C17** | La UAM responde **403 a `robots.txt`** y 200 a sus PDF (E11.1) | **`robots.txt` debe ser fail-open.** Con fail-closed, la cosecha de la UAM da cero documentos sin que exista prohibición real. Persiste con y sin User-Agent, así que no es el patrón de D8 |
| **C18** | El índice de la UAM se sirve en **`iso-8859-1`** (E11.3) | El Lector debe decodificar con la codificación declarada. Asumir UTF-8 corrompe todos los títulos acentuados **en silencio**, y la basura viajaría hasta `doc_slug` y hasta el nombre en disco |
| **C19** | ~~Corpus ≈ 12.6 MB por universidad; ~40 ≈ 500 MB~~ **Corregida (E12.6):** la UAM son 12.6 MB / 45 docs; la **UJAT, 285 MB / 105 docs**. Veintitrés veces más pesada | La extrapolación de 500 MB era falsa: con la varianza medida, ~40 universidades andan por los **varios GB**. Sigue cabiendo en disco local, pero "no hace falta pensar en compresión" ya no se sostiene sin más. La causa está en C21 |
| **C21** | **24 de 105 documentos de la UJAT son escaneos sin texto extraíble** (23 % de los documentos, **63 % del peso**). La UAM: **0 de 42** (E12.5) | **La fase de extracción de texto necesita OCR** para el corpus estatal. No es una anécdota: son 179 MB e incluyen el contrato colectivo y varios acuerdos rectorales. **Alcance por definir en su propia spec** — el Descargador cumplió: los bytes están íntegros y con su hash |
| **C22** | Los escaneos son **documentos firmados** (acuerdos rectorales, contrato colectivo) (E12.5) | El patrón es predecible, no aleatorio: se escanea lo que lleva firma. Permite anticipar qué tipos de norma necesitarán OCR antes de abrirlos |
| **C23** | La UJAT publica **105 documentos**, no ~60 (E12.1) | E4 subestimaba casi al doble. Los conteos hechos a ojo sobre un índice paginado **no son fiables**; hay que contar enlaces únicos con herramienta |
| **C24** | **La idempotencia se cumple dentro de una corrida, no entre corridas de días distintos** (E13). Los 45 documentos de la UAM están **dos veces en disco**, con los mismos bytes y distinto nombre | La fecha de captura entra en el nombre cuando el índice no declara fecha de versión, así que **otro día es otro nombre**. No se sobrescribió nada: la regla funcionó y el diseño falló. **Primera evidencia medida a favor del alias por hash** (D15 de `00`, `01` v2.1): comparar el SHA-256 dentro del `grupo_alias` habría reconocido los 45 pares |
| **C20** | Dos versiones históricas del mismo instrumento colisionan en `entry_id` (E11.6) | **Hueco de `01`**, no del sitio: `CatalogEntry.entry_id` no lleva versión, `doc_id` (N7) sí. **Cerrada.** En M23b se midió que dos pares de la UAM con slug idéntico (`2026`, `rjd`) se separan solo por `url_id`; eran los 2 documentos que v1 perdía. E14 confirma 156 identificadores únicos en base limpia (2026-09-18) |

---

## E6 · Lo que sigue sin medirse (deuda de evidencia)

| # | Sin medir | Por qué importa |
|---|---|---|
| ~~E6.1~~ | ~~Una universidad estatal pequeña~~ | **CERRADA (2026-09-06): UACAM medida, ver E10.** El sitio sirve; lo que falla es la vigencia del contenido |
| E6.2 | Un instituto tecnológico o universidad politécnica | Régimen distinto → esqueleto distinto (pregunta abierta 1 de `04`) |
| E6.3 | Cuántas universidades del total sirven índice por JS | Con **4/4** en HTML plano, la estimación previa se desploma — pero 4 no son 40 |
| E6.4 | Un Periódico Oficial estatal | Fuente de las leyes orgánicas estatales; no se ha tocado ninguno |
| E6.5 | El 70-I accedido programáticamente | Sigue siendo el respaldo de D1 y sigue sin ruta conocida |
| E6.6 | Tasa de PDFs escaneados sin capa de texto | Decide si el OCR entra en v1 (spec `06`). Sospecha: alta en leyes orgánicas viejas |
| E6.7 | Si los PDF de la UJAT de 2012 abren realmente | Rutas viejas con espacios: candidatas a enlace muerto |
| E6.8 | **Recontar UNAM-OAG y UJAT en vivo** | Sus cifras son de la captura original. La re-medición de la UAM corrigió dos conteos; es razonable esperar lo mismo allí |
| ~~E6.9~~ | ~~¿Hay más enlaces sin texto de ancla?~~ | **CERRADA, en contra (E10.3): sí los hay.** 2 de 4 instituciones. Es requisito firme del Lector, no caso raro |
| E6.10 | **Las obligaciones de transparencia VIGENTES de la UACAM** (`/view/paginas/49`) | E10 midió la rama histórica. La rama actual no se ha abierto: puede que el catálogo bueno esté ahí y el hallazgo de E10.1 sea menos grave de lo que parece — o que no exista, y sea peor |
| E6.11 | ¿Cuántos índices más declaran fecha de corte? | Si C13 se repite, el Lector necesita esa comprobación **antes** que ninguna otra |
| E6.12 | **El rate limit real, medido** | Los logs de `httpx` no lo miden (E11.7). Hace falta que `RateLimiter` emita su propia línea. Sin eso, el criterio 7 de `05` se firma a ojo |
| E6.13 | **¿Cuántos sitios devuelven un `robots.txt` inesperado?** | 1 de 1 probado (E11.1). Si el patrón se repite, fail-open pasa de decisión prudente a requisito obvio; si la UAM es rara, conviene saberlo |
| E6.14 | **Qué codificación declaran los otros índices** | La UAM es `iso-8859-1` (E11.3). Si UNAM, UJAT y UACAM son UTF-8, el Lector necesita detectar, no elegir un default |
| E6.15 | **Comportamiento ante un `robots.txt` que sí prohíbe** | La corrida de la UAM nunca llegó a parsear uno. Ese camino solo está cubierto por tests, no por campo |
| E6.16 | **Descargar los 4 documentos de Drive de la UACAM** | E10.2 los halló; nadie ha comprobado que el Descargador los mande a cola manual como `visor_de_terceros` en vivo. Es la validación de campo de C14 |
| E6.17 | **¿Qué proporción de escaneos tienen las otras estatales?** | UJAT 23 %, UAM 0 % (C21). Con dos puntos no hay tendencia. Si las estatales rondan el 20 %, el OCR es infraestructura, no un parche |
| E6.18 | **Calidad de los escaneos de la UJAT** | Nadie ha mirado si son legibles, si están derechos, ni a qué resolución. Determina si un OCR estándar basta o hace falta preprocesado |
| E6.20 | **Estado real de `legisuni.db`** | E13 midió el disco, no la base. Falta saber si las 45 filas duplicadas también se registraron (¿195 filas o 150?). Determina si la duplicación es solo de archivos o también de persistencia |
| E6.21 | **¿La UJAT se duplicaría igual?** | Solo se corrió una vez (2026-09-08). Por C24 debería pasarle lo mismo, pero **no está medido**: son 285 MB, y confirmarlo a propósito cuesta más que asumirlo |
| E6.19 | **¿Cuántos documentos tienen texto pero mal extraído?** | El umbral usado fue "< 100 caracteres en 3 páginas". Un PDF con texto en columnas o con capa OCR mala pasa el filtro y da basura después |

**Próxima medición recomendada: E6.10.** Es la más barata (una URL ya conocida) y la que más
cambia: decide si el hallazgo de E10.1 es una rama histórica correctamente rotulada —molesta
pero honesta— o si la UACAM sencillamente no tiene catálogo vigente publicado. Son dos mundos
distintos para el diseño del Corroborador.

**Después, E6.2:** un tecnológico o politécnica. Es el único régimen sin medir.

---

## E7 · Método (para las próximas mediciones)

Lo que funcionó y conviene repetir con cada universidad nueva:

1. Una búsqueda para hallar la página candidata (buscar "Abogado General" o "Abogacía
   General" da mejores resultados que "legislación" a secas — funcionó en UNAM y UJAT).
2. Una descarga directa de esa página, **sin JavaScript**.
3. Mirar qué llegó: ¿lista real, o cáscara con instrucciones de tabla?
4. Si hay lista: contar instrumentos; ver si declara vigencia; ver si las URLs son estables;
   **ver si la Ley Orgánica y el Estatuto están donde deberían** (E4.1 enseñó que no siempre).
5. **Buscar la fecha de corte antes de creerse nada.** Mirar el pie de página, los rótulos de
   navegación y el título de la sección en busca de "fecha de corte", "actualizado al",
   "histórico" o "antes de la reforma". La UACAM (E10.1) enseñó que un índice perfecto puede
   tener nueve años y decirlo en una sola línea que es fácil no leer.
6. **Contar cuántos enlaces son normativa de verdad**, no cuántos enlaces hay. En la UACAM eran
   27 de ~82 (E10).
7. Anotar el resultado aquí, con la fecha, aunque el resultado sea "falló".

**Las mediciones que fallan valen tanto como las que salen bien.** El fallo del 70-I es la
razón de que exista el criterio de aceptación más importante de la spec `03`. La medición de
la UJAT tumbó dos suposiciones del diseño original en un solo intento. Y la de la UACAM
—técnicamente la más exitosa de las cuatro— destapó el peor fallo posible: **un catálogo que
pasa todas las verificaciones y está caducado**.

**Corolario incómodo:** las mediciones que salen "bien" son las más peligrosas, porque invitan
a dejar de mirar. La UACAM se habría dado por buena tras el paso 4.

---

## E8 · Validez externa: qué se puede y qué NO se puede inferir de cinco mediciones

Esta sección existe porque el documento pasa de **cinco mediciones sobre cuatro instituciones**
a **dieciséis conclusiones de diseño** sin detenerse a preguntar si alcanzan. La respuesta honesta es: para unas sí,
para otras no, y conviene tenerlo escrito antes de que las conclusiones se endurezcan por
repetición.

### E8.1 · La muestra está sesgada, y el sesgo tiene nombre

Las cuatro universidades se hallaron **buscándolas**. Es decir: la muestra está compuesta
exclusivamente de instituciones **cuyo sitio de legislación es hallable por búsqueda web**.

Las que no aparecen en una búsqueda —porque no tienen página, porque la tienen sin indexar,
porque la esconden tras un portal de transparencia— **son invisibles para el método que
produjo esta evidencia**. Sesgo de supervivencia en estado puro.

**Consecuencia:** "4 de 4 funcionan" no significa "el 100 % funciona". Significa "el 100 % de
las que se pueden encontrar buscando, se pueden leer". Que no es poco, pero es otra cosa.

**Lo que la UACAM corrigió del sesgo, y lo que no.** Corrigió el tamaño: ya no son solo
universidades grandes y con recursos. Pero **agravó otra cosa**: mostró que "se puede leer" y
"sirve" son preguntas distintas, y que las cuatro mediciones solo respondían la primera. Con
ese criterio nuevo, el marcador honesto no es 4 de 4 sino **3 de 4**.

### E8.2 · Qué conclusiones aguantan y cuáles son extrapolación

| Conclusión | ¿Aguanta? | Por qué |
|---|---|---|
| C2 · la vigencia rara vez se declara | **Sólida** | Un contraejemplo (UAM) contra tres; y la dirección del sesgo juega a favor: si las grandes no la declaran, las chicas menos |
| C13 · un índice puede estar caducado y declararlo al pie | **Sólida como requisito** | Un caso basta para obligar a comprobarlo. **No** dice nada sobre su frecuencia — eso es E6.11 |
| C15 · puede faltar el estatuto habilitante | **Sólida como requisito** | Ídem: la existencia se prueba con un ejemplo |
| C3 · la taxonomía puede estar rota | **Sólida** | Basta **un** caso para justificar no confiar en ella. La existencia se prueba con un ejemplo |
| C5 · URLs sucias | **Sólida** | Ídem: un caso basta para exigir normalización |
| C9 · enlaces sin texto de ancla | **Sólida como requisito** | Un caso obliga a manejarlo; **no** dice nada sobre su frecuencia |
| C10 · un enlace vivo no prueba vigencia | **Sólida** | Es una propiedad de cómo funcionan los servidores de archivos, no de la UAM |
| C12 · varias versiones históricas a la vez | **Sólida** | Ídem C3: la existencia se prueba con un ejemplo |
| C4 · cada sitio tiene su mecanismo de identidad | **Razonable** | Tres sitios, tres mecanismos distintos. La conclusión operativa (fallback por título) es conservadora, así que el riesgo de equivocarse es bajo |
| C6 · la Ley Orgánica a veces está pero vieja | **Razonable** | Un caso, pero el mecanismo que lo explica (la universidad no actualiza lo que no promulga) es general |
| C7 · los contratos colectivos se publican | **Débil** | Dos de tres, y ambos son sindicatos grandes y consolidados |
| C14 · visor de terceros | **Débil en frecuencia, sólida en existencia** | 4 documentos en 1 de 4 instituciones. Obliga a manejarlo; no dice que sea común |
| **C1 · todos los sitios sirven HTML plano** | **Sigue siendo la más débil** | Cuatro casos ahora, no tres — mejor, pero todos hallables por búsqueda. Es exactamente la que más decisión sostiene (no pagar Playwright) |

**Léase con cuidado:** las conclusiones que dicen *"esto existe, manéjalo"* aguantan con un
solo caso. Las que dicen *"esto es lo normal"* necesitan muchos más. C1 es del segundo tipo y
se está usando como si fuera del primero.

### E8.3 · Qué medición refutaría el diseño (prueba de falsación)

Vale más tener escrito qué nos haría cambiar de opinión que acumular evidencia a favor:

| Si al medir… | …se cae |
|---|---|
| 3 de 5 estatales pequeñas sirven índice por JavaScript | **C1 y la decisión de no pagar Playwright.** Habría que reabrir la pregunta 1 de `00` |
| Que la mitad de los índices declare fecha de corte | El Lector tendría que empezar por ahí, y el Corroborador dejaría de poder confiar en ningún catálogo sin cotejarlo contra el 70-I |
| Una universidad sin ninguna página de legislación hallable | **D1 entera.** La PNT volvería a ser fuente primaria, y con ella el problema sin resolver de E6.5 |
| Un sitio que sirve su índice pero con enlaces mayoritariamente muertos | El Descargador dejaría de ser la pieza fácil, y la cola manual pasaría de excepción a norma |
| Que el 70-I resulte accesible y completo por una ruta simple | **D1 se volvería a invertir**, esta vez con datos de los dos lados |

**Ninguna de las cuatro está descartada.** Las cuatro se resuelven con las mediciones de E6.

### E8.4 · La regla operativa que se deriva de todo esto

**No escalar a las 40 universidades hasta haber medido seis**, y que al menos dos sean pequeñas
y una sea tecnológica. Seis no es una muestra representativa, pero es suficiente para que C1
deje de descansar en cuatro casos elegidos por conveniencia.

**Y a partir de la UACAM, cada medición cuenta dos veces:** ¿se puede leer el índice? y ¿el
índice está vigente? Las cuatro mediciones existentes solo respondieron la primera pregunta
con rigor; la segunda apareció por accidente al leer el pie de una página.

Mientras tanto, el sistema se construye asumiendo que **el caso difícil existe aunque no lo
hayamos visto todavía**: por eso la cola manual es salida legítima (D7) y no un parche.

---

## E9 · Congelar la evidencia: fixtures y su caducidad

Las specs `02` a `06` piden repetidamente *"captúralo como fixture"*, pero en ninguna parte
está escrito **qué capturar exactamente, cuándo, ni por qué corre prisa**. Esta sección cierra
ese hueco.

### E9.1 · La evidencia de este documento se pudre, y ya hay pruebas

No es una precaución teórica. Está medido en este mismo documento:

- **E1.2:** las URLs de la UAM llevan la fecha de consolidación dentro. En la próxima
  consolidación mueren **todas a la vez**.
- **E1.4:** la carpeta de marzo de 2026 **ya desapareció del índice** entre la primera captura
  y la re-medición. Sigue respondiendo, pero dejó de estar listada.
- **E1.1:** ocho instrumentos declaran fecha de cese; varios ya la pasaron. El índice de hoy
  no es el de hace tres meses ni será el de dentro de tres.

**El índice de la UAM que sostiene el criterio de aceptación 1 de la spec `03` dejará de
existir.** Si no se congela ahora, ese criterio se vuelve inverificable y la spec queda
apoyada en una descripción en prosa de algo que ya no se puede consultar.

### E9.2 · Qué capturar, exactamente

Por cada universidad medida, y **antes** de escribir la primera línea de código:

| Qué | Dónde | Por qué |
|---|---|---|
| **HTML crudo del índice**, sin reducir ni limpiar | `tests/fixtures/indices/<inst_id>__<AAAA-MM-DD>.html` | Es la entrada real del Lector. Reducirlo antes de guardar destruye justo lo que hay que probar: el ancla vacía de E1.5 desaparece de cualquier extracción de texto |
| **Catálogo esperado**, escrito a mano | `tests/fixtures/indices/<inst_id>__<AAAA-MM-DD>.esperado.json` | Los 31 + 5 + 8 + 1 de la UAM, con su `tipo_norma` y `estado`. Es el oráculo del test |
| **Fecha y URL exacta de captura** | Cabecera del JSON | Sin esto la fixture no es reproducible ni auditable |
| **2–3 PDF representativos** por universidad | `tests/fixtures/docs/` | Uno con leyenda de reforma clara, uno sin ella, y —si aparece— uno escaneado |
| **El HTML de la rejilla vacía** (70-I de la UNAM) | Igual que los demás | Es la fixture del criterio de honestidad de la spec `03`, y es la más fácil de perder porque "no tiene datos" |
| **El HTML de la UACAM** | Igual que los demás | Es la única fixture que contiene una **fecha de corte** (E10.1), un **visor de terceros** (E10.2) y un **hueco crítico real** (E10.5) a la vez. Tres criterios de aceptación de tres specs distintas dependen de este solo archivo |

**Regla:** el HTML se guarda **tal como llegó del servidor**, bytes incluidos. La reducción
(`reduce.py` de la spec `03`) es parte del código bajo prueba, no del material de prueba.

**La UACAM demuestra por qué la regla no es un capricho.** Su "Fecha de corte: Diciembre del
2016" vive en el pie de página, después del `<footer>`, junto a un contador de visitas y el
crédito del proveedor. Cualquier reducción razonable —quedarse con el contenido principal,
tirar el pie— **la borra**. Y con ella desaparece el hallazgo más importante del proyecto.

### E9.3 · Dos capturas separadas en el tiempo, no una

El criterio 6 de la spec `03` —estabilidad de `doc_slug` cuando las URLs cambian por
completo— **no se puede probar con una sola captura**. Necesita dos del mismo sitio en fechas
distintas.

La buena noticia: para la UAM ya existen las dos, porque la primera medición pilló la
consolidación anterior y la segunda la de julio de 2026. **Esa pareja es el activo de prueba
más valioso del proyecto y hay que salvarla explícitamente**, porque es irrepetible: no se
puede volver atrás en el tiempo a capturar un índice que ya cambió.

### E9.4 · Las fixtures caducan, y hay que decir cuándo

Una fixture de 2026 sigue siendo válida para probar **el parser** indefinidamente: el HTML no
cambia una vez guardado. Lo que caduca es su valor como **descripción del mundo**.

Convención propuesta:

- Las fixtures **nunca se actualizan en sitio**. Se añade una nueva con su fecha y conviven.
- El test de regresión corre contra **todas** las capturas, no solo la última. Un Lector que
  acierte la de 2026 y falle la de 2025 tiene un problema.
- Cuando una captura nueva difiere de la anterior, **la diferencia se anota en este documento**
  como hallazgo. Así el `08` crece con el mismo mecanismo que el sistema usa para vigilar
  reformas: por diff.

### E9.5 · Lo que esto le cuesta al proyecto

Nada. Son cuatro archivos HTML y un puñado de PDF: unos pocos megabytes en el repo, capturados
en una tarde. Comparado con el coste de descubrir en la micro-tarea 12 que el criterio de
aceptación 1 se refiere a una página que ya no existe, es gratis.

**Hazlo antes de la conversación de la spec `01`.** Es la única tarea de este proyecto cuyo
coste sube con cada día que pasa.

---

## E10 · UACAM — la estatal pequeña: el índice que caducó en 2016

**Fuente:** `https://transparencia.uacam.mx/view/paginas/11`
**Medido en vivo:** 2026-09-06.
**Resultado: éxito técnico, fracaso de contenido.** Es el caso que E6.1 pedía y el que más
enseña de los cuatro.

HTML plano, sin JavaScript, en dominio oficial, bien estructurado en ocho rúbricas (a–h), con
enlace directo a cada PDF. Técnicamente es el índice más fácil de leer de los cuatro.

**Composición de los ~82 enlaces a documento:**

| Rúbrica | Qué contiene | ¿Normativa propia? |
|---|---|---|
| a.1–a.3 | Constituciones federal y estatal | No (3) |
| b.1–b.9 | Leyes generales y estatales + **Ley Constitutiva** y **Ley Orgánica** | **2 de 9** |
| c.1–c.11 | Reglamentos de la UACAM | **Sí (11)** |
| c.12–c.14 | Manuales y reglas de operación | **Sí (3)** |
| d.1–d.4 | Circulares administrativas 2012–2015 | Marginal |
| e.1–e.10 | Formularios (solicitud de análisis clínicos, préstamo de sala…) | **No** |
| f.1–f.6 | Contratos y convenios por ejercicio, desde 2010 | **No** (~30 enlaces) |
| g.1–g.6 | Lineamientos | **Sí (5 de 6)** |
| h.1–h.6 | Acuerdos del Consejo Universitario | **Sí (6)** |

**27 instrumentos normativos propios entre ~82 enlaces.** Dos de cada tres enlaces del índice
son ruido para nuestros fines: constituciones ajenas, formularios de trámite y contratos de
laboratorio de 2010.

### E10.1 · «Fecha de corte: Diciembre del 2016» — el hallazgo más importante del proyecto

Al pie de la página, una sola línea:

> Fecha de corte: Diciembre del 2016

Y en la navegación, el rótulo que lo explica:
**Histórico → Ley de Transparencia antes de la Reforma 2016 → X. Disposiciones legales**.

**Todo ese catálogo está congelado hace nueve años.** Las obligaciones vigentes viven en otra
rama del mismo sitio (`/view/paginas/49`, "Obligaciones de Transparencia Comunes"), que **no
se midió** — ver E6.10.

**Por qué es el hallazgo más importante:** no hay error de red, ni HTTP distinto de 200, ni
HTML roto, ni dominio sospechoso. Todas las defensas del sistema —guardián `%PDF-`, verificación
de dominio (D9), hash de integridad— **pasarían limpias**. Un Lector que no cace esa línea
ingiere legislación de 2016 rotulada como actual, y nada aguas abajo lo detectaría salvo el
Verificador Documental leyendo las fechas dentro de los PDF.

Es la justificación definitiva de tres decisiones que hasta ahora se apoyaban en menos:
**D6** (`estado="desconocido"` por defecto, nunca `vigente` por omisión), la **subida de
prioridad de la pieza ⑤**, y la regla de que **un enlace vivo no prueba vigencia** (C10, que
aquí se agrava: aquí ni siquiera el índice prueba vigencia).

**Requisito nuevo para el Lector (spec `03`):** buscar activamente marcas de corte temporal en
la página —"fecha de corte", "actualizado al", "histórico", "antes de la reforma"— y, si las
halla, propagarlas a **todas** las entradas del catálogo como `estado="desconocido"` más una
nota. La marca puede estar en el pie, en un rótulo de navegación o en el título de la sección;
no hay un lugar canónico.

### E10.2 · Cuatro documentos servidos por Google Drive

En el menú "Normativa" y en "Formato ARCO":

- Formato ARCO
- Ley de Transparencia
- Ley de Protección de Datos Personales
- **Lineamientos de Protección de Datos Personales UAC** ← este sí es normativa propia

Cuatro enlaces a `drive.google.com/file/d/…/view`. **El fenómeno del visor de terceros existe
y aquí está medido**, aunque sea marginal en volumen.

**Dos consecuencias concretas:**

1. **D9:** `drive.google.com` no es dominio institucional ni subdominio suyo. Un documento de
   esa procedencia entra con autenticidad degradada y verificación obligatoria.
2. **Spec `05` — problema nuevo, no previsto:** una URL de Drive `/view` devuelve **HTML, no
   PDF**. El guardián `%PDF-` la rechazará y el documento se perderá con `motivo_fallo="no_es_pdf"`,
   que es un diagnóstico **falso**: el archivo existe, solo que detrás de un visor. Hace falta
   o resolución previa al enlace de descarga directa, o un motivo de fallo propio que mande el
   caso a cola manual en vez de confundirlo con una landing page rota.

### E10.3 · Segundo enlace sin texto de ancla — E6.9 respondida, y en contra

En la rúbrica f, entre los convenios:

```html
<a href="http://etzna.uacam.mx/transparencia/X/f/Contratos%20Interinstitucionales%20(2014).pdf"></a>
```

**Segunda institución, mismo patrón que E1.5 de la UAM.** Con dos casos de cuatro, deja de ser
anécdota y pasa a ser requisito firme del Lector (C9 se refuerza). En este caso el documento
huérfano es un contrato, no una norma, así que el coste de perderlo es bajo — pero eso no se
sabe hasta abrirlo, que es justamente el argumento.

### E10.4 · Tres subdominios y una Ley Orgánica en cinco lugares

El índice vive en `transparencia.uacam.mx`; los PDF cuelgan de `etzna.uacam.mx`; y hay otra
copia de la Ley Orgánica en `uacam.mx/modulos/paginas/archivos/11/`. Los tres son subdominios
legítimos, así que D9 los acepta — el mecanismo funciona.

**Fuera del dominio institucional, la misma Ley Orgánica aparece en el Congreso del Estado de
Campeche (en dos rutas distintas) y en el repositorio de normas de la CNDH.** Y **las versiones
difieren**: la copia de la CNDH ya contiene la figura del Abogado General y un articulado
reordenado; la del sitio universitario conserva numeración y contenido anteriores.

**D2 y C6 confirmadas con dureza en una segunda institución.** No basta con hallar la Ley
Orgánica: hay que hallarla en ambos lados y dejar que el Verificador Documental decida cuál
rige.

### E10.5 · Falta el Estatuto Orgánico — hueco crítico real

La Ley Orgánica invoca el Estatuto Orgánico repetidamente ("las facultades específicas de la o
el Abogado General y la Oficina misma se establecerán en el Estatuto Orgánico"). **No está en
el índice.**

Es el primer hueco crítico detectado en datos reales, y es exactamente lo que el esqueleto
esperado de la spec `04` existe para cachar: un catálogo con once reglamentos y sin la norma
que los habilita está incompleto por construcción, sin necesidad de LLM.

### E10.6 · URLs sucias, segunda confirmación

Espacios sin codificar (`Convenios Becas PROMEP (2010).pdf`) **mezclados en la misma página**
con rutas correctamente codificadas con `%20`. El índice se sirve por `https` y los PDF por
`http` — contenido mixto que algunos clientes bloquean.

Segundo caso tras la UJAT (E4.3). El requisito de normalización de la spec `05` deja de
apoyarse en una sola institución.

---

## E11 · Primera descarga real (UAM, 2026-09-06)

Todo lo anterior en este documento vino de **mirar páginas**. Esta sección viene de **correr
código contra un servidor real**: el Descargador (spec `05`) completo, sobre las 45 URLs
extraídas del índice de la UAM.

**Resultado: 45 de 45 exitosas.** El criterio de aceptación 1 de la spec `05` pedía ≥ 90 %.

| Métrica | Valor |
|---|---|
| Documentos pedidos | 45 |
| Éxitos | 45 (100 %) |
| Fallos | 0 |
| Formatos | 42 `.pdf` + 3 `.docx` |
| Peso total del corpus | **12.6 MB** |
| Documento más grande | El consolidado, **4.3 MB** |
| Duración | ~2 min (rate limit de 1 s por dominio) |

### E11.1 · La UAM responde 403 a `robots.txt` y 200 a sus PDF

**El hallazgo más importante de esta corrida**, y el que valida una decisión de diseño:

```
GET https://www.uam.mx/robots.txt                      → 403 Forbidden
GET https://www.uam.mx/legislacion/…-lo.pdf            → 200 OK
```

Mismo host, misma sesión. Se probó **con y sin** cabecera de User-Agent: el 403 persiste en
ambos casos, así que no es el patrón conocido de servidores que bloquean clientes sin UA (D8,
heredado del proyecto hermano). **La UAM sirve su archivo de política con 403 mientras entrega
su contenido con 200.**

**Consecuencia dura:** la política de `robots.txt` **debe ser fail-open**. Con fail-closed
—negarse a descargar cuando `robots.txt` no se puede leer— la cosecha de la UAM habría
terminado en **cero documentos**, sin que ninguna prohibición real lo justificara.

La muestra es mínima (1 de 1), pero la asimetría del costo no lo es: fail-open sobre un sitio
que sí prohibía es un error recuperable y registrado en el log; fail-closed sobre un sitio que
no prohibía nada es un corpus vacío sin diagnóstico.

**Lo que la corrida NO probó:** que un `robots.txt` legible se respete de verdad. Ese camino
no se ejerció aquí porque nunca hubo archivo que parsear (E6.15).

### E11.2 · Las rutas de consolidaciones retiradas siguen vivas — segunda confirmación

C10 se había establecido observando el índice. Ahora está probado con bytes: los documentos
alojados bajo `/legis-uam-arch/` (históricos) y `/legis-uam-abr/` (el reglamento abrogado)
**respondieron 200 y se descargaron íntegros**.

Refuerza que **un enlace vivo no prueba vigencia** — y se conecta con C13: en la UACAM ni
siquiera el índice lo prueba. La sospecha de enlaces muertos en rutas viejas no se materializó
en la UAM; queda pendiente para la UJAT (E6.7).

### E11.3 · El índice de la UAM se sirve en `iso-8859-1`, no en UTF-8

La página declara `charset=iso-8859-1` en su `<meta>`. Leerla asumiendo UTF-8 corrompe todos
los títulos con acentos y eñes — es decir, prácticamente todos.

**Requisito para el Lector de Índice (spec `03`):** `reduce.py` debe detectar la codificación
declarada y decodificar con ella, no asumir UTF-8. Es un modo de fallo silencioso: no lanza
excepción, solo produce títulos con basura, y esa basura viajaría hasta `doc_slug` y hasta el
nombre del archivo en disco.

Refuerza también la regla de E9.2: **la fixture se guarda en bytes crudos**. Una fixture
guardada ya decodificada a UTF-8 escondería este problema en vez de permitir probarlo.

### E11.4 · El guardián de dos firmas funcionó sobre `.docx` reales

Los tres anexos `.docx` de la UAM (E1.6) pasaron el guardián por su firma `PK\x03\x04` y
quedaron en disco con extensión `.docx`, derivada de los bytes y no de la URL. Primera
validación en campo de la decisión tomada en `01` v1.3.

El camino de `visor_de_terceros` (C14) está implementado y cubierto por tests —incluido el
orden: visor antes que guardián— pero **no se ha ejercido en campo**, porque la UAM no sirve
nada por Drive. Los cuatro documentos de la UACAM son el material para hacerlo (E6.16).

### E11.5 · Escala del corpus, medida en vez de estimada

12.6 MB para una universidad con 45 documentos. Extrapolando a ~40 universidades públicas:
**del orden de 500 MB**. SQLite y disco local sobran; no hace falta pensar en almacenamiento
de objetos ni en compresión. Una decisión de arquitectura que ya no hay que tomar.

El consolidado pesa 4.3 MB, muy lejos del tope de 100 MB por documento. **Cierra la pregunta
abierta 2 de la spec `05`** a favor de descargarlo: es barato y sirve de respaldo y de base
para el diff.

### E11.6 · `entry_id` no distingue versiones de un mismo instrumento

Al derivar identificadores de los nombres de archivo apareció un problema que no es del
Descargador sino de los contratos.

La UAM publica **dos** versiones históricas del Reglamento de Estudios Superiores:

```
legis-univ-uam-res-VIGENTE-HASTA-16.03.2026.pdf
leg-univ-uam-res-VIGENTE-HASTA-04.11.2024.pdf
```

Ambas son el instrumento `res`. Con `doc_slug` derivado correctamente, ambas producirían
`entry_id = "uam:res"` — **y colisionarían**, porque `entry_id` (N2) no lleva la versión
dentro. `doc_id` (N7) sí la lleva, pero `CatalogEntry` es anterior a la descarga y no tiene
fecha de versión fiable en el momento de construirse.

**Esto es un hueco de `01`, no un hallazgo de campo del sitio.** Se anota aquí porque el dato
lo expuso, pero **la decisión pertenece a la conversación de la spec `03`** y toca contratos.

> **Aviso metodológico:** la corrida usó slugs derivados con una heurística provisional
> (*"lo que va tras el último guión"*), que falla en estos mismos archivos: produjo
> `uam:16.03.2026` en vez de `uam:res`. Los nombres en disco de esta primera corrida son, por
> tanto, **desechables**; se rehacen en dos minutos cuando el Lector produzca slugs correctos.
> Lo que esta corrida midió es el Descargador, no la identidad de los documentos.

### E11.7 · Nota de método: los logs de `httpx` no miden el rate limit

`httpx` registra al **recibir** la respuesta, no al enviar la petición. Los huecos entre líneas
de log no son, por tanto, los intervalos entre peticiones, y el criterio de aceptación 7 de la
spec `05` (≥ 1 s entre peticiones al mismo dominio) **no se puede verificar leyendo ese log**.
Hace falta que `RateLimiter.esperar` emita su propia línea con los segundos que durmió (E6.12).

---

## E12 · Segunda descarga real: UJAT, la prueba de suciedad (2026-09-08)

La corrida de la UAM (E11) fue el caso limpio: un dominio, URLs bien formadas, todo `https`.
La UJAT es lo contrario, y por eso era el criterio 2 de la spec `05`: espacios sin codificar,
`http` y `https` mezclados, rutas que van de 2012 a 2026 y un índice repartido en varias
páginas.

**Resultado: 105 de 105 exitosas.**

| Métrica | UAM (E11) | UJAT (E12) |
|---|---|---|
| Documentos | 45 | **105** |
| Éxitos | 45 (100 %) | **105 (100 %)** |
| Peso | 12.6 MB | **285 MB** |
| Peso medio por documento | 0.28 MB | **2.7 MB** |
| Escaneos sin texto | **0 de 42** | **24 de 105** |
| Codificación del índice | `iso-8859-1` | **`utf-8`** |
| `robots.txt` | **403** | **404** |
| URLs con espacios crudos | 0 | **17** |
| URLs en `http` | 0 | 5 |

### E12.1 · El índice está repartido y el conteo previo estaba mal

Cinco páginas enlazadas entre sí (`/abogado/15763`, `16443`, `17669`, `33794`, `4232`), pero
**solo dos contienen documentos**: la `15763` (90) y la `17669` (19). Las otras tres son
navegación. Total: **105 enlaces únicos**, no los ~60 que estimaba E4.

**Lección de método:** contar documentos a ojo sobre un índice paginado subestima. Hay que
recorrer las páginas y deduplicar con herramienta (C23).

### E12.2 · `urlnorm` funcionó en campo — primera vez

Diecisiete URLs traen espacios sin codificar. Todas se normalizaron y respondieron:

```
cruda:  https://archivos.ujat.mx/abogado_gral/Acuerdos/acuerdos rect 2.pdf
pedida: https://archivos.ujat.mx/abogado_gral/Acuerdos/acuerdos%20rect%202.pdf   → 200 OK
```

Y la **idempotencia** también quedó probada con datos reales: `Acuerdo%20de%20Genero.pdf` ya
venía codificada desde el sitio y se pidió idéntica, sin convertirse en `%2520`.

Hasta esta corrida, la normalización de URLs solo estaba cubierta por tests.

### E12.3 · Los cinco `http` redirigen solos: el TLS estricto se queda

Los cinco documentos servidos por `http` son de **2021, 2024, 2025 y 2026** — no son legado.
Hay documentos de 2026 en `http` mientras sus vecinos de la misma carpeta van por `https`. Es
inconsistencia editorial, no una migración a medias.

Los cinco devolvieron **301 a `https`** y el cliente siguió la redirección sin problema. Cero
fallos de certificado en 105 peticiones.

**Cierra la pregunta abierta 4 de la spec `05`:** la verificación TLS estricta se queda.
Relajarla no habría ganado nada, y promover `http` a `https` por cuenta propia habría sido
adivinar cuando el servidor ya lo hace bien.

### E12.4 · Las rutas de 2012 siguen vivas — E6.7 cerrada

`archivos.ujat.mx/abogado_gral/legislacion_univ2012/…` responde **200**. La sospecha de
enlaces muertos en rutas viejas no se materializó, igual que no se materializó en la UAM
(E11.2). Dos universidades, cero enlaces muertos.

También se confirmó que **las dos capitalizaciones funcionan**: existen enlaces a
`/2015/Abogado General/` y a `/2015/abogado general/`, y ambas responden. El servidor no
distingue mayúsculas, o existen las dos carpetas.

### E12.5 · **Un cuarto del corpus estatal son escaneos sin texto**

**El hallazgo más consecuente de esta corrida**, y no tiene nada que ver con el Descargador.

| | UJAT | UAM |
|---|---|---|
| Documentos sin texto extraíble | **24 de 105** (23 %) | **0 de 42** |
| Peso de esos documentos | **179 MB** de 285 (63 %) | — |

Medido con `pdfplumber` sobre las tres primeras páginas de cada PDF; umbral: menos de 100
caracteres extraídos.

Los más grandes:

```
33.7 MB  tablas-de-aplicabilidad
32.7 MB  acuerdo-disposiciones-de-aplicacion-general-en-materia-de-…
28.1 MB  cc-staiujat                    ← el contrato colectivo
15.8 MB  acuerdo-de-genero
10.8 MB  acuerdo-firma-electronica-avanzada-fiel
```

**El patrón no es aleatorio: son documentos firmados.** Acuerdos rectorales y el contrato
colectivo se escanean porque llevan firma. Eso los hace **predecibles**: se puede anticipar qué
tipos de norma necesitarán OCR antes de abrirlos (C22).

**Qué significa y qué no:**

- **No es un fallo del Descargador.** Su contrato es traer bytes íntegros con su hash y su
  proveniencia, y lo cumplió: 105 de 105. Un escaneo descargado correctamente es un éxito.
- **Sí es un requisito nuevo para aguas abajo.** La fase de extracción de texto necesita OCR
  para el corpus estatal. **Alcance, motor y umbral quedan por definir en su propia spec**; no
  se decide aquí, porque decidirlo ahora sería suponer sin haber mirado la calidad de los
  escaneos (E6.18).
- **La UAM tiene cero.** No es un problema del país: es un problema de las estatales, o al
  menos de la UJAT. Con dos puntos no hay tendencia (E6.17).

> **Corrección de una inferencia previa:** se supuso, por su tamaño (16 MB), que el
> *Reglamento de la Honorable Junta de Gobierno* era un escaneo. **No lo es**: tiene texto
> extraíble. Era un PDF pesado, nada más. El tamaño no predice si un documento es imagen; hay
> que medirlo.

### E12.6 · La escala del corpus estaba mal estimada

C19 decía "~12.6 MB por universidad, ~500 MB para 40". Con la UJAT en **285 MB**, la varianza
entre instituciones es de **23×**, y la extrapolación se va a **varios GB**.

Sigue cabiendo en disco local y SQLite sigue bastando. Lo que ya no se sostiene es la
conclusión de que no hay que pensar en el peso: 63 % de ese peso son imágenes que, tras el
OCR, se convertirán en unos pocos MB de texto. **La decisión de si se conservan los originales
tras extraer el texto pasa a ser real**, y pertenece a la spec de extracción.

### E12.7 · El percent-encoding se cuela en los slugs derivados

Al derivar `doc_slug` del nombre de archivo aparecieron slugs como
`acuerdo-20de-20genero` y `manual-…-actualizaci-c3-93n`: `paths.sanear` recibió texto ya
percent-encoded y convirtió el `%` en guion, dejando `20` y `c3-93` como si fueran palabras.

**No es un defecto de `sanear`** —su trabajo es sanear texto, no decodificar URLs— sino de
quien la llama. Se corrigió aplicando `urllib.parse.unquote` antes.

**Requisito para el Lector de Índice (spec `03`):** decodificar el nombre **antes** de
normalizarlo. Le va a pasar exactamente igual.

---

## E13 · Auditoría de disco antes de la migración (2026-09-10)

**No es una corrida nueva.** Es lo que apareció al inventariar el repositorio antes de migrar el
Descargador a `Encargo`, cuando se notó que `08` fechaba las dos corridas el mismo día y el
disco decía otra cosa.

### E13.1 · Hubo dos corridas de la UAM, no una

```
git log --format='%ad %s' --date=short
2026-09-08 M13: corrida real contra la UJAT
2026-09-08 M12: reanudación explícita de corridas interrumpidas
2026-09-08 M11: log de cortesía en RateLimiter
2026-09-06 M10: primera corrida real contra la UAM
```

La UJAT se descargó el **08**, no el 06 como decía la v7. Y entre M10 y M13 la UAM se volvió a
descargar, en una corrida que **nunca se registró en este documento**: E11 solo habla de la del
06.

### E13.2 · Los 45 documentos de la UAM están duplicados en disco

```
find data/norm -type f -printf '%TF %h\n' | sort | uniq -c
     45 2026-09-06 data/norm/uam
     45 2026-09-08 data/norm/uam
    105 2026-09-08 data/norm/ujat

find data/norm/uam -type f -exec sha256sum {} + | awk '{print $1}' | sort | uniq -d | wc -l
45
```

**Los 45 hashes están repetidos.** No son documentos distintos ni versiones nuevas: son los
mismos bytes dos veces. El corpus de la UAM en disco no son 45 archivos, son **90**.

```
data/norm/uam/ceuam__2026-09-06.pdf
data/norm/uam/ceuam__2026-09-08.pdf
```

### E13.3 · Por qué pasó: la fecha de captura entra en el nombre

La ruta es `<doc_slug>__<AAAA-MM-DD>.<ext>`, donde la fecha es la de **versión** del documento
— y, **cuando el índice no la declara, la de captura** (`01`, §Nombres de archivo). El índice de
la UAM declara vigencia solo en sus históricos (C2), así que la mayoría de sus documentos se
nombró con la fecha del día.

Correr dos días distintos produce, por tanto, **dos nombres para el mismo documento**. La regla
de no sobrescribir jamás (criterio 4 de `05`) hizo exactamente lo que debía: conservó ambos.

**El criterio 4 se cumplió y aun así el resultado está mal.** Lo que la suite prueba es
idempotencia *dentro de una corrida*; entre corridas de días distintos no hay ninguna prueba, y
resulta que tampoco había diseño. **Es un defecto de la especificación, no de la
implementación**, y por eso se registra aquí y no como bug.

### E13.4 · Primera evidencia medida a favor del alias por hash

El alias por hash (D15 de `00`, `01` v2.1, `05` v3) se decidió el 2026-09-10 razonando sobre las
reconsolidaciones de la UAM, que matan todas sus URLs a la vez. **Hasta ahora no tenía un solo
dato detrás.** Ahora tiene 45 pares medidos: comparar el SHA-256 dentro del `grupo_alias` antes
de escribir habría reconocido los 45 y no habría duplicado nada.

**Es una validación parcial, no completa:** aquí los duplicados vienen de correr dos veces el
mismo índice, no de una reconsolidación real. El caso que motivó la decisión —URLs nuevas para
los mismos bytes— sigue sin medirse en campo.

### E13.5 · Los slugs confirman en disco lo que E11.6 dijo en teoría

Entre los nombres aparecen `2026__2026-09-06.pdf`, `24.03.2025__2026-09-06.pdf` y
`25.02.2026__2026-09-08.pdf`: **fechas usadas como nombre del instrumento**. Es la heurística
provisional que E11.6 ya había señalado, ahora visible en el corpus. Confirma que estos nombres
son desechables y que la base se rehace, no se migra (`01`, §Migración).

### E13.6 · Qué cambia para la migración

1. **`data/` se vacía antes de la corrida de verificación**, no solo la base. Si no, el criterio
   11 de `05` (156/156 en base limpia, `01` v2.4) mediría contra un disco que ya trae 195 archivos.
2. **El criterio 4 de `05` necesita un segundo nivel:** dos corridas del mismo índice en días
   distintos producen los mismos 45 archivos, no 90. Se cubre con el alias por hash (criterio 16
   de `05` v3), que ahora tiene un caso real que reproducir.
3. **Falta medir la base** (E6.20): esta auditoría miró el disco. Si `legisuni.db` tiene 195
   filas en vez de 150, la duplicación también quedó persistida.

### E13.7 · Nota de método: el disco es evidencia

Las dos corridas se dieron por buenas con sus resúmenes —45/45 y 105/105— y ambos eran ciertos.
Ninguno era falso; lo que faltaba era mirar el estado acumulado después. **Un resumen por
corrida no ve lo que pasa entre corridas.** El hallazgo salió de tres comandos sobre el
sistema de archivos, y solo porque una fecha no cuadraba con otra.

---

## E14 · Corrida de migración (2026-09-18)

**Es la corrida de verificación que E13.6 pedía:** UAM y UJAT descargadas otra vez, ahora a
través de `Encargo`, sobre disco y base vacíos. Todo lo que sigue sale de los comandos que se
muestran; no hay otra medición.

### E14.1 · Punto de partida: disco y base vacíos

`data/` y la base se vaciaron **antes** de correr (E13.6, punto 1). La base consultada es
`legisuni_v2.db`. Sin eso, el 156 se habría medido contra un disco que ya traía archivos, que es
justo lo que E13.6 quería evitar. Consecuencia verificable abajo: **todos** los archivos llevan
la fecha de esta corrida.

### E14.2 · 156 archivos, 156 filas, cero fallos

```
find data/norm -type f | wc -l
156
find data/norm/uam -type f | wc -l; find data/norm/ujat -type f | wc -l
47
109
find data/norm -type f -printf '%TF %h\n' | sort | uniq -c
     47 2026-09-18 data/norm/uam
    109 2026-09-18 data/norm/ujat

sqlite3 legisuni_v2.db "select count(*) from descargas; select count(*) from documentos; select count(*) from intentos;"
156
156
156

sqlite3 legisuni_v2.db "select exito, motivo_fallo, count(*) from descargas group by 1,2;"
1||156
```

Resúmenes que imprimieron los dos scripts:

```
Resultado para uam:    total: 47    exitosas: 47    omitidos: 0
Resultado para ujat:   total: 109   exitosas: 109   omitidos: 0
```

El disco, `descargas`, `documentos` e `intentos` dan **156** cada uno. Los 156 archivos llevan
una sola fecha, 2026-09-18. Las 156 filas de `descargas` tienen `exito=1` y `motivo_fallo`
vacío: **cero fallos, cero omitidos.**

156 es el denominador que fijó `01` v2.4 (UAM 47, UJAT 109), no el 150 de E11 y E12: aquella
cifra la había recortado la heurística de slug de v1. Esta corrida es la primera que se mide
contra el denominador correcto.

### E14.3 · 156 hashes distintos

```
sqlite3 legisuni_v2.db "select count(distinct sha256) from descargas;"
156
```

Ningún par de encargos produjo los mismos bytes. Es el contrapunto de E13.2, donde 45 hashes
estaban repetidos y el corpus de la UAM eran 90 archivos en vez de 45.

**Es una validación parcial:** una sola corrida, en un solo día, sobre base vacía. No ejercita
lo que C24 pide —dos corridas en días distintos— ni el caso de URLs nuevas para los mismos
bytes (E13.4). El alias por hash sigue sin caso real en campo.

### E14.4 · El RES en tres identificadores distintos — C20 cerrado con datos

```
sqlite3 legisuni_v2.db "select encargo_id, ruta_local from descargas where encargo_id like 'uam:res:%';"
uam:res:c4ab5a26a57f|data/norm/uam/res__2026-09-18.pdf

sqlite3 legisuni_v2.db "select encargo_id, url from intentos where lower(url) like '%res%' or lower(url) like '%estudios-superiores%';"
uam:res:c4ab5a26a57f|legislacion-uam-julio-24-2026/legislacion-uam-julio-24-2026-res.pdf
uam:16.03.2026:3d4725469ba9|legis-uam-arch/legis-univ-uam-res-VIGENTE-HASTA-16.03.2026.pdf
uam:04.11.2024:e21bc5a32f71|legis-uam-arch/leg-univ-uam-res-VIGENTE-HASTA-04.11.2024.pdf
```

*(El filtro `%res%` también atrapó 10 filas de la UJAT —«egresados», «representativos»,
«presupuestarias»…—; se omiten aquí.)*

El Reglamento de Estudios Superiores tiene **tres** publicaciones en el índice de la UAM: la
vigente y los dos históricos que E11.6 señaló. Cada una tiene su propio `encargo_id`, y los tres
difieren también en el tercer segmento (`c4ab5a26a57f`, `3d4725469ba9`, `e21bc5a32f71`). Los
nombres `04.11.2024__2026-09-18.pdf` y `16.03.2026__2026-09-18.pdf`, que aparecen en el
directorio de la UAM, coinciden con los slugs de los dos históricos.

**C20 queda cerrado con datos.** Pasa de decisión de contrato (`01` v2.0, D15) a comportamiento
medido en campo: los dos históricos que en E11.6 colisionaban ya no colisionan, y la corrida no
perdió ninguno de los tres.

### E14.5 · Siete slugs con forma de fecha en la UAM — E13.5 sigue abierta

```
sqlite3 legisuni_v2.db "select encargo_id from descargas where encargo_id like 'uam:%' order by 1;" | grep -c "^uam:[0-9][0-9]\."
7

ls data/norm/uam | head -3
04.11.2024__2026-09-18.pdf
16.03.2026__2026-09-18.pdf
20.07.2026__2026-09-18.pdf
```

**Siete `encargo_id` de la UAM tienen como slug una fecha**; dos de ellos son los históricos del
RES (E14.4). Es la heurística provisional que E11.6 señaló y E13.5 vio en disco, **y la
migración no la tocó**: los slugs los produce el Lector de Índice, no el Descargador.
**E13.5 sigue abierta y es del Lector.** El patrón cuenta solo los slugs que empiezan con dos
dígitos y un punto; no cubre otras formas de fecha como el `2026__` que E13.5 también citó.

### E14.6 · Tres `.docx`

```
ls data/norm/uam | grep -c docx
3
ls data/norm/ujat | grep -c docx
0
```

Los tres `.docx` están en la UAM y ninguno en la UJAT. El conteo coincide con los tres anexos
de E1.6 que ya habían pasado el guardián de dos firmas en E11.4; esta corrida cuenta archivos
por extensión y no verifica cuáles son.

### E14.7 · Unicidad de `encargo_id`, medida

```
sqlite3 -readonly legisuni_v2.db "select count(*), count(distinct encargo_id) from descargas;"
156|156
```

156 filas y 156 `encargo_id` distintos en `descargas`: **ningún identificador se repite** en
la base limpia. Es una consulta de solo lectura, hecha después de las de E14.2 a E14.6.

**Lo que esto no mide:** los pares de la UAM con slug idéntico (`2026`, `rjd`) que se separan
solo por `url_id` **no** están respaldados por ninguna medición sobre la base. Su respaldo es
`tests/test_extraccion_indices.py` y M23b del plan (`docs/PLAN-MIGRACION.md`).

---

## E15 · Primera corrida académica (2026-09-25)

**Es la medición del criterio 18 de `05`:** la primera vez que el modo académico pide artículos
a servidores reales. Entrada: `datos/encargos_bloque_a.json` (M30), lote
`bloque-a-txt-71bdfaf1`. Todo lo que sigue sale del log de `scripts/lote.py` y de las cinco
consultas que se muestran; no hay otra medición. Donde el texto **interpreta** el log, lo dice.

### E15.1 · Qué se corrió: 3 de 7

```
.venv/bin/python scripts/lote.py 2>&1 | tee ~/respaldo-acervo/m31-bloque-a.log
…
--- resumen ---
total: 7
exitosas: 3
  puertas_agotadas: 3
  http_error: 1
sin puertas (no se piden): 1

find data/papers -type f | wc -l
3

sqlite3 legisuni_v2.db "select count(*) from descargas where modo='academico';"
7
sqlite3 legisuni_v2.db "select count(*) from descargas;"
163
```

Siete encargos, **16 puertas declaradas** en el JSON y **12 pedidas**: las que no se pidieron
quedaban detrás de una puerta que ya había entregado. La octava ficha, A.5 (Hallam & Wignall
1997, monografía), no tiene puertas y no se pidió (`no_obtenidos`, motivo `sin_puertas`).
El log toca **13 hosts distintos**. La corrida fue en serie y duró 13.3 s (02:40:45.108 →
02:40:58.456).

**3 de 7 exitosas, 3 archivos en `data/papers`.** La base es `legisuni_v2.db`, la misma de E14:
163 filas en `descargas`, 7 académicas. 163 − 7 = 156, el conteo jurídico de E14.2. **Lo que
esto no mide:** que las 156 filas jurídicas sigan intactas; solo que su número no cambió.

### E15.2 · Las tres que funcionaron: puerta 0, `copia_libre`

```
sqlite3 legisuni_v2.db "select encargo_id, exito, motivo_fallo, puerta_usada from descargas where modo='academico' order by encargo_id;"
doi:10.1017/ext.2022.4|1||0
doi:10.1126/science.215.4539.1501|1||0
ref:alroy-2008-617afec9|1||0

ls -la data/papers/
-rw-r--r-- 1 mock_ mock_  891577 Sep 25 02:40 alroy-2008__6dd8a57c.pdf
-rw-r--r-- 1 mock_ mock_ 1016676 Sep 25 02:40 marshall-2023__a830b299.pdf
-rw-r--r-- 1 mock_ mock_  905589 Sep 25 02:40 raup-1982__1fd5f147.pdf
```

*(De la primera consulta se muestran solo las tres filas exitosas.)*

| Encargo | Lista | Puerta 0 (`copia_libre`) |
|---|---|---|
| `doi:10.1126/science.215.4539.1501` | A.1 | `coleoguy.github.io/…/Raup_Sepkoski_1982.pdf` |
| `ref:alroy-2008-617afec9` | A.3S | `geosci.uchicago.edu/~foote/REPRINTS/SCI2008.SOM.pdf` |
| `doi:10.1017/ext.2022.4` | A.7 | `pdfs.semanticscholar.org/581f/….pdf` |

Las tres entregaron un PDF directo en la **primera** puerta, las tres de tipo `copia_libre`
según el JSON, con una sola petición cada una aparte del `robots.txt`.

**Interpretación:** el orden de `01` (línea 776: copias libres, luego la oficial, al final el
resolutor) **acertó en los tres casos**, en el sentido de que la primera puerta pedida fue la
que entregó. No dice qué habría pasado con las demás. En A.7 la oficial es un PDF abierto de
Cambridge (hallazgo de M30) y **no se pidió**, así que la corrida no aporta nada a la pregunta
abierta 5 de `01`.

### E15.3 · `muro_de_pago` no se emitió ni una vez, y Nature es un muro

```
sqlite3 legisuni_v2.db "select i.encargo_id, i.orden, i.exito, i.motivo_fallo, i.http_status, substr(i.url,1,60), i.enlace_vestibulo from intentos i join descargas d using(encargo_id) where d.modo='academico' order by i.encargo_id, i.orden;"
…
doi:10.1038/nature09678|0|0|vestibulo_sin_pdf|200|https://www.nature.com/articles/nature09678|https://www.nature.com/articles/nature09678.pdf
doi:10.1038/nature09678|1|0|vestibulo_sin_pdf|200|https://doi.org/10.1038/nature09678|https://www.nature.com/articles/nature09678.pdf
…
```

Ninguno de los 12 intentos ni de las 7 descargas lleva `muro_de_pago`. La puerta 0 de A.6
(`oficial`, Nature), en el log:

```
GET https://www.nature.com/articles/nature09678 "HTTP/1.1 303 See Other"
GET https://idp.nature.com/authorize?response_type=cookie&client_id=grover&redirect_uri=https%3A%2F%2Fwww.nature.com%2Farticles%2Fnature09678 "HTTP/1.1 302 Found"
GET https://idp.nature.com/transit?redirect_uri=https%3A%2F%2Fwww.nature.com%2Farticles%2Fnature09678&code=… "HTTP/1.1 302 Found"
GET https://www.nature.com/articles/nature09678 "HTTP/1.1 200 OK"
GET https://www.nature.com/articles/nature09678.pdf "HTTP/1.1 303 See Other"
GET https://www.nature.com/articles/nature09678 "HTTP/1.1 200 OK"
```

**Medido:** la puerta devolvió HTML con `200`. M28 extrajo un enlace
(`enlace_vestibulo = …/nature09678.pdf`) y saltó. El salto respondió `303` de vuelta a la página
del artículo, otra vez HTML con `200` → `vestibulo_sin_pdf`. Por el camino la cadena de
redirecciones de la puerta pasó por `idp.nature.com/authorize` y `idp.nature.com/transit`.

**Medido en el código:** `muros.es_muro_de_pago(status, url_final)` recibe solo el status y la
URL **final** de la cadena, que aquí era la página del artículo con `200`. Las URLs intermedias
no le llegan. El log no dice cuál de las tres reglas de `vestibulo.extraer_enlace` produjo el
enlace; la primera en prioridad es `citation_pdf_url`.

**Interpretación, no comprobación:** que `idp.nature.com/authorize` sea un proveedor de
identidad y que A.6 esté detrás de un muro es una **lectura del log**. Nadie comprobó en esta
corrida qué pide ese endpoint ni si el artículo es de pago. La lectura se apoya en dos cosas:
el nombre y los parámetros del endpoint (`response_type=cookie`, `redirect_uri` de vuelta al
artículo) y que la URL del PDF redirija a la página del artículo en vez de servirlo.

**`patrones.toml` no falló: no llegó a mirar donde estaba la evidencia.** Sus dos patrones
(`/Shibboleth.sso/`, `/cas/login`) se evalúan contra `url_final`, y la señal estaba en un salto
intermedio. Tampoco habría coincidido si la hubiera visto: la ruta es `/authorize`, que no es
ninguno de los dos. Queda como **motivo de una micro-tarea futura**; E15 no propone el arreglo.

**Lectura revisada (2026-09-26, M32).** La interpretación de arriba se revisó **con el mismo
log**, sin medición nueva. La puerta 1 de A.6 acabó en la misma página del artículo 1.4 s
después y **no pasó por `idp.nature.com`** (E15.6: `doi.org` `302` → artículo `200`). Tampoco
pasó por él ninguno de los dos saltos al PDF. Si el IdP fuera el muro, la puerta 1 lo habría
atravesado. La lectura corregida es que `idp.nature.com/authorize?response_type=cookie` es un
intercambio de cookie de sesión en la primera visita al host, no una señal de muro. Un patrón
sobre esa ruta haría depender el diagnóstico de las cookies del cliente. M32 hizo que los
patrones se evalúen contra toda la cadena de redirecciones y **no añadió ningún patrón**.
**La señal candidata es otra:** el enlace del PDF (`…/nature09678.pdf`) redirige (`303`) a la
página del artículo en vez de servir el archivo. **No está implementada y no tiene criterio en
`05`.** A.6 sigue siendo `vestibulo_sin_pdf`. Ningún número de E15 cambia.

### E15.4 · Cuatro hosts con 403: bloqueo anti-bot, no muro

```
doi:10.1016/j.palaeo.2016.11.005|0|0|http_error|403|https://hull-repository.worktribe.com/OutputFile/445196|
doi:10.1016/j.palaeo.2016.11.005|1|0|http_error|403|https://hull-repository.worktribe.com/output/445171/on-the-c|
doi:10.1016/j.palaeo.2016.11.005|2|0|http_error|403|https://www.sciencedirect.com/science/article/pii/S003101821|
doi:10.1126/science.1156963|0|0|http_error|403|https://doi.org/10.1126/science.1156963|
doi:10.1146/annurev.earth.33.092203.122654|0|0|http_error|403|https://www.annualreviews.org/content/journals/10.1146/annur|
doi:10.1146/annurev.earth.33.092203.122654|1|0|http_error|403|https://doi.org/10.1146/annurev.earth.33.092203.122654|
```

Seis intentos con `403`, en cuatro hosts: `www.annualreviews.org` (A.2, dos puertas: la
directa y la del resolutor acaban ahí), `www.science.org` (A.3, tras el `302` de `doi.org`),
`www.sciencedirect.com` y `hull-repository.worktribe.com` (A.4). Todos quedaron en
`http_error`. A.3 tenía una sola puerta y por eso su descarga termina en `http_error` y no en
`puertas_agotadas`.

Lo que el log dice del `robots.txt` de esos hosts no es lo mismo en los cuatro:

```
GET https://www.annualreviews.org/robots.txt "HTTP/1.1 200 OK"
GET https://www.annualreviews.org/content/journals/10.1146/… "HTTP/1.1 403 Forbidden"

GET https://hull-repository.worktribe.com/robots.txt "HTTP/1.1 403 Forbidden"
GET https://www.sciencedirect.com/robots.txt "HTTP/1.1 403 Forbidden"
```

- **Annual Reviews:** el mismo cliente, con el mismo User-Agent, recibió `robots.txt` con `200`
  y el artículo con `403`, con 80 ms de diferencia.
- **Hull y ScienceDirect:** `403` también en `robots.txt` (E15.7). El host rechaza al cliente
  entero, no solo el artículo.
- **Science:** el log no pide `robots.txt` de `www.science.org`. La puerta era `doi.org` y
  `www.science.org` solo aparece como destino de su redirección.

**Interpretación:** en ninguno de los cuatro hay señal de muro, es decir, ni `401`/`402` ni
redirección a un login. El patrón es el de un bloqueo al cliente: selectivo en Annual Reviews,
general en Hull y ScienceDirect, y sin datos de contraste en Science. **La regla conservadora
de M27 (`403` ≠ muro) aguantó:** el cliente ni siquiera llegó a ver la página en ninguno de
los cuatro hosts, y llamarlos `muro_de_pago` habría sido un diagnóstico falso. Es el primer
dato para la pregunta 8 de `05`: seis `http_error` que no distinguen la causa.

### E15.5 · Un `[PDF]` verificado el 2026-09-10 ya no servía el 25

```
grep -n "VERIFICADOS\|445196" datos/lotes/bloque-a.txt
2:# ENLACES VERIFICADOS EL: 2026-09-10
87:[PDF] https://hull-repository.worktribe.com/OutputFile/445196

GET https://hull-repository.worktribe.com/OutputFile/445196 "HTTP/1.1 403 Forbidden"
```

La lista marca ese enlace como `[PDF]` verificado el 2026-09-10. El 2026-09-25 respondió `403`:
**de PDF a `403` en quince días.** Era la puerta 0 de A.4, la copia libre que el orden de `01`
pone primero.

**Lo que esto no distingue:** si el archivo cambió o si cambió el trato al cliente. Como el
`robots.txt` del mismo host también dio `403` (E15.4), lo segundo es posible, pero no está
medido. Lo medido es el efecto sobre la corrida: una verificación de hace dos semanas no
garantizó el enlace.

### E15.6 · Vestíbulo en campo: primera vez que se ejercita

Hasta esta corrida el cruce de vestíbulo (M28) solo existía en tests. Tres intentos llegaron a
HTML y los tres terminaron en `vestibulo_sin_pdf`:

| Intento | Enlace extraído | Salto | Resultado |
|---|---|---|---|
| A.4 puerta 3 (`doi.org` → `linkinghub.elsevier.com`, `200`) | ninguno | no | `vestibulo_sin_pdf` |
| A.6 puerta 0 (`oficial`) | `…/nature09678.pdf` | `303` → HTML | `vestibulo_sin_pdf` |
| A.6 puerta 1 (`resolutor_doi`) | `…/nature09678.pdf` | `303` → HTML | `vestibulo_sin_pdf` |

**Cero vestíbulos cruzados con éxito.** En A.6 la puerta oficial y el resolutor DOI acaban en
la misma página, `www.nature.com/articles/nature09678`, y se pidió **dos veces, con su
vestíbulo cada una**:

```
02:40:52.941 GET https://www.nature.com/articles/nature09678 "303 See Other"      ← puerta 0
02:40:53.354 GET https://idp.nature.com/authorize?… "302 Found"
02:40:53.584 GET https://idp.nature.com/transit?… "302 Found"
02:40:54.148 GET https://www.nature.com/articles/nature09678 "200 OK"
02:40:54.666 GET https://www.nature.com/articles/nature09678.pdf "303 See Other"  ← salto
02:40:55.206 GET https://www.nature.com/articles/nature09678 "200 OK"
02:40:55.527 GET https://doi.org/10.1038/nature09678 "302 Found"                  ← puerta 1
02:40:55.964 GET https://www.nature.com/articles/nature09678 "200 OK"
02:40:56.513 GET https://www.nature.com/articles/nature09678.pdf "303 See Other"  ← salto
02:40:56.992 GET https://www.nature.com/articles/nature09678 "200 OK"
```

Cuatro peticiones del Fetcher (dos puertas y dos saltos), **diez respuestas HTTP** contando
redirecciones, más el `robots.txt` de `www.nature.com`, para un artículo que no se obtuvo. La
segunda vuelta repite la misma página y el mismo salto. **Candidato a deduplicar puertas por
destino.** A.2 muestra lo mismo sin vestíbulo: la oficial y el resolutor terminan en
`www.annualreviews.org` y ambos dan `403` (E15.4).

**Lo que esto no mide:** la pregunta 10 de `05` (vestíbulos perdidos por tener dos `<a>` a
`.pdf`). En A.4 no se extrajo enlace, y `intentos` no distingue «no había enlace» de «había
dos».

### E15.7 · Fail-open de `robots.txt`, en campo por segunda vez

```
GET https://hull-repository.worktribe.com/robots.txt "HTTP/1.1 403 Forbidden"
WARNING legisuni.descargador.robots: status inesperado 403 al pedir https://hull-repository.worktribe.com/robots.txt; fail-open (permitido)
GET https://www.sciencedirect.com/robots.txt "HTTP/1.1 403 Forbidden"
WARNING legisuni.descargador.robots: status inesperado 403 al pedir https://www.sciencedirect.com/robots.txt; fail-open (permitido)
```

Dos hosts respondieron `403` a `robots.txt` y la corrida continuó, como manda E11.1 (C17).
Ninguno de los dos entregó después el archivo, así que aquí el fail-open no salvó ningún
documento. Lo que muestra es que el `403` de la UAM no es un caso único (E6.13).
**Cero `robots_prohibido`** en la corrida.

### E15.8 · Las redirecciones no pasan por `robots.txt`

```
02:40:48.314 GET https://doi.org/10.1126/science.1156963 "302 Found"
02:40:48.693 GET https://www.science.org/doi/10.1126/science.1156963 "403 Forbidden"

02:40:51.781 GET https://doi.org/10.1016/j.palaeo.2016.11.005 "302 Found"
02:40:52.194 GET https://linkinghub.elsevier.com/retrieve/pii/S0031018216306915 "200 "

02:40:52.674 GET https://www.nature.com/robots.txt "200 OK"
02:40:52.941 GET https://www.nature.com/articles/nature09678 "303 See Other"
02:40:53.354 GET https://idp.nature.com/authorize?… "302 Found"
02:40:53.584 GET https://idp.nature.com/transit?… "302 Found"
```

*(El `robots.txt` de `doi.org` se pidió una sola vez, a las 02:40:46.903, en la puerta 1 de
A.2, y desde entonces sale de la caché.)*

**Medido en esta corrida:** `www.science.org`, `linkinghub.elsevier.com` e `idp.nature.com`
se visitaron **sin que se pidiera su `robots.txt`**. El log no tiene ninguna petición a
`/robots.txt` de esos tres hosts. Los tres aparecen solo como destinos de una redirección.

**Medido en el código:** `puertas.probar_puertas` consulta `robots.permitido` con la URL de la
puerta, y `_cruzar_vestibulo` con la del enlace del salto. `Fetcher._intentar` pide con
`follow_redirects=True`, así que `httpx` sigue la cadena sin volver a pasar por robots.

**Queda abierto si es un fallo o un hueco de la spec.** La pregunta 7 de `05` ratificó «la
misma política que el modo jurídico, aplicada también al enlace del vestíbulo». No dice nada de
los destinos de una redirección. E15.8 no propone arreglo.

## E16 · Idempotencia en campo (2026-09-23)

Segunda corrida de la UAM sobre los mismos fixtures, **cinco días después de E14**, con la base
`legisuni_v2.db` de E14. Es anterior a E15 en el tiempo; se registra aquí porque no se anotó
cuando se hizo.

```
$ .venv/bin/python scripts/cosecha_uam.py --html fixtures/uam-index.html \
    --url-indice https://www.uam.mx/legislacion/index.html
[...]
--- resumen ---
total: 47
exitosas: 47
omitidos: 47

$ find data/norm/uam -type f | wc -l
47
$ sqlite3 legisuni_v2.db "select count(*) from descargas; select count(*) from intentos;"
156
156
```

**Medido:** los 47 encargos de la UAM ya estaban registrados y los 47 salieron como omitidos.
El disco sigue con 47 archivos de la UAM y las tablas con 156 filas cada una, los mismos
números que dejó E14.2. Ninguno se volvió a pedir ni a escribir: el disco y las tablas quedaron
intactos.

**Es la primera medición en campo de la regla 5 de `05`** (idempotencia de red, M21). **Y es
el primer dato sobre C24:** una segunda corrida en otro día no duplicó la UAM en disco, al
contrario que en E13.2.

**El resumen cuenta los omitidos también como exitosas.** `exitosas: 47` y `omitidos: 47` con
`total: 47`: las categorías no son disjuntas. Es lo que motiva M33.

## E17 · Una omisión pisó 47 filas (2026-09-26)

Una corrida de verificación del 26 de septiembre, sin red y sobre los mismos fixtures, reescribió
las 47 filas de la UAM en `descargas`: `bytes`, `content_type`, `http_status`, `url_final` y
`puerta_usada` quedaron en NULL, y `capturado_en` = 2026-09-26 en las 47 filas. **El valor
anterior de `capturado_en` no se conserva en la base.** Que fuera 2026-09-18 se deduce de E14;
no está medido.

```
$ sqlite3 -readonly legisuni_v2.db "SELECT COUNT(*) FROM descargas WHERE encargo_id LIKE 'uam:%' AND exito=1 AND bytes IS NULL;"
47
$ sqlite3 -readonly legisuni_v2.db "SELECT COUNT(*) FROM descargas WHERE encargo_id LIKE 'uam:%' AND exito=1 AND content_type IS NULL;"
47
$ sqlite3 -readonly legisuni_v2.db "SELECT modo, COUNT(*) FROM descargas WHERE exito=1 AND bytes IS NULL GROUP BY modo;"
juridico|47
$ sqlite3 -readonly legisuni_v2.db "SELECT COUNT(*) FROM descargas WHERE duplicado_de IS NOT NULL;"
0
$ sqlite3 -readonly legisuni_v2.db "SELECT encargo_id, bytes, http_status, substr(capturado_en,1,10) FROM descargas WHERE encargo_id LIKE 'uam:%' LIMIT 3;"
uam:2026:c24626739b6f|||2026-09-26
uam:lo:315cd99e5cb9|||2026-09-26
uam:ro:2225840dbe72|||2026-09-26
```

**Causa:** los scripts llamaban a `guardar_descarga` también con el resultado de una omisión,
que no trae esos campos, y el upsert sobre `(encargo_id, sha256)` los sobrescribió.

**El daño empezó el 23.** El código de E16 (2026-09-23) ya persistía el resultado de la
omisión: `guardar` y `guardar_descarga` sin condición en `cosecha_uam.py` desde M23c, visto en
git. La corrida del 26 lo repitió. Por eso el `capturado_en` que se mide es el del 26.

**Alcance medido:** 47 filas, solo modo jurídico. La UJAT y las 7 académicas, intactas. Cero
alias en la base, así que el riesgo de borrar `duplicado_de` no se materializó. `documentos`
sufrió el mismo daño y no se repara.

**`content_type` es pérdida definitiva:** `intentos` no guarda esa columna, y deducirla de la
extensión sería inventar la cabecera del servidor.

**Lo demás es recuperable** desde `intentos` y desde los archivos en disco (M35b, pendiente).
**`capturado_en` no es reparable con certeza:** la fecha de modificación de un archivo es cuándo
se escribió el archivo, no cuándo se capturó la respuesta. Sirve como estimación, y M35b tiene
que declararla como tal.

**Arreglado en M35:** una omisión ya no escribe nada.

**Los números de E14 y E16 no cambian:** describen lo medido entonces, y lo medido fue correcto.
Lo que cambió después es la base.

**Nota sobre E16 (2026-09-26).** E16 dice que ninguno de los 47 se volvió a pedir **ni a
escribir** y que «el disco y las tablas quedaron intactos». Lo medido fue el número de archivos y
de filas (47 y 156), y esos números son correctos. Que las filas quedaran intactas no se midió, y
con el código del 23 no pudo ser cierto: la corrida reescribió los campos de las 47 filas. E16 se
conserva tal como se escribió.

## E18 · Reparación de las 47 filas (2026-09-26)

`scripts/reparar_omisiones.py` (M35b) reparó las 47 filas de E17 en una transacción:
**47 afectadas, 47 reparables, 0 intactas.** Antes se hizo una copia en
`~/respaldo-acervo/legisuni_v2.antes-M35b.db`, fuera del repo.

**Fuentes:** `url_final` y `http_status` salen de `intentos`. `bytes` es el tamaño del archivo,
con el SHA-256 verificado contra la fila. `puerta_usada = 0`, comprobado contra el `orden` del
intento.

**`capturado_en` es una estimación** (fecha de modificación del archivo). Las 47 caen el
2026-09-18, en secuencia de 13:57:31 a 13:58:14, unos 43 segundos. La fecha y la secuencia
respaldan que son los archivos de E14.

**`content_type` sigue en NULL en las 47:** pérdida definitiva (E17).

**Verificación posterior:** 0 filas con `bytes` en NULL. `descargas` sigue con 163 filas e
`intentos` con 168, sin cambios. 168 = 156 jurídicos + 12 puertas pedidas por las 7 fichas del
Bloque A (E15.1).

### E18.1 · Anomalía abierta: 43 s es menos que el mínimo del rate limit

Con `rate_limit_s = 1.0` (el valor por defecto de `legisuni/config.py`), 47 peticiones seguidas
a un mismo host están separadas, entre la primera y la última, por **al menos 46 s**. Entre el
primer archivo y el último se observan **43 s**. No es una confirmación del rate limit: es una
discrepancia.

Dos cosas impiden cerrarla:
- **`rate_limit_s` no se registró en E14.** El 1.0 es el valor por defecto, no el valor medido
  de esa corrida.
- **`capturado_en` marca cuándo se escribió el archivo, no cuándo se recibió la respuesta.** La
  distancia observada no es la distancia entre peticiones.

Hay tres explicaciones posibles, y una cuarta desde E19.7. **Ninguna está medida:**
1. La primera respuesta tardó al menos 3 s más que la última.
2. `rate_limit_s` era menor que 1 en esa corrida.
3. Los 47 no fueron a un mismo host.
4. *(Hipótesis nueva, 2026-09-27, E19.7; no medida.)* El reloj del sistema retrocedió durante la
   corrida (WSL ajustando la hora): los 43 s medidos podrían ser 46 s reales.

**Pendiente:** que el informe de las corridas futuras registre `rate_limit_s` y el host, para
que esto sea medible. No está implementado.

> **Nota (2026-09-27) — pendiente cubierto desde M36.1.** El resumen de `cosecha.py`,
> `cosecha_uam.py` y `lote.py` imprime ahora `rate_limit_s`, `user_agent` y
> `hosts distintos pedidos`. **Salvedad:** el conteo de hosts sale de la URL pedida de cada
> puerta y **no incluye** los hosts de las redirecciones ni el del salto de vestíbulo. La
> anomalía sigue abierta: E14 no se puede re-medir, y hará falta una corrida nueva para
> distinguir entre las tres explicaciones.

## E19 · Corrida del Bloque B (2026-09-27)

**Segunda medición del criterio 18 de `05`.** Entrada: `datos/encargos_bloque_b.json` (M36).
Es la primera corrida con el resumen de M36.1.

**Fuente.** El operador leyó el log de `scripts/lote.py`, el resumen de una corrida parcial
anterior y tres consultas a PMC, y resumió lo que encontró. **El log no está en el repositorio y
aquí no se cita.** A diferencia de E15, ningún número de esta sección se comprobó contra un
fragmento de log reproducido. Donde el texto interpreta, lo dice.

### E19.1 · Qué se corrió: 8 de 30

- **30 encargos, 85 puertas declaradas, 27 hosts pedidos, `rate_limit_s = 1.0`.** Los hosts
  cuentan con la salvedad de M36.1: no incluyen los de redirecciones ni los de saltos de
  vestíbulo.
- **Resultado: 8/30, más 1 omitido.** El omitido es B.12, ya descargado en la corrida parcial.
  **Es la primera idempotencia académica en campo.**
- **2 `sin_puertas`** (B.11 y B.22, monografías). No generan encargo (M36).
- **9 archivos nuevos en disco.**

### E19.2 · El control de Nature: la señal de E15.3 distingue muro de acceso abierto

E15.3 (lectura revisada en M32) dejó como señal candidata de muro que el enlace
`articles/….pdf` de Nature redirija a la página del artículo en vez de servir el archivo. Esta
corrida trae **un control positivo y uno negativo**:

- **Acceso abierto: B.16 y B.26.** `articles/….pdf` responde `200`.
- **De pago: B.20.** `articles/….pdf` responde `303` y vuelve al artículo, **igual que A.6**
  en E15.

**La señal distingue un muro de un acceso abierto** en el mismo host. **Sigue sin
implementarse** y sin criterio en `05`.

### E19.3 · PMC sirve HTML en la ruta del PDF

Cuatro fichas: **B.15, B.15C, B.16 y B.34.** En las cuatro:

1. La página de PMC responde `200` con HTML.
2. El vestíbulo (M28) encuentra el enlace al PDF y salta.
3. El salto devuelve **HTML otra vez** → `vestibulo_sin_pdf`.

**Medido:** el diagnóstico del Descargador es correcto. Hubo un solo salto, y la respuesta no
era un archivo. **Lo que falla es la fuente**, no el cruce.

**Interpretación, no medición:** parece un bloqueo anti-bot, como los `403` de E15.4, pero
servido con `200`. Si es así, es el caso que plantea la pregunta 8 de `05`: una página de
desafío que cae en `vestibulo_sin_pdf` sin que el motivo lo diga.

### E19.4 · `robots_prohibido` en campo por primera vez

La puerta 0 de **B.13** apunta al host viejo de PMC, `www.ncbi.nlm.nih.gov`, cuyo `robots.txt`
**prohíbe `/pmc/`**. Se respetó: la puerta no se pidió. **La puerta 1 (Ginebra,
`archive-ouverte.unige.ch`) descargó.**

Es la primera vez que un `robots.txt` legible prohíbe algo en una corrida real. Cierra lo que
`05` §Cortesía de red daba como «todavía NO probado en campo» (E6.15): un `robots.txt` legible
se respetó de verdad, y el encargo no se perdió porque tenía otra puerta.

### E19.5 · Un enlace muerto en un día

**B.27:** el `[PDF]` de Rutgers (`ebme.marine.rutgers.edu`) se verificó el 2026-09-26 al armar
el lote y respondió `404` el 2026-09-27. Es el mismo patrón que E15.5 (un `[PDF]` verificado
que ya no servía), ahora con un intervalo de un día.

### E19.6 · Puertas duplicadas por destino (M33): 10 veces

La regla de M33 (no volver a pedir una puerta cuyo destino ya se pidió en el mismo encargo)
**actuó 10 veces**, casi siempre con `science.org`. Es el caso de la puerta oficial y el
resolutor DOI de una misma ficha, que acaban en la misma página del editor.

### E19.7 · El reloj del sistema retrocede en el log

En el log el tiempo va hacia atrás: `01:21:44.554` → `01:21:43.605`. Hay otro caso en la corrida
parcial. **Es WSL ajustando la hora del sistema.**

**Hipótesis nueva para E18.1, no medida:** si el reloj retrocedió durante E14, los **43 s**
medidos entre el primer archivo y el último podrían ser **46 s reales** o más, y no habría
anomalía. Se añade como cuarta explicación en E18.1. Nada de esta corrida la confirma para E14.

### E19.8 · Los nueve portales CRIS: cero éxitos

M36 clasificó `copia_libre` nueve portales CRIS, sin evidencia y a revisar con M37. En esta
corrida **dieron cero éxitos.** Ninguno entregó archivo. **Dos publicaron un enlace a PDF y
devolvieron `403` al pedirlo.**

**Queda como hallazgo medido para revisar su clasificación, no como decisión tomada.** La
clasificación de M36 no cambia en esta sección.

---

| Versión | Fecha | Cambio |
|---|---|---|
| v1 | — | Solo UAM y el fallo del 70-I de la UNAM. |
| v2 | — | Se añaden UNAM-OAG y UJAT. Ocho conclusiones (C1–C8). D1 invertida, D2 suavizada. |
| v3 | 2026-09-06 | **Re-medición en vivo de la UAM.** Conteos corregidos (31 vigentes, 8 históricos — la v2 decía ~30 y 9). Cuatro hallazgos nuevos: prefijos inconsistentes en el archivo (E1.3), consolidaciones huérfanas que siguen respondiendo (E1.4), **enlace sin texto de ancla** (E1.5), cinco anexos con tres `.docx` (E1.6). Cuatro conclusiones nuevas (C9–C12). Se marca explícitamente que UNAM-OAG y UJAT **no** se re-verificaron. |
| v4 | 2026-09-06 | Se añaden **E8** (validez externa: sesgo de la muestra, qué conclusiones aguantan, prueba de falsación) y **E9** (congelar la evidencia: qué capturar como fixture y por qué corre prisa). El registro de cambios se mueve al final, donde corresponde. |
| v5 | 2026-09-06 | **Medición en vivo de la UACAM (E10)** — la estatal pequeña que E6.1 pedía. Éxito técnico, fracaso de contenido: índice HTML plano e impecable **caducado en diciembre de 2016**, declarado en una línea al pie (E10.1). Además: cuatro documentos vía Google Drive (E10.2), **segundo** enlace sin texto de ancla (E10.3), Ley Orgánica en cinco lugares con versiones divergentes (E10.4), falta el Estatuto Orgánico (E10.5), URLs sucias por segunda vez (E10.6). Cuatro conclusiones nuevas (C13–C16). **E6.1 y E6.9 cerradas**; E6.10 y E6.11 abiertas. E7 gana dos pasos de método; E8 recalibrada a cuatro instituciones y con el marcador honesto corregido a 3 de 4. |
| **v6** | **2026-09-06** | **Primera evidencia obtenida ejecutando código, no mirando páginas.** Nueva sección **E11**: corrida real del Descargador sobre la UAM, 45/45 exitosas. Siete hallazgos: `robots.txt` con 403 mientras los PDF dan 200 (E11.1, valida fail-open), rutas retiradas vivas (E11.2, refuerza C10), índice en `iso-8859-1` (E11.3), guardián de dos firmas validado sobre `.docx` reales (E11.4), escala del corpus medida (E11.5), colisión de `entry_id` entre versiones históricas (E11.6, **hueco de `01`**), y los logs de `httpx` no miden el rate limit (E11.7). Cuatro conclusiones nuevas (**C17–C20**) y cinco deudas nuevas (E6.12–E6.16). **Correcciones:** C14 citaba el contrato equivocado (`visor_de_terceros` es de `DownloadResult.motivo_fallo`, no de `OrigenFuente`) y daba por abierto un problema que `01` v1.2 ya había resuelto; E6.3 seguía diciendo 3/3 en HTML plano; C7 llevaba denominador de tres; la tabla de este registro estaba partida por un separador suelto desde la v4. |
| **v7** | **2026-09-06** | **Segunda descarga real: la UJAT, el caso sucio (E12).** 105/105 exitosas. Siete hallazgos: el índice está repartido en cinco páginas y son **105 documentos, no ~60** (E12.1); **`urlnorm` probado en campo** por primera vez, 17 URLs con espacios y una ya codificada (E12.2); los cinco `http` redirigen solos y **cierra la pregunta abierta 4 de `05`** a favor del TLS estricto (E12.3); las rutas de 2012 siguen vivas, **E6.7 cerrada** (E12.4); **24 de 105 documentos son escaneos sin texto**, 179 MB, contra 0 de 42 en la UAM (E12.5); la escala del corpus estaba mal estimada por 23× (E12.6); el percent-encoding se cuela en los slugs derivados (E12.7). **C19 corregida** — la extrapolación de 500 MB era falsa. Tres conclusiones nuevas (**C21–C23**) y tres deudas nuevas (E6.17–E6.19). Se corrige además una inferencia previa: el Reglamento de la Junta de Gobierno **no** era un escaneo; se dedujo del tamaño en vez de medirlo. **Con esto la spec `05` queda cerrada: diez de diez criterios de aceptación cumplidos, 150 documentos de dos universidades, 150/150.** |
| **v8** | **2026-09-10** | **Auditoría de disco previa a la migración (E13).** No es una corrida nueva: es lo que apareció al inventariar el repo. Cinco hallazgos: hubo **dos corridas de la UAM**, el 06 y el 08, y la segunda nunca se registró (E13.1); **los 45 documentos de la UAM están duplicados en disco**, 45 hashes repetidos, 90 archivos (E13.2); la causa es la fecha de captura en el nombre cuando el índice no declara versión, así que **la idempotencia no cruza días** (E13.3); es la **primera evidencia medida a favor del alias por hash** (E13.4); y los slugs con forma de fecha confirman en disco lo que E11.6 anticipó (E13.5). Una conclusión nueva (**C24**) y dos deudas nuevas (E6.20, E6.21). **Corrección:** la corrida de la UJAT fue el **2026-09-08**, no el 2026-09-06 como decía la v7 en la cabecera y en el título de E12. Consecuencia para la migración: `data/` se vacía antes de verificar el criterio 11 de `05` (E13.6). |
| **v9** | **2026-09-18** | **Corrida de migración (E14): UAM y UJAT a través de `Encargo`, sobre disco y base vacíos (E13.6).** **156/156**: 156 archivos con fecha 2026-09-18 (UAM 47, UJAT 109), 156 filas en `descargas`, `documentos` e `intentos`, cero fallos y cero omitidos (E14.2); 156 hashes distintos, aunque en una sola corrida, así que el alias por hash sigue sin caso real entre días (E14.3). **El Reglamento de Estudios Superiores aparece con tres `encargo_id` distintos: C20 cerrado con datos** (E14.4). **7 slugs con forma de fecha en la UAM: E13.5 sigue abierta, es del Lector** (E14.5). 3 `.docx`, todos en la UAM (E14.6). Ninguna conclusión ni deuda nueva. |
| **v10** | **2026-09-25** | **Primera corrida académica (E15): 7 encargos del lote `bloque-a-txt-71bdfaf1`, 3/7.** 16 puertas declaradas, 12 pedidas, 13 hosts; base `legisuni_v2.db` con 163 filas, 7 académicas y las 156 jurídicas de E14 en número (E15.1). **Las tres exitosas, en la puerta 0 y `copia_libre`**; la oficial abierta de A.7 no se pidió (E15.2). **`muro_de_pago` no se emitió ni una vez, y Nature es un muro:** en A.6 la cadena de redirecciones pasó por `idp.nature.com/authorize`, pero `es_muro_de_pago` solo ve la URL final; queda como motivo de una micro-tarea futura. Que sea un IdP es lectura del log, no comprobación (E15.3). **Seis `403` en cuatro hosts (Annual Reviews, Science, ScienceDirect, Hull): bloqueo al cliente, no muro**, y la regla de M27 aguantó (E15.4). Un `[PDF]` de Hull verificado el 2026-09-10 dio `403` el 25 (E15.5). **Vestíbulo en campo por primera vez: 3 `vestibulo_sin_pdf`, cero cruces con éxito**; A.6 pidió la misma página dos veces, diez respuestas HTTP para un artículo, lo que la hace candidata a deduplicar puertas por destino (E15.6). Fail-open de `robots.txt` en dos hosts más, cero `robots_prohibido` (E15.7). **Tres hosts visitados solo por redirección, sin consultar su `robots.txt`** (science.org, linkinghub.elsevier.com, idp.nature.com); queda abierto si es fallo o hueco de la spec, porque la pregunta 7 de `05` solo cubre el enlace del vestíbulo (E15.8, añadido el mismo día). Ninguna conclusión C ni deuda E6 nueva. |
| **v11** | **2026-09-26** | **Lectura revisada de E15.3, con el mismo log de E15; sin cambios de medición.** El paso de A.6 por `idp.nature.com/authorize` es un intercambio de cookie de sesión en la primera visita al host, no un muro: la puerta 1 acabó en la misma página del artículo sin pasar por el IdP, y los saltos al PDF tampoco pasaron (E15.6). Un patrón sobre esa ruta haría depender el diagnóstico de las cookies. **La señal candidata es otra:** el enlace del PDF redirige (`303`) a la página del artículo en vez de servir el archivo; no está implementada y no tiene criterio en `05`. M32 hizo que los patrones de muro se evalúen contra toda la cadena de redirecciones, sin añadir ninguno; A.6 sigue siendo `vestibulo_sin_pdf`. La nota va en E15.3, fechada. La fila v10 se conserva tal como se escribió. Ningún número de E15 cambia. |
| **v12** | **2026-09-26** | **Idempotencia en campo (E16), medida el 2026-09-23 y registrada ahora.** Segunda corrida de la UAM sobre los mismos fixtures, cinco días después de E14: `total: 47`, `omitidos: 47`; el disco sigue con 47 archivos de la UAM y `descargas` e `intentos` con 156 filas. Ninguno de los 47 encargos se volvió a pedir ni a escribir. **Primera medición en campo de la regla 5 de `05` (M21) y primer dato sobre C24.** **El resumen cuenta los omitidos también como exitosas** (`exitosas: 47` a la vez que `omitidos: 47`), lo que motiva M33. |
| **v13** | **2026-09-26** | **Una omisión pisó 47 filas (E17).** Una corrida de verificación del 26, sin red y sobre los mismos fixtures, dejó las 47 filas de la UAM en `descargas` con `bytes`, `content_type`, `http_status`, `url_final` y `puerta_usada` en NULL y `capturado_en` = 2026-09-26; el valor anterior no se conserva en la base. Causa: los scripts persistían el resultado de la omisión y el upsert sobrescribía la fila. **El daño empezó el 23** (el código de E16 ya pisaba) y el 26 lo repitió. Solo modo jurídico; la UJAT y las 7 académicas, intactas; cero alias, así que `duplicado_de` no se perdió. `documentos`, mismo daño, no se repara. **`content_type` es pérdida definitiva**; lo demás es recuperable (M35b, pendiente), y `capturado_en` solo como estimación. Arreglado en M35. **Nota fechada sobre E16:** «las tablas quedaron intactas» solo lo respaldan los recuentos, que siguen siendo correctos; E16 se conserva tal como se escribió. Ningún número de E14 ni de E16 cambia. |
| **v14** | **2026-09-26** | **Reparación de las 47 filas (E18).** `scripts/reparar_omisiones.py` (M35b), en una transacción: 47 afectadas, 47 reparables, 0 intactas. `url_final` y `http_status` de `intentos`; `bytes` del tamaño del archivo con SHA-256 verificado; `puerta_usada = 0` comprobado contra el `orden` del intento. `capturado_en` es estimación (fecha de modificación): las 47 caen el 2026-09-18, de 13:57:31 a 13:58:14. `content_type` sigue en NULL: pérdida definitiva. Después: 0 filas con `bytes` en NULL; `descargas` 163 e `intentos` 168, sin cambios. Copia previa fuera del repo. **Anomalía abierta (E18.1):** 43 s entre el primer archivo y el último es menos que los 46 s mínimos de un rate limit de 1 s sobre 47 peticiones a un host; hay tres explicaciones y ninguna está medida, porque `rate_limit_s` no se registró en E14 y la fecha de un archivo no es la de su petición. Pendiente: registrar `rate_limit_s` y el host en el informe de las corridas futuras. |
| **v15** | **2026-09-27** | **Corrida del Bloque B (E19): 8/30, más 1 omitido.** 30 encargos, 85 puertas, 27 hosts pedidos, `rate_limit_s` 1.0; 2 `sin_puertas`; 9 archivos nuevos. Primera idempotencia académica en campo (B.12). Control de Nature: la señal de E15.3 distingue muro de acceso abierto, pero sigue sin implementarse (E19.2). PMC sirve HTML en la ruta del PDF en 4 fichas (E19.3). Primer `robots_prohibido` en campo (E19.4). Un enlace muerto en un día (E19.5). M33 actuó 10 veces (E19.6). El reloj de WSL retrocede: cuarta hipótesis, no medida, para E18.1 (E19.7). Los 9 portales CRIS dieron 0 éxitos (E19.8). **Fuente: resumen del operador; el log no se conserva en el repositorio.** Incluye además la nota de M36.2 en E18.1: el pendiente de registrar `rate_limit_s` y los hosts queda cubierto desde M36.1, con la salvedad de que el conteo no incluye los hosts de las redirecciones ni el del salto de vestíbulo. |
