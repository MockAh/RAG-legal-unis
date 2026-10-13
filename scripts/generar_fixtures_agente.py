"""M49: genera `truncado.json` y `uacam.json` del agente maniquí desde las fixtures reales.

Solo lee fixtures del disco: sin red, sin base y sin LLM. Los demás JSON de
`tests/fixtures/agente/` se escriben a mano.

- `truncado.json`: las 40 primeras de las 47 entradas de la UAM, cero descartes (criterio 17).
- `uacam.json`: las 87 de la UACAM como entradas, cero descartes.

Las entradas llevan el `href` crudo, como lo recibe el agente; `tipo_norma` es "otro" porque
el maniquí no clasifica. Si el ancla viene vacía, el título sale del nombre de archivo y se
marca `titulo_derivado`.

Uso:
    .venv/bin/python scripts/generar_fixtures_agente.py            # escribe en tests/fixtures/agente/
    .venv/bin/python scripts/generar_fixtures_agente.py <carpeta>  # escribe en otra, para comparar
"""

import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from legisuni.lector import classify, cuenta, reduce

_RAIZ = Path(__file__).resolve().parent.parent
_FIXTURES = _RAIZ / "fixtures"
_DESTINO = _RAIZ / "tests" / "fixtures" / "agente"


def _tabla(nombre: str, content_type: str | None, url_indice: str) -> list[reduce.Enlace]:
    pagina = reduce.reducir((_FIXTURES / nombre).read_bytes(), content_type)
    return cuenta.deduplicar(classify.candidatos(pagina.enlaces), url_indice)


def _entrada(enlace: reduce.Enlace) -> dict:
    titulo = " ".join(enlace.texto.split())
    derivado = not titulo
    if derivado:
        titulo = Path(unquote(urlsplit(enlace.href.strip()).path)).stem
    return {"href": enlace.href, "titulo": titulo, "tipo_norma": "otro", "titulo_derivado": derivado}


def _escribir(destino: Path, nombre: str, entradas: list[dict]) -> None:
    datos = {"entradas": entradas, "descartados": [], "agotado": False, "notas": None}
    texto = json.dumps(datos, ensure_ascii=False, indent=2) + "\n"
    (destino / nombre).write_text(texto, encoding="utf-8")


def main() -> None:
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else _DESTINO
    destino.mkdir(parents=True, exist_ok=True)

    uam = _tabla("uam-index.html", None, "https://www.uam.mx/")
    assert len(uam) == 47, len(uam)
    _escribir(destino, "truncado.json", [_entrada(e) for e in uam[:40]])

    uacam = _tabla("uacam__2026-10-01.html", "text/html; charset=UTF-8", "https://www.uacam.mx/")
    assert len(uacam) == 87, len(uacam)
    _escribir(destino, "uacam.json", [_entrada(e) for e in uacam])


if __name__ == "__main__":
    main()
