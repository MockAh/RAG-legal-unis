from datetime import datetime
from typing import get_args

import pytest
from pydantic import ValidationError

from legisuni.contracts import (
    JERARQUIA,
    CatalogEntry,
    DownloadResult,
    TipoNorma,
)


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
        entry_id="e1",
        exito=False,
        motivo_fallo="visor_de_terceros",
        capturado_en=datetime(2026, 1, 1),
    )
    assert resultado.motivo_fallo == "visor_de_terceros"


def test_download_result_motivo_fallo_invalido_lanza_validation_error() -> None:
    with pytest.raises(ValidationError):
        DownloadResult(
            entry_id="e1",
            exito=False,
            motivo_fallo="basura",
            capturado_en=datetime(2026, 1, 1),
        )


def test_jerarquia_cubre_exactamente_el_vocabulario_de_tipo_norma() -> None:
    tipos_validos = set(get_args(TipoNorma))
    assert set(JERARQUIA.keys()) == tipos_validos
