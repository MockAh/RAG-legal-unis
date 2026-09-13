import hashlib
from datetime import datetime
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from legisuni.config import Settings
from legisuni.contracts import CatalogEntry, DownloadResult
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
    valores = dict(user_agent="LegisUni-test/1.0", data_dir=tmp_path)
    valores.update(overrides)
    return Settings(**valores)


def _fetcher(settings: Settings) -> Fetcher:
    return Fetcher(
        settings=settings, limitador=LimitadorSinEspera(), robots=None, dormir=DormirFalso()
    )


def _entrada(**overrides) -> CatalogEntry:
    datos = dict(
        entry_id="uam:reglamento-organico",
        inst_id="uam",
        titulo="Reglamento Orgánico",
        tipo_norma="reglamento",
        url_documento="https://a.mx/x.pdf",
        origen="sitio_institucional",
        url_indice="https://a.mx/indice",
        extraido_en=datetime(2026, 1, 1),
    )
    datos.update(overrides)
    return CatalogEntry(**datos)


def test_pdf_valido_se_escribe_y_hash_coincide(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada()

    resultado = descargar(
        entrada, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=datetime(2026, 3, 16)
    )

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.exists()
    assert resultado.ruta_local.suffix == ".pdf"
    assert hashlib.sha256(resultado.ruta_local.read_bytes()).hexdigest() == resultado.sha256


def test_robots_prohibe_no_llama_al_fetcher(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    entrada = _entrada()
    fetcher = FetcherContador()

    resultado = descargar(entrada, fetcher, RobotsProhibeTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "robots_prohibido"
    assert fetcher.llamadas == 0


def test_landing_page_no_es_pdf_no_escribe_nada(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=_HTML_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada()

    resultado = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "no_es_pdf"
    assert list(tmp_path.rglob("*")) == []


def test_visor_de_terceros_no_escribe_nada(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    url = "https://drive.google.com/file/d/1AbC_xyz/view"
    httpx_mock.add_response(url=url, status_code=200, content=_HTML_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada(url_documento=url, url_indice="https://drive.google.com/")

    resultado = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.motivo_fallo == "visor_de_terceros"
    assert list(tmp_path.rglob("*")) == []


def test_404_no_escribe_nada(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404)
    settings = _settings(tmp_path)
    entrada = _entrada()

    resultado = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.motivo_fallo == "url_muerta"
    assert list(tmp_path.rglob("*")) == []


def test_idempotencia_misma_respuesta_deja_un_solo_archivo(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada()
    fecha = datetime(2026, 3, 16)

    resultado1 = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)
    resultado2 = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)

    archivos = list(tmp_path.rglob("*.pdf"))
    assert len(archivos) == 1
    assert resultado1.ruta_local == resultado2.ruta_local


def test_version_nueva_con_bytes_distintos_deja_dos_archivos(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES_V2)
    settings = _settings(tmp_path)
    entrada = _entrada()
    fecha = datetime(2026, 3, 16)

    resultado1 = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)
    resultado2 = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings, ahora=fecha)

    archivos = list(tmp_path.rglob("*.pdf"))
    assert len(archivos) == 2
    nombres = sorted(a.name for a in archivos)
    assert nombres[0].count("__") == 1   # slug__fecha.pdf
    assert nombres[1].count("__") == 2   # slug__fecha__hash.pdf


def test_url_cruda_no_se_modifica(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    cruda = "/2015/abogado general/nuevos/A_DISTANCIA.pdf"
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada(url_documento=cruda, url_indice="https://www.ujat.mx/abogado/15763")

    descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert entrada.url_documento == cruda


def test_docx_se_guarda_con_extension_docx(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=_DOCX_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada(url_documento="https://a.mx/x.docx")

    resultado = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.suffix == ".docx"


def test_fallo_de_escritura_no_propaga_excepcion(
    tmp_path: Path, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada()

    def _falla(self, data):
        raise OSError("disco lleno")

    monkeypatch.setattr(Path, "write_bytes", _falla)

    resultado = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings)

    assert resultado.exito is False
    assert resultado.motivo_fallo == "http_error"


def test_reanudar_omite_entry_id_ya_registrado_con_exito(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    entrada = _entrada()
    fetcher = FetcherContador()

    with Store(tmp_path / "store.db") as store:
        store.guardar(
            DownloadResult(
                entry_id=entrada.entry_id,
                modo="juridico",
                exito=True,
                capturado_en=datetime(2026, 1, 1),
                ruta_local=tmp_path / "reglamento-organico.pdf",
                sha256="abc123",
                intentos=[],
            )
        )

        resultado = descargar(
            entrada, fetcher, RobotsPermiteTodo(), settings, store=store, omitir_si_registrado=True
        )

    assert resultado.exito is True
    assert resultado.ruta_local == tmp_path / "reglamento-organico.pdf"
    assert fetcher.llamadas == 0


def test_reanudar_con_entry_id_no_registrado_descarga_normalmente(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada()

    with Store(tmp_path / "store.db") as store:
        resultado = descargar(
            entrada,
            _fetcher(settings),
            RobotsPermiteTodo(),
            settings,
            store=store,
            omitir_si_registrado=True,
        )

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.exists()


def test_reanudar_con_entry_id_registrado_como_fallo_descarga_igual(
    tmp_path: Path, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada()

    with Store(tmp_path / "store.db") as store:
        store.guardar(
            DownloadResult(
                entry_id=entrada.entry_id,
                modo="juridico",
                exito=False,
                motivo_fallo="timeout",
                capturado_en=datetime(2026, 1, 1),
                intentos=[],
            )
        )

        resultado = descargar(
            entrada,
            _fetcher(settings),
            RobotsPermiteTodo(),
            settings,
            store=store,
            omitir_si_registrado=True,
        )

    assert resultado.exito is True
    assert resultado.ruta_local is not None
    assert resultado.ruta_local.exists()


def test_default_no_omite_y_llama_al_fetcher(tmp_path: Path, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, content=_PDF_BYTES)
    settings = _settings(tmp_path)
    entrada = _entrada()

    with Store(tmp_path / "store.db") as store:
        store.guardar(
            DownloadResult(
                entry_id=entrada.entry_id,
                modo="juridico",
                exito=True,
                capturado_en=datetime(2026, 1, 1),
                ruta_local=tmp_path / "reglamento-organico.pdf",
                sha256="abc123",
                intentos=[],
            )
        )

        resultado = descargar(entrada, _fetcher(settings), RobotsPermiteTodo(), settings, store=store)

    assert resultado.exito is True
    assert resultado.ruta_local != tmp_path / "reglamento-organico.pdf"
    assert len(httpx_mock.get_requests()) == 1
