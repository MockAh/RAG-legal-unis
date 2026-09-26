"""Bucle de puertas del Encargo: prueba cada una en orden y arma su recibo (docs/05, criterio 13).

Orden dentro de una puerta (docs/01 línea 937): petición → guardián → vestíbulo (un
salto, solo con `cruzar_vestibulos=True` y respuesta HTML) → guardián.

M33 (E15.6 de docs/08): si la respuesta de una puerta acaba en una `url_final` a la
que ya llegó una puerta anterior del mismo encargo, no se evalúa ni se cruza su
vestíbulo otra vez: su intento lleva el motivo de la primera. Se detecta después de
pedir, porque en A.6 las URLs iniciales eran distintas y solo coincidían tras redirigir.
"""

import logging
from dataclasses import dataclass

from legisuni.config import Settings
from legisuni.contracts import Encargo, IntentoPuerta, MotivoFallo, Puerta
from legisuni.descargador import guard, muros, urlnorm, vestibulo
from legisuni.descargador.fetch import Fetcher, RespuestaCruda
from legisuni.descargador.robots import RobotsCache

logger = logging.getLogger(__name__)


@dataclass
class ResultadoPuertas:
    exito: bool
    puerta_usada: int | None
    respuesta: RespuestaCruda | None
    extension: str | None
    motivo_fallo: MotivoFallo | None
    intentos: list[IntentoPuerta]


def probar_puertas(
    encargo: Encargo, fetcher: Fetcher, robots: RobotsCache, settings: Settings
) -> ResultadoPuertas:
    intentos: list[IntentoPuerta] = []
    ultimo_motivo: MotivoFallo | None = None
    # url_final de cada puerta que tuvo respuesta HTTP (antes del vestíbulo) → (orden, motivo)
    destinos: dict[str, tuple[int, MotivoFallo]] = {}

    for orden, puerta in enumerate(encargo.puertas):
        # puerta.url nunca se modifica: es proveniencia (D5)
        url = urlnorm.normalizar(puerta.url, puerta.url_base or "")

        if not robots.permitido(url):
            ultimo_motivo = "robots_prohibido"
            intentos.append(construir_intento(orden, puerta, url, None, exito=False, motivo=ultimo_motivo))
            continue

        respuesta = fetcher.pedir(url)
        destino = respuesta.url_final if respuesta.status is not None else None

        if destino is not None and destino in destinos:
            orden_previo, ultimo_motivo = destinos[destino]
            logger.info("puerta %d: destino %s ya pedido por la puerta %d", orden, destino, orden_previo)
            intentos.append(construir_intento(orden, puerta, url, respuesta, exito=False, motivo=ultimo_motivo))
            continue

        motivo, extension = _evaluar_respuesta(respuesta, settings)
        enlace_vestibulo: str | None = None

        if (
            motivo == "no_es_pdf"
            and encargo.cruzar_vestibulos
            and vestibulo.es_html(respuesta.primeros_bytes, respuesta.content_type)
        ):
            motivo, extension, respuesta, enlace_vestibulo = _cruzar_vestibulo(
                respuesta, fetcher, robots, settings
            )

        if motivo is not None:
            ultimo_motivo = motivo
            if destino is not None:
                destinos.setdefault(destino, (orden, motivo))
            intentos.append(
                construir_intento(
                    orden, puerta, url, respuesta, exito=False, motivo=motivo,
                    enlace_vestibulo=enlace_vestibulo,
                )
            )
            continue

        intentos.append(
            construir_intento(orden, puerta, url, respuesta, exito=True, enlace_vestibulo=enlace_vestibulo)
        )
        return ResultadoPuertas(
            exito=True,
            puerta_usada=orden,
            respuesta=respuesta,
            extension=extension,
            motivo_fallo=None,
            intentos=intentos,
        )

    motivo_final = ultimo_motivo if len(encargo.puertas) == 1 else "puertas_agotadas"
    return ResultadoPuertas(
        exito=False,
        puerta_usada=None,
        respuesta=None,
        extension=None,
        motivo_fallo=motivo_final,
        intentos=intentos,
    )


def _evaluar_respuesta(
    respuesta: RespuestaCruda, settings: Settings
) -> tuple[MotivoFallo | None, str | None]:
    """Lo que pasa una respuesta, sea de puerta o de salto: muros → red → tamaño → guardián."""
    if muros.es_muro_de_pago(respuesta.status, respuesta.url_final, respuesta.redirecciones):
        return "muro_de_pago", None
    if respuesta.motivo_red is not None:
        return respuesta.motivo_red, None
    if respuesta.excedio_tamano:
        return "demasiado_grande", None
    return guard.evaluar(
        respuesta.url_final, respuesta.primeros_bytes, respuesta.tamano, settings.max_bytes
    )


def _cruzar_vestibulo(
    respuesta: RespuestaCruda, fetcher: Fetcher, robots: RobotsCache, settings: Settings
) -> tuple[MotivoFallo | None, str | None, RespuestaCruda, str | None]:
    """Un solo salto. Devuelve (motivo, extensión, respuesta, enlace literal de la página)."""
    enlace = vestibulo.extraer_enlace(respuesta.cuerpo or b"")
    if enlace is None:
        return "vestibulo_sin_pdf", None, respuesta, None

    # relativo → contra la url_final del vestíbulo, con la misma normalización que una puerta
    url_enlace = urlnorm.normalizar(enlace, respuesta.url_final)
    if not robots.permitido(url_enlace):
        return "robots_prohibido", None, respuesta, enlace

    salto = fetcher.pedir(url_enlace)
    motivo, extension = _evaluar_respuesta(salto, settings)
    # HTML otra vez: no hay recursión, ninguna petición más
    if motivo == "no_es_pdf" and vestibulo.es_html(salto.primeros_bytes, salto.content_type):
        motivo = "vestibulo_sin_pdf"
    return motivo, extension, salto, enlace


def construir_intento(
    orden: int,
    puerta: Puerta,
    url_pedida: str,
    respuesta: RespuestaCruda | None,
    exito: bool,
    motivo: MotivoFallo | None = None,
    enlace_vestibulo: str | None = None,
) -> IntentoPuerta:
    return IntentoPuerta(
        orden=orden,
        url=puerta.url,
        url_pedida=url_pedida,
        url_final=respuesta.url_final if respuesta is not None else None,
        enlace_vestibulo=enlace_vestibulo,
        http_status=respuesta.status if respuesta is not None else None,
        exito=exito,
        motivo_fallo=motivo,
    )
