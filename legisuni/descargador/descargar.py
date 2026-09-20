"""Cose las piezas puras del Descargador: normaliza, pide, valida y escribe sin pisar nada."""

import hashlib
import logging
from datetime import datetime

from legisuni.config import Settings
from legisuni.contracts import DownloadResult, Encargo
from legisuni.descargador import paths
from legisuni.descargador.fetch import Fetcher
from legisuni.descargador.puertas import construir_intento, probar_puertas
from legisuni.descargador.robots import RobotsCache
from legisuni.descargador.store import Store

logger = logging.getLogger(__name__)


def descargar(
    encargo: Encargo,
    fetcher: Fetcher,
    robots: RobotsCache,
    settings: Settings,
    ahora: datetime | None = None,
    store: Store | None = None,
) -> DownloadResult:
    capturado_en = ahora if ahora is not None else datetime.now()

    if store is not None:
        sha256_previo = store.hash_registrado(encargo.encargo_id)
        if sha256_previo is not None:
            logger.info("omitido: %s ya registrado", encargo.encargo_id)
            return DownloadResult(
                encargo_id=encargo.encargo_id,
                modo=encargo.modo,
                exito=True,
                capturado_en=capturado_en,
                ruta_local=store.ruta_registrada(encargo.encargo_id),
                sha256=sha256_previo,
                intentos=[],
            )

    resultado = probar_puertas(encargo, fetcher, robots, settings)

    if not resultado.exito:
        ultimo = resultado.intentos[-1] if resultado.intentos else None
        return DownloadResult(
            encargo_id=encargo.encargo_id,
            modo=encargo.modo,
            exito=False,
            motivo_fallo=resultado.motivo_fallo,
            capturado_en=capturado_en,
            http_status=ultimo.http_status if ultimo is not None else None,
            url_final=ultimo.url_final if ultimo is not None else None,
            intentos=resultado.intentos,
        )

    assert resultado.respuesta is not None and resultado.extension is not None
    assert resultado.puerta_usada is not None
    puerta = encargo.puertas[resultado.puerta_usada]
    url_pedida = resultado.intentos[-1].url_pedida
    respuesta = resultado.respuesta
    extension = resultado.extension
    cuerpo = respuesta.cuerpo
    assert cuerpo is not None
    sha256 = hashlib.sha256(cuerpo).hexdigest()
    ruta = paths.ruta_documento(settings.data_root, encargo.cajon, encargo.etiqueta, extension)

    try:
        if ruta.exists() and hashlib.sha256(ruta.read_bytes()).hexdigest() == sha256:
            pass  # bytes idénticos ya en disco: no se reescribe
        else:
            if ruta.exists():
                # misma etiqueta, bytes distintos: conviven ambas versiones
                ruta = paths.ruta_documento(
                    settings.data_root, encargo.cajon, encargo.etiqueta, extension, sha256=sha256
                )
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(cuerpo)
    except Exception as exc:
        logger.error("fallo al escribir %s: %s", ruta, exc)
        intento_fallo = construir_intento(
            resultado.puerta_usada, puerta, url_pedida, respuesta, exito=False, motivo="http_error"
        )
        return DownloadResult(
            encargo_id=encargo.encargo_id,
            modo=encargo.modo,
            exito=False,
            motivo_fallo="http_error",
            capturado_en=capturado_en,
            http_status=respuesta.status,
            url_final=respuesta.url_final,
            intentos=[*resultado.intentos[:-1], intento_fallo],
        )

    return DownloadResult(
        encargo_id=encargo.encargo_id,
        modo=encargo.modo,
        exito=True,
        capturado_en=capturado_en,
        ruta_local=ruta,
        sha256=sha256,
        bytes=len(cuerpo),
        content_type=respuesta.content_type,
        http_status=respuesta.status,
        url_final=respuesta.url_final,
        puerta_usada=resultado.puerta_usada,
        intentos=resultado.intentos,
    )
