from legisuni.descargador import muros


def test_patrones_reales_compilan() -> None:
    # Carga legisuni/datos/patrones.toml de verdad, no un fixture: un ruta_regex
    # mal escrito debe romper aquí, en los tests, no en una corrida real.
    patrones = muros._cargar_patrones()

    assert len(patrones) >= 1
    for patron in patrones:
        assert patron["_regex"].pattern == patron["ruta_regex"]


def test_401_es_muro() -> None:
    assert muros.es_muro_de_pago(401, "https://a.mx/articulo") is True


def test_402_es_muro() -> None:
    assert muros.es_muro_de_pago(402, "https://a.mx/articulo") is True


def test_403_no_es_muro() -> None:
    assert muros.es_muro_de_pago(403, "https://a.mx/articulo") is False


def test_redireccion_a_shibboleth_es_muro() -> None:
    url = "https://cualquier-universidad.mx/Shibboleth.sso/Login?target=x"
    assert muros.es_muro_de_pago(200, url) is True


def test_url_sin_patron_no_es_muro() -> None:
    assert muros.es_muro_de_pago(200, "https://a.mx/articulo.pdf") is False
