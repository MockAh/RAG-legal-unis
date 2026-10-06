"""Cableado de la cosecha jurídica: páginas de índice guardadas → CatalogEntry (M47c).

Sustituye a `scripts/cosecha.py` y `scripts/cosecha_uam.py`. No extrae nada por su
cuenta: encadena `lector` (reduce → classify → cuenta → slug) y compone `entry_id`
con `identificadores.entry_id`. La traducción a Encargo sigue en `traduccion.py`.

`tipo_norma` y `estado` quedan fijos ("otro", "desconocido"): clasificar es tarea
del agente del Lector (spec 03), que todavía no existe.
"""

from datetime import datetime
from pathlib import Path

from legisuni.contracts import CatalogEntry
from legisuni.descargador.urlnorm import normalizar
from legisuni.juridico import identificadores
from legisuni.lector import classify, cuenta, reduce, slug


def _content_type(ruta_html: Path) -> str | None:
    """`Content-Type` del `.headers` guardado junto al HTML, si existe.

    Si el volcado trae varias respuestas (redirecciones), vale la última.
    """
    ruta_headers = ruta_html.with_suffix(".headers")
    if not ruta_headers.exists():
        return None
    valor = None
    for linea in ruta_headers.read_text(encoding="utf-8", errors="replace").splitlines():
        nombre, _, resto = linea.partition(":")
        if nombre.strip().lower() == "content-type":
            valor = resto.strip()
    return valor


def entradas_desde_paginas(inst_id: str, paginas: list[tuple[Path, str]]) -> list[CatalogEntry]:
    """Una entrada por documento distinto, en el orden en que aparece.

    `paginas` son pares `(ruta_html, url_indice)`; `url_indice` es la base exacta de
    resolución (M24: cambiarla cambia los `entry_id`). Un documento enlazado desde
    dos páginas produce una sola entrada, con el `url_indice` de la primera.
    """
    entradas: list[CatalogEntry] = []
    vistos: set[str] = set()
    for ruta_html, url_indice in paginas:
        pagina = reduce.reducir(ruta_html.read_bytes(), _content_type(ruta_html))
        for enlace in cuenta.deduplicar(classify.candidatos(pagina.enlaces), url_indice):
            # entre páginas, con la misma normalización que usa cuenta.deduplicar
            clave = normalizar(enlace.href, url_indice)
            if clave in vistos:
                continue
            vistos.add(clave)

            titulo = enlace.texto.strip()
            doc_slug = slug.doc_slug(enlace.href, titulo, inst_id)
            entradas.append(
                CatalogEntry(
                    entry_id=identificadores.entry_id(inst_id, doc_slug, enlace.href, url_indice),
                    inst_id=inst_id,
                    titulo=titulo,
                    tipo_norma="otro",
                    url_documento=enlace.href,  # crudo, sin normalizar (D5)
                    estado="desconocido",
                    origen="sitio_institucional",
                    url_indice=url_indice,
                    extraido_en=datetime.now(),
                )
            )
    return entradas
