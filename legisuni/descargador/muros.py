"""Reconocimiento conservador de muro_de_pago (docs/05 v3, sección "Muros", criterio 15).

El Descargador nunca intenta pasar un muro (D8): esta función solo diagnostica, nunca
actúa distinto ante la duda. Se declara `muro_de_pago` SOLO con una señal sin
ambigüedad: `401`/`402`, o una redirección a una ruta de login federado conocida
(`datos/patrones.toml`). Un `403` nunca es muro: también lo producen bloqueos
anti-bots o servidores mal configurados.

**Ante la duda, este módulo no decide nada** (`docs/01` línea 155: "en la duda, el
motivo es `vestibulo_sin_pdf`", no `http_error` ni `muro_de_pago` mal diagnosticado).
Hoy (M27) no existe cruce de vestíbulo todavía, así que un HTML que no matchea ningún
patrón sigue el camino de siempre: `guard.evaluar` lo marca `no_es_pdf`. Desde M28,
con vestíbulo, ese mismo caso dudoso pasará primero por el cruce y solo si falla
llegará a `vestibulo_sin_pdf`. M27 no adelanta ese cambio.
"""

import re
import tomllib
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

_PATRONES_PATH = Path(__file__).parent.parent / "datos" / "patrones.toml"

_STATUS_MURO = (401, 402)


@lru_cache(maxsize=1)
def _cargar_patrones() -> tuple[dict, ...]:
    datos = tomllib.loads(_PATRONES_PATH.read_text(encoding="utf-8"))
    return tuple(
        {**patron, "_regex": re.compile(patron["ruta_regex"])}
        for patron in datos.get("patrones", ())
    )


def _redirige_a_patron_de_autenticacion(url_final: str) -> bool:
    partes = urlsplit(url_final)
    host = (partes.hostname or "").lower()
    for patron in _cargar_patrones():
        host_esperado = patron.get("host")
        if host_esperado is not None and host != host_esperado.lower():
            continue
        if patron["_regex"].search(partes.path):
            return True
    return False


def es_muro_de_pago(status: int | None, url_final: str) -> bool:
    if status in _STATUS_MURO:
        return True
    return _redirige_a_patron_de_autenticacion(url_final)
