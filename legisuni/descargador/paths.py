"""Construcción de rutas de disco: funciones puras, sin I/O."""

import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

from legisuni.contracts import CatalogEntry

_CARACTERES_NO_SEGUROS = re.compile(r"[^a-z0-9._-]+")
_GUIONES_REPETIDOS = re.compile(r"-{2,}")


def doc_slug_de(entry_id: str) -> str:
    if ":" not in entry_id:
        raise ValueError(f"entry_id malformado, falta ':': {entry_id!r}")
    return entry_id.split(":", 1)[1]


def fecha_de_version(entrada: CatalogEntry, capturado_en: datetime) -> date:
    if entrada.fecha_ultima_reforma is not None:
        return entrada.fecha_ultima_reforma
    if entrada.fecha_publicacion is not None:
        return entrada.fecha_publicacion
    return capturado_en.date()


def sanear(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto.lower())
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    con_guiones = _CARACTERES_NO_SEGUROS.sub("-", sin_acentos)
    colapsado = _GUIONES_REPETIDOS.sub("-", con_guiones).strip("-")
    return colapsado or "sin-nombre"


def ruta_documento(
    data_dir: Path,
    inst_id: str,
    entry_id: str,
    fecha_version: date,
    extension: str,
    sha256: str | None = None,
) -> Path:
    doc_slug = doc_slug_de(entry_id)
    sufijo = "" if sha256 is None else f"__{sha256[:8]}"
    nombre = f"{sanear(doc_slug)}__{fecha_version:%Y-%m-%d}{sufijo}{extension}"
    return data_dir / sanear(inst_id) / nombre
