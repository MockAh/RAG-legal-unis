"""Contabilidad de la lectura (01 N3): deduplicación y enlaces sin cuenta.

Todo se compara sobre la URL normalizada (`urlnorm.normalizar`); el href crudo solo se
conserva para devolverlo. No construye Catalog ni decide `lector_agotado`/`fallo_lector`.
"""

from collections.abc import Iterable

from legisuni.descargador.urlnorm import normalizar
from legisuni.lector.reduce import Enlace


def deduplicar(enlaces: Iterable[Enlace], url_indice: str) -> list[Enlace]:
    vistos: set[str] = set()
    unicos: list[Enlace] = []
    for enlace in enlaces:
        clave = normalizar(enlace.href, url_indice)
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(enlace)
    return unicos


def sin_cuenta(
    vistos: Iterable[Enlace],
    emitidos: Iterable[str],
    descartados: Iterable[str],
    url_indice: str,
) -> list[str]:
    con_cuenta = {normalizar(h, url_indice) for h in emitidos}
    con_cuenta |= {normalizar(h, url_indice) for h in descartados}
    return [
        e.href for e in deduplicar(vistos, url_indice) if normalizar(e.href, url_indice) not in con_cuenta
    ]


def contabilidad(
    vistos: Iterable[Enlace],
    emitidos: Iterable[str],
    descartados: Iterable[str],
    url_indice: str,
) -> tuple[int, list[str], bool]:
    vistos = list(vistos)
    huerfanos = sin_cuenta(vistos, emitidos, descartados, url_indice)
    return len(deduplicar(vistos, url_indice)), huerfanos, bool(huerfanos)
