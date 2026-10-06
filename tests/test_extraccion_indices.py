"""M23b: ningún enlace publicado se pierde al extraer las entradas del índice.

Corre la extracción de `legisuni.juridico.cosecha` (M47c, sustituye a
scripts/cosecha.py y scripts/cosecha_uam.py) contra las fixtures reales del
2026-09-06/08 — sin red, solo parseo local de HTML.
"""

from pathlib import Path

from legisuni.juridico import cosecha

_RAIZ = Path(__file__).resolve().parent.parent
_FIXTURES = _RAIZ / "fixtures"

_UJAT_PAGINAS = [
    ("ujat-15763.html", "https://www.ujat.mx/abogado/15763"),
    ("ujat-16443.html", "https://www.ujat.mx/abogado/16443"),
    ("ujat-17669.html", "https://www.ujat.mx/abogado/17669"),
    ("ujat-33794.html", "https://www.ujat.mx/abogado/33794"),
    ("ujat-4232.html", "https://www.ujat.mx/abogado/4232"),
]


def _entradas_uam() -> list:
    return cosecha.entradas_desde_paginas(
        "uam", [(_FIXTURES / "uam-index.html", "https://www.uam.mx/legislacion/index.html")]
    )


def _entradas_ujat() -> list:
    return cosecha.entradas_desde_paginas("ujat", [(_FIXTURES / nombre, url) for nombre, url in _UJAT_PAGINAS])


def test_uam_extrae_47_entradas() -> None:
    assert len(_entradas_uam()) == 47


def test_ujat_extrae_109_entradas() -> None:
    assert len(_entradas_ujat()) == 109


def test_los_156_entry_id_son_unicos() -> None:
    entry_ids = [e.entry_id for e in _entradas_uam()] + [e.entry_id for e in _entradas_ujat()]
    assert len(entry_ids) == 156
    assert len(set(entry_ids)) == 156


def test_ujat_conserva_los_4_href_con_salto_de_linea_final() -> None:
    crudos = [e.url_documento for e in _entradas_ujat() if e.url_documento.endswith("\n")]
    assert len(crudos) == 4
