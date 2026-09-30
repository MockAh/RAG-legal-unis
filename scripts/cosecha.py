"""Script de un solo uso: corrida real del Descargador sobre el índice de una institución.

No forma parte del paquete `legisuni` — vive en `scripts/` y no se importa desde ahí.
"""

import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

import typer
from selectolax.parser import HTMLParser

from legisuni.config import Settings
from legisuni.contracts import CatalogEntry
from legisuni.descargador import paths
from legisuni.descargador.descargar import descargar, ya_descargado
from legisuni.descargador.fetch import Fetcher, construir_cliente
from legisuni.descargador.ratelimit import RateLimiter
from legisuni.descargador.robots import RobotsCache
from legisuni.descargador.store import Store
from legisuni.juridico import identificadores, traduccion

logger = logging.getLogger(__name__)

_EXTENSIONES = (".pdf", ".docx")
_LARGO_MAX_SLUG = 60


def entradas_desde_html(ruta_html: Path, url_indice: str, inst_id: str) -> list[CatalogEntry]:
    arbol = HTMLParser(_leer_html(ruta_html))
    entradas: list[CatalogEntry] = []
    vistos: set[str] = set()

    for enlace in arbol.css("a[href]"):
        href = enlace.attributes.get("href")
        if href is None or not href.strip().lower().endswith(_EXTENSIONES):
            continue

        titulo = enlace.text(strip=True)
        doc_slug = _doc_slug_desde_href(href)
        entry_id = identificadores.entry_id(inst_id, doc_slug, href, url_indice)
        if entry_id in vistos:
            continue
        vistos.add(entry_id)

        entradas.append(
            CatalogEntry(
                entry_id=entry_id,
                inst_id=inst_id,
                titulo=titulo,
                tipo_norma="otro",  # clasificar es tarea del Lector de Índice (spec 03), no de este script
                url_documento=href,  # crudo, sin normalizar (D5)
                estado="desconocido",
                origen="sitio_institucional",
                url_indice=url_indice,
                extraido_en=datetime.now(),
            )
        )

    return entradas


def _leer_html(ruta_html: Path) -> str:
    crudo = ruta_html.read_bytes()
    # el HTML declara su charset (a menudo iso-8859-1); no asumimos utf-8
    coincidencia = re.search(rb'charset=["\']?([\w-]+)', crudo, re.IGNORECASE)
    codificacion = coincidencia.group(1).decode("ascii") if coincidencia else "utf-8"
    return crudo.decode(codificacion)


def _doc_slug_desde_href(href: str) -> str:
    # sin patrón de sufijo por institución: slug largo del nombre de archivo, y punto
    nombre_archivo = unquote(Path(urlsplit(href).path).stem)
    return paths.sanear(nombre_archivo)[:_LARGO_MAX_SLUG]


def _entradas_desde_paginas(
    htmls: list[Path], urls_indice: list[str], inst_id: str
) -> list[CatalogEntry]:
    entradas: list[CatalogEntry] = []
    vistos: set[str] = set()
    for ruta_html, url_indice in zip(htmls, urls_indice, strict=True):
        for entrada in entradas_desde_html(ruta_html, url_indice, inst_id):
            if entrada.entry_id in vistos:
                continue
            vistos.add(entrada.entry_id)
            entradas.append(entrada)
    return entradas


def main(
    html: list[Path] = typer.Option(..., "--html", help="Ruta al HTML del índice guardado (repetible)"),
    url_indice: list[str] = typer.Option(
        ..., "--url-indice", help="URL de origen del índice (repetible, emparejada por posición con --html)"
    ),
    inst_id: str = typer.Option(..., "--inst-id"),
    limite: int | None = typer.Option(None, "--limite", help="Procesar solo las primeras N entradas"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Solo muestra qué haría, no descarga nada"),
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

    entradas = _entradas_desde_paginas(html, url_indice, inst_id)
    if limite is not None:
        entradas = entradas[:limite]

    encargos = [
        traduccion.traducir(entrada, _doc_slug_desde_href(entrada.url_documento)) for entrada in entradas
    ]

    if dry_run:
        typer.echo(f"[dry-run] {len(entradas)} entradas encontradas, no se pide nada:")
        for entrada, encargo in zip(entradas, encargos, strict=True):
            typer.echo(f"  {encargo.encargo_id}  {encargo.cajon}/{encargo.etiqueta}  <-  {entrada.url_documento}")
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
        for entrada, encargo in zip(entradas, encargos, strict=True):
            logger.info("pidiendo %s (%s)", encargo.encargo_id, entrada.url_documento)
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
