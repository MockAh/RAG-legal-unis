"""El agente maniquí (M49): devuelve, crudo, un JSON de `tests/fixtures/agente/`.

Cumple el `Agente` de `lector/models.py`. Cada caso es un archivo, no una rama de código.
"""

from collections.abc import Sequence
from pathlib import Path

from legisuni.lector.reduce import Enlace

AGENTE = Path(__file__).resolve().parent / "fixtures" / "agente"


class AgenteManiqui:
    """Devuelve, crudo, el JSON de `tests/fixtures/agente/<caso>.json`. Cada caso es un archivo."""

    def __init__(self, caso: str) -> None:
        self._ruta = AGENTE / f"{caso}.json"

    def __call__(self, enlaces: Sequence[Enlace]) -> str:
        return self._ruta.read_text(encoding="utf-8")
