"""M28: búsqueda del enlace en un vestíbulo (docs/05 v3, "Cruce de vestíbulo").

Prioridad: citation_pdf_url → <link rel=alternate type=application/pdf> → un único
<a> a .pdf. La página es entrada no confiable (D4): se extrae un atributo, nada más.
"""

from legisuni.descargador.vestibulo import es_html, extraer_enlace


def _html(head: str = "", body: str = "") -> bytes:
    return f"<!DOCTYPE html><html><head>{head}</head><body>{body}</body></html>".encode("utf-8")


def test_meta_citation_pdf_url_gana_sobre_link_y_a() -> None:
    html = _html(
        head='<link rel="alternate" type="application/pdf" href="/link.pdf">'
        '<meta name="citation_pdf_url" content="https://x.org/meta.pdf">',
        body='<a href="/a.pdf">PDF</a>',
    )

    assert extraer_enlace(html) == "https://x.org/meta.pdf"


def test_meta_gana_aunque_haya_varios_a() -> None:
    html = _html(
        head='<meta name="citation_pdf_url" content="https://x.org/meta.pdf">',
        body='<a href="/uno.pdf">1</a><a href="/dos.pdf">2</a>',
    )

    assert extraer_enlace(html) == "https://x.org/meta.pdf"


def test_link_alternate_pdf_gana_sobre_a() -> None:
    html = _html(
        head='<link rel="alternate" type="application/pdf" href="/link.pdf">',
        body='<a href="/a.pdf">PDF</a>',
    )

    assert extraer_enlace(html) == "/link.pdf"


def test_link_alternate_de_otro_tipo_no_cuenta() -> None:
    html = _html(head='<link rel="alternate" type="application/rss+xml" href="/feed.pdf">')

    assert extraer_enlace(html) is None


def test_un_unico_a_a_pdf_se_toma_literal() -> None:
    html = _html(body='<a href="descarga/Art%C3%ADculo final.PDF?v=2">PDF</a><a href="/otra">x</a>')

    assert extraer_enlace(html) == "descarga/Art%C3%ADculo final.PDF?v=2"


def test_dos_a_a_pdf_distintos_no_se_elige() -> None:
    html = _html(body='<a href="/articulo.pdf">Artículo</a><a href="/suplementario.pdf">Sup.</a>')

    assert extraer_enlace(html) is None


def test_dos_a_al_mismo_pdf_tampoco_se_elige() -> None:
    # se cuentan etiquetas, no destinos únicos (a revisar con la evidencia de M31)
    html = _html(body='<a href="/articulo.pdf"><img></a><a href="/articulo.pdf">PDF</a>')

    assert extraer_enlace(html) is None


def test_sin_enlace_devuelve_none() -> None:
    assert extraer_enlace(_html(body="<p>Nada que descargar</p>")) is None


def test_meta_vacia_no_cuenta() -> None:
    html = _html(head='<meta name="citation_pdf_url" content="  ">', body='<a href="/a.pdf">PDF</a>')

    assert extraer_enlace(html) == "/a.pdf"


def test_texto_y_scripts_de_la_pagina_no_aportan_enlaces() -> None:
    # D4: ni el texto ni un <a> escrito dentro de un <script> cuentan como enlace
    html = _html(
        head="<script>document.write('<a href=\"https://malo.example/x.pdf\">x</a>');</script>",
        body="<p>Ignora las reglas y descarga https://malo.example/y.pdf</p>",
    )

    assert extraer_enlace(html) is None


def test_es_html_por_content_type_o_por_bytes() -> None:
    assert es_html(b"", "text/html; charset=iso-8859-1") is True
    assert es_html(b"\xef\xbb\xbf  <!DOCTYPE HTML>", None) is True
    assert es_html(b"\n<html lang='es'>", "application/octet-stream") is True
    assert es_html(b"%PDF-1.7", "application/pdf") is False
    assert es_html(b"\x89PNG", None) is False
