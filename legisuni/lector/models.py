"""Forma de entrada y salida del agente del Lector (docs/03 §Salida estructurada).

No es un contrato de `01`: es lo que el agente produce, y solo eso. El agente declara;
el código resta (03 §Contabilidad). Por eso aquí no hay `entry_id`, `inst_id`,
`origen`, `url_indice`, `extraido_en`, `enlaces_sin_cuenta`, `lectura_incompleta`
ni `catalogo_caducado`: los pone el ensamblado (`juridico/ensamblado.py`). Un campo
de más en la respuesta es salida inválida, no un dato que se ignora.

`agotado` lo DECLARA el agente; el código no lo deriva de `enlaces_vistos == 0`.
Si lo derivara, las tres páginas de la UJAT con cero candidatos y el 70-I saldrían
como agotados sin ser rejillas JS, y D1 saltaría de eslabón por una página que se
leyó perfectamente (03 §Detección de esqueleto vacío).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from legisuni.contracts.vocabularios import EstadoVigencia, TipoNorma
from legisuni.lector.reduce import Enlace


class Agente(Protocol):
    """Recibe la tabla de enlaces ya reducida y devuelve la respuesta CRUDA, sin parsear.

    Cruda a propósito: quien llama la guarda antes de parsear (criterio 20).
    """

    def __call__(self, enlaces: Sequence[Enlace]) -> str: ...


class EntradaAgente(BaseModel):
    """N2 menos lo que pone el código; `url_documento` es `href`."""

    model_config = ConfigDict(extra="forbid")

    href: str                 # tal como el agente lo recibió en la tabla de enlaces
    titulo: str
    tipo_norma: TipoNorma
    formato_declarado: str | None = None
    estado: EstadoVigencia = "desconocido"
    vigente_hasta: date | None = None
    fecha_publicacion: date | None = None
    fecha_ultima_reforma: date | None = None
    categoria_indice: str | None = None
    titulo_derivado: bool = False


class SalidaAgente(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entradas: list[EntradaAgente]
    descartados: list[str]    # hrefs declarados no normativos, tal como los recibió
    agotado: bool             # lo declara el agente: la página no trae nada (rejilla JS)
    notas: str | None = None  # diagnóstico: "índice servido por rejilla JS; sin filas en el HTML"

    @model_validator(mode="after")
    def _agotado_sin_entradas(self) -> SalidaAgente:
        if self.agotado and self.entradas:
            raise ValueError("agotado=True con entradas es incoherente")
        return self


class SalidaInvalida(ValueError):
    """La respuesta no validó. Lleva la cadena cruda para quien quiera conservarla."""

    def __init__(self, cruda: str, motivo: str) -> None:
        super().__init__(motivo)
        self.cruda = cruda


def parsear_salida(cruda: str) -> SalidaAgente:
    """JSON estricto: ni preámbulo, ni cercas de markdown, ni comas finales, ni `eval`."""
    try:
        return SalidaAgente.model_validate_json(cruda)
    except ValidationError as error:
        raise SalidaInvalida(cruda, str(error)) from error
