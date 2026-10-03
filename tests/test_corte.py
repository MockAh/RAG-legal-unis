"""M43: lector/corte.py. Sin red y sin LLM."""

from datetime import date
from pathlib import Path

import pytest

from legisuni.config import Settings
from legisuni.lector.corte import Corte, buscar_corte, esta_caducado
from legisuni.lector.reduce import reducir

FIX = Path(__file__).resolve().parent.parent / "fixtures"
CT = "text/html; charset=UTF-8"


def _texto(nombre: str, ct: str | None) -> str:
    return reducir((FIX / nombre).read_bytes(), ct).texto


def test_uacam_fecha_de_corte_diciembre_2016():
    c = buscar_corte(_texto("uacam__2026-10-01.html", CT))
    assert c is not None
    assert c.fecha == date(2016, 12, 31)
    assert "Fecha de corte" in c.texto and "Diciembre del 2016" in c.texto
    assert "\u00a0" not in c.texto
    assert c.patron == "fecha de corte"


@pytest.mark.parametrize(
    "nombre,ct",
    [
        ("uam-index.html", None),
        ("ujat-15763.html", None),
        ("ujat-16443.html", None),
        ("ujat-17669.html", None),
        ("ujat-33794.html", None),
        ("ujat-4232.html", None),
        ("unam-oag__2026-10-01.html", CT),
        ("unam-70i__2026-10-01.html", CT),
    ],
)
def test_control_negativo(nombre, ct):
    assert buscar_corte(_texto(nombre, ct)) is None


@pytest.mark.parametrize(
    "texto,fecha",
    [
        ("Fecha de corte: 16 de marzo de 2026", date(2026, 3, 16)),
        ("Fecha de corte: Diciembre del 2016", date(2016, 12, 31)),
        ("Fecha de corte: diciembre 2016", date(2016, 12, 31)),
        ("Actualizado al febrero de 2024", date(2024, 2, 29)),
        ("Periodo que se informa: 2019", date(2019, 12, 31)),
        ("ÚLTIMA ACTUALIZACIÓN:\u00a0Septiembre\u00a02025", date(2025, 9, 30)),
        ("Vigente al 1 de enero del 2020", date(2020, 1, 1)),
    ],
)
def test_conversion(texto, fecha):
    c = buscar_corte(texto)
    assert c is not None and c.fecha == fecha


def test_literal_colapsado_y_sin_acentos_ni_mayusculas_en_el_patron():
    c = buscar_corte("x  ÚLTIMA\n ACTUALIZACIÓN:\u00a0Marzo\u00a0de\u00a02021 resto")
    assert c == Corte("ÚLTIMA ACTUALIZACIÓN: Marzo de 2021", date(2021, 3, 31), "ultima actualizacion")


def test_patron_sin_fecha_legible_conserva_texto():
    c = buscar_corte("Fecha de corte: próximamente")
    assert c is not None
    assert c.fecha is None
    assert c.texto == "Fecha de corte: próximamente"


def test_fecha_imposible_da_none():
    c = buscar_corte("Fecha de corte: 31 de febrero de 2020")
    assert c is not None and c.fecha is None and "31 de febrero" in c.texto


def test_gana_la_primera_coincidencia():
    c = buscar_corte("Vigente al 2018 y Fecha de corte: 2020")
    assert c is not None and c.patron == "vigente al" and c.fecha == date(2018, 12, 31)


def test_sin_patron():
    assert buscar_corte("nada que ver 2016") is None


def test_esta_caducado():
    hoy = date(2026, 10, 3)
    assert esta_caducado(date(2016, 12, 31), hoy, 18) is True
    assert esta_caducado(date(2026, 4, 3), hoy, 18) is False  # hace 6 meses


def test_limite_exacto_no_es_caducado():
    # Decisión: "anterior a hoy menos umbral" es estricto; justo en el límite NO caduca.
    hoy = date(2026, 10, 3)
    limite = date(2025, 4, 3)
    assert esta_caducado(limite, hoy, 18) is False
    assert esta_caducado(date(2025, 4, 2), hoy, 18) is True


def test_limite_con_dia_inexistente():
    assert esta_caducado(date(2025, 2, 28), date(2026, 8, 31), 18) is False
    assert esta_caducado(date(2025, 2, 27), date(2026, 8, 31), 18) is True


def test_umbral_en_settings():
    assert Settings(user_agent="t").umbral_caducidad_meses == 18
