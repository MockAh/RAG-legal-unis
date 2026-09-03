from legisuni.descargador.guard import es_visor_de_terceros, evaluar, extension_por_firma

_MAX_BYTES = 100 * 1024 * 1024
_PDF_BYTES = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\n"
_DOCX_BYTES = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"
_HTML_BYTES = b"<!DOCTYPE html>\n<html><head><title>Iniciar sesi\xc3\xb3n</title></head></html>"


def test_extension_por_firma_pdf() -> None:
    assert extension_por_firma(_PDF_BYTES) == ".pdf"


def test_extension_por_firma_docx() -> None:
    assert extension_por_firma(_DOCX_BYTES) == ".docx"


def test_extension_por_firma_desconocida_es_none() -> None:
    assert extension_por_firma(_HTML_BYTES) is None


def test_evaluar_pdf_valido() -> None:
    assert evaluar("https://archivos.ujat.mx/2021/x.pdf", _PDF_BYTES, 1024, _MAX_BYTES) == (
        None,
        ".pdf",
    )


def test_evaluar_docx_valido() -> None:
    assert evaluar("https://archivos.ujat.mx/2021/x.docx", _DOCX_BYTES, 1024, _MAX_BYTES) == (
        None,
        ".docx",
    )


def test_evaluar_landing_page_no_es_pdf() -> None:
    assert evaluar("https://archivos.ujat.mx/2021/x.pdf", _HTML_BYTES, 1024, _MAX_BYTES) == (
        "no_es_pdf",
        None,
    )


def test_visor_de_terceros_precede_al_guardian_de_bytes() -> None:
    url = "https://drive.google.com/file/d/1AbC_xyz/view"
    assert es_visor_de_terceros(url) == "Google Drive"
    assert evaluar(url, _HTML_BYTES, 1024, _MAX_BYTES) == ("visor_de_terceros", None)


def test_visor_de_terceros_no_depende_del_contenido() -> None:
    url = "https://drive.google.com/file/d/1AbC_xyz/view"
    assert evaluar(url, _PDF_BYTES, 1024, _MAX_BYTES) == ("visor_de_terceros", None)


def test_host_de_visor_sin_ruta_de_visor_no_es_visor() -> None:
    url = "https://drive.google.com/"
    assert es_visor_de_terceros(url) is None
    assert evaluar(url, _HTML_BYTES, 1024, _MAX_BYTES) == ("no_es_pdf", None)


def test_demasiado_grande() -> None:
    tamano = 200 * 1024 * 1024
    assert evaluar("https://archivos.ujat.mx/2021/x.pdf", _PDF_BYTES, tamano, _MAX_BYTES) == (
        "demasiado_grande",
        None,
    )


def test_tamano_none_no_lanza_excepcion() -> None:
    assert evaluar("https://archivos.ujat.mx/2021/x.pdf", _PDF_BYTES, None, _MAX_BYTES) == (
        None,
        ".pdf",
    )


def test_bytes_vacios_no_lanza_excepcion() -> None:
    assert evaluar("https://archivos.ujat.mx/2021/x.pdf", b"", 0, _MAX_BYTES) == (
        "no_es_pdf",
        None,
    )


def test_xlsx_pasa_como_docx_por_diseno() -> None:
    xlsx_bytes = b"PK\x03\x04\x14\x00\x06\x00\x08\x00"
    assert extension_por_firma(xlsx_bytes) == ".docx"
    assert evaluar("https://archivos.ujat.mx/2021/x.xlsx", xlsx_bytes, 1024, _MAX_BYTES) == (
        None,
        ".docx",
    )
