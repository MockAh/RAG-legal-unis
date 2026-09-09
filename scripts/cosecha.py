"""Script de un solo uso: corrida real del Descargador sobre el índice de una institución.

No forma parte del paquete `legisuni` — vive en `scripts/` y no se importa desde ahí.
"""

import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx
import typer
from selectolax.parser import HTMLParser

from legisuni.config import Settings
from legisuni.contracts import CatalogEntry
from legisuni.descargador import paths
from legisuni.descargador.descargar import descargar
from legisuni.descargador.fetch import Fetcher
from legisuni.descargador.ratelimit import RateLimiter
from legisuni.descargador.robots import RobotsCache
from legisuni.descargador.store import Store

logger = logging.getLogger(__name__)

_EXTENSIONES = (".pdf", ".docx")
_LARGO_MAX_SLUG = 60


def entradas_desde_html(ruta_html: Path, url_indice: str, inst_id: str) -> list[CatalogEntry]:
    arbol = HTMLParser(_leer_html(ruta_html))
    entradas: list[CatalogEntry] = []
    vistos: set[str] = set()

    for enlace in arbol.css("a[href]"):
        href = enlace.attributes.get("href")
        if href is None or not href.lower().endswith(_EXTENSIONES):
            continue

        titulo = enlace.text(strip=True)
        doc_slug = _doc_slug_desde_href(href)
        entry_id = f"{inst_id}:{doc_slug}"
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
    reanudar: bool = typer.Option(False, "--reanudar", help="Omite entradas ya registradas con éxito"),
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

    if dry_run:
        typer.echo(f"[dry-run] {len(entradas)} entradas encontradas, no se pide nada:")
        for entrada in entradas:
            typer.echo(f"  {entrada.entry_id}  <-  {entrada.url_documento}")
        return

    settings = Settings()
    limitador = RateLimiter(settings.rate_limit_s)
    cliente_http = httpx.Client()

    def _fetcher_robots(url: str) -> tuple[int, str]:
        r = httpx.get(
            url,
            timeout=settings.timeout_s,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        )
        return r.status_code, r.text

    robots = RobotsCache(settings.user_agent, _fetcher_robots)
    fetcher = Fetcher(settings, limitador, robots, cliente=cliente_http)

    motivos_fallo: Counter[str] = Counter()
    exitosas = 0
    omitidos = 0

    with Store(settings.db_path) as store:
        for entrada in entradas:
            logger.info("pidiendo %s (%s)", entrada.entry_id, entrada.url_documento)
            if reanudar and store.hash_registrado(entrada.entry_id) is not None:
                omitidos += 1
            resultado = descargar(
                entrada, fetcher, robots, settings, store=store, omitir_si_registrado=reanudar
            )
            store.guardar(resultado)
            if resultado.exito:
                exitosas += 1
            else:
                assert resultado.motivo_fallo is not None
                motivos_fallo[resultado.motivo_fallo] += 1
            logger.info(
                "resultado %s: exito=%s motivo=%s", entrada.entry_id, resultado.exito, resultado.motivo_fallo
            )

    typer.echo("--- resumen ---")
    typer.echo(f"total: {len(entradas)}")
    typer.echo(f"exitosas: {exitosas}")
    typer.echo(f"omitidos: {omitidos}")
    for motivo, cuenta in motivos_fallo.items():
        typer.echo(f"  {motivo}: {cuenta}")


if __name__ == "__main__":
    typer.run(main)
