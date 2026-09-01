from datetime import date, datetime

from pydantic import BaseModel

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
    extraido_en: datetime
