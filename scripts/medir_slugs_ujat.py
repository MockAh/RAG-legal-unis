"""M47a: medición del despacho de `doc_slug` sobre los 109 enlaces de la UJAT.

Solo lee fixtures del disco: sin red y sin base. No modifica `slug.py`; la rama
que produjo cada slug se reconstruye desde fuera recorriendo `_DESPACHO` (M47b)
y se comprueba contra `doc_slug`.

Uso:
    .venv/bin/python scripts/medir_slugs_ujat.py | tee ~/respaldo-acervo/m47a-slugs-ujat.tsv

La tabla TSV sale por stdout; el resumen de conteos, por stderr.
"""

import sys
from collections import defaultdict
from pathlib import Path

from legisuni.descargador.urlnorm import normalizar
from legisuni.lector import classify, cuenta, reduce
from legisuni.lector.slug import (
    _DESPACHO,
    _es_fecha,
    _nombre_archivo,
    _por_titulo,
    _recortar,
    doc_slug,
)

_RAIZ = Path(__file__).resolve().parent.parent
_FIXTURES = _RAIZ / "fixtures"
_INST_ID = "ujat"

_PAGINAS = [
    ("ujat-15763.html", "https://www.ujat.mx/abogado/15763"),
    ("ujat-16443.html", "https://www.ujat.mx/abogado/16443"),
    ("ujat-17669.html", "https://www.ujat.mx/abogado/17669"),
    ("ujat-33794.html", "https://www.ujat.mx/abogado/33794"),
    ("ujat-4232.html", "https://www.ujat.mx/abogado/4232"),
]

_COLUMNAS = ["href", "nombre_archivo", "titulo", "doc_slug", "rama", "slug_por_titulo", "es_fecha"]


def _enlaces_unicos() -> list[tuple[reduce.Enlace, str]]:
    vistos: set[str] = set()
    unicos: list[tuple[reduce.Enlace, str]] = []
    for nombre, url_indice in _PAGINAS:
        pagina = reduce.reducir((_FIXTURES / nombre).read_bytes())
        for enlace in cuenta.deduplicar(classify.candidatos(pagina.enlaces), url_indice):
            # entre páginas: gana la primera aparición
            clave = normalizar(enlace.href, url_indice)
            if clave in vistos:
                continue
            vistos.add(clave)
            unicos.append((enlace, url_indice))
    return unicos


def _slug_por_titulo(href: str, titulo: str) -> str:
    return _recortar(_por_titulo(href, titulo) or "sin-nombre")


def _rama(href: str, titulo: str) -> tuple[str, str]:
    """Recorre el despacho de `doc_slug` desde fuera y dice qué estrategia ganó."""
    for estrategia in [*_DESPACHO.get(_INST_ID, []), _por_titulo]:
        slug = estrategia(href, titulo)
        if slug and not _es_fecha(slug):
            return estrategia.__name__.lstrip("_"), _recortar(slug)
    return "ninguna", "sin-nombre"


def _celda(valor: str) -> str:
    return valor.replace("\\", "\\\\").replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def main() -> int:
    enlaces = _enlaces_unicos()
    if len(enlaces) != 109:
        print(f"ALTO: salieron {len(enlaces)} enlaces únicos, no 109", file=sys.stderr)
        return 1

    filas = []
    for enlace, _url_indice in enlaces:
        titulo = enlace.texto.strip()
        slug = doc_slug(enlace.href, titulo, _INST_ID)
        rama, slug_reconstruido = _rama(enlace.href, titulo)
        if slug_reconstruido != slug:
            print(f"ALTO: la rama reconstruida no cuadra para {enlace.href!r}", file=sys.stderr)
            return 1
        filas.append(
            {
                "href": enlace.href,
                "nombre_archivo": _nombre_archivo(enlace.href),
                "titulo": titulo,
                "doc_slug": slug,
                "rama": rama,
                "slug_por_titulo": _slug_por_titulo(enlace.href, titulo),
                "es_fecha": str(_es_fecha(slug)),
            }
        )

    print("\t".join(_COLUMNAS))
    for fila in filas:
        print("\t".join(_celda(fila[c]) for c in _COLUMNAS))

    _resumen(filas)
    return 0


def _resumen(filas: list[dict[str, str]]) -> None:
    def err(texto: str = "") -> None:
        print(texto, file=sys.stderr)

    ramas: dict[str, int] = defaultdict(int)
    for fila in filas:
        ramas[fila["rama"]] += 1
    err(f"# enlaces únicos: {len(filas)}")
    for rama, n in sorted(ramas.items()):
        err(f"# rama {rama}: {n}")

    por_slug: dict[str, list[dict[str, str]]] = defaultdict(list)
    for fila in filas:
        por_slug[fila["doc_slug"]].append(fila)
    repetidos = {s: fs for s, fs in por_slug.items() if len(fs) > 1}
    err(f"# doc_slug distintos: {len(por_slug)}; grupos repetidos: {len(repetidos)}")
    for slug, fs in sorted(repetidos.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        err(f"#   {slug} ×{len(fs)}")
        for f in fs:
            err(f"#     [{f['rama']}] {_celda(f['nombre_archivo'])}")

    por_titulo: dict[str, list[dict[str, str]]] = defaultdict(list)
    for fila in filas:
        por_titulo[fila["slug_por_titulo"]].append(fila)
    repetidos_t = {s: fs for s, fs in por_titulo.items() if len(fs) > 1}
    err(f"# slug_por_titulo distintos: {len(por_titulo)}; grupos repetidos: {len(repetidos_t)}")
    for slug, fs in sorted(repetidos_t.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        err(f"#   {slug!r} ×{len(fs)}")
        for f in fs:
            err(f"#     {_celda(f['titulo'])!r}  <-  {_celda(f['nombre_archivo'])}")

    err(f"# doc_slug con forma de fecha: {sum(f['es_fecha'] == 'True' for f in filas)}")


if __name__ == "__main__":
    sys.exit(main())
