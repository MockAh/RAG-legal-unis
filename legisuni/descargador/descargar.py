"""Cose las piezas puras del Descargador: normaliza, pide, valida y escribe sin pisar nada."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path

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
        previo = ya_descargado(store, encargo.encargo_id)
        if previo is not None:
            sha256_previo, ruta_previa = previo
            logger.info("omitido: %s ya registrado", encargo.encargo_id)
            return DownloadResult(
                encargo_id=encargo.encargo_id,
                modo=encargo.modo,
                exito=True,
                capturado_en=capturado_en,
                ruta_local=ruta_previa,
                sha256=sha256_previo,
                intentos=[],
            )

    # un solo camino de escritura (M34): se persiste aquí, y una omisión no escribe (M35)
    resultado = _pedir_y_escribir(encargo, fetcher, robots, settings, capturado_en, store)
    if store is not None:
        store.guardar_descarga(resultado, encargo.grupo_alias)
    return resultado


def ya_descargado(store: Store, encargo_id: str) -> tuple[str, Path] | None:
    """Regla 5 de docs/05 (M40): descarga exitosa registrada **y** su archivo en disco con ese hash.

    `Store` solo mira la base; el disco se comprueba aquí, como en `_original_por_hash`. Los
    scripts la usan para su resumen, así que omitir y contar un omitido son la misma decisión.
    Un archivo ausente, ilegible o con otros bytes → None, nunca excepción.
    """
    sha256 = store.hash_registrado(encargo_id)
    ruta = store.ruta_registrada(encargo_id)
    if sha256 is None or ruta is None:
        return None
    try:
        with ruta.open("rb") as archivo:
            if hashlib.file_digest(archivo, "sha256").hexdigest() != sha256:
                return None
    except OSError:
        return None
    return sha256, ruta


def _pedir_y_escribir(
    encargo: Encargo,
    fetcher: Fetcher,
    robots: RobotsCache,
    settings: Settings,
    capturado_en: datetime,
    store: Store | None,
) -> DownloadResult:
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

    # alias por hash (docs/05 criterio 16): mismos bytes ya registrados en el grupo → no se escribe
    original = _original_por_hash(store, encargo, sha256)
    if original is not None:
        encargo_original, ruta_original = original
        logger.info("alias: %s tiene los bytes de %s", encargo.encargo_id, encargo_original)
        return DownloadResult(
            encargo_id=encargo.encargo_id,
            modo=encargo.modo,
            exito=True,
            capturado_en=capturado_en,
            ruta_local=ruta_original,
            sha256=sha256,
            bytes=len(cuerpo),
            content_type=respuesta.content_type,
            http_status=respuesta.status,
            url_final=respuesta.url_final,
            puerta_usada=resultado.puerta_usada,
            intentos=resultado.intentos,
            duplicado_de=encargo_original,
        )

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
            resultado.puerta_usada, puerta, url_pedida, respuesta, exito=False, motivo="http_error",
            enlace_vestibulo=resultado.intentos[-1].enlace_vestibulo,
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


def _original_por_hash(
    store: Store | None, encargo: Encargo, sha256: str
) -> tuple[str, Path] | None:
    """El grupo sale de `encargo.grupo_alias`, nunca del `encargo_id` (docs/01 v2.1).

    `ruta_local` debe apuntar al archivo que ya existía (docs/01 línea 417): si falta en
    disco o sus bytes ya no son esos, no hay alias y se escribe el propio.
    """
    if store is None:
        return None
    original = store.alias_por_hash(encargo.grupo_alias, sha256, encargo.encargo_id)
    if original is None:
        return None
    _, ruta_original = original
    try:
        if hashlib.sha256(ruta_original.read_bytes()).hexdigest() != sha256:
            return None
    except OSError:
        return None
    return original
