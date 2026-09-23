from legisuni.descargador.urlnorm import normalizar, url_id


def test_relativa_con_espacios_en_nombre_de_archivo() -> None:
    cruda = "/abogado_gral/legislacion_univ2012/REGLAMENTO DE LA HONORABLE JUNTA DE GOBIERNO.pdf"
    indice = "https://www.ujat.mx/abogado/15763"

    resultado = normalizar(cruda, indice)

    assert resultado == (
        "https://www.ujat.mx/abogado_gral/legislacion_univ2012/"
        "REGLAMENTO%20DE%20LA%20HONORABLE%20JUNTA%20DE%20GOBIERNO.pdf"
    )


def test_espacio_en_nombre_de_carpeta_tambien_se_codifica() -> None:
    cruda = "/2015/abogado general/nuevos/A_DISTANCIA.pdf"
    indice = "https://www.ujat.mx/abogado/15763"

    resultado = normalizar(cruda, indice)

    assert resultado == "https://www.ujat.mx/2015/abogado%20general/nuevos/A_DISTANCIA.pdf"


def test_espacio_final_en_href_se_recorta() -> None:
    cruda = "https://archivos.ujat.mx/2024/abogado_gral/legislacion-20032024.pdf "
    indice = "https://www.ujat.mx/abogado/15763"

    resultado = normalizar(cruda, indice)

    assert resultado == "https://archivos.ujat.mx/2024/abogado_gral/legislacion-20032024.pdf"
    assert not resultado.endswith(" ")


def test_no_promueve_http_a_https() -> None:
    cruda = "http://archivos.ujat.mx/2021/x.pdf"
    indice = "https://www.ujat.mx/abogado/15763"

    resultado = normalizar(cruda, indice)

    assert resultado == "http://archivos.ujat.mx/2021/x.pdf"
    assert resultado.startswith("http://")


def test_idempotente_con_url_ya_codificada() -> None:
    cruda = "https://www.ujat.mx/abogado_gral/legislacion_univ2012/REGLAMENTO%20DE%20LA%20HONORABLE.pdf"
    indice = "https://www.ujat.mx/abogado/15763"

    primera = normalizar(cruda, indice)
    segunda = normalizar(primera, indice)

    assert primera == cruda
    assert segunda == primera


def test_acento_se_codifica_en_utf8() -> None:
    cruda = "/abogado_gral/legislacion_univ2012/REGLAMENTO_ACADÉMICO.pdf"
    indice = "https://www.ujat.mx/abogado/15763"

    resultado = normalizar(cruda, indice)

    assert resultado == (
        "https://www.ujat.mx/abogado_gral/legislacion_univ2012/"
        "REGLAMENTO_ACAD%C3%89MICO.pdf"
    )


def test_url_absoluta_y_limpia_no_cambia() -> None:
    cruda = "https://archivos.ujat.mx/2021/abogado_gral/reglamento.pdf"
    indice = "https://www.ujat.mx/abogado/15763"

    resultado = normalizar(cruda, indice)

    assert resultado == cruda


def test_url_id_son_12_caracteres_hexadecimales() -> None:
    resultado = url_id("https://archivos.ujat.mx/2021/abogado_gral/reglamento.pdf", "https://www.ujat.mx/abogado/15763")

    assert len(resultado) == 12
    assert all(c in "0123456789abcdef" for c in resultado)


def test_url_id_de_urls_equivalentes_tras_normalizar_coincide() -> None:
    indice = "https://www.ujat.mx/abogado/15763"
    sin_codificar = "https://archivos.ujat.mx/abogado_gral/Acuerdos/acuerdos rect 2.pdf"
    codificada = "https://archivos.ujat.mx/abogado_gral/Acuerdos/acuerdos%20rect%202.pdf"

    assert url_id(sin_codificar, indice) == url_id(codificada, indice)
