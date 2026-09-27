"""Valida la salida de scripts/convertir_bloque.py sobre el Bloque A (M30). El conversor no tiene tests propios."""

import json
from pathlib import Path

import pytest

from legisuni.contracts import Encargo

_JSON = Path(__file__).resolve().parent.parent / "datos" / "encargos_bloque_a.json"


@pytest.fixture(scope="module")
def lote() -> dict:
    return json.loads(_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def encargos(lote: dict) -> dict[str, Encargo]:
    validados = [Encargo.model_validate(e) for e in lote["encargos"]]
    return {e.puertas[0].evidencia.rsplit("#", 1)[-1]: e for e in validados}


def test_siete_encargos_y_a5_sin_puertas(lote: dict, encargos: dict[str, Encargo]) -> None:
    assert sorted(encargos) == ["A.1", "A.2", "A.3", "A.3S", "A.4", "A.6", "A.7"]
    assert len({e.encargo_id for e in encargos.values()}) == 7
    [faltante] = lote["no_obtenidos"]
    assert faltante["motivo"] == "sin_puertas"
    assert faltante["articulo_id"].startswith("ref:hallam-1997-")
    assert faltante["articulo_id"] not in {e.encargo_id for e in encargos.values()}


def test_traduccion_academica(encargos: dict[str, Encargo]) -> None:
    for encargo in encargos.values():
        assert encargo.modo == "academico"
        assert encargo.cajon == "papers"
        assert encargo.cruzar_vestibulos is True
        assert encargo.grupo_alias == encargo.encargo_id
    assert encargos["A.1"].encargo_id == "doi:10.1126/science.215.4539.1501"
    assert encargos["A.1"].etiqueta.startswith("raup-1982__")


_ORDEN_TIPOS = ["copia_libre", "oficial", "resolutor_doi"]


def test_puertas_ordenadas_por_tipo(encargos: dict[str, Encargo]) -> None:
    for encargo in encargos.values():
        rangos = [_ORDEN_TIPOS.index(p.tipo) for p in encargo.puertas]
        assert rangos == sorted(rangos)
        # todos los DOI de este lote traen su enlace doi.org literal: nada se construye
        assert not any(p.construida for p in encargo.puertas)
    # A.7: la copia libre de Semantic Scholar va antes que el PDF de la editorial
    assert [(p.tipo, p.url.split("/")[2]) for p in encargos["A.7"].puertas] == [
        ("copia_libre", "pdfs.semanticscholar.org"),
        ("copia_libre", "www.ncbi.nlm.nih.gov"),
        ("oficial", "www.cambridge.org"),
        ("resolutor_doi", "doi.org"),
    ]


def test_registros_no_son_puerta(lote: dict, encargos: dict[str, Encargo]) -> None:
    hosts = {p.url.split("/")[2] for e in encargos.values() for p in e.puertas}
    assert not hosts & {"pubmed.ncbi.nlm.nih.gov", "ui.adsabs.harvard.edu"}
    assert len(lote["registros"]) == 6  # A.1 ×2, A.2, A.3, A.6, A.7
    assert [p.tipo for p in encargos["A.3"].puertas] == ["resolutor_doi"]


def test_suplemento_sin_relacion_y_vinculo_auxiliar(lote: dict, encargos: dict[str, Encargo]) -> None:
    a3s = encargos["A.3S"]
    assert a3s.encargo_id.startswith("ref:alroy-2008-")
    assert [p.tipo for p in a3s.puertas] == ["copia_libre"]
    assert lote["vinculos"] == [
        {
            "articulo_id": a3s.encargo_id,
            "relacionado_con": encargos["A.3"].encargo_id,
            "literal": "suplemento de A.3",
        }
    ]
