"""Cose las piezas puras del Descargador: normaliza, pide, valida y escribe sin pisar nada."""

import hashlib
import logging
from datetime import datetime

from legisuni.config import Settings
from legisuni.contracts import CatalogEntry, DownloadResult
from legisuni.descargador import guard, paths, urlnorm
from legisuni.descargador.fetch import Fetcher, RespuestaCruda
from legisuni.descargador.robots import RobotsCache
from legisuni.descargador.store import Store

logger = logging.getLogger(__name__)


def descargar(
    entrada: CatalogEntry,
    fetcher: Fetcher,
    robots: RobotsCache,
    settings: Settings,
    ahora: datetime | None = None,
    store: Store | None = None,
    omitir_si_registrado: bool = False,
) -> DownloadResult:
    capturado_en = ahora if ahora is not None else datetime.now()

    if omitir_si_registrado and store is not None:
        sha256_previo = store.hash_registrado(entrada.entry_id)
        if sha256_previo is not None:
            logger.info("omitido: %s ya registrado", entrada.entry_id)
            return DownloadResult(
                entry_id=entrada.entry_id,
                modo="juridico",
                exito=True,
                capturado_en=capturado_en,
                ruta_local=store.ruta_registrada(entrada.entry_id),
                sha256=sha256_previo,
                intentos=[],
            )

    # entrada.url_documento nunca se modifica: es proveniencia (D5)
    url = urlnorm.normalizar(entrada.url_documento, entrada.url_indice)

    if not robots.permitido(url):
        return _fallo(entrada.entry_id, capturado_en, "robots_prohibido")

    respuesta = fetcher.pedir(url)

    if respuesta.motivo_red is not None:
        return _fallo(entrada.entry_id, capturado_en, respuesta.motivo_red, respuesta)

    if respuesta.excedio_tamano:
        return _fallo(entrada.entry_id, capturado_en, "demasiado_grande", respuesta)

    motivo, extension = guard.evaluar(
        respuesta.url_final, respuesta.primeros_bytes, respuesta.tamano, settings.max_bytes
    )
    if motivo is not None:
        return _fallo(entrada.entry_id, capturado_en, motivo, respuesta)

    assert respuesta.cuerpo is not None and extension is not None
    cuerpo = respuesta.cuerpo
    sha256 = hashlib.sha256(cuerpo).hexdigest()
    fecha_version = paths.fecha_de_version(entrada, capturado_en)
    ruta = paths.ruta_documento(
        settings.data_dir, entrada.inst_id, entrada.entry_id, fecha_version, extension
    )

    try:
        if ruta.exists() and hashlib.sha256(ruta.read_bytes()).hexdigest() == sha256:
            pass  # bytes idénticos ya en disco: no se reescribe
        else:
            if ruta.exists():
                # mismos fecha y slug, bytes distintos: conviven ambas versiones
                ruta = paths.ruta_documento(
                    settings.data_dir,
                    entrada.inst_id,
                    entrada.entry_id,
                    fecha_version,
                    extension,
                    sha256=sha256,
                )
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(cuerpo)
    except Exception as exc:
        logger.error("fallo al escribir %s: %s", ruta, exc)
        return _fallo(entrada.entry_id, capturado_en, "http_error", respuesta)

    return DownloadResult(
        entry_id=entrada.entry_id,
        modo="juridico",
        exito=True,
        capturado_en=capturado_en,
        ruta_local=ruta,
        sha256=sha256,
        bytes=len(cuerpo),
        content_type=respuesta.content_type,
        http_status=respuesta.status,
        url_final=respuesta.url_final,
        intentos=[],
    )


def _fallo(
    entry_id: str,
    capturado_en: datetime,
    motivo: str,
    respuesta: RespuestaCruda | None = None,
) -> DownloadResult:
    return DownloadResult(
        entry_id=entry_id,
        modo="juridico",
        exito=False,
        motivo_fallo=motivo,
        capturado_en=capturado_en,
        http_status=respuesta.status if respuesta is not None else None,
        url_final=respuesta.url_final if respuesta is not None else None,
        intentos=[],
    )
