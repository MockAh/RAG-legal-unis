"""Cose las piezas puras del Descargador: normaliza, pide, valida y escribe sin pisar nada."""

import hashlib
import logging
from datetime import datetime

from legisuni.config import Settings
from legisuni.contracts import DownloadResult, Encargo, IntentoPuerta, Puerta
from legisuni.descargador import guard, paths, urlnorm
from legisuni.descargador.fetch import Fetcher, RespuestaCruda
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

    # bucle de puertas: M26. Aquí se prueba solo la primera (v3, comportamiento de v2).
    puerta = encargo.puertas[0]

    # puerta.url nunca se modifica: es proveniencia (D5)
    url = urlnorm.normalizar(puerta.url, puerta.url_base or "")

    if not robots.permitido(url):
        return _fallo(encargo, capturado_en, puerta, url, "robots_prohibido")

    respuesta = fetcher.pedir(url)

    if respuesta.motivo_red is not None:
        return _fallo(encargo, capturado_en, puerta, url, respuesta.motivo_red, respuesta)

    if respuesta.excedio_tamano:
        return _fallo(encargo, capturado_en, puerta, url, "demasiado_grande", respuesta)

    motivo, extension = guard.evaluar(
        respuesta.url_final, respuesta.primeros_bytes, respuesta.tamano, settings.max_bytes
    )
    if motivo is not None:
        return _fallo(encargo, capturado_en, puerta, url, motivo, respuesta)

    assert respuesta.cuerpo is not None and extension is not None
    cuerpo = respuesta.cuerpo
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
        return _fallo(encargo, capturado_en, puerta, url, "http_error", respuesta)

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
        puerta_usada=0,
        intentos=[_intento(puerta, url, respuesta, exito=True)],
    )


def _intento(
    puerta: Puerta,
    url_pedida: str,
    respuesta: RespuestaCruda | None,
    exito: bool,
    motivo: str | None = None,
) -> IntentoPuerta:
    return IntentoPuerta(
        orden=0,
        url=puerta.url,
        url_pedida=url_pedida,
        url_final=respuesta.url_final if respuesta is not None else None,
        enlace_vestibulo=None,
        http_status=respuesta.status if respuesta is not None else None,
        exito=exito,
        motivo_fallo=motivo,
    )


def _fallo(
    encargo: Encargo,
    capturado_en: datetime,
    puerta: Puerta,
    url_pedida: str,
    motivo: str,
    respuesta: RespuestaCruda | None = None,
) -> DownloadResult:
    return DownloadResult(
        encargo_id=encargo.encargo_id,
        modo=encargo.modo,
        exito=False,
        motivo_fallo=motivo,
        capturado_en=capturado_en,
        http_status=respuesta.status if respuesta is not None else None,
        url_final=respuesta.url_final if respuesta is not None else None,
        intentos=[_intento(puerta, url_pedida, respuesta, exito=False, motivo=motivo)],
    )
