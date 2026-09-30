"""Limpieza de datos: las 4 filas de fallo duplicadas de B.7–B.10 (M39b, E19.11 de docs/08).

No forma parte del paquete `legisuni` y no es una corrección de código: M39 ya impide
que un fallo repetido añada fila. Esto borra, en `descargas`, las filas de fallo que se
acumularon antes de M39.

Qué se borra: para cada `encargo_id` con más de una fila con `sha256` NULL, todas salvo
la más reciente (`capturado_en DESC, rowid DESC`), que es lo que habría dejado M39.

Guardas, y aborta sin escribir si falla cualquiera:
- las filas a borrar son exactamente 4 (`FILAS_ESPERADAS`);
- la fila que se conserva de cada encargo es su fila vigente de M34: la última del
  encargo con el mismo orden que `Store._fila_vigente`. Así la limpieza no cambia lo que
  devuelven `hash_registrado` ni `ruta_registrada`;
- cada `DELETE` toca exactamente una fila.

`intentos` y `documentos` no se tocan: esos intentos ocurrieron.

Por defecto solo muestra y abre la base en solo lectura. Escribe únicamente con
`--aplicar`, en una transacción. Antes de aplicar:

    cp legisuni_v2.db ~/respaldo-acervo/legisuni_v2.antes-M39b.db
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import typer

FILAS_ESPERADAS = 4

_ENCARGOS_CON_FALLOS_REPETIDOS = """
SELECT encargo_id FROM descargas
WHERE sha256 IS NULL
GROUP BY encargo_id HAVING COUNT(*) > 1
ORDER BY encargo_id
"""

_FALLOS_DEL_ENCARGO = """
SELECT rowid, capturado_en, motivo_fallo FROM descargas
WHERE encargo_id = ? AND sha256 IS NULL
ORDER BY capturado_en DESC, rowid DESC
"""

# mismo orden que Store._fila_vigente (M34)
_FILA_VIGENTE = """
SELECT rowid FROM descargas
WHERE encargo_id = ?
ORDER BY capturado_en DESC, rowid DESC
LIMIT 1
"""

_BORRAR = "DELETE FROM descargas WHERE rowid = ? AND encargo_id = ? AND sha256 IS NULL"


@dataclass(frozen=True)
class Fila:
    rowid: int
    capturado_en: str
    motivo_fallo: str | None


def _abrir(db: Path, aplicar: bool) -> sqlite3.Connection:
    if aplicar:
        conn = sqlite3.connect(str(db), isolation_level=None)
        conn.execute("BEGIN IMMEDIATE")
        return conn
    return sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)


def _abortar(conn: sqlite3.Connection, aplicar: bool, mensaje: str) -> None:
    typer.echo(f"ABORTADO: {mensaje}. No se escribió nada.")
    if aplicar:
        conn.execute("ROLLBACK")
    raise typer.Exit(code=1)


def main(
    db: Path = typer.Option(..., "--db", help="Base SQLite a limpiar (p. ej. legisuni_v2.db)"),
    aplicar: bool = typer.Option(
        False,
        "--aplicar",
        help="Borra las filas. Antes: cp legisuni_v2.db ~/respaldo-acervo/legisuni_v2.antes-M39b.db",
    ),
) -> None:
    if not db.is_file():
        typer.echo(f"no existe la base: {db}")
        raise typer.Exit(code=1)

    conn = _abrir(db, aplicar)
    try:
        a_borrar: list[tuple[str, Fila]] = []
        for (encargo_id,) in conn.execute(_ENCARGOS_CON_FALLOS_REPETIDOS).fetchall():
            fallos = [Fila(*f) for f in conn.execute(_FALLOS_DEL_ENCARGO, (encargo_id,)).fetchall()]
            conservada, sobrantes = fallos[0], fallos[1:]
            (vigente,) = conn.execute(_FILA_VIGENTE, (encargo_id,)).fetchone()
            if vigente != conservada.rowid:
                _abortar(
                    conn, aplicar,
                    f"la fila que se conservaría de {encargo_id} (rowid {conservada.rowid}) "
                    f"no es su fila vigente (rowid {vigente})",
                )
            typer.echo(
                f"  CONSERVA  {encargo_id}  capturado_en={conservada.capturado_en}"
                f"  motivo={conservada.motivo_fallo}"
            )
            for fila in sobrantes:
                a_borrar.append((encargo_id, fila))
                typer.echo(
                    f"  BORRA     {encargo_id}  capturado_en={fila.capturado_en}  motivo={fila.motivo_fallo}"
                )

        if len(a_borrar) != FILAS_ESPERADAS:
            _abortar(conn, aplicar, f"{len(a_borrar)} filas a borrar, se esperaban {FILAS_ESPERADAS}")

        if aplicar:
            for encargo_id, fila in a_borrar:
                cursor = conn.execute(_BORRAR, (fila.rowid, encargo_id))
                if cursor.rowcount != 1:
                    _abortar(conn, aplicar, f"el DELETE de {encargo_id} tocó {cursor.rowcount} filas")
            conn.execute("COMMIT")
    except typer.Exit:
        raise
    except BaseException:
        if aplicar and conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()

    typer.echo("--- resumen ---")
    typer.echo(f"a borrar: {len(a_borrar)}")
    typer.echo("intentos y documentos: no se tocan")
    if aplicar:
        typer.echo(f"aplicado: {len(a_borrar)} filas borradas en una transacción")
    else:
        typer.echo("vista previa: no se escribió nada")


if __name__ == "__main__":
    typer.run(main)
