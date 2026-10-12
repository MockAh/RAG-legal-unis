"""Un solo sitio para la identidad (docs/03 criterio 15).

`url_id` lo calcula `descargador.urlnorm` y el `entry_id` lo compone
`juridico.identificadores.entry_id`; `lector/` no hace ninguna de las dos.

Inspecciona los .py de `legisuni/lector/` con `ast`, recorridos con `pathlib`
— no una lista escrita a mano: un módulo nuevo queda cubierto sin tocar este
test. `juridico/cosecha.py`, que sí compone, queda fuera del recorrido.
"""

import ast
from pathlib import Path

from legisuni.descargador.urlnorm import url_id

_RAIZ = Path(__file__).resolve().parent.parent / "legisuni"
_LECTOR = _RAIZ / "lector"

_CRITERIO = "docs/03 criterio 15 (un solo sitio para la identidad)"
_NOMBRES_DE_IDENTIDAD = {"entry_id", "url_id", "doc_id", "normalizar"}


def _modulos_python(paquete: Path) -> list[Path]:
    return sorted(paquete.rglob("*.py"))


def _paquete_de(archivo: Path) -> str:
    # Tanto para `x.py` como para `__init__.py`, el paquete es el directorio que lo contiene.
    return ".".join(archivo.relative_to(_RAIZ.parent).parent.parts)


def _rutas_importadas(nodo: ast.AST, archivo: Path) -> list[tuple[str, str | None]]:
    """(módulo_punteado, nombre_importado) por cada alias; resuelve imports relativos."""
    if isinstance(nodo, ast.Import):
        return [(alias.name, None) for alias in nodo.names]
    if isinstance(nodo, ast.ImportFrom):
        base = nodo.module or ""
        if nodo.level:
            paquete = _paquete_de(archivo).split(".")
            ancla = ".".join(paquete[: len(paquete) - (nodo.level - 1)])
            base = f"{ancla}.{base}" if base else ancla
        return [(base, alias.name) for alias in nodo.names]
    return []


def _arbol(archivo: Path) -> ast.Module:
    return ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))


def _imports(archivo: Path) -> list[tuple[str, str | None]]:
    resultado: list[tuple[str, str | None]] = []
    for nodo in ast.walk(_arbol(archivo)):
        resultado.extend(_rutas_importadas(nodo, archivo))
    return resultado


def _empieza_con(modulo: str, prefijo: str) -> bool:
    return modulo == prefijo or modulo.startswith(prefijo + ".")


def _importa(archivo: Path, modulo: str, nombre: str) -> bool:
    """¿`archivo` importa `modulo.nombre`, sea `from modulo import nombre` o `import modulo.nombre`?"""
    completo = f"{modulo}.{nombre}"
    return any(
        (m == modulo and n == nombre) or m == completo for m, n in _imports(archivo)
    )


def test_el_recorrido_encuentra_archivos_en_lector() -> None:
    # Si rglob devolviera cero por un cambio de estructura, los tests de
    # abajo pasarían en verde sin comprobar nada.
    assert len(_modulos_python(_LECTOR)) > 0


def test_lector_no_importa_juridico() -> None:
    violaciones = [
        f"{archivo.relative_to(_RAIZ.parent)}: importa {modulo!r}"
        for archivo in _modulos_python(_LECTOR)
        for modulo, _nombre in _imports(archivo)
        if _empieza_con(modulo, "legisuni.juridico")
    ]
    assert violaciones == [], (
        f"Regla: lector/ no importa legisuni.juridico — componer identificadores no es suyo; "
        f"el cableado vive en juridico/cosecha.py. {_CRITERIO}.\n" + "\n".join(violaciones)
    )


def test_lector_no_define_nombres_de_identidad() -> None:
    violaciones = []
    for archivo in _modulos_python(_LECTOR):
        ruta = archivo.relative_to(_RAIZ.parent)
        if archivo.stem in _NOMBRES_DE_IDENTIDAD:
            violaciones.append(f"{ruta}: el módulo se llama {archivo.stem!r}")
        arbol = _arbol(archivo)
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if nodo.name in _NOMBRES_DE_IDENTIDAD:
                    violaciones.append(f"{ruta}:{nodo.lineno}: define {nodo.name!r}")
        for nodo in arbol.body:
            objetivos = (
                nodo.targets
                if isinstance(nodo, ast.Assign)
                else [nodo.target]
                if isinstance(nodo, (ast.AnnAssign, ast.AugAssign))
                else []
            )
            for objetivo in objetivos:
                for nombre in ast.walk(objetivo):
                    if isinstance(nombre, ast.Name) and nombre.id in _NOMBRES_DE_IDENTIDAD:
                        violaciones.append(f"{ruta}:{nodo.lineno}: asigna el nombre de módulo {nombre.id!r}")
    assert violaciones == [], (
        f"Regla: lector/ no define entry_id, url_id, doc_id ni normalizar — los importa de "
        f"descargador.urlnorm y juridico.identificadores. {_CRITERIO}.\n" + "\n".join(violaciones)
    )


def test_lector_no_importa_hashlib() -> None:
    violaciones = [
        f"{archivo.relative_to(_RAIZ.parent)}: importa {modulo!r}"
        for archivo in _modulos_python(_LECTOR)
        for modulo, _nombre in _imports(archivo)
        if _empieza_con(modulo, "hashlib")
    ]
    assert violaciones == [], (
        f"Regla: lector/ no importa hashlib — es la firma de calcular un url_id por su cuenta; "
        f"url_id vive en descargador.urlnorm. {_CRITERIO}.\n" + "\n".join(violaciones)
    )


def test_lector_identidad_py_no_existe() -> None:
    assert not (_LECTOR / "identidad.py").exists(), (
        f"Regla: lector/identidad.py no existe (docs/03 §Diseño) — sería un tercer sitio "
        f"componiendo entry_id. {_CRITERIO}."
    )


def test_el_modulo_que_deduplica_importa_normalizar_de_urlnorm() -> None:
    deduplicadores = [
        archivo
        for archivo in _modulos_python(_LECTOR)
        if any(
            isinstance(nodo, ast.FunctionDef) and nodo.name == "deduplicar" for nodo in ast.walk(_arbol(archivo))
        )
    ]
    assert deduplicadores, f"Ningún módulo de lector/ define deduplicar: el cableado se movió. {_CRITERIO}."
    sin_import = [
        str(archivo.relative_to(_RAIZ.parent))
        for archivo in deduplicadores
        if not _importa(archivo, "legisuni.descargador.urlnorm", "normalizar")
    ]
    assert sin_import == [], (
        f"Regla: quien deduplica obtiene la normalización de descargador.urlnorm, por import. "
        f"{_CRITERIO}.\n" + "\n".join(sin_import)
    )


def test_juridico_cosecha_importa_identificadores() -> None:
    cosecha = _RAIZ / "juridico" / "cosecha.py"
    assert _importa(cosecha, "legisuni.juridico", "identificadores"), (
        f"Regla: juridico/cosecha.py es donde se compone el entry_id e importa "
        f"juridico.identificadores; si ya no lo hace, el cableado se movió. {_CRITERIO}."
    )


# Los 4 href de la UJAT que terminan en salto de línea (fixtures del 2026-09-06/08).
_HREFS_CON_SALTO = [
    (
        "https://archivos.ujat.mx/2024/abogado-general/17-5/"
        "5-WEB-CODIGO-INSTITUCIONAL-DE-ETICA-PARA-LA-VINCULACION-20032024.pdf\n",
        "https://www.ujat.mx/abogado/15763",
    ),
    (
        "https://archivos.ujat.mx/2024/abogado-general/17-5/"
        "8-WEB-LINEAMIENTO-EXAMEN-PROFESIONAL-VIRTUAL-DE-LICENCIATURA-Y-TSU-20032024.pdf\n",
        "https://www.ujat.mx/abogado/15763",
    ),
    (
        "https://archivos.ujat.mx/2025/abogado-gral/ACUERDO_CEDEM.pdf\n",
        "https://www.ujat.mx/abogado/17669",
    ),
    (
        "https://archivos.ujat.mx/2024/abogado-general/AG-21-08-24/"
        "WEB-ACUERDO-POR-EL-QUE-SE-ESTABLECEN-LOS-LIN-GEN-PARA-LA-CREACION-Y-FUNCIONAMIENTO-"
        "DEL-CENTRO-DE-MECANISMOS-ALTERNATIVOS-DE-SOLUC.pdf\n",
        "https://www.ujat.mx/abogado/17669",
    ),
]


def test_los_4_href_con_salto_de_linea_dan_el_mismo_url_id_con_y_sin_salto() -> None:
    assert len(_HREFS_CON_SALTO) == 4
    for href, indice in _HREFS_CON_SALTO:
        assert href.endswith("\n")
        assert url_id(href, indice) == url_id(href.rstrip("\n"), indice), repr(href)
