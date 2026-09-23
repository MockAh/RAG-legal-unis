import hashlib
from datetime import datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from legisuni.config import Settings
from legisuni.contracts import DownloadResult, Encargo, Puerta
from legisuni.descargador.descargar import descargar
from legisuni.descargador.fetch import Fetcher
from legisuni.descargador.store import Store

_PDF_BYTES = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\n"
_PDF_BYTES_V2 = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n2 0 obj\n<< /Type /Catalog /V2 true >>\n"
_DOCX_BYTES = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"
_HTML_BYTES = b"<!DOCTYPE html>\n<html><head><title>Iniciar sesion</title></head></html>"


class DormirFalso:
    def __call__(self, segundos: float) -> None:
        pass


class LimitadorSinEspera:
    def esperar(self, url: str) -> float:
        return 0.0


class RobotsPermiteTodo:
    def permitido(self, url: str) -> bool:
        return True


class RobotsProhibeTodo:
    def permitido(self, url: str) -> bool:
        return False


class FetcherContador:
    def __init__(self) -> None:
        self.llamadas = 0

    def pedir(self, url: str):
        self.llamadas += 1
        raise AssertionError("fetcher.pedir no debería invocarse")


def _settings(tmp_path: Path, **overrides) -> Settings:
    valores = dict(user_agent="LegisUni-test/1.0", data_root=tmp_path)
    valores.update(overrides)
    return Settings(**valores)


def _fetcher(settings: Settings) -> Fetcher:
    return Fetcher(
        settings=settings,
        limitador=LimitadorSinEspera(),
        robots=None,
        cliente=httpx.Client(),
        dormir=DormirFalso(),
    )


def _puerta(url: str, url_base: str | None = None) -> Puerta:
    return Puerta(url=url, tipo="enlace_indice", url_base=url_base, evidencia="test")


def _encargo(
    url_documento: str = "https://a.mx/x.pdf",
    url_indice: str = "https://a.mx/indice",
    **overrides,
) -> Encargo:
    datos = dict(
        encargo_id="uam:reglamento-organico",
        modo="juridico",
        solicitante="uam",
        puertas=[
            Puerta(
                url=url_documento,
                tipo="enlace_indice",
                url_base=url_indice,
                evidencia=url_indice,
            )
        ],
        cajon="norm/uam",
        etiqueta="reglamento-organico__2026-03-16",
        cruzar_vestibulos=False,
        grupo_alias="uam:reglamento-organico",
        creado_en=datetime(2026, 1, 1),
    )
    datos.update(overrides)
    return Encargo(**datos)


def test_pdf_valido_se_escribe_y_hash_coincide(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo()

    resultado = descargar(
        encargo, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=datetime(2026, 3, 16)
    )

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.exists()
    assert resultado.ruta_local.suffix == ".pdf"
    assert hashlib.sha256(resultado.ruta_local.read_bytes()).hexdigest() == resultado.sha256


def test_robots_prohibe_no_llama_al_fetcher(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    encargo = _encargo()
    fetcher = FetcherContador()

    resultado = descargar(encargo, fetcher, RobotsProhibeTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "robots_prohibido"
    assert fetcher.llamadas == 0


def test_landing_page_no_es_pdf_no_escribe_nada(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=_HTML_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo()

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "no_es_pdf"
    assert list(tmp_path.rglob("*")) == []


def test_visor_de_terceros_no_escribe_nada(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    url = "https://drive.google.com/file/d/1AbC_xyz/view"
    httpx_mock.add_response(url=url, status_code=200, content=_HTML_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo(url_documento=url, url_indice="https://drive.google.com/")

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.motivo_fallo == "visor_de_terceros"
    assert list(tmp_path.rglob("*")) == []


def test_404_no_escribe_nada(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404)
    settings = _settings(tmp_path)
    encargo = _encargo()

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.motivo_fallo == "url_muerta"
    assert list(tmp_path.rglob("*")) == []


def test_idempotencia_misma_respuesta_deja_un_solo_archivo(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo()
    fecha = datetime(2026, 3, 16)

    resultado1 = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)
    resultado2 = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)

    archivos = list(tmp_path.rglob("*.pdf"))
    assert len(archivos) == 1
    assert resultado1.ruta_local == resultado2.ruta_local


def test_version_nueva_con_bytes_distintos_deja_dos_archivos(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES_V2)
    settings = _settings(tmp_path)
    encargo = _encargo()
    fecha = datetime(2026, 3, 16)

    resultado1 = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)
    resultado2 = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)

    archivos = list(tmp_path.rglob("*.pdf"))
    assert len(archivos) == 2
    nombres = sorted(a.name for a in archivos)
    assert nombres[0].count("__") == 1   # slug__fecha.pdf
    assert nombres[1].count("__") == 2   # slug__fecha__hash.pdf


def test_url_cruda_no_se_modifica(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    cruda = "/2015/abogado general/nuevos/A_DISTANCIA.pdf"
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo(url_documento=cruda, url_indice="https://www.ujat.mx/abogado/15763")

    descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert encargo.puertas[0].url == cruda


def test_docx_se_guarda_con_extension_docx(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=_DOCX_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo(url_documento="https://a.mx/x.docx")

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.suffix == ".docx"


def test_fallo_de_escritura_no_propaga_excepcion(
    tmp_path: Path, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo()

    def _falla(self, data):
        raise OSError("disco lleno")

    monkeypatch.setattr(Path, "write_bytes", _falla)

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "http_error"


def test_omite_encargo_id_ya_registrado_con_exito(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    encargo = _encargo()
    fetcher = FetcherContador()

    with Store(tmp_path / "store.db") as store:
        store.guardar(
            DownloadResult(
                encargo_id=encargo.encargo_id,
                modo="juridico",
                exito=True,
                capturado_en=datetime(2026, 1, 1),
                ruta_local=tmp_path / "reglamento-organico.pdf",
                sha256="abc123",
                intentos=[],
            )
        )

        resultado = descargar(encargo, fetcher, RobotsPermiteTodo(), settings, store=store)

    assert resultado.exito is True
    assert resultado.ruta_local == tmp_path / "reglamento-organico.pdf"
    assert fetcher.llamadas == 0


def test_encargo_id_no_registrado_descarga_normalmente(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo()

    with Store(tmp_path / "store.db") as store:
        resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings, store=store)

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.exists()


def test_encargo_id_registrado_como_fallo_descarga_igual(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo()

    with Store(tmp_path / "store.db") as store:
        store.guardar(
            DownloadResult(
                encargo_id=encargo.encargo_id,
                modo="juridico",
                exito=False,
                motivo_fallo="timeout",
                capturado_en=datetime(2026, 1, 1),
                intentos=[],
            )
        )

        resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings, store=store)

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.exists()


# M26, criterio 13: puertas múltiples. Con una sola puerta (todos los tests de
# arriba) el comportamiento es idéntico al de v2 — es lo que exige el criterio 11.


def test_tres_puertas_la_segunda_entrega_pdf(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    url_404 = "https://a.mx/no-existe.pdf"
    url_ok = "https://a.mx/ok.pdf"
    url_nunca = "https://a.mx/nunca-pedida.pdf"
    httpx_mock.add_response(url=url_404, status_code=404)
    httpx_mock.add_response(url=url_ok, status_code=200, content=_PDF_BYTES)
    # url_nunca no se registra: si el bucle la pidiera, pytest-httpx hace fallar el test solo.
    settings = _settings(tmp_path)
    encargo = _encargo(puertas=[_puerta(url_404), _puerta(url_ok), _puerta(url_nunca)])

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is True
    assert resultado.puerta_usada == 1
    assert len(resultado.intentos) == 2
    assert resultado.intentos[0].exito is False
    assert resultado.intentos[1].exito is True


def test_primera_puerta_da_html_segunda_da_pdf(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    # Un 200 que el guardián rechaza (HTML) es puerta fallida, no error de red: el
    # bucle sigue a la siguiente puerta. (En M28, con cruzar_vestibulos=True, esta
    # misma puerta intentará el cruce de vestíbulo antes de darse por fallida.)
    url_html = "https://a.mx/landing.pdf"
    url_ok = "https://a.mx/ok.pdf"
    httpx_mock.add_response(url=url_html, status_code=200, content=_HTML_BYTES)
    httpx_mock.add_response(url=url_ok, status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo(puertas=[_puerta(url_html), _puerta(url_ok)])

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is True
    assert resultado.puerta_usada == 1
    assert len(resultado.intentos) == 2
    assert resultado.intentos[0].motivo_fallo == "no_es_pdf"


def test_todas_las_puertas_fallan_da_puertas_agotadas(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    urls = ["https://a.mx/1.pdf", "https://a.mx/2.pdf", "https://a.mx/3.pdf"]
    for url in urls:
        httpx_mock.add_response(url=url, status_code=404)
    settings = _settings(tmp_path)
    encargo = _encargo(puertas=[_puerta(url) for url in urls])

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "puertas_agotadas"
    assert len(resultado.intentos) == 3
    assert all(intento.motivo_fallo == "url_muerta" for intento in resultado.intentos)


# M27, criterio 15: muros. El reconocimiento no distingue modo (docs/01 989-991),
# así que muro_de_pago puede salir en un Encargo jurídico igual que en uno académico.


def test_401_da_muro_de_pago(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=401)
    settings = _settings(tmp_path)
    encargo = _encargo()

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "muro_de_pago"


def test_402_da_muro_de_pago(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=402)
    settings = _settings(tmp_path)
    encargo = _encargo()

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "muro_de_pago"


def test_403_no_es_muro_sigue_siendo_http_error(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=403)
    settings = _settings(tmp_path)
    encargo = _encargo()

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "http_error"


def test_redireccion_a_shibboleth_da_muro_de_pago(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    url_documento = "https://a.mx/articulo.pdf"
    url_login = "https://a.mx/Shibboleth.sso/Login?target=articulo.pdf"
    httpx_mock.add_response(url=url_documento, status_code=302, headers={"Location": url_login})
    httpx_mock.add_response(url=url_login, status_code=200, content=_HTML_BYTES)
    settings = _settings(tmp_path)
    encargo = _encargo(url_documento=url_documento)

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "muro_de_pago"


# M21, excepción al criterio 11 autorizada por el criterio 4 de docs/05: hasta
# aquí, sin bandera, lo ya registrado SÍ pedía la red (test_default_no_omite_y_
# llama_al_fetcher). Regla 5 invierte ese default a propósito. No se registra
# ninguna respuesta en httpx_mock: si descargar() llegara a pedir la red,
# pytest-httpx hace fallar el test solo.
def test_ya_registrado_no_toca_la_red_sin_ninguna_respuesta_mockeada(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    settings = _settings(tmp_path)
    encargo = _encargo()

    with Store(tmp_path / "store.db") as store:
        store.guardar(
            DownloadResult(
                encargo_id=encargo.encargo_id,
                modo="juridico",
                exito=True,
                capturado_en=datetime(2026, 1, 1),
                ruta_local=tmp_path / "reglamento-organico.pdf",
                sha256="abc123",
                intentos=[],
            )
        )

        resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings, store=store)

    assert resultado.exito is True
    assert resultado.ruta_local == tmp_path / "reglamento-organico.pdf"


# M28, criterio 14: cruce de vestíbulo. Solo con cruzar_vestibulos=True y respuesta
# HTML; un solo salto. httpx_mock sin respuestas de sobra: una petición no
# registrada hace fallar el test solo, y además se cuentan las peticiones.

_URL_VESTIBULO = "https://repo.example.org/articulo/123"
_URL_ARCHIVO = "https://repo.example.org/descarga/123.pdf"


def _html(cuerpo_head: str = "", cuerpo_body: str = "") -> bytes:
    return (
        f"<!DOCTYPE html>\n<html><head><title>Articulo</title>{cuerpo_head}</head>"
        f"<body>{cuerpo_body}</body></html>"
    ).encode("utf-8")


_HTML_CON_META = _html(f'<meta name="citation_pdf_url" content="{_URL_ARCHIVO}">')


def _encargo_academico(url: str = _URL_VESTIBULO, **overrides) -> Encargo:
    datos = dict(
        encargo_id="doi:10.1126/science.215.4539.1501",
        modo="academico",
        solicitante="geologia-dois-3f9a0c1b",
        puertas=[Puerta(url=url, tipo="copia_libre", url_base=None, evidencia="lista:test#1")],
        cajon="papers",
        etiqueta="raup-1982__3f9a0c1b",
        cruzar_vestibulos=True,
        grupo_alias="doi:10.1126/science.215.4539.1501",
        creado_en=datetime(2026, 1, 1),
    )
    datos.update(overrides)
    return Encargo(**datos)


def test_vestibulo_con_citation_pdf_url_cruza_y_guarda(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_URL_VESTIBULO, status_code=200, content=_HTML_CON_META)
    httpx_mock.add_response(url=_URL_ARCHIVO, status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)

    resultado = descargar(_encargo_academico(), _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.read_bytes() == _PDF_BYTES
    assert resultado.url_final == _URL_ARCHIVO
    assert len(resultado.intentos) == 1
    intento = resultado.intentos[0]
    assert intento.enlace_vestibulo == _URL_ARCHIVO
    assert intento.url_final == _URL_ARCHIVO
    assert intento.url_pedida == _URL_VESTIBULO
    assert len(httpx_mock.get_requests()) == 2


def test_vestibulo_sin_enlace_da_vestibulo_sin_pdf(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_URL_VESTIBULO, status_code=200, content=_html(cuerpo_body="<p>Sin archivo</p>")
    )
    settings = _settings(tmp_path)

    resultado = descargar(_encargo_academico(), _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "vestibulo_sin_pdf"
    assert resultado.intentos[0].enlace_vestibulo is None
    assert len(httpx_mock.get_requests()) == 1
    assert list(tmp_path.rglob("*")) == []


def test_enlace_que_devuelve_html_da_vestibulo_sin_pdf_sin_segundo_salto(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    # el segundo HTML también trae meta: si hubiera recursión, habría una tercera petición
    url_otra = "https://repo.example.org/descarga/otra.pdf"
    httpx_mock.add_response(url=_URL_VESTIBULO, status_code=200, content=_HTML_CON_META)
    httpx_mock.add_response(
        url=_URL_ARCHIVO,
        status_code=200,
        content=_html(f'<meta name="citation_pdf_url" content="{url_otra}">'),
    )
    settings = _settings(tmp_path)

    resultado = descargar(_encargo_academico(), _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "vestibulo_sin_pdf"
    assert resultado.intentos[0].enlace_vestibulo == _URL_ARCHIVO
    assert [str(p.url) for p in httpx_mock.get_requests()] == [_URL_VESTIBULO, _URL_ARCHIVO]
    assert list(tmp_path.rglob("*")) == []


def test_dos_enlaces_a_pdf_distintos_sin_meta_da_vestibulo_sin_pdf(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    html = _html(
        cuerpo_body='<a href="/descarga/123.pdf">Artículo</a>'
        '<a href="/descarga/123-suplementario.pdf">Material suplementario</a>'
    )
    httpx_mock.add_response(url=_URL_VESTIBULO, status_code=200, content=html)
    settings = _settings(tmp_path)

    resultado = descargar(_encargo_academico(), _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "vestibulo_sin_pdf"
    assert len(httpx_mock.get_requests()) == 1


def test_mismo_html_sin_cruzar_vestibulos_da_no_es_pdf(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_URL_VESTIBULO, status_code=200, content=_HTML_CON_META)
    settings = _settings(tmp_path)
    encargo = _encargo_academico(cruzar_vestibulos=False)

    resultado = descargar(encargo, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "no_es_pdf"
    assert resultado.intentos[0].enlace_vestibulo is None
    assert len(httpx_mock.get_requests()) == 1


def test_enlace_relativo_se_resuelve_contra_url_final_del_vestibulo(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    html = _html(cuerpo_body='<a href="../descarga/123.pdf">PDF</a>')
    httpx_mock.add_response(url=_URL_VESTIBULO, status_code=200, content=html)
    httpx_mock.add_response(url=_URL_ARCHIVO, status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)

    resultado = descargar(_encargo_academico(), _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is True
    # se registra el literal de la página (D3), no la URL resuelta
    assert resultado.intentos[0].enlace_vestibulo == "../descarga/123.pdf"
    assert resultado.url_final == _URL_ARCHIVO


def test_fallo_del_salto_conserva_su_propio_motivo(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_URL_VESTIBULO, status_code=200, content=_HTML_CON_META)
    httpx_mock.add_response(url=_URL_ARCHIVO, status_code=404)
    settings = _settings(tmp_path)

    resultado = descargar(_encargo_academico(), _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "url_muerta"
    assert resultado.intentos[0].enlace_vestibulo == _URL_ARCHIVO
    assert resultado.intentos[0].http_status == 404


def test_robots_que_prohibe_el_enlace_no_lo_pide(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    class RobotsProhibeEnlace:
        def permitido(self, url: str) -> bool:
            return url != _URL_ARCHIVO

    httpx_mock.add_response(url=_URL_VESTIBULO, status_code=200, content=_HTML_CON_META)
    settings = _settings(tmp_path)

    resultado = descargar(_encargo_academico(), _fetcher(settings), RobotsProhibeEnlace(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "robots_prohibido"
    assert resultado.intentos[0].enlace_vestibulo == _URL_ARCHIVO
    assert len(httpx_mock.get_requests()) == 1
