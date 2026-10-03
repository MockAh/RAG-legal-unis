"""M42: lector/classify.py sobre las fixtures reales."""

from pathlib import Path

import pytest

from legisuni.lector.classify import candidatos, es_candidato
from legisuni.lector.reduce import Enlace, reducir

FIX = Path(__file__).resolve().parent.parent / "fixtures"
CT = "text/html; charset=UTF-8"


def _enlaces(nombre: str, ct: str | None = CT) -> list[Enlace]:
    return reducir((FIX / nombre).read_bytes(), ct).enlaces


def _con_salto(nombre_glob="ujat-*.html") -> list[Enlace]:
    return [
        e
        for f in sorted(FIX.glob(nombre_glob))
        for e in _enlaces(f.name, None)
        if e.href.endswith(("\n", "\r\n"))
    ]


def test_ujat_hrefs_con_salto_de_linea_son_candidatos_y_conservan_href_crudo():
    con_salto = _con_salto()
    assert len(con_salto) >= 4
    assert all(es_candidato(e) for e in con_salto)
    todos = [e for f in sorted(FIX.glob("ujat-*.html")) for e in _enlaces(f.name, None)]
    devueltos = candidatos(todos)
    assert sum(e.href.endswith(("\n", "\r\n")) for e in devueltos) >= 4


def test_comprobar_sobre_href_sin_recortar_perderia_los_de_ujat():
    # Protege la regla dura: el filtro de v1 sobre el crudo los perdía.
    con_salto = _con_salto()
    assert len(con_salto) >= 4
    assert not any(e.href.lower().endswith((".pdf", ".docx")) for e in con_salto)


@pytest.mark.parametrize(
    "nombre,esperado", [("unam-oag__2026-10-01.html", 84), ("uacam__2026-10-01.html", 81)]
)
def test_candidatos_cubren_los_pdf_unicos_de_e20_5(nombre, esperado):
    enlaces = _enlaces(nombre)
    pdf = {e.href for e in enlaces if ".pdf" in e.href}
    assert len(pdf) == esperado
    assert pdf <= {e.href for e in candidatos(enlaces)}


def test_70i_cero_candidatos():
    assert candidatos(_enlaces("unam-70i__2026-10-01.html")) == []


def test_uacam_drive_son_candidatos():
    drive = [e for e in _enlaces("uacam__2026-10-01.html") if "drive.google.com" in e.href]
    assert len(drive) == 4
    assert all(es_candidato(e) for e in drive)


def test_candidatos_no_deduplica_ni_cambia_orden():
    a, b = Enlace("a", "x.pdf"), Enlace("b", "x.pdf")
    assert candidatos([a, Enlace("c", "#"), b]) == [a, b]


@pytest.mark.parametrize(
    "href,esperado",
    [
        ("", False),
        ("   ", False),
        ("#", False),
        ("javascript:void(0)", False),
        ("mailto:a@b.mx", False),
        ("tel:555", False),
        ("x.jpg", False),
        ("x.html", False),
        ("x.PDF", True),
        ("x.pdf?v=2", True),
        ("x.pdf#pag3", True),
        (" x.docx\n", True),
        ("https://drive.google.com/file/d/abc/view?usp=sharing", True),
        ("https://drive.google.com/drive/folders/abc", False),
    ],
)
def test_es_candidato_unitarios(href, esperado):
    assert es_candidato(Enlace("t", href)) is esperado
