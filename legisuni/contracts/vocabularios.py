from typing import Literal

Modo = Literal["juridico", "academico"]   # v2.0

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

TipoPuerta = Literal[            # v2.0
    "enlace_indice",   # jurídico: el enlace publicado en el índice institucional
    "copia_libre",     # académico: PDF de autor, PMC, repositorio institucional
    "oficial",         # académico: página de la editorial
    "resolutor_doi",   # académico: enlace doi.org, literal o construido desde un DOI literal (excepción a D3)
]

Relacion = Literal[              # v2.0 · solo modo académico
    "extra_recomendado",  # otro artículo que la lista sugiere junto a uno pedido
    "correccion",         # corrección / fe de erratas de un artículo pedido
]

MotivoFallo = Literal[           # extraído de N5 en v2.0; valores v1.x intactos
    "http_error", "no_es_pdf", "timeout", "robots_prohibido",
    "url_muerta", "demasiado_grande", "visor_de_terceros",
    # --- v2.0 ---
    "vestibulo_sin_pdf",   # la puerta dio HTML y no se halló en él un enlace a archivo aceptado
    "muro_de_pago",        # la puerta exige pago, suscripción o sesión
    "puertas_agotadas",    # el Encargo traía más de una puerta y todas fallaron
]
