"""Reducción de una página de índice a texto plano y tabla de enlaces (sin LLM).

La página es entrada NO confiable (D4): se parsea con `selectolax`, que no ejecuta
nada. De cada `<a>` solo se leen el texto y el atributo `href`.

Solo se quitan `<script>`, `<style>`, `<noscript>` y comentarios. El pie de página
se conserva: la fecha de corte de la UACAM vive después del `<footer>`.
"""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass
from typing import Literal

from selectolax.parser import HTMLParser

_CHARSET_CABECERA = re.compile(r"charset\s*=\s*[\"']?\s*([A-Za-z0-9_.:\-]+)", re.I)
_META = re.compile(rb"<meta\b[^>]*>", re.I)
_META_CHARSET = re.compile(rb"charset\s*=\s*[\"']?\s*([A-Za-z0-9_.:\-]+)", re.I)
_META_DIRECTO = re.compile(rb"<meta\s+charset", re.I)
_META_HTTP_EQUIV = re.compile(rb"http-equiv\s*=\s*[\"']?\s*content-type", re.I)
_VENTANA_META = 8192
_QUITAR = ["script", "style", "noscript", "-comment"]


@dataclass(frozen=True)
class Enlace:
    texto: str
    href: str


@dataclass(frozen=True)
class PaginaReducida:
    texto: str
    enlaces: list[Enlace]
    codificacion: str
    origen_codificacion: Literal["cabecera", "meta", "fallback"]


def _normalizar(nombre: str) -> str | None:
    try:
        nombre = nombre.strip().lower()
        codecs.lookup(nombre)
        return nombre
    except LookupError:
        return None


def _detectar(
    crudo: bytes, content_type: str | None
) -> tuple[str, Literal["cabecera", "meta", "fallback"]]:
    if content_type:
        m = _CHARSET_CABECERA.search(content_type)
        if m and (nombre := _normalizar(m.group(1))):
            return nombre, "cabecera"
    for etiqueta in _META.findall(crudo[:_VENTANA_META]):
        m = _META_CHARSET.search(etiqueta)
        if m is None:
            continue
        # charset= solo vale en <meta charset> o en http-equiv="Content-Type".
        if _META_DIRECTO.match(etiqueta) or _META_HTTP_EQUIV.search(etiqueta):
            if nombre := _normalizar(m.group(1).decode("ascii", "replace")):
                return nombre, "meta"
    return "utf-8", "fallback"


def reducir(crudo: bytes, content_type: str | None = None) -> PaginaReducida:
    codificacion, origen = _detectar(crudo, content_type)
    html = crudo.decode(codificacion, errors="replace")
    arbol = HTMLParser(html)
    arbol.strip_tags(_QUITAR)
    enlaces = [
        Enlace(texto=a.text(deep=True, separator="", strip=False), href=a.attributes["href"] or "")
        for a in arbol.css("a")
        if "href" in a.attributes
    ]
    raiz = arbol.root
    texto = raiz.text(deep=True, separator="", strip=False) if raiz is not None else ""
    return PaginaReducida(texto, enlaces, codificacion, origen)
