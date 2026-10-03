"""Derivación del `doc_slug` estable de un documento (spec 03, "Estabilidad del identificador").

El slug nunca se deriva de la URL completa ni lleva fechas: la versión la distingue url_id.
"""

import re
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from legisuni.descargador.paths import sanear

_MESES = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
    "octubre|noviembre|diciembre"
)
_FECHAS = [
    re.compile(r"\b\d{1,2}\s+de\s+(?:%s)(?:\s+de\s+\d{4})?\b" % _MESES, re.I),
    re.compile(r"\b(?:%s)\s+(?:de\s+)?(?:\d{1,2}\s+)?(?:de\s+)?\d{4}\b" % _MESES, re.I),
    re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b"),
    re.compile(r"\b(?:19|20)\d{2}\b"),
]
_PREFIJO_NUMERICO = re.compile(r"^(\d+)-(?=[^\W\d_])")
_SOLO_NUMEROS = re.compile(r"^[\d.\-_]+$")


def _nombre_archivo(href: str) -> str:
    ruta = unquote(urlsplit(href).path)
    return PurePosixPath(ruta).stem


def _carpeta(href: str) -> str:
    return PurePosixPath(unquote(urlsplit(href).path)).parent.name


def _es_fecha(slug: str) -> bool:
    return bool(_SOLO_NUMEROS.match(slug))


def _sufijo_de_archivo(nombre: str) -> str | None:
    tokens = [t for t in nombre.split("-") if t]
    mayus = [t.upper() for t in tokens]

    for i, t in enumerate(mayus):
        if t == "ABROGADO" or (t == "VIGENTE" and mayus[i + 1 : i + 2] == ["HASTA"]):
            return tokens[i - 1] if i > 0 else None

    for i, t in enumerate(mayus):
        if t.startswith("ANEXO") and i > 0:
            resto = tokens[i][len("ANEXO") :] + "".join(tokens[i + 1 :])
            return f"{tokens[i - 1]}-anexo{resto}"

    if len(tokens) > 1:
        return tokens[-1]
    return None


def _quitar_fechas(titulo: str) -> str:
    for patron in _FECHAS:
        titulo = patron.sub(" ", titulo)
    return titulo


def doc_slug(href: str, titulo: str, inst_id: str) -> str:
    """Devuelve el slug estable; la primera estrategia que da resultado gana.

    1. Sufijo de archivo (UAM): token previo a VIGENTE-HASTA/ABROGADO, `<tok>-anexoN`
       para anexos, o el último token. El consolidado (archivo con el mismo nombre
       que su carpeta, sin sufijo) vale "consolidado".
    2. Prefijo numérico (UNAM): "29-ReglamentoGeneralExamenes" -> "n29". Se usa solo
       el número, con prefijo "n" para que nunca parezca año o fecha; el resto del
       nombre cambia con las reformas, el número no.
    3. Respaldo por título (UJAT, UACAM): normalizado y sin fechas.

    `inst_id` se acepta por contrato de la interfaz; el slug es único por institución.
    """
    nombre = _nombre_archivo(href)

    if nombre and nombre == _carpeta(href):
        return "consolidado"

    if nombre and not _PREFIJO_NUMERICO.match(nombre):
        sufijo = _sufijo_de_archivo(nombre)
        if sufijo:
            slug = sanear(sufijo)
            if not _es_fecha(slug):
                return slug

    prefijo = _PREFIJO_NUMERICO.match(nombre)
    if prefijo:
        return sanear(f"n{int(prefijo.group(1))}")

    return sanear(_quitar_fechas(unquote(titulo)))
