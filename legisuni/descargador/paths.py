"""Construcción de rutas de disco: funciones puras, sin I/O."""

import re
import unicodedata
from pathlib import Path

_CARACTERES_NO_SEGUROS = re.compile(r"[^a-z0-9._-]+")
_GUIONES_REPETIDOS = re.compile(r"-{2,}")
_ETIQUETA_SEGURA = re.compile(r"^[a-z0-9._-]+$")
_CAJON_SEGURO = re.compile(r"^[a-z0-9._/-]+$")


def sanear(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto.lower())
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    con_guiones = _CARACTERES_NO_SEGUROS.sub("-", sin_acentos)
    colapsado = _GUIONES_REPETIDOS.sub("-", con_guiones).strip("-")
    return colapsado or "sin-nombre"


def _validar_cajon(cajon: str) -> None:
    if cajon.startswith("/") or ".." in cajon.split("/") or not _CAJON_SEGURO.match(cajon):
        raise ValueError(f"cajon inseguro: {cajon!r}")


def _validar_etiqueta(etiqueta: str) -> None:
    if ".." in etiqueta or not _ETIQUETA_SEGURA.match(etiqueta):
        raise ValueError(f"etiqueta insegura: {etiqueta!r}")


def ruta_documento(
    data_root: Path,
    cajon: str,
    etiqueta: str,
    extension: str,
    sha256: str | None = None,
) -> Path:
    _validar_cajon(cajon)
    _validar_etiqueta(etiqueta)
    sufijo = "" if sha256 is None else f"__{sha256[:8]}"
    nombre = f"{etiqueta}{sufijo}{extension}"
    return data_root / cajon / nombre
