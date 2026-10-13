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
    SourceCandidate,
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


def test_encargo_acepta_los_valores_reales_de_la_traduccion_juridica() -> None:
    encargo = _encargo_minimo(
        modo="juridico",
        cajon="norm/uam",
        etiqueta="reglamento-organico__2026-03-16",
        cruzar_vestibulos=False,
    )
    assert encargo.cajon == "norm/uam"
    assert encargo.etiqueta == "reglamento-organico__2026-03-16"


@pytest.mark.parametrize("etiqueta", ["..", "sub/dir", "ANEXO1", "anexo%201"])
def test_encargo_rechaza_etiqueta_peligrosa(etiqueta: str) -> None:
    with pytest.raises(ValidationError):
        _encargo_minimo(etiqueta=etiqueta)


@pytest.mark.parametrize("cajon", ["/etc", "norm/../../etc"])
def test_encargo_rechaza_cajon_peligroso(cajon: str) -> None:
    with pytest.raises(ValidationError):
        _encargo_minimo(cajon=cajon)


def test_encargo_acepta_cajon_con_barra() -> None:
    encargo = _encargo_minimo(cajon="norm/uam")
    assert encargo.cajon == "norm/uam"


def test_guard_motivos_validos_contiene_los_diez_motivos() -> None:
    assert guard._MOTIVOS_VALIDOS == {
        "http_error", "no_es_pdf", "timeout", "robots_prohibido",
        "url_muerta", "demasiado_grande", "visor_de_terceros",
        "vestibulo_sin_pdf", "muro_de_pago", "puertas_agotadas",
    }


def test_catalog_entry_minima_titulo_derivado_false_por_defecto() -> None:
    entrada = _catalog_entry_minima()
    assert entrada.titulo_derivado is False


def test_catalog_entry_acepta_titulo_derivado_true() -> None:
    entrada = _catalog_entry_minima(titulo_derivado=True)
    assert entrada.titulo_derivado is True


def _source_candidate_minima(**overrides) -> SourceCandidate:
    datos = dict(
        inst_id="uam",
        url="https://www.uam.mx/legislacion/",
        origen="sitio_institucional",
        titulo_pagina="Legislación UAM",
        dominio="www.uam.mx",
        es_dominio_institucional=True,
        confianza="alta",
        razon="la página lista la Ley Orgánica y los reglamentos",
        descubierta_en=datetime(2026, 1, 1),
        evidencia_url="https://www.uam.mx/",
    )
    datos.update(overrides)
    return SourceCandidate(**datos)


def test_source_candidate_se_construye_con_los_campos_de_n1() -> None:
    # N1 no declara defaults: todos sus campos son obligatorios.
    candidata = _source_candidate_minima()
    assert candidata.confianza == "alta"
    assert candidata.origen == "sitio_institucional"


def test_source_candidate_sin_evidencia_url_lanza_validation_error() -> None:
    datos = _source_candidate_minima().model_dump()
    del datos["evidencia_url"]
    with pytest.raises(ValidationError):
        SourceCandidate(**datos)


def test_source_candidate_confianza_fuera_de_vocabulario_lanza_validation_error() -> None:
    with pytest.raises(ValidationError):
        _source_candidate_minima(confianza="total")


# Listas escritas a mano a propósito, copiadas de docs/01 v2.7: un campo que
# desaparezca del código o de N1/N2 tiene que hacer ruido aquí.
def test_campos_de_catalog_entry_coinciden_con_n2() -> None:
    assert list(CatalogEntry.model_fields) == [
        "entry_id", "inst_id", "titulo", "tipo_norma", "url_documento",
        "formato_declarado", "estado", "vigente_hasta", "fecha_publicacion",
        "fecha_ultima_reforma", "categoria_indice", "origen", "url_indice",
        "titulo_derivado", "extraido_en",
    ]


def test_campos_de_source_candidate_coinciden_con_n1() -> None:
    assert list(SourceCandidate.model_fields) == [
        "inst_id", "url", "origen", "titulo_pagina", "dominio",
        "es_dominio_institucional", "confianza", "razon", "descubierta_en",
        "evidencia_url",
    ]
