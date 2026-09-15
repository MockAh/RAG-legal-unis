"""Script de un solo uso: primera corrida real del Descargador sobre el índice de la UAM.

No forma parte del paquete `legisuni` — vive en `scripts/` y no se importa desde ahí.
"""

import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

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
from legisuni.juridico import identificadores, traduccion

logger = logging.getLogger(__name__)

_EXTENSIONES = (".pdf", ".docx")


def entradas_desde_html(ruta_html: Path, url_indice: str, inst_id: str) -> list[CatalogEntry]:
    arbol = HTMLParser(_leer_html(ruta_html))
    entradas: list[CatalogEntry] = []
    vistos: set[str] = set()

    for enlace in arbol.css("a[href]"):
        href = enlace.attributes.get("href")
        if href is None or not href.strip().lower().endswith(_EXTENSIONES):
            continue

        titulo = enlace.text(strip=True)
        doc_slug = _doc_slug_desde_href(href, titulo)
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
    # el HTML de la UAM declara su charset (a menudo iso-8859-1); no asumimos utf-8
    coincidencia = re.search(rb'charset=["\']?([\w-]+)', crudo, re.IGNORECASE)
    codificacion = coincidencia.group(1).decode("ascii") if coincidencia else "utf-8"
    return crudo.decode(codificacion)


def _doc_slug_desde_href(href: str, titulo: str) -> str:
    nombre_archivo = Path(urlsplit(href).path).stem
    if "-" in nombre_archivo:
        return nombre_archivo.rsplit("-", 1)[-1]
    return paths.sanear(titulo)


def main(
    html: Path = typer.Option(..., "--html", help="Ruta al HTML del índice guardado"),
    url_indice: str = typer.Option(..., "--url-indice", help="URL de origen del índice"),
    inst_id: str = typer.Option("uam", "--inst-id"),
    limite: int | None = typer.Option(None, "--limite", help="Procesar solo las primeras N entradas"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Solo muestra qué haría, no descarga nada"),
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    entradas = entradas_desde_html(html, url_indice, inst_id)
    if limite is not None:
        entradas = entradas[:limite]

    encargos = [
        traduccion.traducir(entrada, _doc_slug_desde_href(entrada.url_documento, entrada.titulo))
        for entrada in entradas
    ]

    if dry_run:
        typer.echo(f"[dry-run] {len(entradas)} entradas encontradas, no se pide nada:")
        for entrada, encargo in zip(entradas, encargos, strict=True):
            typer.echo(f"  {encargo.encargo_id}  {encargo.cajon}/{encargo.etiqueta}  <-  {entrada.url_documento}")
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
        for entrada, encargo in zip(entradas, encargos, strict=True):
            logger.info("pidiendo %s (%s)", encargo.encargo_id, entrada.url_documento)
            if store.hash_registrado(encargo.encargo_id) is not None:
                omitidos += 1
            resultado = descargar(encargo, fetcher, robots, settings, store=store)
            store.guardar(resultado)
            store.guardar_descarga(resultado, encargo.grupo_alias)
            if resultado.exito:
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


if __name__ == "__main__":
    typer.run(main)
