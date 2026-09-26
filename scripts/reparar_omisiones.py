"""Reparación de datos: las 47 filas de la UAM que pisó una omisión (M35b, E17 de docs/08).

No forma parte del paquete `legisuni` y no es una corrección de código: M35 ya impide
que una omisión escriba. Esto repara, en `descargas`, lo que las omisiones del 23 y
del 26 dejaron en NULL.

Fuentes, y ninguna otra:
- `url_final`, `http_status`: del único intento con `exito = 1` del encargo, que
  además debe tener `orden = 0`.
- `puerta_usada = 0`: el `orden` de ese intento.
- `bytes`: tamaño del archivo en `ruta_local`, solo si su SHA-256 coincide con el
  `sha256` de la fila.
- `capturado_en`: **ESTIMACIÓN.** Fecha de modificación del archivo: cuándo se escribió
  el archivo, no cuándo se capturó la respuesta.
- `content_type`: no se toca. Pérdida definitiva (E17).

Una fila se repara entera o no se toca; la que no cumple una condición queda intacta
y se reporta. Nada se rellena por analogía. `documentos` e `intentos` no se tocan.

Por defecto solo muestra y abre la base en solo lectura. Escribe únicamente con
`--aplicar`, en una transacción. Aborta si las filas afectadas no son exactamente 47.
Se ejecuta desde la raíz del repo (`ruta_local` es relativa a ella). Antes de aplicar:

    cp legisuni_v2.db ~/respaldo-acervo/legisuni_v2.antes-M35b.db
"""

import hashlib
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import typer

FILAS_ESPERADAS = 47

_AFECTADAS = """
SELECT encargo_id, sha256, ruta_local FROM descargas
WHERE encargo_id LIKE 'uam:%' AND exito = 1
  AND bytes IS NULL AND http_status IS NULL AND url_final IS NULL AND puerta_usada IS NULL
ORDER BY encargo_id
"""

_ACTUALIZAR = """
UPDATE descargas
SET url_final = ?, http_status = ?, bytes = ?, puerta_usada = ?, capturado_en = ?
WHERE encargo_id = ? AND sha256 = ? AND exito = 1
  AND bytes IS NULL AND http_status IS NULL AND url_final IS NULL AND puerta_usada IS NULL
"""

_CABECERA = (
    "capturado_en es una ESTIMACIÓN: fecha de modificación del archivo, que indica cuándo se\n"
    "escribió el archivo, no cuándo se capturó la respuesta. content_type no se toca:\n"
    "pérdida definitiva (E17 de docs/08)."
)


@dataclass(frozen=True)
class Reparacion:
    encargo_id: str
    sha256: str
    url_final: str
    http_status: int
    bytes: int
    puerta_usada: int
    capturado_en: str


def _sha256_de(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _evaluar_fila(
    conn: sqlite3.Connection, encargo_id: str, sha256: str | None, ruta_local: str | None
) -> Reparacion | str:
    """Devuelve la reparación completa, o el motivo por el que la fila queda intacta."""
    if sha256 is None:
        return "fila sin sha256"
    intentos = conn.execute(
        "SELECT orden, url_final, http_status FROM intentos WHERE encargo_id = ? AND exito = 1",
        (encargo_id,),
    ).fetchall()
    if len(intentos) != 1:
        return f"{len(intentos)} intentos con exito=1, se exige exactamente uno"
    orden, url_final, http_status = intentos[0]
    if orden != 0:
        return f"el intento exitoso tiene orden={orden}, se exige 0"
    if url_final is None or http_status is None:
        return "el intento exitoso no tiene url_final o http_status"
    if ruta_local is None:
        return "fila sin ruta_local"
    ruta = Path(ruta_local)
    try:
        if not ruta.is_file():
            return f"archivo ausente: {ruta_local}"
        sha_disco = _sha256_de(ruta)
        estado = ruta.stat()
    except OSError as error:
        return f"archivo ilegible: {ruta_local} ({error})"
    if sha_disco != sha256:
        return f"el SHA-256 del archivo no coincide con la fila: {ruta_local}"
    return Reparacion(
        encargo_id=encargo_id,
        sha256=sha256,
        url_final=url_final,
        http_status=http_status,
        bytes=estado.st_size,
        puerta_usada=orden,
        capturado_en=datetime.fromtimestamp(estado.st_mtime).isoformat(),
    )


def _abrir(db: Path, aplicar: bool) -> sqlite3.Connection:
    if aplicar:
        conn = sqlite3.connect(str(db), isolation_level=None)
        conn.execute("BEGIN IMMEDIATE")
        return conn
    return sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)


def main(
    db: Path = typer.Option(..., "--db", help="Base SQLite a reparar (p. ej. legisuni_v2.db)"),
    aplicar: bool = typer.Option(
        False,
        "--aplicar",
        help="Escribe las reparaciones. Antes: cp legisuni_v2.db ~/respaldo-acervo/legisuni_v2.antes-M35b.db",
    ),
) -> None:
    if not db.is_file():
        typer.echo(f"no existe la base: {db}")
        raise typer.Exit(code=1)

    typer.echo(_CABECERA)
    conn = _abrir(db, aplicar)
    try:
        afectadas = conn.execute(_AFECTADAS).fetchall()
        if len(afectadas) != FILAS_ESPERADAS:
            typer.echo(f"ABORTADO: {len(afectadas)} filas afectadas, se esperaban {FILAS_ESPERADAS}. No se escribió nada.")
            if aplicar:
                conn.execute("ROLLBACK")
            raise typer.Exit(code=1)

        reparaciones: list[Reparacion] = []
        intactas: list[tuple[str, str]] = []
        for encargo_id, sha256, ruta_local in afectadas:
            evaluacion = _evaluar_fila(conn, encargo_id, sha256, ruta_local)
            if isinstance(evaluacion, Reparacion):
                reparaciones.append(evaluacion)
                typer.echo(
                    f"  REPARABLE  {encargo_id}  url_final={evaluacion.url_final}"
                    f"  http_status={evaluacion.http_status}  bytes={evaluacion.bytes}"
                    f"  puerta_usada={evaluacion.puerta_usada}"
                    f"  capturado_en≈{evaluacion.capturado_en} (estimación)"
                )
            else:
                intactas.append((encargo_id, evaluacion))
                typer.echo(f"  INTACTA    {encargo_id}  {evaluacion}")

        if aplicar:
            for r in reparaciones:
                cursor = conn.execute(
                    _ACTUALIZAR,
                    (r.url_final, r.http_status, r.bytes, r.puerta_usada, r.capturado_en, r.encargo_id, r.sha256),
                )
                if cursor.rowcount != 1:
                    conn.execute("ROLLBACK")
                    typer.echo(f"ABORTADO: el UPDATE de {r.encargo_id} tocó {cursor.rowcount} filas. No se escribió nada.")
                    raise typer.Exit(code=1)
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
    typer.echo(f"afectadas: {len(afectadas)}")
    typer.echo(f"reparables: {len(reparaciones)}")
    typer.echo(f"intactas: {len(intactas)}")
    for motivo, cuenta in Counter(motivo for _, motivo in intactas).items():
        typer.echo(f"  {cuenta}  {motivo}")
    typer.echo("capturado_en estimado, por día (solo informativo, no filtra):")
    for dia, cuenta in sorted(Counter(r.capturado_en[:10] for r in reparaciones).items()):
        typer.echo(f"  {dia}: {cuenta}")
    typer.echo("content_type: no se toca (pérdida definitiva)")
    if aplicar:
        typer.echo(f"aplicado: {len(reparaciones)} filas reparadas en una transacción")
    else:
        typer.echo("vista previa: no se escribió nada")


if __name__ == "__main__":
    typer.run(main)
