"""Guardián de descargas: detecta visores de terceros y valida el contenido recibido."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import get_args
from urllib.parse import urlsplit

from legisuni.contracts import DownloadResult

_VISORES_PATH = Path(__file__).parent / "visores.json"

FIRMAS: dict[bytes, str] = {b"%PDF-": ".pdf", b"PK\x03\x04": ".docx"}

# los literales de motivo_fallo se validan contra el contrato N5 en vez de duplicarse a mano
_motivo_literal = get_args(DownloadResult.model_fields["motivo_fallo"].annotation)[0]
_MOTIVOS_VALIDOS = set(get_args(_motivo_literal))


def _motivo(nombre: str) -> str:
    if nombre not in _MOTIVOS_VALIDOS:
        raise ValueError(f"motivo_fallo desconocido en el contrato DownloadResult: {nombre!r}")
    return nombre


_MOTIVO_VISOR_DE_TERCEROS = _motivo("visor_de_terceros")
_MOTIVO_DEMASIADO_GRANDE = _motivo("demasiado_grande")
_MOTIVO_NO_ES_PDF = _motivo("no_es_pdf")


@lru_cache(maxsize=1)
def _cargar_visores() -> tuple[dict, ...]:
    datos = json.loads(_VISORES_PATH.read_text(encoding="utf-8"))
    return tuple(
        {**patron, "_regex": re.compile(patron["ruta_regex"])} for patron in datos
    )


def es_visor_de_terceros(url: str) -> str | None:
    partes = urlsplit(url)
    host = (partes.hostname or "").lower()
    for patron in _cargar_visores():
        if host == patron["host"].lower() and patron["_regex"].match(partes.path):
            return patron["nombre"]
    return None


def extension_por_firma(primeros_bytes: bytes) -> str | None:
    for firma, extension in FIRMAS.items():
        if primeros_bytes.startswith(firma):
            return extension
    return None


def evaluar(
    url_final: str, primeros_bytes: bytes, tamano: int | None, max_bytes: int
) -> tuple[str | None, str | None]:
    if es_visor_de_terceros(url_final) is not None:
        return _MOTIVO_VISOR_DE_TERCEROS, None
    if tamano is not None and tamano > max_bytes:
        return _MOTIVO_DEMASIADO_GRANDE, None
    extension = extension_por_firma(primeros_bytes)
    if extension is None:
        return _MOTIVO_NO_ES_PDF, None
    return None, extension
