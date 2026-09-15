"""M23b: ningún enlace publicado se pierde al extraer las entradas del índice.

Corre la extracción de scripts/cosecha.py y scripts/cosecha_uam.py contra las
fixtures reales del 2026-09-06/08 — sin red, solo parseo local de HTML.
scripts/ no es un paquete de legisuni (a propósito, ver su docstring), así
que se importa por ruta.
"""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
_FIXTURES = _RAIZ / "fixtures"

sys.path.insert(0, str(_RAIZ / "scripts"))

import cosecha  # noqa: E402
import cosecha_uam  # noqa: E402

_UJAT_PAGINAS = [
    ("ujat-15763.html", "https://www.ujat.mx/abogado/15763"),
    ("ujat-16443.html", "https://www.ujat.mx/abogado/16443"),
    ("ujat-17669.html", "https://www.ujat.mx/abogado/17669"),
    ("ujat-33794.html", "https://www.ujat.mx/abogado/33794"),
    ("ujat-4232.html", "https://www.ujat.mx/abogado/4232"),
]


def _entradas_uam() -> list:
    return cosecha_uam.entradas_desde_html(
        _FIXTURES / "uam-index.html", "https://www.uam.mx/legislacion/index.html", "uam"
    )


def _entradas_ujat() -> list:
    htmls = [_FIXTURES / nombre for nombre, _ in _UJAT_PAGINAS]
    urls_indice = [url for _, url in _UJAT_PAGINAS]
    return cosecha._entradas_desde_paginas(htmls, urls_indice, "ujat")


def test_uam_extrae_47_entradas() -> None:
    assert len(_entradas_uam()) == 47


def test_ujat_extrae_109_entradas() -> None:
    assert len(_entradas_ujat()) == 109


def test_los_156_entry_id_son_unicos() -> None:
    entry_ids = [e.entry_id for e in _entradas_uam()] + [e.entry_id for e in _entradas_ujat()]
    assert len(entry_ids) == 156
    assert len(set(entry_ids)) == 156


def test_doc_slug_uam_anexos_saneado_a_minusculas() -> None:
    casos = [
        ("legislacion-uam-julio-24-2026/legislacion-uam-julio-24-2026-pavrg-ANEXO1.pdf", "anexo1"),
        ("legislacion-uam-julio-24-2026/legislacion-uam-julio-24-2026-pavrg-ANEXO-3A.docx", "3a"),
        ("legislacion-uam-julio-24-2026/legislacion-uam-julio-24-2026-pavrg-ANEXO-3B.docx", "3b"),
        ("legislacion-uam-julio-24-2026/legislacion-uam-julio-24-2026-pavrg-ANEXO3C.pdf", "anexo3c"),
    ]
    for href, esperado in casos:
        assert cosecha_uam._doc_slug_desde_href(href, "titulo irrelevante") == esperado
