"""Cortesía de red: respeta robots.txt, cacheado por host y con fail-open."""

import logging
from collections.abc import Callable
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


class RobotsCache:
    def __init__(self, user_agent: str, fetcher: Callable[[str], tuple[int, str]]) -> None:
        self._user_agent = user_agent
        self._fetcher = fetcher
        self._cache: dict[str, RobotFileParser | None] = {}

    def permitido(self, url: str) -> bool:
        partes = urlsplit(url)
        host = (partes.hostname or "").lower()
        if host not in self._cache:
            self._cache[host] = self._cargar(partes.scheme, host)
        parser = self._cache[host]
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)

    def _cargar(self, esquema: str, host: str) -> RobotFileParser | None:
        robots_url = f"{esquema}://{host}/robots.txt"
        try:
            status, texto = self._fetcher(robots_url)
        except Exception:
            logger.warning("fetcher falló al pedir %s; fail-open (permitido)", robots_url)
            return None
        if status == 200:
            parser = RobotFileParser()
            parser.parse(texto.splitlines())
            return parser
        if status in (404, 410):
            return None
        logger.warning(
            "status inesperado %s al pedir %s; fail-open (permitido)", status, robots_url
        )
        return None
