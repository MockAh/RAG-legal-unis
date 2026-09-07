"""Persistencia SQLite de resultados de descarga."""

import sqlite3
from pathlib import Path
from types import TracebackType

from legisuni.contracts import DownloadResult

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS documentos (
    entry_id     TEXT PRIMARY KEY,
    exito        INTEGER NOT NULL,
    ruta_local   TEXT,
    sha256       TEXT,
    bytes        INTEGER,
    content_type TEXT,
    http_status  INTEGER,
    motivo_fallo TEXT,
    capturado_en TEXT NOT NULL,
    url_final    TEXT
)
"""


class Store:
    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_ESQUEMA)
        self._conn.commit()

    def guardar(self, resultado: DownloadResult) -> None:
        self._conn.execute(
            """
            INSERT INTO documentos (
                entry_id, exito, ruta_local, sha256, bytes,
                content_type, http_status, motivo_fallo, capturado_en, url_final
            ) VALUES (:entry_id, :exito, :ruta_local, :sha256, :bytes,
                :content_type, :http_status, :motivo_fallo, :capturado_en, :url_final)
            ON CONFLICT(entry_id) DO UPDATE SET
                exito = excluded.exito,
                ruta_local = excluded.ruta_local,
                sha256 = excluded.sha256,
                bytes = excluded.bytes,
                content_type = excluded.content_type,
                http_status = excluded.http_status,
                motivo_fallo = excluded.motivo_fallo,
                capturado_en = excluded.capturado_en,
                url_final = excluded.url_final
            """,
            {
                "entry_id": resultado.entry_id,
                "exito": int(resultado.exito),
                "ruta_local": str(resultado.ruta_local) if resultado.ruta_local is not None else None,
                "sha256": resultado.sha256,
                "bytes": int(resultado.bytes) if resultado.bytes is not None else None,
                "content_type": resultado.content_type,
                "http_status": int(resultado.http_status) if resultado.http_status is not None else None,
                "motivo_fallo": resultado.motivo_fallo,
                "capturado_en": resultado.capturado_en.isoformat(),
                "url_final": resultado.url_final,
            },
        )
        self._conn.commit()

    def hash_registrado(self, entry_id: str) -> str | None:
        fila = self._conn.execute(
            "SELECT sha256 FROM documentos WHERE entry_id = ? AND exito = 1",
            (entry_id,),
        ).fetchone()
        return fila["sha256"] if fila is not None else None

    def ruta_registrada(self, entry_id: str) -> Path | None:
        fila = self._conn.execute(
            "SELECT ruta_local FROM documentos WHERE entry_id = ?",
            (entry_id,),
        ).fetchone()
        if fila is None or fila["ruta_local"] is None:
            return None
        return Path(fila["ruta_local"])

    def contar(self) -> int:
        fila = self._conn.execute("SELECT COUNT(*) AS n FROM documentos").fetchone()
        return fila["n"]

    def cerrar(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.cerrar()
