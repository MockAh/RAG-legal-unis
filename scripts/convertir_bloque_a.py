"""Script DESECHABLE (M30): convierte `datos/lotes/bloque-a.txt` en Encargos.

NO es el Lector de Lista (docs/00 §3, pieza Ⓐ; sin spec todavía). Lee un
formato de fichas ya estructurado, a mano, para un solo archivo, y escribe
`datos/encargos_bloque_a.json`, que es la entrada de `scripts/lote.py`. El
.txt no se vuelve a leer en tiempo de ejecución. Sin tests propios: solo se
valida su salida (tests/test_encargos_bloque_a.py).

Reglas, todas de docs/01: articulo_id (N11, nota), traducción académica (N10),
fichas sin puertas (N11) → `no_obtenidos` con la forma de `Faltante` (N14).
"""

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from legisuni.contracts import Encargo, Puerta
from legisuni.contracts.vocabularios import TipoPuerta

ENTRADA = Path("datos/lotes/bloque-a.txt")
SALIDA = Path("datos/encargos_bloque_a.json")

_VACIO = "—"
_MARCAS = ("[PDF]", "[REG]", "[DOI]")
# 01 l.776: copias libres (en el orden de la lista), luego la oficial, al final el resolutor
_ORDEN_TIPOS: tuple[TipoPuerta, ...] = ("copia_libre", "oficial", "resolutor_doi")

# Tipo por host. Un [PDF] cuyo host no esté aquí es `copia_libre`; un [REG]
# cuyo host no esté aquí es un error.
_TIPO_POR_HOST: dict[str, TipoPuerta] = {
    "www.ncbi.nlm.nih.gov": "copia_libre",           # PMC (01 l.128)
    "hull-repository.worktribe.com": "copia_libre",  # repositorio institucional (01 l.128)
    "www.annualreviews.org": "oficial",
    "www.sciencedirect.com": "oficial",
    "www.nature.com": "oficial",
    "www.cambridge.org": "oficial",                  # PDF abierto de la editorial (A.7)
}

# Registros bibliográficos: ningún TipoPuerta los describe. No son puerta;
# quedan en el bloque auxiliar `registros` (M30, a revisar con M31).
_REGISTROS = {"pubmed.ncbi.nlm.nih.gov", "ui.adsabs.harvard.edu"}


def slug(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", sin_acentos.lower()).strip("-")


def _normalizar_titulo(titulo: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode("ascii")
    return " ".join(sin_acentos.lower().split())


def _normalizar_doi(doi: str) -> str:
    # 01, Parámetros, "Revisión académica"
    doi = doi.strip().lower()
    for prefijo in ("doi:", "https://doi.org/", "http://dx.doi.org/"):
        if doi.startswith(prefijo):
            doi = doi[len(prefijo):]
    return doi.rstrip(".,;)]")


def _sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _leer_fichas(texto: str) -> list[dict]:
    fichas = []
    for bloque in texto.split("===="):
        campos: dict[str, str] = {}
        enlaces: list[tuple[str, str]] = []
        for linea in bloque.splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            marca = linea[:5]
            if marca in _MARCAS:
                enlaces.append((marca, linea[5:].strip()))
            elif ":" in linea:
                clave, valor = linea.split(":", 1)
                campos[clave.strip()] = valor.strip()
        if "ID" in campos:
            fichas.append({"campos": campos, "enlaces": enlaces})
    return fichas


def _valor(campos: dict[str, str], clave: str) -> str | None:
    valor = campos.get(clave)
    return None if valor in (None, "", _VACIO) else valor


def _articulo_id(campos: dict[str, str]) -> str:
    doi = _valor(campos, "DOI")
    if doi:
        return f"doi:{_normalizar_doi(doi)}"
    h8 = _sha256(_normalizar_titulo(campos["TITULO"]))[:8]
    return f"ref:{slug(_primer_autor(campos))}-{campos['AÑO']}-{h8}"


def _primer_autor(campos: dict[str, str]) -> str:
    return campos["AUTORES"].split(";")[0].split(",")[0].strip()


def _tipo(marca: str, url: str) -> TipoPuerta:
    if marca == "[DOI]":
        return "resolutor_doi"
    host = urlsplit(url).hostname or ""
    if host in _TIPO_POR_HOST:
        return _TIPO_POR_HOST[host]
    if marca == "[PDF]":
        return "copia_libre"
    raise SystemExit(f"host [REG] sin tipo asignado: {host} ({url})")


def _es_registro(url: str) -> bool:
    return urlsplit(url).hostname in _REGISTROS


def _puertas(campos: dict[str, str], enlaces: list[tuple[str, str]], lote_id: str) -> list[Puerta]:
    evidencia = f"lista:{lote_id}#{campos['ID']}"
    puertas = [
        Puerta(url=url, tipo=_tipo(marca, url), url_base=None, evidencia=evidencia)
        for marca, url in enlaces
        if not _es_registro(url)
    ]
    puertas.sort(key=lambda p: _ORDEN_TIPOS.index(p.tipo))  # estable: respeta el orden de la lista
    doi = _valor(campos, "DOI")
    if doi and not any(p.tipo == "resolutor_doi" for p in puertas):
        # única excepción a D3: solo si la lista no trae ya el enlace doi.org
        puertas.append(
            Puerta(
                url=f"https://doi.org/{_normalizar_doi(doi)}",
                tipo="resolutor_doi",
                url_base=None,
                evidencia=evidencia,
                construida=True,
            )
        )
    return puertas


def main() -> None:
    crudo = ENTRADA.read_bytes()
    sha256_archivo = hashlib.sha256(crudo).hexdigest()
    lote_id = f"{slug(ENTRADA.name)}-{sha256_archivo[:8]}"
    fichas = _leer_fichas(crudo.decode("utf-8"))
    ahora = datetime.now()

    ids_por_posicion = {f["campos"]["ID"]: _articulo_id(f["campos"]) for f in fichas}
    encargos: list[Encargo] = []
    no_obtenidos: list[dict] = []
    vinculos: list[dict] = []
    registros: list[dict] = []

    for ficha in fichas:
        campos = ficha["campos"]
        articulo_id = ids_por_posicion[campos["ID"]]
        puertas = _puertas(campos, ficha["enlaces"], lote_id)
        registros.extend(
            {"articulo_id": articulo_id, "posicion_en_lista": campos["ID"], "url": url}
            for _, url in ficha["enlaces"]
            if _es_registro(url)
        )

        relacion = _valor(campos, "RELACION")
        if relacion:
            # «suplemento» no está en Relacion (01): el vínculo vive solo aquí (M30)
            relacionado = relacion.split()[-1]
            vinculos.append(
                {"articulo_id": articulo_id, "relacionado_con": ids_por_posicion[relacionado], "literal": relacion}
            )

        if not puertas:
            no_obtenidos.append(
                {
                    "articulo_id": articulo_id,
                    "referencia_literal": campos["REFERENCIA"],
                    "motivo": "sin_puertas",
                    "intentos": 0,
                    "ruta_sugerida": "buscar por título o cita",
                }
            )
            continue

        encargos.append(
            Encargo(
                encargo_id=articulo_id,
                modo="academico",
                solicitante=lote_id,
                puertas=puertas,
                cajon="papers",
                etiqueta=f"{slug(_primer_autor(campos))}-{campos['AÑO']}__{_sha256(articulo_id)[:8]}",
                cruzar_vestibulos=True,
                grupo_alias=articulo_id,
                creado_en=ahora,
            )
        )

    salida = {
        "lote_id": lote_id,
        "archivo_origen": ENTRADA.name,
        "sha256_archivo": sha256_archivo,
        "encargos": [e.model_dump(mode="json") for e in encargos],
        "no_obtenidos": no_obtenidos,
        "vinculos": vinculos,
        "registros": registros,
    }
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(encargos)} encargos, {len(no_obtenidos)} sin puertas → {SALIDA}")


if __name__ == "__main__":
    main()
