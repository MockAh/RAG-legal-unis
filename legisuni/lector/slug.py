"""Derivación del `doc_slug` estable de un documento (spec 03, "Estabilidad del identificador").

El slug nunca se deriva de la URL completa ni lleva fechas: la versión la distingue url_id.
"""

import re
from collections.abc import Callable
from datetime import date
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
_TOPE = 100  # legibilidad, no identidad: 63 era el mínimo medido sin choques en la UJAT, sin margen (M47b)


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


def _consolidado(href: str, titulo: str) -> str | None:
    nombre = _nombre_archivo(href)
    return "consolidado" if nombre and nombre == _carpeta(href) else None


def _por_sufijo(href: str, titulo: str) -> str | None:
    nombre = _nombre_archivo(href)
    if not nombre or _PREFIJO_NUMERICO.match(nombre):
        return None
    sufijo = _sufijo_de_archivo(nombre)
    return sanear(sufijo) if sufijo else None


def _es_fecha_compacta(digitos: str) -> bool:
    """DDMMAA, AAMMDD (6 dígitos) o DDMMAAAA, AAAAMMDD (8) que sean fecha válida."""
    if len(digitos) == 6:
        formas = [(digitos[4:], digitos[2:4], digitos[:2]), (digitos[:2], digitos[2:4], digitos[4:])]
        formas = [(f"20{a}", m, d) for a, m, d in formas]
    elif len(digitos) == 8:
        formas = [(digitos[4:], digitos[2:4], digitos[:2]), (digitos[:4], digitos[4:6], digitos[6:])]
    else:
        return False
    for anio, mes, dia in formas:
        try:
            date(int(anio), int(mes), int(dia))
            return True
        except ValueError:
            continue
    return False


def _por_prefijo(href: str, titulo: str) -> str | None:
    prefijo = _PREFIJO_NUMERICO.match(_nombre_archivo(href))
    # la fecha se mira antes de anteponer la "n", que la disfrazaría
    if not prefijo or _es_fecha_compacta(prefijo.group(1)):
        return None
    return sanear(f"n{int(prefijo.group(1))}")


def _por_titulo(href: str, titulo: str) -> str | None:
    titulo = unquote(titulo)
    if titulo.strip():
        return sanear(_quitar_fechas(titulo))
    # C9: ancla sin texto; el nombre de archivo completo antes de rendirse
    nombre = _nombre_archivo(href)
    return sanear(nombre) if nombre else None


_Estrategia = Callable[[str, str], str | None]

_DESPACHO: dict[str, list[_Estrategia]] = {
    "uam": [_consolidado, _por_sufijo],
    "unam": [_por_prefijo],
    "ujat": [],
    "uacam": [],
}


def _recortar(slug: str) -> str:
    if len(slug) <= _TOPE:
        return slug
    frontera = slug.rfind("-", 0, _TOPE + 1)
    recorte = slug[:frontera] if frontera > 0 else slug[:_TOPE]
    return recorte.rstrip("-")


def doc_slug(href: str, titulo: str, inst_id: str) -> str:
    """Devuelve el slug estable con el mecanismo del sitio; si no hay, por título (01 N2).

    Despacho por `inst_id` (`_DESPACHO`); la primera estrategia que da un slug
    sin forma de fecha gana, y el título cierra siempre la lista:

    - uam: "consolidado" (archivo con el mismo nombre que su carpeta) y sufijo de
      archivo: token previo a VIGENTE-HASTA/ABROGADO, `<tok>-anexoN` para anexos,
      o el último token.
    - unam: prefijo numérico. "29-ReglamentoGeneralExamenes" -> "n29". Se usa solo
      el número, con prefijo "n" para que nunca parezca año o fecha; el resto del
      nombre cambia con las reformas, el número no. Un prefijo de 6 u 8 dígitos
      que sea fecha válida (DDMMAA, AAMMDD, DDMMAAAA, AAAAMMDD) se descarta y el
      documento va por título. Es endurecimiento preventivo: no mueve nada de la
      UNAM medida; los dos casos reales (`210817-`, `060417-`) son de la UJAT,
      que el despacho ya manda a título.
    - ujat, uacam y cualquier otra: título normalizado y sin fechas; si el ancla
      viene vacía (C9), el nombre de archivo completo saneado.

    Ninguna institución hereda el mecanismo de otra: la forma del nombre de
    archivo no decide (M47a). **Cada institución nueva necesita medición para
    ganar su mecanismo**; mientras no la tenga, va por título.

    El resultado se recorta a `_TOPE` caracteres en frontera de guion y sin guion
    final. El tope es de legibilidad, no de identidad.
    """
    for estrategia in [*_DESPACHO.get(inst_id, []), _por_titulo]:
        slug = estrategia(href, titulo)
        if slug and not _es_fecha(slug):
            return _recortar(slug)
    return "sin-nombre"
