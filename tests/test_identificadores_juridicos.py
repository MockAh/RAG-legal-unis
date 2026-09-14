from legisuni.juridico.identificadores import entry_id

_URL_INDICE_UAM = "https://uam.mx/legislacion"
_URL_INDICE_UJAT = "https://www.ujat.mx/abogado/15763"


def test_dos_historicos_del_res_producen_entry_id_distintos() -> None:
    # C20 de docs/08 (E11.6): la UAM publica dos versiones históricas del
    # Reglamento de Estudios Superiores; con doc_slug="res" para ambas,
    # solo la URL las distingue.
    vigente = entry_id(
        "uam", "res",
        "https://uam.mx/legislacion/legis-univ-uam-res-VIGENTE-HASTA-16.03.2026.pdf",
        _URL_INDICE_UAM,
    )
    historico = entry_id(
        "uam", "res",
        "https://uam.mx/legislacion/leg-univ-uam-res-VIGENTE-HASTA-04.11.2024.pdf",
        _URL_INDICE_UAM,
    )

    assert vigente != historico
    assert vigente.startswith("uam:res:")
    assert historico.startswith("uam:res:")


def test_urls_equivalentes_tras_normalizar_dan_el_mismo_entry_id() -> None:
    # E12.2 de docs/08: "acuerdos rect 2.pdf" y "acuerdos%20rect%202.pdf"
    # son la misma dirección tras normalizar.
    sin_codificar = entry_id(
        "ujat", "acuerdo-rectoral-2",
        "https://archivos.ujat.mx/abogado_gral/Acuerdos/acuerdos rect 2.pdf",
        _URL_INDICE_UJAT,
    )
    codificada = entry_id(
        "ujat", "acuerdo-rectoral-2",
        "https://archivos.ujat.mx/abogado_gral/Acuerdos/acuerdos%20rect%202.pdf",
        _URL_INDICE_UJAT,
    )

    assert sin_codificar == codificada
