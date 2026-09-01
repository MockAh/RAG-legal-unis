from typing import Literal

TipoNorma = Literal[
    "ley_organica", "estatuto", "reglamento", "lineamientos",
    "politicas", "criterios", "codigo", "protocolo", "acuerdo", "manual",
    "contrato_colectivo", "tabulador", "anexo", "otro",
]

JERARQUIA: dict[TipoNorma, int] = {
    "ley_organica": 1, "estatuto": 2, "reglamento": 3, "contrato_colectivo": 3,
    "lineamientos": 4, "politicas": 4, "criterios": 4, "codigo": 4,
    "protocolo": 4, "acuerdo": 4, "manual": 4, "tabulador": 4,
    "anexo": 5, "otro": 5,
}

EstadoVigencia = Literal["vigente", "historico", "abrogado", "desconocido"]
OrigenFuente = Literal["sitio_institucional", "pnt_70i", "periodico_oficial", "manual"]
Regimen = Literal["federal", "estatal", "autonoma_estatal", "tecnologico", "otro"]
