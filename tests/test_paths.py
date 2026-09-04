from datetime import date, datetime
from pathlib import Path

import pytest

from legisuni.contracts import CatalogEntry
from legisuni.descargador.paths import doc_slug_de, fecha_de_version, ruta_documento, sanear


def _catalog_entry_minima(**overrides) -> CatalogEntry:
    datos = dict(
        entry_id="uam:reglamento-organico",
        inst_id="uam",
        titulo="Reglamento Orgánico",
        tipo_norma="reglamento",
        url_documento="http://example.org/doc.pdf",
        origen="sitio_institucional",
        url_indice="http://example.org/indice",
        extraido_en=datetime(2026, 1, 1),
    )
    datos.update(overrides)
    return CatalogEntry(**datos)


def test_doc_slug_de_caso_simple() -> None:
    assert doc_slug_de("uam:reglamento-organico") == "reglamento-organico"


def test_doc_slug_de_con_prefijo_numerico() -> None:
    assert doc_slug_de("unam:2-LeyOrganicaUNAM") == "2-LeyOrganicaUNAM"


def test_doc_slug_de_sin_dos_puntos_lanza_value_error() -> None:
    with pytest.raises(ValueError):
        doc_slug_de("uam")


def test_doc_slug_de_parte_solo_por_el_primer_separador() -> None:
    assert doc_slug_de("uam:algo:raro") == "algo:raro"


def test_fecha_de_version_elige_ultima_reforma_si_esta_presente() -> None:
    entrada = _catalog_entry_minima(
        fecha_ultima_reforma=date(2020, 1, 1),
        fecha_publicacion=date(2010, 1, 1),
    )
    assert fecha_de_version(entrada, datetime(2026, 1, 1)) == date(2020, 1, 1)


def test_fecha_de_version_elige_publicacion_si_no_hay_ultima_reforma() -> None:
    entrada = _catalog_entry_minima(
        fecha_ultima_reforma=None,
        fecha_publicacion=date(2010, 1, 1),
    )
    assert fecha_de_version(entrada, datetime(2026, 1, 1)) == date(2010, 1, 1)


def test_fecha_de_version_usa_capturado_en_si_ambas_son_none() -> None:
    entrada = _catalog_entry_minima(fecha_ultima_reforma=None, fecha_publicacion=None)
    assert fecha_de_version(entrada, datetime(2026, 3, 16, 12, 0)) == date(2026, 3, 16)


def test_sanear_minusculas_sin_acentos_ni_espacios() -> None:
    assert sanear("REGLAMENTO Académico Ñ") == "reglamento-academico-n"


def test_sanear_todo_eliminado_devuelve_sin_nombre() -> None:
    assert sanear("---") == "sin-nombre"


def test_ruta_documento_sin_hash() -> None:
    ruta = ruta_documento(
        Path("data/norm"), "uam", "uam:reglamento-organico", date(2026, 3, 16), ".pdf"
    )
    assert ruta == Path("data/norm/uam/reglamento-organico__2026-03-16.pdf")


def test_ruta_documento_con_hash() -> None:
    ruta = ruta_documento(
        Path("data/norm"),
        "uam",
        "uam:reglamento-organico",
        date(2026, 3, 16),
        ".pdf",
        sha256="abcdef1234567890",
    )
    assert ruta == Path("data/norm/uam/reglamento-organico__2026-03-16__abcdef12.pdf")


def test_ruta_documento_con_y_sin_hash_conviven() -> None:
    sin_hash = ruta_documento(
        Path("data/norm"), "uam", "uam:reglamento-organico", date(2026, 3, 16), ".pdf"
    )
    con_hash = ruta_documento(
        Path("data/norm"),
        "uam",
        "uam:reglamento-organico",
        date(2026, 3, 16),
        ".pdf",
        sha256="abcdef1234567890",
    )
    assert sin_hash != con_hash


def test_ruta_documento_con_slug_con_espacios_y_acentos_es_segura() -> None:
    ruta = ruta_documento(
        Path("data/norm"),
        "uam",
        "uam:Reglamento Académico Ñ",
        date(2026, 3, 16),
        ".pdf",
    )
    assert " " not in ruta.name
    assert "/" not in ruta.name
    assert ruta.name == "reglamento-academico-n__2026-03-16.pdf"
