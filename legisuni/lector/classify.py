"""Filtro barato de enlaces candidatos, sin LLM.

La extensión se comprueba sobre el href RECORTADO y sobre la ruta (sin query ni
fragmento), pero el Enlace devuelto conserva su href crudo (D5).
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit

from legisuni.descargador.guard import es_visor_de_terceros
from legisuni.lector.reduce import Enlace

_EXTENSIONES = (".pdf", ".docx")
_ESQUEMAS_DESCARTADOS = ("javascript:", "mailto:", "tel:")


def es_candidato(enlace: Enlace) -> bool:
    href = enlace.href.strip()
    if not href or href.startswith("#"):
        return False
    if href.lower().startswith(_ESQUEMAS_DESCARTADOS):
        return False
    if es_visor_de_terceros(href) is not None:
        return True
    return urlsplit(href).path.strip().lower().endswith(_EXTENSIONES)


def candidatos(enlaces: Iterable[Enlace]) -> list[Enlace]:
    return [e for e in enlaces if es_candidato(e)]
