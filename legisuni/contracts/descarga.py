from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class DownloadResult(BaseModel):
    entry_id: str
    exito: bool
    ruta_local: Path | None = None
    sha256: str | None = None
    bytes: int | None = None  # sombrea el builtin `bytes` a propósito
    content_type: str | None = None
    http_status: int | None = None
    capturado_en: datetime
    url_final: str | None = None
    motivo_fallo: Literal[
        "http_error", "no_es_pdf", "timeout", "robots_prohibido",
        "url_muerta", "demasiado_grande", "visor_de_terceros",
    ] | None = None
