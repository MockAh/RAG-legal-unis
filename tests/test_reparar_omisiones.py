"""M35b: reparación de las filas que pisó una omisión (E17 de docs/08).

Cada fila dañada se fabrica por el mismo camino que en campo: una descarga buena
guardada con guardar_descarga y, encima, el resultado de su omisión.
"""

import hashlib
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest
import typer

from legisuni.contracts import DownloadResult, IntentoPuerta
from legisuni.descargador.store import Store

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import reparar_omisiones  # noqa: E402

_MTIME = datetime(2026, 9, 18, 14, 5, 0)


def _intento(orden: int, exito: bool) -> IntentoPuerta:
    return IntentoPuerta(
        orden=orden,
        url=f"https://www.uam.mx/p{orden}.pdf",
        url_pedida=f"https://www.uam.mx/p{orden}.pdf",
        url_final=f"https://www.uam.mx/final{orden}.pdf" if exito else None,
        enlace_vestibulo=None,
        http_status=200 if exito else 404,
        exito=exito,
        motivo_fallo=None if exito else "http_error",
    )


def _danar(
    store: Store,
    tmp_path: Path,
    encargo_id: str,
    intentos: list[IntentoPuerta] | None = None,
    contenido: bytes = b"%PDF-1.7\n",
    sha256: str | None = None,
) -> Path:
    ruta = tmp_path / "data" / f"{encargo_id.replace(':', '_')}.pdf"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    os.utime(ruta, (_MTIME.timestamp(), _MTIME.timestamp()))
    sha = sha256 or hashlib.sha256(contenido).hexdigest()
    bueno = DownloadResult(
        encargo_id=encargo_id,
        modo="juridico",
        exito=True,
        ruta_local=ruta,
        sha256=sha,
        bytes=len(contenido),
        content_type="application/pdf",
        http_status=200,
        capturado_en=_MTIME,
        url_final="https://www.uam.mx/final0.pdf",
        puerta_usada=0,
        intentos=intentos if intentos is not None else [_intento(0, True)],
    )
    store.guardar(bueno)
    store.guardar_descarga(bueno, grupo_alias=encargo_id)
    omision = DownloadResult(
        encargo_id=encargo_id,
        modo="juridico",
        exito=True,
        capturado_en=datetime(2026, 9, 26, 10, 0, 0),
        ruta_local=ruta,
        sha256=sha,
        intentos=[],
    )
    store.guardar_descarga(omision, grupo_alias=encargo_id)
    return ruta


def _descargas(db: Path) -> list[tuple]:
    conn = sqlite3.connect(str(db))
    filas = conn.execute(
        "SELECT encargo_id, url_final, http_status, bytes, puerta_usada, capturado_en, content_type "
        "FROM descargas ORDER BY encargo_id"
    ).fetchall()
    conn.close()
    return filas


def test_vista_previa_no_escribe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "v2.db"
    with Store(db) as store:
        _danar(store, tmp_path, "uam:ro:aaaaaaaaaaaa")
    monkeypatch.setattr(reparar_omisiones, "FILAS_ESPERADAS", 1)
    antes = db.read_bytes()

    reparar_omisiones.main(db=db, aplicar=False)

    assert db.read_bytes() == antes


def test_aborta_si_las_afectadas_no_son_las_esperadas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "v2.db"
    with Store(db) as store:
        _danar(store, tmp_path, "uam:ro:aaaaaaaaaaaa")
    monkeypatch.setattr(reparar_omisiones, "FILAS_ESPERADAS", 2)
    antes = _descargas(db)

    with pytest.raises(typer.Exit):
        reparar_omisiones.main(db=db, aplicar=True)

    assert "ABORTADO: 1 filas afectadas, se esperaban 2" in capsys.readouterr().out
    assert _descargas(db) == antes


def test_aplicar_repara_la_fila_entera_y_no_toca_content_type_ni_documentos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "v2.db"
    with Store(db) as store:
        _danar(store, tmp_path, "uam:ro:aaaaaaaaaaaa")
    monkeypatch.setattr(reparar_omisiones, "FILAS_ESPERADAS", 1)
    conn = sqlite3.connect(str(db))
    documentos_antes = conn.execute("SELECT * FROM documentos").fetchall()
    conn.close()

    reparar_omisiones.main(db=db, aplicar=True)

    assert _descargas(db) == [
        (
            "uam:ro:aaaaaaaaaaaa",
            "https://www.uam.mx/final0.pdf",
            200,
            len(b"%PDF-1.7\n"),
            0,
            _MTIME.isoformat(),
            None,
        )
    ]
    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT * FROM documentos").fetchall() == documentos_antes
    conn.close()
    salida = capsys.readouterr().out
    assert "ESTIMACIÓN" in salida
    assert "(estimación)" in salida
    assert "aplicado: 1 filas reparadas" in salida


def test_filas_que_no_cumplen_quedan_intactas_y_se_reportan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "v2.db"
    with Store(db) as store:
        _danar(store, tmp_path, "uam:a:ok")
        _danar(store, tmp_path, "uam:b:hash", sha256="f" * 64)
        _danar(store, tmp_path, "uam:c:ausente").unlink()
        _danar(store, tmp_path, "uam:d:ceroexitos", intentos=[_intento(0, False)])
        _danar(store, tmp_path, "uam:e:dosexitos", intentos=[_intento(0, True), _intento(1, True)])
        _danar(store, tmp_path, "uam:f:orden1", intentos=[_intento(0, False), _intento(1, True)])
    monkeypatch.setattr(reparar_omisiones, "FILAS_ESPERADAS", 6)
    antes = {fila[0]: fila for fila in _descargas(db)}

    reparar_omisiones.main(db=db, aplicar=True)

    despues = {fila[0]: fila for fila in _descargas(db)}
    assert despues["uam:a:ok"][3] == len(b"%PDF-1.7\n")
    for encargo_id in ["uam:b:hash", "uam:c:ausente", "uam:d:ceroexitos", "uam:e:dosexitos", "uam:f:orden1"]:
        assert despues[encargo_id] == antes[encargo_id]
    salida = capsys.readouterr().out
    assert "INTACTA    uam:b:hash  el SHA-256 del archivo no coincide" in salida
    assert "INTACTA    uam:c:ausente  archivo ausente" in salida
    assert "INTACTA    uam:d:ceroexitos  0 intentos con exito=1" in salida
    assert "INTACTA    uam:e:dosexitos  2 intentos con exito=1" in salida
    assert "INTACTA    uam:f:orden1  el intento exitoso tiene orden=1" in salida
    assert "reparables: 1\nintactas: 5\n" in salida


def test_segunda_aplicacion_aborta_sin_escribir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "v2.db"
    with Store(db) as store:
        _danar(store, tmp_path, "uam:ro:aaaaaaaaaaaa")
    monkeypatch.setattr(reparar_omisiones, "FILAS_ESPERADAS", 1)
    reparar_omisiones.main(db=db, aplicar=True)
    tras_primera = _descargas(db)

    with pytest.raises(typer.Exit):
        reparar_omisiones.main(db=db, aplicar=True)

    assert _descargas(db) == tras_primera
