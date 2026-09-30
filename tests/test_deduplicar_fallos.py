"""M39b: limpieza de las filas de fallo duplicadas (E19.11 de docs/08).

Desde M39, `Store.guardar_descarga` ya no deja dos fallos del mismo encargo, así que los
duplicados se fabrican con INSERT directo: la forma de B.7–B.10 en la base v2, un fallo de
la parcial y otro de la completa, cada uno con sus intentos.
"""

import sqlite3
import sys
from pathlib import Path

import pytest
import typer

from legisuni.descargador.store import Store

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import deduplicar_fallos  # noqa: E402


def _insertar(db: Path, encargo_id: str, capturado_en: str, sha256: str | None = None) -> None:
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO descargas (encargo_id, modo, sha256, exito, capturado_en, motivo_fallo, grupo_alias) "
        "VALUES (?, 'academico', ?, ?, ?, ?, ?)",
        (encargo_id, sha256, int(sha256 is not None), capturado_en,
         None if sha256 else "http_error", encargo_id),
    )
    conn.execute(
        "INSERT INTO intentos (encargo_id, orden, url, exito, motivo_fallo) VALUES (?, 0, 'https://x.org/a', 0, 'http_error')",
        (encargo_id,),
    )
    conn.commit()
    conn.close()


def _base(tmp_path: Path) -> Path:
    db = tmp_path / "v2.db"
    Store(db).cerrar()
    return db


def _duplicar(db: Path, encargo_id: str) -> None:
    _insertar(db, encargo_id, "2026-09-27T01:18:00")  # parcial
    _insertar(db, encargo_id, "2026-09-27T01:21:00")  # completa


def _filas(db: Path, tabla: str) -> list[tuple]:
    conn = sqlite3.connect(str(db))
    filas = conn.execute(f"SELECT * FROM {tabla} ORDER BY rowid").fetchall()
    conn.close()
    return filas


def test_vista_previa_no_escribe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = _base(tmp_path)
    _duplicar(db, "doi:10.1/b7")
    monkeypatch.setattr(deduplicar_fallos, "FILAS_ESPERADAS", 1)
    antes = db.read_bytes()

    deduplicar_fallos.main(db=db, aplicar=False)

    assert db.read_bytes() == antes


def test_aborta_si_las_filas_a_borrar_no_son_las_esperadas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db = _base(tmp_path)
    _duplicar(db, "doi:10.1/b7")
    monkeypatch.setattr(deduplicar_fallos, "FILAS_ESPERADAS", 2)
    antes = _filas(db, "descargas")

    with pytest.raises(typer.Exit):
        deduplicar_fallos.main(db=db, aplicar=True)

    assert "ABORTADO: 1 filas a borrar, se esperaban 2" in capsys.readouterr().out
    assert _filas(db, "descargas") == antes


def test_aborta_si_la_fila_conservada_no_es_la_vigente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # dos fallos y un éxito posterior: el fallo que se conservaría no es la fila vigente
    db = _base(tmp_path)
    _duplicar(db, "doi:10.1/b7")
    _insertar(db, "doi:10.1/b7", "2026-09-28T00:00:00", sha256="a" * 64)
    monkeypatch.setattr(deduplicar_fallos, "FILAS_ESPERADAS", 1)
    antes = _filas(db, "descargas")

    with pytest.raises(typer.Exit):
        deduplicar_fallos.main(db=db, aplicar=True)

    assert "no es su fila vigente" in capsys.readouterr().out
    assert _filas(db, "descargas") == antes


def test_aplicar_deja_el_fallo_mas_reciente_y_no_toca_lo_demas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db = _base(tmp_path)
    _duplicar(db, "doi:10.1/b7")
    _duplicar(db, "doi:10.1/b8")
    _insertar(db, "doi:10.1/b13", "2026-09-27T01:20:00")  # un solo fallo: no se toca
    _insertar(db, "doi:10.1/b16", "2026-09-27T01:21:00", sha256="a" * 64)  # éxito: no se toca
    monkeypatch.setattr(deduplicar_fallos, "FILAS_ESPERADAS", 2)
    intentos_antes = _filas(db, "intentos")
    documentos_antes = _filas(db, "documentos")

    deduplicar_fallos.main(db=db, aplicar=True)

    conn = sqlite3.connect(str(db))
    restantes = conn.execute(
        "SELECT encargo_id, capturado_en FROM descargas ORDER BY encargo_id"
    ).fetchall()
    conn.close()
    assert restantes == [
        ("doi:10.1/b13", "2026-09-27T01:20:00"),
        ("doi:10.1/b16", "2026-09-27T01:21:00"),
        ("doi:10.1/b7", "2026-09-27T01:21:00"),
        ("doi:10.1/b8", "2026-09-27T01:21:00"),
    ]
    assert _filas(db, "intentos") == intentos_antes
    assert _filas(db, "documentos") == documentos_antes
    assert "aplicado: 2 filas borradas" in capsys.readouterr().out


def test_segunda_aplicacion_aborta_sin_escribir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = _base(tmp_path)
    _duplicar(db, "doi:10.1/b7")
    monkeypatch.setattr(deduplicar_fallos, "FILAS_ESPERADAS", 1)
    deduplicar_fallos.main(db=db, aplicar=True)
    tras_primera = _filas(db, "descargas")

    with pytest.raises(typer.Exit):
        deduplicar_fallos.main(db=db, aplicar=True)

    assert _filas(db, "descargas") == tras_primera
