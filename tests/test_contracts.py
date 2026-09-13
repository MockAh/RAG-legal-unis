from datetime import datetime
from typing import get_args

import pytest
from pydantic import ValidationError

from legisuni.contracts import (
    JERARQUIA,
    CatalogEntry,
    DownloadResult,
    Encargo,
    IntentoPuerta,
    Puerta,
    TipoNorma,
)
from legisuni.descargador import guard


def _catalog_entry_minima(**overrides) -> CatalogEntry:
    datos = dict(
        entry_id="e1",
        inst_id="i1",
        titulo="Reglamento Interior",
        tipo_norma="reglamento",
        url_documento="http://example.org/doc.pdf",
        formato_declarado=None,
        origen="sitio_institucional",
        url_indice="http://example.org/indice",
        extraido_en=datetime(2026, 1, 1),
    )
    datos.update(overrides)
    return CatalogEntry(**datos)


def test_catalog_entry_minima_estado_desconocido_por_defecto() -> None:
    entrada = _catalog_entry_minima()
    assert entrada.estado == "desconocido"


def test_url_documento_con_espacios_se_guarda_identica() -> None:
    url = "http://archivos.ujat.mx/2015/abogado general/A_DISTANCIA.pdf"
    entrada = _catalog_entry_minima(url_documento=url)
    assert entrada.url_documento == url


def test_tipo_norma_fuera_de_vocabulario_lanza_validation_error() -> None:
    with pytest.raises(ValidationError):
        _catalog_entry_minima(tipo_norma="no_existe")


def test_download_result_motivo_fallo_valido() -> None:
    resultado = DownloadResult(
        encargo_id="e1",
        modo="juridico",
        exito=False,
        motivo_fallo="visor_de_terceros",
        capturado_en=datetime(2026, 1, 1),
        intentos=[],
    )
    assert resultado.motivo_fallo == "visor_de_terceros"


def test_download_result_motivo_fallo_invalido_lanza_validation_error() -> None:
    with pytest.raises(ValidationError):
        DownloadResult(
            encargo_id="e1",
            modo="juridico",
            exito=False,
            motivo_fallo="basura",
            capturado_en=datetime(2026, 1, 1),
            intentos=[],
        )


def test_jerarquia_cubre_exactamente_el_vocabulario_de_tipo_norma() -> None:
    tipos_validos = set(get_args(TipoNorma))
    assert set(JERARQUIA.keys()) == tipos_validos


def _puerta_minima(**overrides) -> Puerta:
    datos = dict(
        url="https://doi.org/10.1000/xyz",
        tipo="resolutor_doi",
        url_base=None,
        evidencia="lista:lote1#0",
    )
    datos.update(overrides)
    return Puerta(**datos)


def _encargo_minimo(**overrides) -> Encargo:
    datos = dict(
        encargo_id="a1",
        modo="academico",
        solicitante="lote1",
        puertas=[_puerta_minima()],
        cajon="papers",
        etiqueta="autor-2026__abcd1234",
        cruzar_vestibulos=True,
        grupo_alias="a1",
        creado_en=datetime(2026, 1, 1),
    )
    datos.update(overrides)
    return Encargo(**datos)


def test_puerta_se_construye_con_los_campos_de_n10() -> None:
    puerta = _puerta_minima()
    assert puerta.tipo == "resolutor_doi"
    assert puerta.url_base is None
    assert puerta.construida is False


def test_encargo_se_construye_con_los_campos_de_n10() -> None:
    encargo = _encargo_minimo()
    assert encargo.modo == "academico"
    assert encargo.puertas[0].tipo == "resolutor_doi"


def test_intento_puerta_se_construye_con_los_campos_de_n5() -> None:
    intento = IntentoPuerta(
        orden=0,
        url="https://doi.org/10.1000/xyz",
        url_pedida="https://doi.org/10.1000/xyz",
        url_final=None,
        enlace_vestibulo=None,
        http_status=None,
        exito=False,
        motivo_fallo="muro_de_pago",
    )
    assert intento.motivo_fallo == "muro_de_pago"


def test_encargo_sin_puertas_lanza_validation_error() -> None:
    datos = _encargo_minimo().model_dump()
    del datos["puertas"]
    with pytest.raises(ValidationError):
        Encargo(**datos)


def test_encargo_sin_grupo_alias_lanza_validation_error() -> None:
    datos = _encargo_minimo().model_dump()
    del datos["grupo_alias"]
    with pytest.raises(ValidationError):
        Encargo(**datos)


def test_encargo_sin_cruzar_vestibulos_lanza_validation_error() -> None:
    datos = _encargo_minimo().model_dump()
    del datos["cruzar_vestibulos"]
    with pytest.raises(ValidationError):
        Encargo(**datos)


@pytest.mark.parametrize(
    "motivo", ["vestibulo_sin_pdf", "muro_de_pago", "puertas_agotadas"]
)
def test_motivos_fallo_nuevos_son_validos(motivo: str) -> None:
    resultado = DownloadResult(
        encargo_id="e1",
        modo="academico",
        exito=False,
        motivo_fallo=motivo,
        capturado_en=datetime(2026, 1, 1),
        intentos=[],
    )
    assert resultado.motivo_fallo == motivo


def test_download_result_sin_modo_lanza_validation_error() -> None:
    with pytest.raises(ValidationError):
        DownloadResult(
            encargo_id="e1",
            exito=False,
            capturado_en=datetime(2026, 1, 1),
            intentos=[],
        )


def test_download_result_sin_intentos_lanza_validation_error() -> None:
    with pytest.raises(ValidationError):
        DownloadResult(
            encargo_id="e1",
            modo="juridico",
            exito=False,
            capturado_en=datetime(2026, 1, 1),
        )


def test_guard_motivos_validos_contiene_los_diez_motivos() -> None:
    assert guard._MOTIVOS_VALIDOS == {
        "http_error", "no_es_pdf", "timeout", "robots_prohibido",
        "url_muerta", "demasiado_grande", "visor_de_terceros",
        "vestibulo_sin_pdf", "muro_de_pago", "puertas_agotadas",
    }
