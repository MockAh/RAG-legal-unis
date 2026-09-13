from datetime import datetime

from pydantic import BaseModel

from legisuni.contracts.vocabularios import Modo, TipoPuerta


class Puerta(BaseModel):
    url: str                  # cruda, tal como apareció (D3). Única excepción: resolutor DOI
    tipo: TipoPuerta
    url_base: str | None      # para resolver relativas. Jurídico: url_indice
    evidencia: str            # dónde apareció: url_indice | f"lista:{lote_id}#{posicion}"
    construida: bool = False  # v2.0 · True solo para la puerta doi.org armada desde un DOI literal


class Encargo(BaseModel):
    encargo_id: str           # jurídico: entry_id · académico: articulo_id
    modo: Modo
    solicitante: str          # quién lo pide. Jurídico: inst_id · académico: lote_id
    puertas: list[Puerta]     # en orden de preferencia; al menos una
    cajon: str                # relativo a data/. Jurídico: f"norm/{inst_id}" · académico: "papers"
    etiqueta: str             # nombre de archivo sin extensión; la extensión la deciden los bytes
    cruzar_vestibulos: bool   # jurídico: False · académico: True (ver Parámetros)
    grupo_alias: str          # v2.1 · ámbito del alias por hash. Jurídico: f"{inst_id}:{doc_slug}" · académico: articulo_id
    creado_en: datetime
