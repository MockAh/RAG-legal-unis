"""Normaliza URLs crudas de sitios institucionales a URLs pedibles por httpx."""

import hashlib
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

# sub-delims + ":@" (RFC 3986) más "%" para no re-codificar secuencias ya escapadas.
_SAFE = "/:@!$&'()*+,;=%"


def normalizar(url_cruda: str, url_indice: str) -> str:
    """Convierte `url_cruda` (tal como la publica el sitio) en una URL absoluta y pedible."""
    cruda = url_cruda.strip()
    try:
        absoluta = urljoin(url_indice, cruda)
        partes = urlsplit(absoluta)
        ruta = quote(partes.path, safe=_SAFE)
        consulta = quote(partes.query, safe=_SAFE)
        return urlunsplit((partes.scheme, partes.netloc, ruta, consulta, partes.fragment))
    except Exception:
        return cruda


def url_id(url: str, base: str) -> str:
    """Primeros 12 hex del SHA-256 de la URL normalizada (01 N2, v2.0).

    Una sola normalización para dos usos (05 v3): quien necesite distinguir
    direcciones (el Lector de Índice, para `entry_id`) llama a esta función
    en vez de normalizar por su cuenta. Dos normalizaciones distintas darían
    dos `url_id` para la misma dirección y romperían C20 en silencio.
    """
    normalizada = normalizar(url, base)
    return hashlib.sha256(normalizada.encode("utf-8")).hexdigest()[:12]
