import sqlite3
from datetime import datetime
from pathlib import Path

from legisuni.contracts import DownloadResult
from legisuni.descargador.store import Store


def _resultado_exitoso(**overrides) -> DownloadResult:
    datos = dict(
        entry_id="uam:reglamento-organico",
        exito=True,
        ruta_local=Path("/datos/uam/reglamento-organico__2026-01-01.pdf"),
        sha256="a" * 64,
        bytes=1234,
        content_type="application/pdf",
        http_status=200,
        capturado_en=datetime(2026, 1, 1, 12, 0, 0),
        url_final="http://example.org/doc.pdf",
    )
    datos.update(overrides)
    return DownloadResult(**datos)


def test_crear_store_crea_archivo_y_tabla_vacia(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with Store(db_path) as store:
        assert db_path.exists()
        assert store.contar() == 0


def test_guardar_exitoso_y_recuperar_hash(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar(resultado)
        assert store.hash_registrado(resultado.entry_id) == resultado.sha256


def test_guardar_dos_veces_mismo_entry_id_no_duplica(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar(resultado)
        store.guardar(resultado)
        assert store.contar() == 1


def test_guardar_mismo_entry_id_con_datos_distintos_actualiza(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar(resultado)
        actualizado = resultado.model_copy(update={"sha256": "b" * 64})
        store.guardar(actualizado)
        assert store.contar() == 1
        assert store.hash_registrado(resultado.entry_id) == "b" * 64


def test_hash_registrado_entry_id_inexistente_devuelve_none(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        assert store.hash_registrado("uam:no-existe") is None


def test_hash_registrado_con_exito_falso_devuelve_none(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso(exito=False, sha256="c" * 64)
        store.guardar(resultado)
        assert store.hash_registrado(resultado.entry_id) is None


def test_ruta_registrada_vuelve_como_path(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso()
        store.guardar(resultado)
        ruta = store.ruta_registrada(resultado.entry_id)
        assert isinstance(ruta, Path)
        assert ruta == resultado.ruta_local


def test_tipos_en_disco_son_texto_no_blob(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with Store(db_path) as store:
        store.guardar(_resultado_exitoso())

    conn = sqlite3.connect(str(db_path))
    fila = conn.execute(
        "SELECT typeof(ruta_local) AS t_ruta, typeof(capturado_en) AS t_capturado "
        "FROM documentos"
    ).fetchone()
    conn.close()
    assert fila[0] == "text"
    assert fila[1] == "text"


def test_utf8_se_conserva_intacto(tmp_path: Path) -> None:
    entry_id = "uñam:reglamento-académico"
    with Store(tmp_path / "test.db") as store:
        resultado = _resultado_exitoso(entry_id=entry_id)
        store.guardar(resultado)
        assert store.hash_registrado(entry_id) == resultado.sha256


def test_guardar_resultado_fallido_sin_excepcion(tmp_path: Path) -> None:
    with Store(tmp_path / "test.db") as store:
        resultado = DownloadResult(
            entry_id="uam:url-muerta",
            exito=False,
            motivo_fallo="url_muerta",
            capturado_en=datetime(2026, 1, 1),
        )
        store.guardar(resultado)
        assert store.contar() == 1


def test_cerrar_y_reabrir_conserva_filas(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    store = Store(db_path)
    store.guardar(_resultado_exitoso())
    store.cerrar()

    with Store(db_path) as reabierto:
        assert reabierto.contar() == 1
