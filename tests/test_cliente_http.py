"""M25: cliente HTTP único (criterio 15 de docs/07, cierra CD-05-2 de docs/05).

Fetcher y RobotsCache reciben el mismo objeto httpx.Client, y ese cliente es
quien pone el User-Agent, incluso en la petición a /robots.txt.

M28: el cruce de vestíbulo no tiene cliente propio ni es un receptor más. El
salto solo puede pedir a través del mismo `Fetcher` (UA, rate limit, reintentos,
tope de tamaño); lo prueban `test_el_salto_del_vestibulo_sale_por_el_fetcher` y
`test_vestibulo_no_importa_httpx`.
"""

import ast
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from legisuni.config import Settings
from legisuni.contracts import Encargo, Puerta
from legisuni.descargador import vestibulo
from legisuni.descargador.descargar import descargar
from legisuni.descargador.fetch import Fetcher, construir_cliente
from legisuni.descargador.ratelimit import RateLimiter
from legisuni.descargador.robots import RobotsCache

_RAIZ = Path(__file__).resolve().parent.parent
_FIXTURES = _RAIZ / "fixtures"

sys.path.insert(0, str(_RAIZ / "scripts"))

import cosecha  # noqa: E402
import cosecha_uam  # noqa: E402
import lote  # noqa: E402

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

    receptores = {"fetcher": fetcher, "robots": robots}

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
    clientes = {nombre: _cliente_de(receptor) for nombre, receptor in receptores.items()}
    assert clientes["fetcher"] is clientes["robots"]
    assert clientes["robots"].headers["User-Agent"] == _USER_AGENT
    assert httpx_mock.get_requests() == []


def test_el_salto_del_vestibulo_sale_por_el_fetcher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock
) -> None:
    url_vestibulo = "https://repo.example.org/articulo/1"
    url_archivo = "https://repo.example.org/descarga/1.pdf"
    html = f'<!DOCTYPE html><html><head><meta name="citation_pdf_url" content="{url_archivo}"></head></html>'
    httpx_mock.add_response(url="https://repo.example.org/robots.txt", status_code=404)
    httpx_mock.add_response(url=url_vestibulo, status_code=200, content=html.encode())
    httpx_mock.add_response(url=url_archivo, status_code=200, content=b"%PDF-1.7\n")
    settings = Settings(user_agent=_USER_AGENT, data_root=tmp_path, rate_limit_s=0)
    _, fetcher, robots = _armar(settings)
    pedidas_por_fetcher: list[str] = []
    pedir_original = fetcher.pedir

    def pedir_espiado(url: str):
        pedidas_por_fetcher.append(url)
        return pedir_original(url)

    monkeypatch.setattr(fetcher, "pedir", pedir_espiado)
    encargo = Encargo(
        encargo_id="doi:10.1/x",
        modo="academico",
        solicitante="lote-test",
        puertas=[Puerta(url=url_vestibulo, tipo="copia_libre", url_base=None, evidencia="lista:t#1")],
        cajon="papers",
        etiqueta="autor-2020__00000000",
        cruzar_vestibulos=True,
        grupo_alias="doi:10.1/x",
        creado_en=datetime(2026, 1, 1),
    )

    resultado = descargar(encargo, fetcher, robots, settings)

    assert resultado.exito is True
    assert resultado.intentos[0].enlace_vestibulo == url_archivo
    assert pedidas_por_fetcher == [url_vestibulo, url_archivo]
    peticiones = httpx_mock.get_requests()
    assert all(p.headers["User-Agent"] == _USER_AGENT for p in peticiones)


def test_vestibulo_no_importa_httpx() -> None:
    arbol = ast.parse(Path(vestibulo.__file__).read_text(encoding="utf-8"))
    modulos = [
        alias.name for nodo in ast.walk(arbol) if isinstance(nodo, ast.Import) for alias in nodo.names
    ] + [nodo.module or "" for nodo in ast.walk(arbol) if isinstance(nodo, ast.ImportFrom)]

    assert not any(m == "httpx" or m.startswith("httpx.") for m in modulos)


# M33: las categorías del resumen son disjuntas. Medido en E16 de docs/08: la segunda
# corrida de la UAM dio `exitosas: 47` y `omitidos: 47` con `total: 47`.


def _servir_pdf(peticion: httpx.Request) -> httpx.Response:
    if peticion.url.path == "/robots.txt":
        return httpx.Response(404)
    return httpx.Response(200, content=b"%PDF-1.7\n")


def _lote_de_un_encargo(tmp_path: Path) -> dict:
    encargo = Encargo(
        encargo_id="doi:10.1/x",
        modo="academico",
        solicitante="lote-test",
        puertas=[Puerta(url="https://repo.example.org/1.pdf", tipo="copia_libre", url_base=None, evidencia="lista:t#1")],
        cajon="papers",
        etiqueta="autor-2020__00000000",
        cruzar_vestibulos=True,
        grupo_alias="doi:10.1/x",
        creado_en=datetime(2026, 1, 1),
    )
    ruta = tmp_path / "lote.json"
    ruta.write_text(
        json.dumps({"lote_id": "lote-test", "encargos": [encargo.model_dump(mode="json")], "no_obtenidos": []}),
        encoding="utf-8",
    )
    return dict(encargos_json=ruta, limite=None)


@pytest.mark.parametrize("modulo", [cosecha, cosecha_uam, lote], ids=["cosecha", "cosecha_uam", "lote"])
def test_resumen_no_cuenta_los_omitidos_como_exitosas(
    modulo: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    httpx_mock: HTTPXMock,
) -> None:
    monkeypatch.setenv("LEGISUNI_USER_AGENT", _USER_AGENT)
    monkeypatch.setenv("LEGISUNI_DB_PATH", str(tmp_path / "prueba.db"))
    monkeypatch.setenv("LEGISUNI_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("LEGISUNI_RATE_LIMIT_S", "0")
    httpx_mock.add_callback(_servir_pdf, is_reusable=True)
    if modulo is lote:
        argumentos = _lote_de_un_encargo(tmp_path)
    else:
        argumentos = {**(_UJAT if modulo is cosecha else _UAM), "limite": 1}

    modulo.main(dry_run=False, **argumentos)
    primera = capsys.readouterr().out
    peticiones_primera = len(httpx_mock.get_requests())
    modulo.main(dry_run=False, **argumentos)
    segunda = capsys.readouterr().out

    assert "total: 1\nexitosas: 1\nomitidos: 0\n" in primera
    assert "total: 1\nexitosas: 0\nomitidos: 1\n" in segunda
    # la segunda corrida no pide nada: el omitido lo es de verdad
    assert len(httpx_mock.get_requests()) == peticiones_primera



# M36.1: el resumen registra los parámetros de la corrida. Sin ellos, la anomalía de
# E18.1 de docs/08 (43 s para 47 peticiones a un host) no es medible.


@pytest.mark.parametrize("modulo", [cosecha, cosecha_uam, lote], ids=["cosecha", "cosecha_uam", "lote"])
def test_resumen_registra_parametros_de_la_corrida(
    modulo: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    httpx_mock: HTTPXMock,
) -> None:
    monkeypatch.setenv("LEGISUNI_USER_AGENT", _USER_AGENT)
    monkeypatch.setenv("LEGISUNI_DB_PATH", str(tmp_path / "prueba.db"))
    monkeypatch.setenv("LEGISUNI_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("LEGISUNI_RATE_LIMIT_S", "0")
    httpx_mock.add_callback(_servir_pdf, is_reusable=True)
    if modulo is lote:
        argumentos = _lote_de_un_encargo(tmp_path)
    else:
        argumentos = {**(_UJAT if modulo is cosecha else _UAM), "limite": 1}

    modulo.main(dry_run=False, **argumentos)
    primera = capsys.readouterr().out
    modulo.main(dry_run=False, **argumentos)
    segunda = capsys.readouterr().out

    parametros = f"rate_limit_s: 0.0\nuser_agent: {_USER_AGENT}\n"
    assert parametros + "hosts distintos pedidos: 1\n" in primera
    # un omitido no pide nada: no aporta host
    assert parametros + "hosts distintos pedidos: 0\n" in segunda

# M35: una omisión no escribe. Medido en la base v2: la segunda corrida de la UAM
# (E16) dejó 47 filas con bytes, content_type, http_status, url_final y
# puerta_usada en NULL y capturado_en con la fecha de la omisión.


def _filas(db_path: Path) -> tuple[list[tuple], list[tuple]]:
    conn = sqlite3.connect(str(db_path))
    descargas = conn.execute("SELECT * FROM descargas ORDER BY encargo_id, sha256").fetchall()
    documentos = conn.execute("SELECT * FROM documentos ORDER BY entry_id").fetchall()
    conn.close()
    return descargas, documentos


@pytest.mark.parametrize("modulo", [cosecha, cosecha_uam, lote], ids=["cosecha", "cosecha_uam", "lote"])
def test_omision_no_pisa_la_fila_registrada(
    modulo: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    httpx_mock: HTTPXMock,
) -> None:
    db_path = tmp_path / "prueba.db"
    monkeypatch.setenv("LEGISUNI_USER_AGENT", _USER_AGENT)
    monkeypatch.setenv("LEGISUNI_DB_PATH", str(db_path))
    monkeypatch.setenv("LEGISUNI_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("LEGISUNI_RATE_LIMIT_S", "0")
    httpx_mock.add_callback(_servir_pdf, is_reusable=True)
    if modulo is lote:
        argumentos = _lote_de_un_encargo(tmp_path)
    else:
        argumentos = {**(_UJAT if modulo is cosecha else _UAM), "limite": 1}

    modulo.main(dry_run=False, **argumentos)
    tras_primera = _filas(db_path)
    modulo.main(dry_run=False, **argumentos)

    assert len(tras_primera[0]) == 1
    assert _filas(db_path) == tras_primera


@pytest.mark.parametrize("modulo", [cosecha, cosecha_uam, lote], ids=["cosecha", "cosecha_uam", "lote"])
def test_los_scripts_ya_no_escriben_en_documentos(
    modulo: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    httpx_mock: HTTPXMock,
) -> None:
    # M34: documentos queda congelada; el único camino de escritura es descargar()
    db_path = tmp_path / "prueba.db"
    monkeypatch.setenv("LEGISUNI_USER_AGENT", _USER_AGENT)
    monkeypatch.setenv("LEGISUNI_DB_PATH", str(db_path))
    monkeypatch.setenv("LEGISUNI_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("LEGISUNI_RATE_LIMIT_S", "0")
    httpx_mock.add_callback(_servir_pdf, is_reusable=True)
    if modulo is lote:
        argumentos = _lote_de_un_encargo(tmp_path)
    else:
        argumentos = {**(_UJAT if modulo is cosecha else _UAM), "limite": 1}

    modulo.main(dry_run=False, **argumentos)

    descargas, documentos = _filas(db_path)
    assert len(descargas) == 1
    assert documentos == []
