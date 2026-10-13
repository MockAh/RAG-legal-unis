"""M50: la grabadora de artefactos de evaluación (criterio 20 de 03), con el maniquí de M49."""

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import pytest

from legisuni.contracts import SourceCandidate
from legisuni.juridico import grabadora
from legisuni.juridico.grabadora import grabar_corrida
from legisuni.lector.classify import candidatos
from legisuni.lector.cuenta import deduplicar
from legisuni.lector.reduce import Enlace, reducir
from maniqui import AGENTE, AgenteManiqui

FIX = Path(__file__).resolve().parent.parent / "fixtures"
AHORA = datetime(2026, 10, 1, 12, 0, 0)
PROMPT = "Eres el Lector de Índice. Responde solo JSON."
MODELO = "maniqui-m50"
ARCHIVOS = {"meta.json", "prompt.txt", "enlaces.json", "respuesta_cruda.txt", "catalogo.json"}

UAM = SourceCandidate(
    inst_id="uam",
    url="https://www.uam.mx/",
    origen="sitio_institucional",
    titulo_pagina="Legislación",
    dominio="www.uam.mx",
    es_dominio_institucional=True,
    confianza="alta",
    razon="maniquí",
    descubierta_en=AHORA,
    evidencia_url="https://www.uam.mx/",
)


def _uam_47() -> list[Enlace]:
    return deduplicar(candidatos(reducir((FIX / "uam-index.html").read_bytes(), None).enlaces), UAM.url)


def _grabar(agente, raiz: Path, **cambios):
    argumentos = dict(prompt=PROMPT, modelo=MODELO, ahora=AHORA, umbral_caducidad_meses=18, raiz=raiz)
    argumentos.update(cambios)
    return grabar_corrida(agente, UAM, _uam_47(), None, **argumentos)


class AgenteQueRevienta:
    def __call__(self, enlaces: Sequence[Enlace]) -> str:
        raise RuntimeError("timeout simulado")


def test_corrida_normal_deja_los_artefactos(tmp_path: Path) -> None:
    catalogo, carpeta = _grabar(AgenteManiqui("truncado"), tmp_path)
    assert {p.name for p in carpeta.iterdir()} == ARCHIVOS
    assert carpeta.parent == tmp_path
    assert carpeta.name == "uam__2026-10-01T12-00-00"

    tabla = json.loads((carpeta / "enlaces.json").read_text(encoding="utf-8"))
    assert tabla == [{"texto": e.texto, "href": e.href} for e in _uam_47()]
    assert len(tabla) == 47

    assert (carpeta / "prompt.txt").read_text(encoding="utf-8") == PROMPT
    meta = json.loads((carpeta / "meta.json").read_text(encoding="utf-8"))
    assert meta == {
        "modelo": MODELO,
        "inst_id": "uam",
        "url_indice": "https://www.uam.mx/",
        "marca_de_tiempo": "2026-10-01T12:00:00",
    }
    guardado = json.loads((carpeta / "catalogo.json").read_text(encoding="utf-8"))
    assert guardado["enlaces_sin_cuenta"] == catalogo.enlaces_sin_cuenta
    assert len(guardado["enlaces_sin_cuenta"]) == 7


def test_json_invalido_la_cruda_queda_en_disco_exacta(tmp_path: Path) -> None:
    catalogo, carpeta = _grabar(AgenteManiqui("invalido"), tmp_path)
    assert catalogo.fallo_lector == "salida_invalida"
    esperada = (AGENTE / "invalido.json").read_bytes()
    assert (carpeta / "respuesta_cruda.txt").read_bytes() == esperada


def test_si_el_agente_revienta_la_tabla_ya_esta_escrita(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="timeout simulado"):
        _grabar(AgenteQueRevienta(), tmp_path)
    (carpeta,) = tmp_path.iterdir()
    assert len(json.loads((carpeta / "enlaces.json").read_text(encoding="utf-8"))) == 47
    assert (carpeta / "meta.json").exists()
    assert (carpeta / "prompt.txt").exists()
    assert not (carpeta / "respuesta_cruda.txt").exists()


def test_dos_corridas_en_el_mismo_segundo_no_se_pisan(tmp_path: Path) -> None:
    _, primera = _grabar(AgenteManiqui("truncado"), tmp_path)
    _, segunda = _grabar(AgenteManiqui("invalido"), tmp_path)
    assert primera != segunda
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "uam__2026-10-01T12-00-00",
        "uam__2026-10-01T12-00-00-2",
    ]
    assert (primera / "respuesta_cruda.txt").read_bytes() == (AGENTE / "truncado.json").read_bytes()
    assert (segunda / "respuesta_cruda.txt").read_bytes() == (AGENTE / "invalido.json").read_bytes()


@pytest.mark.parametrize("modelo", ["", "   ", None])
def test_sin_modelo_falla_y_no_escribe_nada(tmp_path: Path, modelo) -> None:
    raiz = tmp_path / "evaluacion"
    with pytest.raises(ValueError, match="modelo"):
        _grabar(AgenteManiqui("truncado"), raiz, modelo=modelo)
    assert not raiz.exists()


def test_sin_argumento_modelo_falla(tmp_path: Path) -> None:
    raiz = tmp_path / "evaluacion"
    with pytest.raises(TypeError):
        grabar_corrida(
            AgenteManiqui("truncado"), UAM, _uam_47(), None,
            prompt=PROMPT, ahora=AHORA, umbral_caducidad_meses=18, raiz=raiz,
        )  # fmt: skip
    assert not raiz.exists()


def test_la_raiz_por_defecto_no_es_data() -> None:
    # data/ es del corpus y debe poder quedar vacío (03 §Prerrequisito). No «simplificar».
    assert grabadora.RAIZ_POR_DEFECTO == Path("evaluacion")
    assert "data" not in grabadora.RAIZ_POR_DEFECTO.parts
