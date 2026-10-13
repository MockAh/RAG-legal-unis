from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, model_validator

from legisuni.contracts.candidata import SourceCandidate
from legisuni.contracts.vocabularios import EstadoVigencia, OrigenFuente, TipoNorma


class CatalogEntry(BaseModel):
    entry_id: str
    inst_id: str
    titulo: str
    tipo_norma: TipoNorma
    url_documento: str
    formato_declarado: str | None = None
    estado: EstadoVigencia = "desconocido"
    vigente_hasta: date | None = None
    fecha_publicacion: date | None = None
    fecha_ultima_reforma: date | None = None
    categoria_indice: str | None = None
    origen: OrigenFuente
    url_indice: str
    titulo_derivado: bool = False
    extraido_en: datetime


class Catalog(BaseModel):
    inst_id: str
    entries: list[CatalogEntry]
    fuentes_usadas: list[SourceCandidate]
    generado_en: datetime
    lector_agotado: bool      # True si el Lector devolvió vacío y hubo que ir al respaldo
    notas: str | None         # "índice servido por rejilla JS; sin filas en el HTML"
    # --- v2.3 · fecha de corte del índice (D12, C13) ---
    fecha_corte_declarada: date | None = None   # la que declara la página
    fecha_corte_texto: str | None = None        # declaración literal: «Fecha de corte: Diciembre del 2016»
    catalogo_caducado: bool = False             # fecha_corte_declarada más vieja que el umbral
    # --- v2.6 · contabilidad de la lectura (C13: no mentir sin errores) ---
    enlaces_vistos: int | None = None          # enlaces únicos (URL normalizada) entregados al agente, tras classify.py; None = no hubo lectura
    enlaces_descartados: list[str] = []        # hrefs que el agente declaró explícitamente no normativos
    enlaces_sin_cuenta: list[str] = []         # vistos − (url_documento de entries) − descartados; lo calcula código, nunca el agente
    lectura_incompleta: bool = False           # enlaces_sin_cuenta no vacío (derivado, como catalogo_caducado)
    fallo_lector: Literal["salida_invalida"] | None = None   # el agente respondió, pero su JSON no validó

    @model_validator(mode="after")
    def _agotado_y_fallo_excluyentes(self) -> "Catalog":
        # 01 N3 y 03 §Contabilidad, regla dura 1
        if self.lector_agotado and self.fallo_lector is not None:
            raise ValueError("lector_agotado y fallo_lector son excluyentes")
        return self
