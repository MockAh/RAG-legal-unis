"""M25: cliente HTTP único (criterio 15 de docs/07, cierra CD-05-2 de docs/05).

Fetcher y RobotsCache reciben el mismo objeto httpx.Client, y ese cliente es
quien pone el User-Agent, incluso en la petición a /robots.txt. El cruce de
vestíbulo llega en M28: añadirlo aquí es una línea en cada `receptores`.
"""

import sys
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from legisuni.config import Settings
from legisuni.descargador.fetch import Fetcher, construir_cliente
from legisuni.descargador.ratelimit import RateLimiter
from legisuni.descargador.robots import RobotsCache

_RAIZ = Path(__file__).resolve().parent.parent
_FIXTURES = _RAIZ / "fixtures"

sys.path.insert(0, str(_RAIZ / "scripts"))

import cosecha  # noqa: E402
import cosecha_uam  # noqa: E402

_USER_AGENT = "LegisUni-test/9.9 (+https://example.org)"


@pytest.fixture(autouse=True)
def _aislar_entorno(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # sin esto, Settings() leería el .env real de la raíz del repo
    monkeypatch.chdir(tmp_path)


def _cliente_de(receptor: object) -> httpx.Client:
    return receptor._cliente  # type: ignore[attr-defined]


def _armar(settings: Settings) -> tuple[httpx.Client, Fetcher, RobotsCache]:
    cliente = construir_cliente(settings)
    robots = RobotsCache(settings.user_agent, cliente)
    fetcher = Fetcher(settings, RateLimiter(settings.rate_limit_s), robots, cliente)
    return cliente, fetcher, robots


def test_fetcher_y_robots_reciben_el_mismo_cliente() -> None:
    cliente, fetcher, robots = _armar(Settings(user_agent=_USER_AGENT))

    receptores = {"fetcher": fetcher, "robots": robots}  # M28: + "vestibulo": vestibulo

    for nombre, receptor in receptores.items():
        assert _cliente_de(receptor) is cliente, nombre


def test_peticion_a_robots_lleva_el_user_agent_configurado(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://x.mx/robots.txt", status_code=404)
    _, _, robots = _armar(Settings(user_agent=_USER_AGENT))

    assert robots.permitido("https://x.mx/a.pdf") is True

    peticiones = httpx_mock.get_requests()
    assert [str(p.url) for p in peticiones] == ["https://x.mx/robots.txt"]
    assert peticiones[0].headers["User-Agent"] == _USER_AGENT


def test_cliente_lleva_el_timeout_de_settings() -> None:
    cliente = construir_cliente(Settings(user_agent=_USER_AGENT, timeout_s=17))

    assert cliente.timeout == httpx.Timeout(17)


def _espiar(
    monkeypatch: pytest.MonkeyPatch, modulo: object, nombre: str, capturas: dict[str, object]
) -> None:
    clase = getattr(modulo, nombre)

    def fabrica(*args: object, **kwargs: object) -> object:
        capturas[nombre] = clase(*args, **kwargs)
        return capturas[nombre]

    monkeypatch.setattr(modulo, nombre, fabrica)


_UJAT = dict(
    html=[_FIXTURES / "ujat-15763.html"],
    url_indice=["https://www.ujat.mx/abogado/15763"],
    inst_id="ujat",
)
_UAM = dict(
    html=_FIXTURES / "uam-index.html",
    url_indice="https://www.uam.mx/legislacion/index.html",
    inst_id="uam",
)


@pytest.mark.parametrize(
    ("modulo", "argumentos"),
    [(cosecha, _UJAT), (cosecha_uam, _UAM)],
    ids=["cosecha", "cosecha_uam"],
)
def test_main_de_los_scripts_cablea_un_solo_cliente(
    modulo: object,
    argumentos: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    httpx_mock: HTTPXMock,  # sin respuestas registradas: cualquier petición real falla el test
) -> None:
    """El --dry-run termina antes de construir nada; esto corre el cableado real con --limite 0."""
    monkeypatch.setenv("LEGISUNI_USER_AGENT", _USER_AGENT)
    monkeypatch.setenv("LEGISUNI_DB_PATH", str(tmp_path / "prueba.db"))
    monkeypatch.setenv("LEGISUNI_DATA_ROOT", str(tmp_path / "data"))
    capturas: dict[str, object] = {}
    _espiar(monkeypatch, modulo, "Fetcher", capturas)
    _espiar(monkeypatch, modulo, "RobotsCache", capturas)

    modulo.main(limite=0, dry_run=False, **argumentos)

    receptores = {"fetcher": capturas["Fetcher"], "robots": capturas["RobotsCache"]}
    # M28: + "vestibulo": capturas["Vestibulo"], con su _espiar
    clientes = {nombre: _cliente_de(receptor) for nombre, receptor in receptores.items()}
    assert clientes["fetcher"] is clientes["robots"]
    assert clientes["robots"].headers["User-Agent"] == _USER_AGENT
    assert httpx_mock.get_requests() == []
