"""Cosecha de un índice institucional guardado: extrae con `lector/` y descarga (M47c).

Sustituye a `cosecha.py` y `cosecha_uam.py`; sirve para cualquier institución.
No forma parte del paquete `legisuni` — vive en `scripts/` y no se importa desde ahí.

Con `--solo-extraer` solo imprime conteos: no toca red ni base.
"""

import logging
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import typer

from legisuni.config import Settings
from legisuni.descargador.descargar import descargar, ya_descargado
from legisuni.descargador.fetch import Fetcher, construir_cliente
from legisuni.descargador.ratelimit import RateLimiter
from legisuni.descargador.robots import RobotsCache
from legisuni.descargador.store import Store
from legisuni.juridico import cosecha, traduccion
from legisuni.lector import slug

logger = logging.getLogger(__name__)


def main(
    html: list[Path] = typer.Option(..., "--html", help="Ruta al HTML del índice guardado (repetible)"),
    url_indice: list[str] = typer.Option(
        ..., "--url-indice", help="URL de origen del índice (repetible, emparejada por posición con --html)"
    ),
    inst_id: str = typer.Option(..., "--inst-id"),
    limite: int | None = typer.Option(None, "--limite", help="Procesar solo las primeras N entradas"),
    solo_extraer: bool = typer.Option(
        False, "--solo-extraer", help="Solo imprime los conteos de la extracción; no toca red ni base"
    ),
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(url_indice) == 1 and len(html) > 1:
        url_indice = url_indice * len(html)
    if len(url_indice) != len(html):
        raise typer.BadParameter("--url-indice debe repetirse una vez, o una vez por cada --html")

    entradas = cosecha.entradas_desde_paginas(inst_id, list(zip(html, url_indice, strict=True)))

    if solo_extraer:
        por_pagina = Counter(e.url_indice for e in entradas)
        typer.echo(f"[solo-extraer] {inst_id}: no se pide nada ni se escribe en la base")
        for ruta, url in zip(html, url_indice, strict=True):
            typer.echo(f"  {ruta}  <-  {url}: {por_pagina[url]} entradas nuevas")
        typer.echo(f"entradas: {len(entradas)}")
        typer.echo(f"entry_id distintos: {len({e.entry_id for e in entradas})}")
        typer.echo(f"href con salto de línea final: {sum(e.url_documento.endswith(chr(10)) for e in entradas)}")
        return  # antes de construir Settings: ni .env, ni cliente, ni base

    if limite is not None:
        entradas = entradas[:limite]

    encargos = [
        traduccion.traducir(entrada, slug.doc_slug(entrada.url_documento, entrada.titulo, inst_id))
        for entrada in entradas
    ]

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
        for entrada, encargo in zip(entradas, encargos, strict=True):
            logger.info("pidiendo %s (%s)", encargo.encargo_id, entrada.url_documento)
            omitido = ya_descargado(store, encargo.encargo_id) is not None
            # una omisión no escribe (M35): la regla vive dentro de descargar()
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
                "resultado %s: exito=%s motivo=%s", encargo.encargo_id, resultado.exito, resultado.motivo_fallo
            )

    typer.echo("--- resumen ---")
    typer.echo(f"total: {len(entradas)}")
    typer.echo(f"exitosas: {exitosas}")
    typer.echo(f"omitidos: {omitidos}")
    for motivo, cuenta in motivos_fallo.items():
        typer.echo(f"  {motivo}: {cuenta}")
    # parámetros de la corrida (E18.1 de docs/08)
    typer.echo(f"rate_limit_s: {settings.rate_limit_s}")
    typer.echo(f"user_agent: {settings.user_agent}")
    typer.echo(f"hosts distintos pedidos: {len(hosts_pedidos)}")


if __name__ == "__main__":
    typer.run(main)
