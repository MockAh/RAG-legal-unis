"""M41: lector/reduce.py sobre las fixtures reales."""

from pathlib import Path

import pytest

from legisuni.lector.reduce import reducir

FIX = Path(__file__).resolve().parent.parent / "fixtures"
NUEVAS = ["uacam__2026-10-01", "unam-70i__2026-10-01", "unam-oag__2026-10-01"]


def _content_type(nombre: str) -> str:
    for linea in (FIX / f"{nombre}.headers").read_text(encoding="utf-8").splitlines():
        if linea.lower().startswith("content-type:"):
            return linea.split(":", 1)[1].strip()
    raise AssertionError(f"{nombre}.headers sin Content-Type")


def _reducir_nueva(nombre: str):
    return reducir((FIX / f"{nombre}.html").read_bytes(), _content_type(nombre))


def test_uam_iso_8859_1_por_meta_con_acentos_correctos():
    p = reducir((FIX / "uam-index.html").read_bytes(), None)
    assert p.codificacion == "iso-8859-1"
    assert p.origen_codificacion == "meta"
    assert "Legislación" in p.texto
    assert "Orgánica" in p.texto
    assert "\ufffd" not in p.texto
    assert "Ã" not in p.texto  # mojibake de leer iso-8859-1 como utf-8


@pytest.mark.parametrize("nombre", NUEVAS)
def test_nuevas_utf8_por_cabecera(nombre):
    p = _reducir_nueva(nombre)
    assert p.codificacion == "utf-8"
    assert p.origen_codificacion == "cabecera"


def test_uacam_fecha_de_corte_con_nbsp_y_pie_conservado():
    p = _reducir_nueva("uacam__2026-10-01")
    assert "Fecha de corte" in p.texto
    assert "Diciembre del 2016" in p.texto
    i = p.texto.index("Fecha de corte")
    j = p.texto.index("Diciembre del 2016")
    assert "\u00a0" in p.texto[i:j]


def test_70i_sin_pdf_y_con_instrucciones():
    p = _reducir_nueva("unam-70i__2026-10-01")
    assert [e for e in p.enlaces if ".pdf" in e.href] == []
    t = p.texto.lower()
    assert "doble clic" in t
    assert "ordenar" in t


def test_ujat_hrefs_con_salto_de_linea():
    total = 0
    for f in sorted(FIX.glob("ujat-*.html")):
        p = reducir(f.read_bytes(), None)
        assert p.origen_codificacion == "meta"
        total += sum(e.href.endswith(("\n", "\r\n")) for e in p.enlaces)
    assert total >= 4


def test_uam_enlace_sin_texto_a_pdf_no_se_descarta():
    p = reducir((FIX / "uam-index.html").read_bytes(), None)
    assert any(e.texto == "" and ".pdf" in e.href.lower() for e in p.enlaces)


def test_quita_script_style_noscript_comentarios_y_conserva_pie():
    html = (
        b'<head><style>.a{}</style><script>var x="SCRIPT";</script></head>'
        b"<body><!-- COMENTARIO --><noscript>NOSCRIPT</noscript>"
        b"<main>cuerpo</main><footer>PIE&nbsp;&amp;</footer></body>"
    )
    t = reducir(html).texto
    for ausente in ("SCRIPT", "COMENTARIO", "NOSCRIPT", ".a{}"):
        assert ausente not in t
    assert "cuerpo" in t and "PIE\u00a0&" in t


def test_href_crudo_y_ancla_vacia():
    p = reducir(b'<a href=" ../x y.pdf ">  T </a><a href="">e</a><a href="z.pdf"></a>')
    assert p.enlaces[0].href == " ../x y.pdf "
    assert p.enlaces[0].texto == "  T "
    assert p.enlaces[1].href == ""
    assert p.enlaces[2].texto == "" and p.enlaces[2].href == "z.pdf"


def test_prioridad_cabecera_sobre_meta_y_fallback():
    crudo = '<meta charset="iso-8859-1">é'.encode("utf-8")
    assert reducir(crudo, "text/html; charset=UTF-8").origen_codificacion == "cabecera"
    assert reducir(crudo, "text/html").origen_codificacion == "meta"
    p = reducir(b"hola", None)
    assert (p.codificacion, p.origen_codificacion) == ("utf-8", "fallback")
    p = reducir(b"hola", "text/html; charset=nope-9")
    assert p.origen_codificacion == "fallback"


def test_meta_http_equiv_content_type():
    crudo = b'<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">\xe9'
    p = reducir(crudo)
    assert p.origen_codificacion == "meta"
    assert "é" in p.texto


@pytest.mark.parametrize(
    "nombre,esperado", [("unam-oag__2026-10-01", 84), ("uacam__2026-10-01", 81)]
)
def test_medicion_hrefs_unicos_pdf(nombre, esperado):
    """Conteo medido, no inventado: E20.5 dio 84 y 81 con grep."""
    p = _reducir_nueva(nombre)
    medido = {e.href for e in p.enlaces if ".pdf" in e.href}
    assert len(medido) == esperado


def test_texto_separa_elementos_sin_saltos_en_el_html():
    t = _reducir_nueva("uacam__2026-10-01").texto
    assert "CampecheFecha" not in t
    i = t.index("Fecha de corte")
    j = t.index("Diciembre del 2016")
    assert "\u00a0" in t[i:j]
