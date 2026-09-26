"""Cliente HTTP del Descargador: pide bytes crudos, sin escribir a disco ni construir el contrato."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import httpx

from legisuni.config import Settings
from legisuni.descargador.ratelimit import RateLimiter
from legisuni.descargador.robots import RobotsCache

MotivoRed = Literal["timeout", "http_error", "url_muerta"]

_TAMANO_PRIMEROS_BYTES = 512


def construir_cliente(settings: Settings) -> httpx.Client:
    """El único `httpx.Client` de una corrida: UA, timeout y TLS estricto salen de `Settings`."""
    return httpx.Client(
        headers={"User-Agent": settings.user_agent},
        timeout=settings.timeout_s,
        verify=True,
    )


@dataclass
class RespuestaCruda:
    status: int | None
    primeros_bytes: bytes  # hasta 512, para el guardián de formato
    cuerpo: bytes | None  # None si se abortó por tamaño
    content_type: str | None
    url_final: str  # tras redirecciones (proveniencia, D5)
    tamano: int | None  # bytes leídos realmente
    excedio_tamano: bool
    motivo_red: MotivoRed | None
    intentos: int
    # URLs pedidas antes de url_final, en orden (la primera es la pedida); para muros.py
    redirecciones: tuple[str, ...] = ()


class Fetcher:
    def __init__(
        self,
        settings: Settings,
        limitador: RateLimiter,
        robots: RobotsCache,
        cliente: httpx.Client,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._limitador = limitador
        self._robots = robots
        self._cliente = cliente
        self._dormir = dormir

    def pedir(self, url: str) -> RespuestaCruda:
        # robots.permitido() no se consulta aquí: es una decisión de política de M7, no un fallo de red
        self._limitador.esperar(url)
        max_intentos = self._settings.max_reintentos
        headers = {"User-Agent": self._settings.user_agent}

        for intento in range(1, max_intentos + 1):
            ultimo_intento = intento == max_intentos
            try:
                respuesta = self._intentar(url, headers)
            except httpx.TimeoutException:
                if not ultimo_intento:
                    self._dormir(min(2**intento, 60))
                    continue
                return self._respuesta_vacia(url, "timeout", intento)
            except httpx.HTTPError:
                # errores de transporte que no son timeout (DNS, conexión, etc.) no se reintentan
                return self._respuesta_vacia(url, "http_error", intento)

            respuesta.intentos = intento

            if respuesta.status == 404:
                respuesta.motivo_red = "url_muerta"
                return respuesta

            es_reintentable = respuesta.status == 429 or (
                respuesta.status is not None and 500 <= respuesta.status < 600
            )
            if es_reintentable:
                if not ultimo_intento:
                    self._dormir(min(2**intento, 60))
                    continue
                respuesta.motivo_red = "http_error"
                return respuesta

            if respuesta.status is not None and 400 <= respuesta.status < 500:
                respuesta.motivo_red = "http_error"
                return respuesta

            return respuesta

        raise AssertionError("bucle de reintentos terminó sin retornar")  # inalcanzable

    def _intentar(self, url: str, headers: dict[str, str]) -> RespuestaCruda:
        with self._cliente.stream(
            "GET",
            url,
            follow_redirects=True,
            timeout=self._settings.timeout_s,
            headers=headers,
        ) as respuesta:
            primeros_bytes = b""
            trozos: list[bytes] = []
            tamano = 0
            excedio = False
            for trozo in respuesta.iter_bytes():
                if len(primeros_bytes) < _TAMANO_PRIMEROS_BYTES:
                    primeros_bytes += trozo[: _TAMANO_PRIMEROS_BYTES - len(primeros_bytes)]
                tamano += len(trozo)
                if tamano > self._settings.max_bytes:
                    excedio = True
                    break
                trozos.append(trozo)

            return RespuestaCruda(
                status=respuesta.status_code,
                primeros_bytes=primeros_bytes,
                cuerpo=None if excedio else b"".join(trozos),
                content_type=respuesta.headers.get("content-type"),
                url_final=str(respuesta.url),
                tamano=tamano,
                excedio_tamano=excedio,
                motivo_red=None,
                intentos=0,
                redirecciones=tuple(str(paso.url) for paso in respuesta.history),
            )

    def _respuesta_vacia(self, url: str, motivo: MotivoRed, intentos: int) -> RespuestaCruda:
        return RespuestaCruda(
            status=None,
            primeros_bytes=b"",
            cuerpo=None,
            content_type=None,
            url_final=url,
            tamano=None,
            excedio_tamano=False,
            motivo_red=motivo,
            intentos=intentos,
        )
