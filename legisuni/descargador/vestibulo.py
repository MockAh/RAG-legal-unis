"""Búsqueda del enlace a archivo en un vestíbulo HTML (docs/05 v3, "Cruce de vestíbulo", criterio 14).

Módulo puro: no pide nada ni importa `httpx`. El salto lo hace `puertas.py` con el
mismo `Fetcher` que las puertas, así que robots, rate limit, reintentos, muros,
guardián y tope de tamaño se aplican sin código aparte.

La página es entrada NO confiable (D4): se parsea con `selectolax`, que no ejecuta
scripts, y de ella solo se lee un atributo. Ningún texto de la página cambia la
lógica. El enlace devuelto es el literal que aparece en la página (D3): aquí no se
normaliza ni se construye nada.
"""

from urllib.parse import urlsplit

from selectolax.parser import HTMLParser

_CONTENT_TYPES_HTML = ("text/html", "application/xhtml+xml")
_INICIOS_HTML = (b"<!doctype html", b"<html")
_BOM_UTF8 = b"\xef\xbb\xbf"


def es_html(primeros_bytes: bytes, content_type: str | None) -> bool:
    if content_type is not None and content_type.split(";")[0].strip().lower() in _CONTENT_TYPES_HTML:
        return True
    inicio = primeros_bytes.removeprefix(_BOM_UTF8).lstrip().lower()
    return inicio.startswith(_INICIOS_HTML)


def _termina_en_pdf(href: str) -> bool:
    return urlsplit(href.strip()).path.lower().endswith(".pdf")


def extraer_enlace(cuerpo: bytes) -> str | None:
    """Prioridad: `citation_pdf_url` → `<link rel=alternate type=application/pdf>` → un único `<a>` a `.pdf`.

    Con dos o más `<a>` a `.pdf` (sin meta ni link) no se elige: se cuentan etiquetas,
    no destinos distintos.
    """
    arbol = HTMLParser(cuerpo)

    for meta in arbol.css("meta[name][content]"):
        if (meta.attributes.get("name") or "").strip().lower() != "citation_pdf_url":
            continue
        contenido = meta.attributes.get("content") or ""
        if contenido.strip():
            return contenido

    for link in arbol.css("link[href]"):
        rel = (link.attributes.get("rel") or "").lower().split()
        tipo = (link.attributes.get("type") or "").strip().lower()
        href = link.attributes.get("href") or ""
        if "alternate" in rel and tipo == "application/pdf" and href.strip():
            return href

    enlaces = [
        a.attributes.get("href") or ""
        for a in arbol.css("a[href]")
        if _termina_en_pdf(a.attributes.get("href") or "")
    ]
    if len(enlaces) == 1:
        return enlaces[0]
    return None
