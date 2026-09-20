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
