"""Traducción jurídica: CatalogEntry → Encargo (01 N10, §Traducción jurídica)."""

from datetime import datetime

from legisuni.contracts import CatalogEntry, Encargo, Puerta


def traducir(entry: CatalogEntry, doc_slug: str, ahora: datetime | None = None) -> Encargo:
    ahora = ahora if ahora is not None else datetime.now()
    fecha = entry.fecha_ultima_reforma or entry.fecha_publicacion or ahora.date()
    return Encargo(
        encargo_id=entry.entry_id,
        modo="juridico",
        solicitante=entry.inst_id,
        puertas=[Puerta(url=entry.url_documento, tipo="enlace_indice",
                        url_base=entry.url_indice, evidencia=entry.url_indice)],
        cajon=f"norm/{entry.inst_id}",
        etiqueta=f"{doc_slug}__{fecha:%Y-%m-%d}",
        cruzar_vestibulos=False,
        grupo_alias=f"{entry.inst_id}:{doc_slug}",
        creado_en=ahora,
    )
