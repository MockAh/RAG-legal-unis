import logging

import pytest

from legisuni.descargador.robots import RobotsCache

_ROBOTS_DISALLOW_PRIVADO = "User-agent: *\nDisallow: /privado/\n"


class FetcherFalso:
    def __init__(self, respuestas: dict[str, tuple[int, str]]) -> None:
        self._respuestas = respuestas
        self.llamadas: list[str] = []

    def __call__(self, url: str) -> tuple[int, str]:
        self.llamadas.append(url)
        return self._respuestas[url]


class FetcherQueLanza:
    def __init__(self) -> None:
        self.llamadas: list[str] = []

    def __call__(self, url: str) -> tuple[int, str]:
        self.llamadas.append(url)
        raise ConnectionError("no hay red")


def test_disallow_bloquea_ruta_privada_y_permite_publica() -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (200, _ROBOTS_DISALLOW_PRIVADO)})
    cache = RobotsCache(user_agent="legisuni-bot", fetcher=fetcher)

    assert cache.permitido("https://x.mx/privado/a.pdf") is False
    assert cache.permitido("https://x.mx/publico/a.pdf") is True


def test_status_404_es_permitido() -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (404, "")})
    cache = RobotsCache(user_agent="legisuni-bot", fetcher=fetcher)

    assert cache.permitido("https://x.mx/a.pdf") is True


def test_status_500_es_permitido_con_warning(caplog: pytest.LogCaptureFixture) -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (500, "")})
    cache = RobotsCache(user_agent="legisuni-bot", fetcher=fetcher)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert any("500" in registro.message for registro in caplog.records)


def test_fetcher_lanza_excepcion_es_permitido_sin_propagar(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fetcher = FetcherQueLanza()
    cache = RobotsCache(user_agent="legisuni-bot", fetcher=fetcher)

    with caplog.at_level(logging.WARNING):
        assert cache.permitido("https://x.mx/a.pdf") is True
    assert len(caplog.records) == 1


def test_mismo_host_invoca_fetcher_una_sola_vez() -> None:
    fetcher = FetcherFalso({"https://x.mx/robots.txt": (200, _ROBOTS_DISALLOW_PRIVADO)})
    cache = RobotsCache(user_agent="legisuni-bot", fetcher=fetcher)

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
    cache = RobotsCache(user_agent="legisuni-bot", fetcher=fetcher)

    cache.permitido("https://x.mx/a.pdf")
    cache.permitido("https://y.mx/a.pdf")

    assert fetcher.llamadas == ["https://x.mx/robots.txt", "https://y.mx/robots.txt"]
