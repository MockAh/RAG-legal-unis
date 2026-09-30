"""Script de corrida: descarga los Encargos académicos de un JSON armado de antemano (M30).

No forma parte del paquete `legisuni` — vive en `scripts/` y no se importa desde ahí.
La entrada es el JSON (p. ej. `datos/encargos_bloque_a.json`); la lista original
no se lee aquí.
"""

import json
import logging
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import typer

from legisuni.config import Settings
from legisuni.contracts import Encargo
from legisuni.descargador.descargar import descargar, ya_descargado
from legisuni.descargador.fetch import Fetcher, construir_cliente
from legisuni.descargador.ratelimit import RateLimiter
from legisuni.descargador.robots import RobotsCache
from legisuni.descargador.store import Store

logger = logging.getLogger(__name__)


def main(
    encargos_json: Path = typer.Option(
        Path("datos/encargos_bloque_a.json"), "--encargos", help="JSON con los Encargos del lote"
    ),
    limite: int | None = typer.Option(None, "--limite", help="Procesar solo los primeros N encargos"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Solo muestra qué haría, no descarga nada"),
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    lote = json.loads(encargos_json.read_text(encoding="utf-8"))
    encargos = [Encargo.model_validate(e) for e in lote["encargos"]]
    if limite is not None:
        encargos = encargos[:limite]

    if dry_run:
        typer.echo(f"[dry-run] lote {lote['lote_id']}: {len(encargos)} encargos, no se pide nada:")
        for encargo in encargos:
            posicion = encargo.puertas[0].evidencia.rsplit("#", 1)[-1]
            typer.echo(f"  {posicion}  {encargo.encargo_id}  ->  {encargo.cajon}/{encargo.etiqueta}")
            for orden, puerta in enumerate(encargo.puertas):
                marca = "  (construida)" if puerta.construida else ""
                typer.echo(f"      {orden}. {puerta.tipo:<14} {puerta.url}{marca}")
        for faltante in lote["no_obtenidos"]:
            typer.echo(
                f"  no descargable: {faltante['articulo_id']}  motivo={faltante['motivo']}"
                f"  ({faltante['referencia_literal']})"
            )
        return

    settings = Settings()
    limitador = RateLimiter(settings.rate_limit_s)
    cliente_http = construir_cliente(settings)
    robots = RobotsCache(settings.user_agent, cliente_http)
    fetcher = Fetcher(settings, limitador, robots, cliente=cliente_http)

    motivos_fallo: Counter[str] = Counter()
    exitosas = 0
    omitidos = 0
    hosts_pedidos: set[str] = set()

    with Store(settings.db_path) as store:
        for encargo in encargos:
            logger.info("pidiendo %s (%d puertas)", encargo.encargo_id, len(encargo.puertas))
            omitido = ya_descargado(store, encargo.encargo_id) is not None
            resultado = descargar(encargo, fetcher, robots, settings, store=store)
            # E18.1 de docs/08: una puerta con robots_prohibido no llega a pedirse
            hosts_pedidos.update(
                urlsplit(i.url_pedida).hostname or ""
                for i in resultado.intentos
                if i.url_pedida and i.motivo_fallo != "robots_prohibido"
            )
            # categorías disjuntas: un omitido también trae exito=True (E16 de docs/08)
            if omitido:
                omitidos += 1
            elif resultado.exito:
                exitosas += 1
            else:
                assert resultado.motivo_fallo is not None
                motivos_fallo[resultado.motivo_fallo] += 1
            logger.info(
                "resultado %s: exito=%s puerta=%s motivo=%s",
                encargo.encargo_id, resultado.exito, resultado.puerta_usada, resultado.motivo_fallo,
            )

    typer.echo("--- resumen ---")
    typer.echo(f"total: {len(encargos)}")
    typer.echo(f"exitosas: {exitosas}")
    typer.echo(f"omitidos: {omitidos}")
    for motivo, cuenta in motivos_fallo.items():
        typer.echo(f"  {motivo}: {cuenta}")
    typer.echo(f"sin puertas (no se piden): {len(lote['no_obtenidos'])}")
    # parámetros de la corrida (E18.1 de docs/08)
    typer.echo(f"rate_limit_s: {settings.rate_limit_s}")
    typer.echo(f"user_agent: {settings.user_agent}")
    typer.echo(f"hosts distintos pedidos: {len(hosts_pedidos)}")


if __name__ == "__main__":
    typer.run(main)
