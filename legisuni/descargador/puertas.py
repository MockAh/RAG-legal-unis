"""Bucle de puertas del Encargo: prueba cada una en orden y arma su recibo (docs/05, criterio 13)."""

from dataclasses import dataclass

from legisuni.config import Settings
from legisuni.contracts import Encargo, IntentoPuerta, MotivoFallo, Puerta
from legisuni.descargador import guard, muros, urlnorm
from legisuni.descargador.fetch import Fetcher, RespuestaCruda
from legisuni.descargador.robots import RobotsCache


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

    for orden, puerta in enumerate(encargo.puertas):
        # puerta.url nunca se modifica: es proveniencia (D5)
        url = urlnorm.normalizar(puerta.url, puerta.url_base or "")

        if not robots.permitido(url):
            ultimo_motivo = "robots_prohibido"
            intentos.append(construir_intento(orden, puerta, url, None, exito=False, motivo=ultimo_motivo))
            continue

        respuesta = fetcher.pedir(url)

        if muros.es_muro_de_pago(respuesta.status, respuesta.url_final):
            ultimo_motivo = "muro_de_pago"
            intentos.append(
                construir_intento(orden, puerta, url, respuesta, exito=False, motivo=ultimo_motivo)
            )
            continue

        if respuesta.motivo_red is not None:
            ultimo_motivo = respuesta.motivo_red
            intentos.append(
                construir_intento(orden, puerta, url, respuesta, exito=False, motivo=ultimo_motivo)
            )
            continue

        if respuesta.excedio_tamano:
            ultimo_motivo = "demasiado_grande"
            intentos.append(
                construir_intento(orden, puerta, url, respuesta, exito=False, motivo=ultimo_motivo)
            )
            continue

        motivo, extension = guard.evaluar(
            respuesta.url_final, respuesta.primeros_bytes, respuesta.tamano, settings.max_bytes
        )
        if motivo is not None:
            ultimo_motivo = motivo
            intentos.append(construir_intento(orden, puerta, url, respuesta, exito=False, motivo=motivo))
            continue

        intentos.append(construir_intento(orden, puerta, url, respuesta, exito=True))
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


def construir_intento(
    orden: int,
    puerta: Puerta,
    url_pedida: str,
    respuesta: RespuestaCruda | None,
    exito: bool,
    motivo: MotivoFallo | None = None,
) -> IntentoPuerta:
    return IntentoPuerta(
        orden=orden,
        url=puerta.url,
        url_pedida=url_pedida,
        url_final=respuesta.url_final if respuesta is not None else None,
        enlace_vestibulo=None,
        http_status=respuesta.status if respuesta is not None else None,
        exito=exito,
        motivo_fallo=motivo,
    )
