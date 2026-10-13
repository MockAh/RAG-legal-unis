"""Ensamblado de un `Catalog` (01 N3) a partir de UNA página de índice (M49).

Vive en `juridico/` por la misma razón que `cosecha.py`: compone `entry_id` con
`identificadores.entry_id`, y `lector/` no debe hacerlo (criterio 15 de `03`).

El agente declara; el código resta (03 §Contabilidad). De la respuesta del agente
salen las entradas, los descartes, `agotado` y las notas. Todo lo demás —la
contabilidad, `catalogo_caducado`, `fallo_lector`— lo pone este módulo.

La fusión de varias páginas en un `Catalog` no está aquí: `01` no dice qué pasa
cuando una de cinco falla.
"""

from collections.abc import Sequence
from datetime import datetime

from legisuni.contracts import Catalog, CatalogEntry, SourceCandidate
from legisuni.juridico import identificadores
from legisuni.lector import cuenta, slug
from legisuni.lector.corte import Corte, esta_caducado
from legisuni.lector.models import SalidaInvalida, parsear_salida
from legisuni.lector.reduce import Enlace


def ensamblar(
    fuente: SourceCandidate,
    enlaces: Sequence[Enlace],
    corte: Corte | None,
    cruda: str,
    ahora: datetime,
    umbral_caducidad_meses: int,
) -> Catalog:
    """`enlaces`: la tabla ya pasada por `classify` y `cuenta.deduplicar`, la misma que
    recibió el agente. `corte`: lo que devolvió `corte.buscar_corte` sobre la página.
    `cruda`: la respuesta del agente sin tocar; persistirla es de quien llama (M50).

    La página es `fuente.url`, que hace de `url_indice` de cada entrada.
    """
    inst_id = fuente.inst_id
    url_indice = fuente.url

    caducado = (
        corte is not None
        and corte.fecha is not None
        and esta_caducado(corte.fecha, ahora.date(), umbral_caducidad_meses)
    )
    comun = dict(
        inst_id=inst_id,
        fuentes_usadas=[fuente],
        generado_en=ahora,
        fecha_corte_declarada=corte.fecha if corte else None,
        fecha_corte_texto=corte.texto if corte else None,
        catalogo_caducado=caducado,
    )

    try:
        salida = parsear_salida(cruda)
    except SalidaInvalida:
        # Nunca lector_agotado: la página podía ser perfectamente legible (03, regla dura 1).
        vistos, sin_cuenta, incompleta = cuenta.contabilidad(enlaces, [], [], url_indice)
        return Catalog(
            **comun,
            entries=[],
            lector_agotado=False,
            notas=None,
            enlaces_vistos=vistos,
            enlaces_sin_cuenta=sin_cuenta,
            lectura_incompleta=incompleta,
            fallo_lector="salida_invalida",
        )

    entries = []
    for entrada in salida.entradas:
        doc_slug = slug.doc_slug(entrada.href, entrada.titulo, inst_id)
        datos = entrada.model_dump(exclude={"href"})
        entries.append(
            CatalogEntry(
                **datos,
                entry_id=identificadores.entry_id(inst_id, doc_slug, entrada.href, url_indice),
                inst_id=inst_id,
                url_documento=entrada.href,  # crudo, como lo declaró el agente (D5)
                origen=fuente.origen,
                url_indice=url_indice,
                extraido_en=ahora,
            )
        )

    vistos, sin_cuenta, incompleta = cuenta.contabilidad(
        enlaces, [e.href for e in salida.entradas], salida.descartados, url_indice
    )
    return Catalog(
        **comun,
        entries=entries,
        lector_agotado=salida.agotado,
        notas=salida.notas,
        enlaces_vistos=vistos,
        enlaces_descartados=salida.descartados,
        enlaces_sin_cuenta=sin_cuenta,
        lectura_incompleta=incompleta,
    )
