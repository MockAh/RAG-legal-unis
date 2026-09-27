"""Valida la salida de scripts/convertir_bloque.py sobre el Bloque B (M36). El conversor no tiene tests propios."""

import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from legisuni.contracts import Encargo

_JSON = Path(__file__).resolve().parent.parent / "datos" / "encargos_bloque_b.json"


@pytest.fixture(scope="module")
def lote() -> dict:
    return json.loads(_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def encargos(lote: dict) -> dict[str, Encargo]:
    validados = [Encargo.model_validate(e) for e in lote["encargos"]]
    return {e.puertas[0].evidencia.rsplit("#", 1)[-1]: e for e in validados}


def test_treinta_encargos_y_dos_monografias_sin_puertas(lote: dict, encargos: dict[str, Encargo]) -> None:
    assert len(encargos) == 30
    assert "B.11" not in encargos and "B.22" not in encargos
    assert len({e.encargo_id for e in encargos.values()}) == 30
    faltantes = {f["articulo_id"].split("-")[0]: f for f in lote["no_obtenidos"]}
    assert sorted(faltantes) == ["ref:erwin", "ref:mcghee"]
    assert all(f["motivo"] == "sin_puertas" and f["intentos"] == 0 for f in faltantes.values())


def test_traduccion_academica(encargos: dict[str, Encargo]) -> None:
    for encargo in encargos.values():
        assert encargo.modo == "academico"
        assert encargo.cajon == "papers"
        assert encargo.cruzar_vestibulos is True
        assert encargo.grupo_alias == encargo.encargo_id


_ORDEN_TIPOS = ["copia_libre", "oficial", "resolutor_doi"]


def test_puertas_ordenadas_por_tipo(encargos: dict[str, Encargo]) -> None:
    for encargo in encargos.values():
        rangos = [_ORDEN_TIPOS.index(p.tipo) for p in encargo.puertas]
        assert rangos == sorted(rangos)
        # todos los DOI de este lote traen su enlace doi.org literal: nada se construye
        assert not any(p.construida for p in encargo.puertas)


def test_pmc_es_copia_libre_por_lo_que_es(encargos: dict[str, Encargo]) -> None:
    for posicion in ("B.13", "B.15", "B.15C", "B.16", "B.34"):
        primera = encargos[posicion].puertas[0]
        assert "ncbi.nlm.nih.gov" in primera.url
        assert primera.tipo == "copia_libre"


def test_no_son_puerta_researchgate_doaj_ni_el_suplemento(lote: dict, encargos: dict[str, Encargo]) -> None:
    hosts = {urlsplit(p.url).hostname for e in encargos.values() for p in e.puertas}
    for fuera in ("www.researchgate.net", "doaj.org", "gsapubs.figshare.com", "pubmed.ncbi.nlm.nih.gov"):
        assert fuera not in hosts
    [suplemento] = [r for r in lote["registros"] if "figshare" in r["url"]]
    assert suplemento["posicion_en_lista"] == "B.10"
    assert suplemento["nota"] == "material suplementario"
    assert [r["posicion_en_lista"] for r in lote["registros"] if "researchgate" in r["url"]] == ["B.7", "B.9"]
    assert [p.tipo for p in encargos["B.7"].puertas] == ["oficial", "resolutor_doi"]
    assert [p.tipo for p in encargos["B.9"].puertas] == ["oficial", "resolutor_doi"]


def test_b29_conserva_el_doi_crudo(encargos: dict[str, Encargo]) -> None:
    encargo = encargos["B.29"]
    assert encargo.encargo_id == "doi:10.1130/0091-7613(1991)019<0867:ccapct>2.3.co;2"
    # la url cruda va intacta (D3); la codifica urlnorm al pedir
    assert encargo.puertas[-1].url == "https://doi.org/10.1130/0091-7613(1991)019<0867:CCAPCT>2.3.CO;2"


def test_correccion_b15c(lote: dict, encargos: dict[str, Encargo]) -> None:
    correccion = encargos["B.15C"]
    corregido = encargos["B.15"]
    assert correccion.encargo_id.startswith(f"corr:{corregido.encargo_id}:")
    assert correccion.etiqueta.startswith("corr-burgess-2014__")
    vinculo = next(v for v in lote["vinculos"] if v["articulo_id"] == correccion.encargo_id)
    assert vinculo["relacionado_con"] == corregido.encargo_id
    assert vinculo["relacion"] == "correccion"


def test_publicados_en_paralelo_sin_relacion(lote: dict, encargos: dict[str, Encargo]) -> None:
    b33, b33b = encargos["B.33"].encargo_id, encargos["B.33B"].encargo_id
    paralelos = {(v["articulo_id"], v["relacionado_con"]): v["relacion"] for v in lote["vinculos"]}
    assert paralelos[(b33, b33b)] is None
    assert paralelos[(b33b, b33)] is None
