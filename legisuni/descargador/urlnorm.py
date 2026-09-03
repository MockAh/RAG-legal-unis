"""Normaliza URLs crudas de sitios institucionales a URLs pedibles por httpx."""

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
