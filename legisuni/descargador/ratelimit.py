"""Cortesía de red: limita la frecuencia de peticiones por host (no global)."""

import logging
import time
from collections.abc import Callable
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(
        self,
        min_intervalo_s: float = 1.0,
        reloj: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._min_intervalo_s = min_intervalo_s
        self._reloj = reloj
        self._dormir = dormir
        self._ultima_peticion: dict[str, float] = {}

    def esperar(self, url: str) -> float:
        host = (urlsplit(url).hostname or "").lower()
        ahora = self._reloj()
        ultima = self._ultima_peticion.get(host)
        espera = 0.0
        if ultima is not None:
            faltante = self._min_intervalo_s - (ahora - ultima)
            if faltante > 0:
                espera = faltante
        if espera > 0:
            logger.info(
                "cortesia: %s espera %.3fs (ultima hace %.3fs)",
                host,
                espera,
                ahora - ultima,
            )
            self._dormir(espera)
        else:
            logger.debug(
                "cortesia: %s sin espera (primera peticion o intervalo cumplido)",
                host,
            )
        self._ultima_peticion[host] = ahora + espera
        return espera
