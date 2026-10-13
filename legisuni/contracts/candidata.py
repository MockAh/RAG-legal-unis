from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from legisuni.contracts.vocabularios import OrigenFuente


class SourceCandidate(BaseModel):
    inst_id: str
    url: str                  # DEBE haber aparecido en una búsqueda o como enlace (D3)
    origen: OrigenFuente
    titulo_pagina: str        # tal como lo devolvió la fuente
    dominio: str              # extraído de url; se compara contra dominio_raiz (D9)
    es_dominio_institucional: bool
    confianza: Literal["alta", "media", "baja"]
    razon: str                # por qué el agente cree que esta es la página de legislación
    descubierta_en: datetime
    evidencia_url: str        # la búsqueda o página desde la que se llegó a esta URL (D3)
