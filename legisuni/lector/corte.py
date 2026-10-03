"""Piso determinista de la fecha de corte del índice (C13, criterio 21 de `03`).

No llama a ningún LLM ni importa nada del agente: la detección funciona con el agente
desconectado.

Decisión: si varios patrones coinciden, gana la PRIMERA coincidencia en el texto y las
demás se ignoran. Se revisará con evidencia si hace falta.

La interpretación de la fecha es la más generosa con la universidad (docs/01 N3): un mes
vale su último día y un año vale el 31 de diciembre. Si aun así resulta caducado, lo está
sin discusión.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from dataclasses import dataclass
from datetime import date

_PATRONES = (
    "fecha de corte",
    "ultima actualizacion",
    "actualizado al",
    "periodo que se informa",
    "vigente al",
)
_REGEX_PATRON = re.compile("|".join(re.escape(p) for p in _PATRONES))

_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}  # fmt: skip
_MES = "(" + "|".join(_MESES) + ")"
_SEP = r"[\s:.\-–—]*"
_DE = r"\s+(?:de|del)\s+"
_FECHA_COMPLETA = re.compile(rf"{_SEP}(\d{{1,2}}){_DE}{_MES}(?:{_DE}|\s+)(\d{{4}})\b")
_FECHA_MES = re.compile(rf"{_SEP}{_MES}(?:{_DE}|\s+)(\d{{4}})\b")
_FECHA_ANIO = re.compile(rf"{_SEP}(\d{{4}})\b")

# Sin fecha reconocible, el literal llega hasta este número de caracteres tras el patrón.
_VENTANA_LITERAL = 60


@dataclass(frozen=True)
class Corte:
    texto: str
    fecha: date | None
    patron: str


def _colapsar(texto: str) -> str:
    # str.split() sin argumentos trata \u00a0 como blanco
    return " ".join(texto.split())


def _plegar(texto: str) -> str:
    """Minúsculas y sin acentos, conservando la longitud (una letra por letra)."""
    return "".join(unicodedata.normalize("NFD", c)[0] for c in texto.lower())


def _ultimo_dia(anio: int, mes: int) -> date:
    return date(anio, mes, calendar.monthrange(anio, mes)[1])


def _anio_valido(anio: int) -> bool:
    return 1900 <= anio <= 2100


def _interpretar(resto: str) -> tuple[date, int] | None:
    """Fecha al inicio de `resto` (ya plegado) y dónde termina el literal."""
    if m := _FECHA_COMPLETA.match(resto):
        anio = int(m.group(3))
        if _anio_valido(anio):
            try:
                return date(anio, _MESES[m.group(2)], int(m.group(1))), m.end()
            except ValueError:
                return None
        return None
    if m := _FECHA_MES.match(resto):
        anio = int(m.group(2))
        if _anio_valido(anio):
            return _ultimo_dia(anio, _MESES[m.group(1)]), m.end()
        return None
    if m := _FECHA_ANIO.match(resto):
        anio = int(m.group(1))
        if _anio_valido(anio):
            return date(anio, 12, 31), m.end()
    return None


def buscar_corte(texto: str) -> Corte | None:
    colapsado = _colapsar(texto)
    plegado = _plegar(colapsado)
    m = _REGEX_PATRON.search(plegado)
    if m is None:
        return None
    resto = plegado[m.end() :]
    interpretado = _interpretar(resto)
    if interpretado is not None:
        fecha, fin = interpretado
    else:
        fecha, fin = None, _VENTANA_LITERAL
    literal = colapsado[m.start() : m.end() + fin].strip()
    return Corte(texto=literal, fecha=fecha, patron=m.group(0))


def _restar_meses(hoy: date, meses: int) -> date:
    indice = hoy.year * 12 + (hoy.month - 1) - meses
    anio, mes = divmod(indice, 12)
    mes += 1
    dia = min(hoy.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def esta_caducado(fecha: date, hoy: date, umbral_meses: int) -> bool:
    """True si `fecha` es estrictamente anterior a `hoy` menos `umbral_meses`."""
    return fecha < _restar_meses(hoy, umbral_meses)
