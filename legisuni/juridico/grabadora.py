"""Artefactos de evaluación de una corrida del Lector, una página (criterio 20 de `03`, M50).

Vive en `juridico/` porque llama a `ensamblado.ensamblar`, y `lector/` no importa
`legisuni.juridico` (criterio 15).

Orden de escritura, que es lo que da sentido a la grabadora:

1. `meta.json` y `prompt.txt`, antes de nada;
2. `enlaces.json`, ANTES de llamar al agente: si la llamada revienta, queda lo que se le iba a dar;
3. `respuesta_cruda.txt`, ANTES de parsear: si el parseo da `salida_invalida`, la cruda ya está;
4. `catalogo.json`, el `Catalog` resultante con su contabilidad (03 §Evaluación).

El identificador de modelo no se inventa: lo da quien llama, y sin él no se escribe nada.
"""

import json
from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from legisuni.contracts import Catalog, SourceCandidate
from legisuni.juridico.ensamblado import ensamblar
from legisuni.lector.corte import Corte
from legisuni.lector.models import Agente
from legisuni.lector.reduce import Enlace

# Relativa al directorio de trabajo, como `Settings.data_root`. Nunca `data/`: es del corpus,
# y su prerrequisito es quedar vacío (03 §Prerrequisito).
RAIZ_POR_DEFECTO = Path("evaluacion")


def _carpeta_nueva(raiz: Path, inst_id: str, ahora: datetime) -> Path:
    """`<inst_id>__<marca>`, y si ya existe, `-2`, `-3`… `mkdir` sin `exist_ok` es atómico:
    dos corridas en el mismo segundo no pueden quedarse con la misma carpeta."""
    base = f"{inst_id}__{ahora.strftime('%Y-%m-%dT%H-%M-%S')}"
    raiz.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        carpeta = raiz / (base if n == 1 else f"{base}-{n}")
        try:
            carpeta.mkdir()
            return carpeta
        except FileExistsError:
            n += 1


def _escribir_json(ruta: Path, datos: object) -> None:
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def grabar_corrida(
    agente: Agente,
    fuente: SourceCandidate,
    enlaces: Sequence[Enlace],
    corte: Corte | None,
    *,
    prompt: str,
    modelo: str,
    ahora: datetime,
    umbral_caducidad_meses: int,
    raiz: Path = RAIZ_POR_DEFECTO,
) -> tuple[Catalog, Path]:
    """Llama al agente sobre `enlaces`, ensambla el `Catalog` y deja los artefactos en disco.

    `prompt` y `modelo` (identificador con su versión, tal cual) los da quien llama: el
    `Agente` de `lector/models.py` no los expone. Devuelve el `Catalog` y la carpeta.
    Una excepción del agente se propaga; la tabla de enlaces ya quedó escrita.
    """
    if not isinstance(modelo, str) or not modelo.strip():
        raise ValueError("falta el identificador de modelo: sin él el artefacto no es auditable")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("falta el prompt: sin él el artefacto no es auditable")

    carpeta = _carpeta_nueva(raiz, fuente.inst_id, ahora)
    _escribir_json(
        carpeta / "meta.json",
        {
            "modelo": modelo,
            "inst_id": fuente.inst_id,
            "url_indice": fuente.url,
            "marca_de_tiempo": ahora.isoformat(),
        },
    )
    (carpeta / "prompt.txt").write_text(prompt, encoding="utf-8")
    _escribir_json(carpeta / "enlaces.json", [asdict(e) for e in enlaces])

    cruda = agente(enlaces)
    # .txt y no .json: puede no ser JSON válido, y es justo cuando más importa tenerla.
    (carpeta / "respuesta_cruda.txt").write_bytes(cruda.encode("utf-8"))

    catalogo = ensamblar(fuente, enlaces, corte, cruda, ahora, umbral_caducidad_meses)
    (carpeta / "catalogo.json").write_text(catalogo.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return catalogo, carpeta
