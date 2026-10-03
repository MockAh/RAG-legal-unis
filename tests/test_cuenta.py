"""M46: lector/cuenta.py."""

from pathlib import Path

from legisuni.lector.classify import candidatos
from legisuni.lector.cuenta import contabilidad, deduplicar, sin_cuenta
from legisuni.lector.reduce import Enlace, reducir

FIX = Path(__file__).resolve().parent.parent / "fixtures"
CT = "text/html; charset=UTF-8"
BASE = "https://sitio.example/indice/"


def _cands(nombre):
    return candidatos(reducir((FIX / nombre).read_bytes(), CT).enlaces)


def _enlaces(n):
    return [Enlace(texto=f"d{i}", href=f"x/doc{i}.pdf") for i in range(n)]


def test_uam_index_47_unicos():
    cands = _cands("uam-index.html")
    assert len(cands) == 47
    assert len(deduplicar(cands, "https://www.uam.mx/")) == 47


def test_uacam_89_a_87():
    cands = _cands("uacam__2026-10-01.html")
    assert len(cands) == 89
    assert len(deduplicar(cands, "https://www.uacam.mx/")) == 87


def test_e12_2_espacio_y_percent_son_la_misma_direccion():
    a = Enlace("a", "x/acuerdos rect 2.pdf")
    b = Enlace("b", "x/acuerdos%20rect%202.pdf")
    assert deduplicar([a, b], BASE) == [a]
    assert deduplicar([a, b], BASE)[0].href == "x/acuerdos rect 2.pdf"


def test_relativas_que_resuelven_a_la_misma_absoluta():
    a = Enlace("a", "docs/a.pdf")
    b = Enlace("b", "../indice/docs/a.pdf")
    c = Enlace("c", "https://sitio.example/indice/docs/a.pdf")
    assert deduplicar([a, b, c], BASE) == [a]


def test_40_de_47_sin_cuenta():
    v = _enlaces(47)
    emitidos = [e.href for e in v[:40]]
    assert sin_cuenta(v, emitidos, [], BASE) == [e.href for e in v[40:]]
    n, huerfanos, incompleta = contabilidad(v, emitidos, [], BASE)
    assert (n, len(huerfanos), incompleta) == (47, 7, True)


def test_47_con_descartados_cuadra():
    v = _enlaces(47)
    n, huerfanos, incompleta = contabilidad(
        v, [e.href for e in v[:40]], [e.href for e in v[40:]], BASE
    )
    assert (n, huerfanos, incompleta) == (47, [], False)


def test_emitido_con_otra_ortografia_cuenta():
    v = [Enlace("a", "x/acuerdos rect 2.pdf")]
    assert sin_cuenta(v, ["x/acuerdos%20rect%202.pdf"], [], BASE) == []


def test_cero_vistos():
    assert contabilidad([], [], [], BASE) == (0, [], False)
