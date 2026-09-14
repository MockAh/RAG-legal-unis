"""entry_id de tres segmentos (docs/01 N2, «Nota sobre entry_id», v2.0).

Resuelve C20 de docs/08 (E11.6): dos fotos del mismo instrumento con URLs
distintas —los dos históricos del Reglamento de Estudios Superiores de la
UAM— ya no colisionan. `doc_slug` no se deriva de la URL (docs/01, «Nota
sobre doc_slug»): llega de quien invoca; el mecanismo por sitio no vive aquí.
"""

from legisuni.descargador.urlnorm import url_id as _url_id


def entry_id(inst_id: str, doc_slug: str, url_documento: str, url_indice: str) -> str:
    return f"{inst_id}:{doc_slug}:{_url_id(url_documento, url_indice)}"
