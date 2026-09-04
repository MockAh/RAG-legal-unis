import httpx
import pytest
from pytest_httpx import HTTPXMock

from legisuni.config import Settings
from legisuni.descargador.fetch import Fetcher


class DormirFalso:
    def __init__(self) -> None:
        self.llamadas: list[float] = []

    def __call__(self, segundos: float) -> None:
        self.llamadas.append(segundos)


class LimitadorContador:
    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def esperar(self, url: str) -> float:
        self.llamadas.append(url)
        return 0.0


def _settings(**overrides) -> Settings:
    valores = {"user_agent": "LegisUni-test/1.0"}
    valores.update(overrides)
    return Settings(**valores)


def _fetcher(**overrides) -> tuple[Fetcher, DormirFalso, LimitadorContador]:
    dormir = DormirFalso()
    limitador = LimitadorContador()
    fetcher = Fetcher(
        settings=_settings(**overrides),
        limitador=limitador,
        robots=None,
        dormir=dormir,
    )
    return fetcher, dormir, limitador


def test_200_devuelve_cuerpo_completo(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=b"%PDF-1.7 contenido")
    fetcher, _, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.status == 200
    assert respuesta.cuerpo == b"%PDF-1.7 contenido"
    assert respuesta.primeros_bytes.startswith(b"%PDF-")
    assert respuesta.motivo_red is None
    assert respuesta.intentos == 1


def test_peticion_lleva_el_user_agent_de_settings(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=b"contenido")
    fetcher, _, _ = _fetcher(user_agent="LegisUni/9.9 (+https://example.org)")

    fetcher.pedir("https://a.mx/x.pdf")

    peticiones = httpx_mock.get_requests()
    assert len(peticiones) == 1
    assert peticiones[0].headers["User-Agent"] == "LegisUni/9.9 (+https://example.org)"


def test_404_no_se_reintenta(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404)
    fetcher, dormir, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.motivo_red == "url_muerta"
    assert respuesta.intentos == 1
    assert dormir.llamadas == []


def test_403_no_se_reintenta(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=403)
    fetcher, dormir, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.motivo_red == "http_error"
    assert respuesta.intentos == 1
    assert dormir.llamadas == []


def test_dos_503_seguidos_de_200_tiene_exito(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(status_code=200, content=b"contenido")
    fetcher, dormir, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.status == 200
    assert respuesta.motivo_red is None
    assert respuesta.intentos == 3
    assert dormir.llamadas == [2, 4]


def test_cinco_503_agota_reintentos(httpx_mock: HTTPXMock) -> None:
    for _ in range(5):
        httpx_mock.add_response(status_code=503)
    fetcher, dormir, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.motivo_red == "http_error"
    assert respuesta.intentos == 5
    assert dormir.llamadas == [2, 4, 8, 16]


def test_429_se_reintenta_como_5xx(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=200, content=b"contenido")
    fetcher, dormir, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.status == 200
    assert respuesta.motivo_red is None
    assert respuesta.intentos == 2
    assert dormir.llamadas == [2]


def test_timeout_agota_reintentos_sin_propagar(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.TimeoutException("tiempo agotado"), is_reusable=True)
    fetcher, dormir, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.motivo_red == "timeout"
    assert respuesta.intentos == 5
    assert dormir.llamadas == [2, 4, 8, 16]


def test_cuerpo_que_excede_max_bytes_se_aborta(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=b"x" * 200)
    fetcher, _, _ = _fetcher(max_bytes=100)

    respuesta = fetcher.pedir("https://a.mx/x.pdf")

    assert respuesta.excedio_tamano is True
    assert respuesta.cuerpo is None
    assert respuesta.primeros_bytes != b""


def test_limitador_se_llama_una_sola_vez_por_peticion(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(status_code=200, content=b"contenido")
    fetcher, _, limitador = _fetcher()

    fetcher.pedir("https://a.mx/x.pdf")

    assert limitador.llamadas == ["https://a.mx/x.pdf"]


def test_redireccion_deja_url_final_con_el_destino(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://a.mx/origen.pdf",
        status_code=302,
        headers={"Location": "https://a.mx/destino.pdf"},
    )
    httpx_mock.add_response(url="https://a.mx/destino.pdf", status_code=200, content=b"contenido")
    fetcher, _, _ = _fetcher()

    respuesta = fetcher.pedir("https://a.mx/origen.pdf")

    assert respuesta.url_final == "https://a.mx/destino.pdf"
