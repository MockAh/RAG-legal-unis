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
);

-- v2 (M20, docs/07 criterio 16): espejo de N5, PK compuesta para convivir
-- con criterio 5 de docs/05 (hash nuevo → fila nueva, ninguna se pierde).
-- grupo_alias no vive en N5 (DownloadResult): lo trae quien construyó el
-- Encargo y lo pasa a guardar_descarga(), sin tocar el contrato.
CREATE TABLE IF NOT EXISTS descargas (
    encargo_id   TEXT NOT NULL,
    modo         TEXT NOT NULL,
    sha256       TEXT,
    exito        INTEGER NOT NULL,
    ruta_local   TEXT,
    bytes        INTEGER,
    content_type TEXT,
    http_status  INTEGER,
    capturado_en TEXT NOT NULL,
    url_final    TEXT,
    motivo_fallo TEXT,
    puerta_usada INTEGER,
    duplicado_de TEXT,
    grupo_alias  TEXT NOT NULL,
    PRIMARY KEY (encargo_id, sha256)
);
CREATE INDEX IF NOT EXISTS idx_descargas_grupo_alias ON descargas(grupo_alias);

-- espejo de IntentoPuerta, una fila por puerta pedida. encargo_id es FK en
-- el sentido de docs/07; no se declara FOREIGN KEY de SQL porque no hay
-- todavía una tabla `encargos` cuya PK sea encargo_id (M20 no la crea).
CREATE TABLE IF NOT EXISTS intentos (
    encargo_id       TEXT NOT NULL,
    orden            INTEGER NOT NULL,
    url              TEXT NOT NULL,
    url_pedida       TEXT,
    url_final        TEXT,
    enlace_vestibulo TEXT,
    http_status      INTEGER,
    exito            INTEGER NOT NULL,
    motivo_fallo     TEXT
);
CREATE INDEX IF NOT EXISTS idx_intentos_encargo_id ON intentos(encargo_id);
"""


class Store:
    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_ESQUEMA)
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
                "entry_id": resultado.encargo_id,
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

    def guardar_descarga(self, resultado: DownloadResult, grupo_alias: str) -> None:
        self._conn.execute(
            """
            INSERT INTO descargas (
                encargo_id, modo, sha256, exito, ruta_local, bytes,
                content_type, http_status, capturado_en, url_final,
                motivo_fallo, puerta_usada, duplicado_de, grupo_alias
            ) VALUES (:encargo_id, :modo, :sha256, :exito, :ruta_local, :bytes,
                :content_type, :http_status, :capturado_en, :url_final,
                :motivo_fallo, :puerta_usada, :duplicado_de, :grupo_alias)
            ON CONFLICT(encargo_id, sha256) DO UPDATE SET
                modo = excluded.modo,
                exito = excluded.exito,
                ruta_local = excluded.ruta_local,
                bytes = excluded.bytes,
                content_type = excluded.content_type,
                http_status = excluded.http_status,
                capturado_en = excluded.capturado_en,
                url_final = excluded.url_final,
                motivo_fallo = excluded.motivo_fallo,
                puerta_usada = excluded.puerta_usada,
                duplicado_de = excluded.duplicado_de,
                grupo_alias = excluded.grupo_alias
            """,
            {
                "encargo_id": resultado.encargo_id,
                "modo": resultado.modo,
                "sha256": resultado.sha256,
                "exito": int(resultado.exito),
                "ruta_local": str(resultado.ruta_local) if resultado.ruta_local is not None else None,
                "bytes": int(resultado.bytes) if resultado.bytes is not None else None,
                "content_type": resultado.content_type,
                "http_status": int(resultado.http_status) if resultado.http_status is not None else None,
                "capturado_en": resultado.capturado_en.isoformat(),
                "url_final": resultado.url_final,
                "motivo_fallo": resultado.motivo_fallo,
                "puerta_usada": resultado.puerta_usada,
                "duplicado_de": resultado.duplicado_de,
                "grupo_alias": grupo_alias,
            },
        )
        for intento in resultado.intentos:
            self._conn.execute(
                """
                INSERT INTO intentos (
                    encargo_id, orden, url, url_pedida, url_final,
                    enlace_vestibulo, http_status, exito, motivo_fallo
                ) VALUES (:encargo_id, :orden, :url, :url_pedida, :url_final,
                    :enlace_vestibulo, :http_status, :exito, :motivo_fallo)
                """,
                {
                    "encargo_id": resultado.encargo_id,
                    "orden": intento.orden,
                    "url": intento.url,
                    "url_pedida": intento.url_pedida,
                    "url_final": intento.url_final,
                    "enlace_vestibulo": intento.enlace_vestibulo,
                    "http_status": int(intento.http_status) if intento.http_status is not None else None,
                    "exito": int(intento.exito),
                    "motivo_fallo": intento.motivo_fallo,
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

    def alias_por_hash(
        self, grupo_alias: str, sha256: str, excluir_encargo_id: str
    ) -> tuple[str, Path] | None:
        """El original registrado con estos bytes en el grupo (docs/05 criterio 16, docs/01 línea 940).

        Solo descargas exitosas que son dueñas de su archivo (`duplicado_de IS NULL`), así
        que un alias nunca apunta a otro alias. Un encargo no es alias de sí mismo.
        """
        fila = self._conn.execute(
            """
            SELECT encargo_id, ruta_local FROM descargas
            WHERE grupo_alias = ? AND sha256 = ? AND exito = 1
              AND duplicado_de IS NULL AND encargo_id != ?
              AND ruta_local IS NOT NULL
            ORDER BY capturado_en, rowid
            LIMIT 1
            """,
            (grupo_alias, sha256, excluir_encargo_id),
        ).fetchone()
        if fila is None:
            return None
        return fila["encargo_id"], Path(fila["ruta_local"])

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
