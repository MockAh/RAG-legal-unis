from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from legisuni.contracts.vocabularios import Modo, MotivoFallo


class IntentoPuerta(BaseModel):    # v2.0
    orden: int                     # posición de la puerta en Encargo.puertas (desde 0)
    url: str                       # la cruda de la Puerta
    url_pedida: str | None         # tras normalizar
    url_final: str | None          # tras redirecciones y, si hubo, tras cruzar el vestíbulo
    enlace_vestibulo: str | None   # enlace seguido dentro del vestíbulo (literal en la página, D3)
    http_status: int | None
    exito: bool
    motivo_fallo: MotivoFallo | None


class DownloadResult(BaseModel):
    encargo_id: str
    modo: Modo
    exito: bool
    ruta_local: Path | None = None
    sha256: str | None = None
    bytes: int | None = None  # sombrea el builtin `bytes` a propósito
    content_type: str | None = None
    http_status: int | None = None
    capturado_en: datetime
    url_final: str | None = None
    motivo_fallo: MotivoFallo | None = None
    puerta_usada: int | None = None
    intentos: list[IntentoPuerta]
    duplicado_de: str | None = None
