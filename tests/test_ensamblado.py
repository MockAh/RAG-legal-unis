"""M49: el ensamblado de un Catalog de una página, con un agente maniquí (criterio 17 de 03)."""

from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from legisuni.contracts import Catalog, SourceCandidate
from legisuni.descargador.urlnorm import url_id
from legisuni.juridico.ensamblado import ensamblar
from legisuni.lector.classify import candidatos
from legisuni.lector.corte import buscar_corte
from legisuni.lector.cuenta import deduplicar
from legisuni.lector.models import Agente, SalidaInvalida, parsear_salida
from legisuni.lector.reduce import Enlace, reducir
from maniqui import AGENTE, AgenteManiqui

FIX = Path(__file__).resolve().parent.parent / "fixtures"
AHORA = datetime(2026, 10, 1, 12, 0)
UMBRAL = 18


def _fuente(inst_id: str, url: str) -> SourceCandidate:
    return SourceCandidate(
        inst_id=inst_id,
        url=url,
        origen="sitio_institucional",
        titulo_pagina="Legislación",
        dominio=url.split("/")[2],
        es_dominio_institucional=True,
        confianza="alta",
        razon="maniquí",
        descubierta_en=AHORA,
        evidencia_url=url,
    )


def _leer(fixture: str, ct: str | None, fuente: SourceCandidate, caso: str) -> Catalog:
    """El camino entero de una página: reduce → corte → classify → deduplicar → agente → ensamblado."""
    pagina = reducir((FIX / fixture).read_bytes(), ct)
    enlaces = deduplicar(candidatos(pagina.enlaces), fuente.url)
    agente: Agente = AgenteManiqui(caso)
    cruda = agente(enlaces)
    return ensamblar(fuente, enlaces, buscar_corte(pagina.texto), cruda, AHORA, UMBRAL)


UAM = _fuente("uam", "https://www.uam.mx/")
UACAM = _fuente("uacam", "https://www.uacam.mx/")
CT_UTF8 = "text/html; charset=UTF-8"


def _uam_47() -> list[Enlace]:
    return deduplicar(candidatos(reducir((FIX / "uam-index.html").read_bytes(), None).enlaces), UAM.url)


# --- criterio 17: los tres casos ---


def test_rejilla_js_es_agotado() -> None:
    catalogo = _leer("unam-70i__2026-10-01.html", CT_UTF8, _fuente("unam", "https://www.unam.mx/"), "agotado")
    assert catalogo.lector_agotado is True
    assert catalogo.fallo_lector is None
    assert catalogo.lectura_incompleta is False
    assert catalogo.enlaces_vistos == 0
    assert catalogo.entries == []
    assert catalogo.notas == "índice servido por rejilla JS; sin filas en el HTML"


def test_40_de_47_lista_exactamente_los_7_que_faltan() -> None:
    catalogo = _leer("uam-index.html", None, UAM, "truncado")
    assert catalogo.lector_agotado is False
    assert catalogo.fallo_lector is None
    assert catalogo.lectura_incompleta is True
    assert catalogo.enlaces_vistos == 47
    assert len(catalogo.entries) == 40
    assert catalogo.enlaces_sin_cuenta == [e.href for e in _uam_47()[40:]]


def test_json_invalido_es_salida_invalida_y_no_agotado() -> None:
    catalogo = _leer("uam-index.html", None, UAM, "invalido")
    assert catalogo.lector_agotado is False
    assert catalogo.fallo_lector == "salida_invalida"
    assert catalogo.lectura_incompleta is True
    assert catalogo.entries == []
    assert catalogo.enlaces_sin_cuenta == [e.href for e in _uam_47()]


# --- los cuatro que valen por sí solos ---


@pytest.mark.parametrize(
    ("fixture", "ct", "fuente", "caso"),
    [
        ("unam-70i__2026-10-01.html", CT_UTF8, _fuente("unam", "https://www.unam.mx/"), "agotado"),
        ("uam-index.html", None, UAM, "truncado"),
        ("uam-index.html", None, UAM, "invalido"),
        ("uacam__2026-10-01.html", CT_UTF8, UACAM, "uacam"),
    ],
)
def test_ningun_catalog_es_agotado_y_fallido_a_la_vez(fixture, ct, fuente, caso) -> None:
    catalogo = _leer(fixture, ct, fuente, caso)
    assert not (catalogo.lector_agotado and catalogo.fallo_lector is not None)


def test_catalog_rechaza_agotado_con_fallo_lector() -> None:
    with pytest.raises(ValidationError):
        Catalog(
            inst_id="uam",
            entries=[],
            fuentes_usadas=[UAM],
            generado_en=AHORA,
            lector_agotado=True,
            notas=None,
            fallo_lector="salida_invalida",
        )


_AGOTADO_CON_ENTRADAS = (
    '{"entradas": [{"href": "a.pdf", "titulo": "A", "tipo_norma": "otro"}],'
    ' "descartados": [], "agotado": true, "notas": null}'
)


def test_agotado_con_entradas_falla_el_parseo() -> None:
    with pytest.raises(SalidaInvalida):
        parsear_salida(_AGOTADO_CON_ENTRADAS)


def test_agotado_con_entradas_es_salida_invalida_en_el_catalog() -> None:
    catalogo = ensamblar(UAM, [Enlace("A", "a.pdf")], None, _AGOTADO_CON_ENTRADAS, AHORA, UMBRAL)
    assert catalogo.fallo_lector == "salida_invalida"
    assert catalogo.lector_agotado is False


def test_uacam_caducada_con_el_agente_devolviendo_sus_87() -> None:
    catalogo = _leer("uacam__2026-10-01.html", CT_UTF8, UACAM, "uacam")
    assert len(catalogo.entries) == 87
    assert catalogo.enlaces_vistos == 87
    assert catalogo.lectura_incompleta is False
    assert catalogo.catalogo_caducado is True
    assert catalogo.fecha_corte_declarada == date(2016, 12, 31)


def test_href_con_otra_ortografia_no_cuenta_como_faltante() -> None:
    # La página trae los espacios codificados; el agente declara el href con espacios (E12.2).
    original = Enlace("Acuerdos rectorales 2", "docs/acuerdos%20rect%202.pdf")
    cruda = AgenteManiqui("ortografia")([original])
    assert "docs/acuerdos rect 2.pdf" in cruda
    catalogo = ensamblar(UAM, [original], None, cruda, AHORA, UMBRAL)
    assert catalogo.enlaces_sin_cuenta == []
    assert catalogo.lectura_incompleta is False
    assert catalogo.entries[0].entry_id.endswith(url_id(original.href, UAM.url))


# --- el parseo no confía en que el JSON venga limpio ---


@pytest.mark.parametrize(
    "cruda",
    [
        'Aquí está el JSON: {"entradas": [], "descartados": [], "agotado": false}',
        '{"entradas": [], "descartados": [], "agotado": false,}',
        '{"entradas": [], "descartados": [], "agotado": false, "enlaces_sin_cuenta": []}',
        '{"entradas": [], "descartados": [], "agotado": false, "lectura_incompleta": false}',
        '{"entradas": [], "descartados": [], "agotado": false, "catalogo_caducado": false}',
        '{"entradas": [{"href": "a.pdf", "titulo": "A", "tipo_norma": "otro", "entry_id": "x"}],'
        ' "descartados": [], "agotado": false}',
        "",
    ],
)
def test_parseo_rechaza_salida_sucia_o_con_campos_que_son_del_codigo(cruda: str) -> None:
    with pytest.raises(SalidaInvalida) as error:
        parsear_salida(cruda)
    assert error.value.cruda == cruda


def test_parseo_de_salida_limpia() -> None:
    salida = parsear_salida((AGENTE / "agotado.json").read_text(encoding="utf-8"))
    assert salida.agotado is True
    assert salida.entradas == []


# --- M49b: la guardia de D3 y las entradas repetidas ---

_TABLA = [
    Enlace("Ley Orgánica", "docs/ley-organica.pdf"),
    Enlace("Estatuto General", "docs/estatuto-general.pdf"),
]


def _con_maniqui(caso: str, enlaces: list[Enlace]) -> Catalog:
    return ensamblar(UAM, enlaces, None, AgenteManiqui(caso)(enlaces), AHORA, UMBRAL)


def test_entrada_inventada_se_descarta_sin_fallo_lector() -> None:
    catalogo = _con_maniqui("inventada", _TABLA)
    assert "docs/reglamento-de-becas.pdf" not in [e.url_documento for e in catalogo.entries]
    assert catalogo.notas is not None
    assert "'docs/reglamento-de-becas.pdf'" in catalogo.notas
    assert catalogo.fallo_lector is None
    assert catalogo.enlaces_descartados == []


def test_las_legitimas_junto_a_una_inventada_sobreviven() -> None:
    catalogo = _con_maniqui("inventada", _TABLA)
    assert [e.url_documento for e in catalogo.entries] == [
        "docs/ley-organica.pdf",
        "docs/estatuto-general.pdf",
    ]


def test_legitima_con_otra_ortografia_no_se_descarta() -> None:
    catalogo = _con_maniqui("ortografia", [Enlace("Acuerdos rectorales 2", "docs/acuerdos%20rect%202.pdf")])
    assert [e.url_documento for e in catalogo.entries] == ["docs/acuerdos rect 2.pdf"]
    assert catalogo.notas is None


def test_mismo_href_dos_veces_da_una_entrada_la_primera() -> None:
    catalogo = _con_maniqui("repetida", _TABLA)
    assert [e.titulo for e in catalogo.entries] == ["Ley Orgánica", "Estatuto General"]
    assert len({e.entry_id for e in catalogo.entries}) == 2
    assert catalogo.notas is not None
    assert "repetidas" in catalogo.notas
    assert "'docs/ley-organica.pdf'" in catalogo.notas
    assert "fuera de la tabla" not in catalogo.notas


def test_dos_ortografias_del_mismo_documento_dan_una_entrada() -> None:
    catalogo = _con_maniqui("dos_ortografias", [Enlace("Acuerdos rectorales 2", "docs/acuerdos%20rect%202.pdf")])
    assert [e.url_documento for e in catalogo.entries] == ["docs/acuerdos%20rect%202.pdf"]
    assert catalogo.notas is not None
    assert "'docs/acuerdos rect 2.pdf'" in catalogo.notas


def test_la_inventada_no_convierte_nada_en_faltante() -> None:
    catalogo = _con_maniqui("inventada", _TABLA)
    assert catalogo.enlaces_vistos == 2
    assert catalogo.enlaces_sin_cuenta == []
    assert catalogo.lectura_incompleta is False
