from pathlib import Path

import pytest

from legisuni.descargador.paths import ruta_documento, sanear

# Etiquetas reales de data/norm/uam/ (corrida v1, 2026-09-06/08). Ya llegaban
# saneadas: sin mayúsculas ni %20. Confirman que la regex de validación no
# rechaza por accidente lo que produce el corpus real.
_ETIQUETAS_REALES_V1 = [
    "04.11.2024__2026-09-06",
    "2026__2026-09-06",
    "2__2026-09-06",
    "3a__2026-09-06",
    "3b__2026-09-06",
    "anexo1__2026-09-06",
    "anexo3c__2026-09-06",
    "ceuam__2026-09-06",
    "lgnma__2026-09-06",
    "lo__2026-09-06",
    "pavrg__2026-09-06",
    "pg__2026-09-06",
    "poai__2026-09-06",
    "pod__2026-09-06",
]


def test_sanear_minusculas_sin_acentos_ni_espacios() -> None:
    assert sanear("REGLAMENTO Académico Ñ") == "reglamento-academico-n"


def test_sanear_todo_eliminado_devuelve_sin_nombre() -> None:
    assert sanear("---") == "sin-nombre"


def test_ruta_documento_sin_hash() -> None:
    ruta = ruta_documento(Path("data"), "norm/uam", "reglamento-organico__2026-03-16", ".pdf")
    assert ruta == Path("data/norm/uam/reglamento-organico__2026-03-16.pdf")


def test_ruta_documento_con_hash() -> None:
    ruta = ruta_documento(
        Path("data"),
        "norm/uam",
        "reglamento-organico__2026-03-16",
        ".pdf",
        sha256="abcdef1234567890",
    )
    assert ruta == Path("data/norm/uam/reglamento-organico__2026-03-16__abcdef12.pdf")


def test_ruta_documento_con_y_sin_hash_conviven() -> None:
    sin_hash = ruta_documento(Path("data"), "norm/uam", "reglamento-organico__2026-03-16", ".pdf")
    con_hash = ruta_documento(
        Path("data"),
        "norm/uam",
        "reglamento-organico__2026-03-16",
        ".pdf",
        sha256="abcdef1234567890",
    )
    assert sin_hash != con_hash


@pytest.mark.parametrize("etiqueta", _ETIQUETAS_REALES_V1)
def test_ruta_documento_acepta_etiquetas_reales_del_corpus_v1(etiqueta: str) -> None:
    ruta = ruta_documento(Path("data"), "norm/uam", etiqueta, ".pdf")
    assert ruta == Path(f"data/norm/uam/{etiqueta}.pdf")


def test_ruta_documento_rechaza_etiqueta_con_traversal() -> None:
    with pytest.raises(ValueError):
        ruta_documento(Path("data"), "norm/uam", "..", ".pdf")


def test_ruta_documento_rechaza_etiqueta_con_barra() -> None:
    with pytest.raises(ValueError):
        ruta_documento(Path("data"), "norm/uam", "sub/dir", ".pdf")


def test_ruta_documento_rechaza_etiqueta_con_mayusculas() -> None:
    with pytest.raises(ValueError):
        ruta_documento(Path("data"), "norm/uam", "ANEXO1", ".pdf")


def test_ruta_documento_rechaza_etiqueta_con_espacio_codificado() -> None:
    with pytest.raises(ValueError):
        ruta_documento(Path("data"), "norm/uam", "anexo%201", ".pdf")


def test_ruta_documento_rechaza_cajon_absoluto() -> None:
    with pytest.raises(ValueError):
        ruta_documento(Path("data"), "/etc", "anexo1", ".pdf")


def test_ruta_documento_rechaza_cajon_con_traversal() -> None:
    with pytest.raises(ValueError):
        ruta_documento(Path("data"), "norm/../../etc", "anexo1", ".pdf")


def test_ruta_documento_acepta_cajon_con_barra() -> None:
    ruta = ruta_documento(Path("data"), "norm/uam", "anexo1", ".pdf")
    assert ruta == Path("data/norm/uam/anexo1.pdf")
