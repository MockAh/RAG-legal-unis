"""Frontera entre modos (docs/05 criterio 12).

Inspecciona los imports de los .py con `ast`, recorridos con `pathlib` — no
una lista escrita a mano, que se queda vieja en cuanto se añade un módulo.
"""

import ast
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent / "legisuni"

_NOMBRES_PROHIBIDOS_EN_DESCARGADOR = {"CatalogEntry", "ArticleRef"}
_PREFIJOS_PROHIBIDOS_EN_DESCARGADOR = ("legisuni.juridico", "legisuni.academico")
_PREFIJOS_PROHIBIDOS_EN_CONTRACTS = (
    "legisuni.descargador",
    "legisuni.juridico",
    "legisuni.academico",
)


def _modulos_python(paquete: Path) -> list[Path]:
    return sorted(paquete.rglob("*.py"))


def _rutas_importadas(nodo: ast.AST) -> list[tuple[str, str | None]]:
    """(módulo_punteado, nombre_importado) por cada alias del nodo."""
    if isinstance(nodo, ast.Import):
        return [(alias.name, None) for alias in nodo.names]
    if isinstance(nodo, ast.ImportFrom):
        base = nodo.module or ""
        return [(base, alias.name) for alias in nodo.names]
    return []


def _empieza_con(modulo: str, prefijos: tuple[str, ...]) -> bool:
    return any(modulo == p or modulo.startswith(p + ".") for p in prefijos)


def _imports_del_paquete(paquete: Path) -> list[tuple[Path, str, str | None]]:
    """(archivo, módulo_punteado, nombre_importado) de cada import del paquete."""
    resultado: list[tuple[Path, str, str | None]] = []
    for archivo in _modulos_python(paquete):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                for modulo, nombre in _rutas_importadas(nodo):
                    resultado.append((archivo, modulo, nombre))
    return resultado


def test_el_recorrido_encuentra_archivos_en_descargador_y_contracts() -> None:
    # Si rglob devolviera cero por un cambio de estructura, los otros dos
    # tests pasarían en verde sin comprobar nada.
    assert len(_modulos_python(_RAIZ / "descargador")) > 0
    assert len(_modulos_python(_RAIZ / "contracts")) > 0


def test_descargador_no_importa_fichas_de_ningun_modo() -> None:
    violaciones = []
    for archivo, modulo, nombre in _imports_del_paquete(_RAIZ / "descargador"):
        if _empieza_con(modulo, _PREFIJOS_PROHIBIDOS_EN_DESCARGADOR):
            violaciones.append(f"{archivo}: importa el módulo {modulo!r}")
        if nombre in _NOMBRES_PROHIBIDOS_EN_DESCARGADOR:
            violaciones.append(f"{archivo}: importa el nombre {nombre!r} (de {modulo!r})")
    assert violaciones == [], "\n".join(violaciones)


def test_contracts_no_importa_de_ningun_modo() -> None:
    violaciones = []
    for archivo, modulo, _nombre in _imports_del_paquete(_RAIZ / "contracts"):
        if _empieza_con(modulo, _PREFIJOS_PROHIBIDOS_EN_CONTRACTS):
            violaciones.append(f"{archivo}: importa el módulo {modulo!r}")
    assert violaciones == [], "\n".join(violaciones)
