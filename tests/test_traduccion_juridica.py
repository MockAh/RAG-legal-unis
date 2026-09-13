from datetime import date, datetime

from legisuni.contracts import CatalogEntry
from legisuni.juridico.traduccion import traducir


def _entrada(**overrides) -> CatalogEntry:
    datos = dict(
        entry_id="uam:reglamento-organico",
        inst_id="uam",
        titulo="Reglamento Orgánico",
        tipo_norma="reglamento",
        url_documento="https://uam.mx/legislacion/reglamento.pdf",
        origen="sitio_institucional",
        url_indice="https://uam.mx/legislacion",
        extraido_en=datetime(2026, 1, 1),
    )
    datos.update(overrides)
    return CatalogEntry(**datos)


def test_fecha_usa_ultima_reforma_si_existe() -> None:
    entrada = _entrada(
        fecha_ultima_reforma=date(2020, 5, 1),
        fecha_publicacion=date(2010, 1, 1),
    )
    encargo = traducir(entrada, "reglamento-organico", ahora=datetime(2026, 3, 16))
    assert encargo.etiqueta == "reglamento-organico__2020-05-01"


def test_fecha_usa_publicacion_si_no_hay_ultima_reforma() -> None:
    entrada = _entrada(fecha_publicacion=date(2010, 1, 1))
    encargo = traducir(entrada, "reglamento-organico", ahora=datetime(2026, 3, 16))
    assert encargo.etiqueta == "reglamento-organico__2010-01-01"


def test_fecha_usa_creacion_del_encargo_si_no_hay_fechas() -> None:
    entrada = _entrada()
    encargo = traducir(entrada, "reglamento-organico", ahora=datetime(2026, 3, 16))
    assert encargo.etiqueta == "reglamento-organico__2026-03-16"


def test_cajon_es_norm_mas_inst_id() -> None:
    entrada = _entrada(inst_id="ujat")
    encargo = traducir(entrada, "reglamento-organico", ahora=datetime(2026, 3, 16))
    assert encargo.cajon == "norm/ujat"


def test_grupo_alias_es_inst_id_mas_doc_slug() -> None:
    entrada = _entrada(inst_id="ujat")
    encargo = traducir(entrada, "reglamento-organico", ahora=datetime(2026, 3, 16))
    assert encargo.grupo_alias == "ujat:reglamento-organico"


def test_una_sola_puerta_enlace_indice_no_construida() -> None:
    entrada = _entrada()
    encargo = traducir(entrada, "reglamento-organico", ahora=datetime(2026, 3, 16))

    assert len(encargo.puertas) == 1
    puerta = encargo.puertas[0]
    assert puerta.tipo == "enlace_indice"
    assert puerta.construida is False
    assert puerta.url == entrada.url_documento
    assert puerta.url_base == entrada.url_indice
    assert puerta.evidencia == entrada.url_indice


def test_cruzar_vestibulos_false() -> None:
    entrada = _entrada()
    encargo = traducir(entrada, "reglamento-organico", ahora=datetime(2026, 3, 16))
    assert encargo.cruzar_vestibulos is False
