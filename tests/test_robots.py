import logging

import httpx
import pytest

from legisuni.descargador.robots import RobotsCache

_ROBOTS_DISALLOW_PRIVADO = "User-agent: *\nDisallow: /privado/\n"


class FetcherFalso:
    """Servidor falso tras un `httpx.Client` real: `.llamadas` registra las URL pedidas."""

    def __init__(self, respuestas: dict[str, tuple[int, str]]) -> None:
        self._respuestas = respuestas
        self.llamadas: list[str] = []
        self.cliente = httpx.Client(transport=httpx.MockTransport(self._responder))

    def _responder(self, peticion: httpx.Request) -> httpx.Response:
        url = str(peticion.url)
        self.llamadas.append(url)
        status, texto = self._respuestas[url]
        return httpx.Response(status, text=texto)


class FetcherQueLanza:
    def __init__(self) -> None:
        self.llamadas: list[str] = []
        self.cliente = httpx.Client(transport=httpx.MockTransport(self._responder))

    def _responder(self, peticion: httpx.Request) -> httpx.Response:
        self.llamadas.append(str(peticion.url))
        raise httpx.ConnectError("no hay red")


def test_disallow_bloquea_ruta_privada_y_permite_publica() -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (200, _ROBOTS_DISALLOW_PRIVADO)})
    cache = RobotsCache(user_agent="legisuni-bot", cliente=fetcher.cliente)

    assert cache.permitido("https://x.mx/privado/a.pdf") is False
    assert cache.permitido("https://x.mx/publico/a.pdf") is True


def test_status_404_es_permitido() -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (404, "")})
    cache = RobotsCache(user_agent="legisuni-bot", cliente=fetcher.cliente)

    assert cache.permitido("https://x.mx/a.pdf") is True


def test_status_500_es_permitido_con_warning(caplog: pytest.LogCaptureFixture) -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (500, "")})
    cache = RobotsCache(user_agent="legisuni-bot", cliente=fetcher.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert any("500" in registro.message for registro in caplog.records)


def test_status_403_es_permitido_con_warning(caplog: pytest.LogCaptureFixture) -> None:
    # E11.1 de docs/08: la UAM responde 403 a /robots.txt y 200 a sus PDF; hay que seguir descargando
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (403, "")})
    cache = RobotsCache(user_agent="legisuni-bot", cliente=fetcher.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert any("403" in registro.message for registro in caplog.records)


def test_fetcher_lanza_excepcion_es_permitido_sin_propagar(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fetcher = FetcherQueLanza()
    cache = RobotsCache(user_agent="legisuni-bot", cliente=fetcher.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert len(caplog.records) == 1


def test_mismo_host_invoca_fetcher_una_sola_vez() -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (200, _ROBOTS_DISALLOW_PRIVADO)})
    cache = RobotsCache(user_agent="legisuni-bot", cliente=fetcher.cliente)

    cache.permitido("https://x.mx/publico/a.pdf")
    cache.permitido("https://x.mx/publico/b.pdf")

    assert fetcher.llamadas == ["https://x.mx/robots.txt"]


def test_hosts_distintos_invocan_fetcher_dos_veces() -> None:
    fetcher = FetcherFalso(
        {
            "https://x.mx/robots.txt": (200, _ROBOTS_DISALLOW_PRIVADO),
            "https://y.mx/robots.txt": (404, ""),
        }
    )
    cache = RobotsCache(user_agent="legisuni-bot", cliente=fetcher.cliente)

    cache.permitido("https://x.mx/a.pdf")
    cache.permitido("https://y.mx/a.pdf")

    assert fetcher.llamadas == ["https://x.mx/robots.txt", "https://y.mx/robots.txt"]


# M38: un 200 que no parece robots.txt no se obedece (E19.12 de docs/08).


class ServidorConCabeceras:
    """Como FetcherFalso, pero cada respuesta lleva sus cabeceras; admite redirecciones."""

    def __init__(self, respuestas: dict[str, tuple[int, dict[str, str], bytes]]) -> None:
        self._respuestas = respuestas
        self.llamadas: list[str] = []
        self.cliente = httpx.Client(transport=httpx.MockTransport(self._responder))

    def _responder(self, peticion: httpx.Request) -> httpx.Response:
        url = str(peticion.url)
        self.llamadas.append(url)
        status, cabeceras, cuerpo = self._respuestas[url]
        return httpx.Response(status, headers=cabeceras, content=cuerpo)


_LOGIN_SAML = b"<!DOCTYPE html>\n<html><head><title>Sign in to your account</title></head></html>\n"


def _avisos_no_parece(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if "no parece robots.txt" in r.message]


def test_200_html_es_permitido_con_warning(caplog: pytest.LogCaptureFixture) -> None:
    servidor = ServidorConCabeceras(
        {"https://x.mx/robots.txt": (200, {"content-type": "text/html; charset=utf-8"}, _LOGIN_SAML)}
    )
    cache = RobotsCache(user_agent="legisuni-bot", cliente=servidor.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert len(_avisos_no_parece(caplog)) == 1


def test_200_html_servido_como_text_plain_es_permitido_con_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    servidor = ServidorConCabeceras(
        {"https://x.mx/robots.txt": (200, {"content-type": "text/plain"}, b"\xef\xbb\xbf\n  " + _LOGIN_SAML)}
    )
    cache = RobotsCache(user_agent="legisuni-bot", cliente=servidor.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert len(_avisos_no_parece(caplog)) == 1


def test_cadena_de_e19_12_hasta_login_saml_es_permitido_con_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # E19.12: cuatro 302 desde /robots.txt hasta un login SAML de otro host que responde 200
    login = "https://login.example.com/tenant/saml2?SAMLRequest=abc"
    servidor = ServidorConCabeceras(
        {
            "https://pure.x.mx/robots.txt": (302, {"location": "https://pure.x.mx/admin"}, b""),
            "https://pure.x.mx/admin": (302, {"location": "https://pure.x.mx/admin/"}, b""),
            "https://pure.x.mx/admin/": (302, {"location": "https://pure.x.mx/admin/saml2/authenticate/pure"}, b""),
            "https://pure.x.mx/admin/saml2/authenticate/pure": (302, {"location": login}, b""),
            login: (200, {"content-type": "text/html; charset=utf-8"}, _LOGIN_SAML),
        }
    )
    cache = RobotsCache(user_agent="legisuni-bot", cliente=servidor.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://pure.x.mx/ws/portalfiles/a.pdf") is True
        assert cache.permitido("https://pure.x.mx/ws/portalfiles/b.pdf") is True
    avisos = _avisos_no_parece(caplog)
    assert len(avisos) == 1
    assert login in avisos[0].message
    assert servidor.llamadas[0] == "https://pure.x.mx/robots.txt"
    assert len(servidor.llamadas) == 5


def test_200_vacio_es_permitido_sin_warning(caplog: pytest.LogCaptureFixture) -> None:
    servidor = ServidorConCabeceras({"https://x.mx/robots.txt": (200, {"content-type": "text/plain"}, b"")})
    cache = RobotsCache(user_agent="legisuni-bot", cliente=servidor.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert caplog.records == []


def test_200_solo_comentarios_sin_content_type_es_permitido_sin_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    servidor = ServidorConCabeceras(
        {"https://x.mx/robots.txt": (200, {}, b"# robots.txt de x.mx\n#   -- sin reglas --\n")}
    )
    cache = RobotsCache(user_agent="legisuni-bot", cliente=servidor.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert caplog.records == []


def test_disallow_servido_como_octet_stream_se_obedece(caplog: pytest.LogCaptureFixture) -> None:
    servidor = ServidorConCabeceras(
        {
            "https://x.mx/robots.txt": (
                200,
                {"content-type": "application/octet-stream"},
                _ROBOTS_DISALLOW_PRIVADO.encode(),
            )
        }
    )
    cache = RobotsCache(user_agent="legisuni-bot", cliente=servidor.cliente)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/privado/a.pdf") is False
        assert cache.permitido("https://x.mx/publico/a.pdf") is True
    assert caplog.records == []
