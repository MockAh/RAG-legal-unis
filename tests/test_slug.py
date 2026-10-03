import csv
import re
from collections import Counter
from pathlib import Path

import pytest

from legisuni.lector.slug import doc_slug

RAIZ = Path(__file__).resolve().parent.parent
ORACULO = RAIZ / "datos" / "oraculo-uam.tsv"
FIXTURE_UNAM = RAIZ / "fixtures" / "unam-oag__2026-10-01.html"


def _filas():
    with ORACULO.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


FILAS = _filas()


def _esperado(fila):
    return fila["slug_correcto"] or fila["slug_actual"]


def test_oraculo_tiene_47_filas():
    assert len(FILAS) == 47


@pytest.mark.parametrize("fila", FILAS, ids=[f"{i}-{f['href'].rsplit('/', 1)[-1]}" for i, f in enumerate(FILAS)])
def test_oraculo_uam(fila):
    assert doc_slug(fila["href"], fila["texto"], "uam") == _esperado(fila)


def test_repeticiones_y_sin_fechas():
    slugs = [doc_slug(f["href"], f["texto"], "uam") for f in FILAS]
    cuenta = Counter(slugs)
    assert cuenta["res"] == 3
    assert cuenta["ripppa"] == 3
    for s in ("rjd", "retra", "repla", "reddu", "ra"):
        assert cuenta[s] == 2
    fecha = re.compile(r"^[\d.\-]+$")
    assert not [s for s in slugs if fecha.match(s)]


def test_percent_encoding():
    assert doc_slug("x/leg-Acuerdo%20de%20Genero.pdf", "t", "ujat") == "acuerdo-de-genero"
    assert doc_slug("x/manual-ACTUALIZACI%C3%93N.pdf", "t", "ujat") == "actualizacion"


def test_prefijo_numerico_unam():
    html = FIXTURE_UNAM.read_text(encoding="utf-8")
    hrefs = re.findall(r'href="([^"]*/\d+-[A-Za-z][^"]*\.pdf)"', html)
    assert hrefs
    esperados = {
        "/archivos/44-ReglamentoPlaneacion_rem38_021220.pdf": "n44",
        "/archivos/LegUniv/10-ReglamentoFuncionamientoComisionEspecialElectoralConsejoUniversitario_rem38_021220.pdf": "n10",
    }
    for h in hrefs:
        assert doc_slug(h, "Reglamento", "unam") == "n" + re.search(r"/(\d+)-", h).group(1)
    for sufijo, slug in esperados.items():
        h = next(h for h in hrefs if h.endswith(sufijo.rsplit("/", 1)[-1]))
        assert doc_slug(h, "x", "unam") == slug


def test_respaldo_por_titulo():
    assert doc_slug("/docs/reglamentogeneral.pdf", "Reglamento de Pagos (julio 2026)", "ujat") == "reglamento-de-pagos"
    assert doc_slug("/ver?id=5", "Código de Ética 24 de julio de 2026", "uacam") == "codigo-de-etica"
