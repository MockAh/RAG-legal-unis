"""Script DESECHABLE (M30, generalizado en M36): convierte un lote ya estructurado en Encargos.

NO es el Lector de Lista (docs/00 §3, pieza Ⓐ; sin spec todavía). Lee un
formato de fichas ya estructurado, a mano (`datos/lotes/bloque-a.txt`,
`datos/lotes/bloque-b.txt`), y escribe el JSON que es la entrada de
`scripts/lote.py`. El .txt no se vuelve a leer en tiempo de ejecución. Sin
tests propios: solo se valida su salida (tests/test_encargos_bloque_*.py).

Reglas, todas de docs/01: articulo_id (N11, nota), traducción académica (N10),
fichas sin puertas (N11) → `no_obtenidos` con la forma de `Faltante` (N14).
"""

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import get_args
from urllib.parse import urlsplit

import typer

from legisuni.contracts import Encargo, Puerta
from legisuni.contracts.vocabularios import Relacion, TipoPuerta
from legisuni.descargador.urlnorm import normalizar

_VACIO = "—"
_MARCAS = ("[PDF]", "[REG]", "[DOI]")
# 01 l.785: copias libres (en el orden de la lista), luego la oficial, al final el resolutor
_ORDEN_TIPOS: tuple[TipoPuerta, ...] = ("copia_libre", "oficial", "resolutor_doi")
_ID_EN_RELACION = re.compile(r"\b[A-Z]\.\d+[A-Z]*\b")

# Tipo por host. Un [PDF] cuyo host no esté aquí es `copia_libre`; un [REG]
# cuyo host no esté aquí es un error.
_TIPO_POR_HOST: dict[str, TipoPuerta] = {
    # PMC (01 l.128); desde M36 también su host nuevo. Son vestíbulos: los cruza la corrida
    "www.ncbi.nlm.nih.gov": "copia_libre",
    "pmc.ncbi.nlm.nih.gov": "copia_libre",
    # repositorios institucionales (01 l.128)
    "hull-repository.worktribe.com": "copia_libre",
    "eprints.whiterose.ac.uk": "copia_libre",
    "eprints.soton.ac.uk": "copia_libre",
    "eprints.gla.ac.uk": "copia_libre",
    "archive-ouverte.unige.ch": "copia_libre",
    "dspace.library.uu.nl": "copia_libre",
    "www.repository.cam.ac.uk": "copia_libre",
    "nora.nerc.ac.uk": "copia_libre",
    "discovery.ucl.ac.uk": "copia_libre",
    "pure-oai.bham.ac.uk": "copia_libre",
    "www.pure.ed.ac.uk": "copia_libre",
    # portales CRIS: copia_libre SIN evidencia; revisar con M37 (M36)
    "www.research.ed.ac.uk": "copia_libre",
    "research.birmingham.ac.uk": "copia_libre",
    "www.researchwithrutgers.com": "copia_libre",
    "experts.arizona.edu": "copia_libre",
    "pure.psu.edu": "copia_libre",
    "research.vu.nl": "copia_libre",
    "research-information.bris.ac.uk": "copia_libre",
    "research-portal.st-andrews.ac.uk": "copia_libre",
    "profiles.wustl.edu": "copia_libre",
    # editoriales; un [PDF] en su host es el PDF de la editorial (A.7, B.8, B.36)
    "www.annualreviews.org": "oficial",
    "www.sciencedirect.com": "oficial",
    "www.nature.com": "oficial",
    "www.cambridge.org": "oficial",
    "www.science.org": "oficial",
    "www.pnas.org": "oficial",
    "pubs.geoscienceworld.org": "oficial",
}

# Enlaces que no son puerta: quedan en el bloque auxiliar `registros` (M30,
# M36). Registros bibliográficos, que ningún TipoPuerta describe, y el
# suplemento de B.10: descargado como artículo sería un falso éxito (M36).
_REGISTROS: dict[str, str | None] = {
    "pubmed.ncbi.nlm.nih.gov": None,
    "ui.adsabs.harvard.edu": None,
    "www.researchgate.net": None,
    "doaj.org": None,
    "gsapubs.figshare.com": "material suplementario",
}


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


def _relacion(campos: dict[str, str]) -> tuple[Relacion | None, str] | None:
    """(valor de Relacion o None si el literal no está en el vocabulario, ID relacionado)."""
    literal = _valor(campos, "RELACION")
    if literal is None:
        return None
    primera = literal.split()[0]
    relacion = primera if primera in get_args(Relacion) else None
    return relacion, _ID_EN_RELACION.findall(literal)[-1]


def _es_correccion_sin_doi(campos: dict[str, str]) -> bool:
    relacion = _relacion(campos)
    return relacion is not None and relacion[0] == "correccion" and not _valor(campos, "DOI")


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


def _registro(articulo_id: str, posicion: str, url: str) -> dict:
    registro = {"articulo_id": articulo_id, "posicion_en_lista": posicion, "url": url}
    nota = _REGISTROS[urlsplit(url).hostname or ""]
    if nota:
        registro["nota"] = nota
    return registro


def main(
    entrada: Path = typer.Option(..., "--entrada", help="Lote estructurado (.txt)"),
    salida: Path = typer.Option(..., "--salida", help="JSON de Encargos para lote.py"),
) -> None:
    crudo = entrada.read_bytes()
    sha256_archivo = hashlib.sha256(crudo).hexdigest()
    lote_id = f"{slug(entrada.name)}-{sha256_archivo[:8]}"
    fichas = _leer_fichas(crudo.decode("utf-8"))
    ahora = datetime.now()

    por_posicion = {f["campos"]["ID"]: f for f in fichas}
    puertas_por_posicion = {pos: _puertas(f["campos"], f["enlaces"], lote_id) for pos, f in por_posicion.items()}
    ids_por_posicion = {
        pos: _articulo_id(f["campos"]) for pos, f in por_posicion.items() if not _es_correccion_sin_doi(f["campos"])
    }
    for pos, f in por_posicion.items():
        if _es_correccion_sin_doi(f["campos"]):
            # 01 l.767: corr:{relacionado_con}:{h8 de la url normalizada de su primera puerta}
            _, corregida = _relacion(f["campos"])
            primera = puertas_por_posicion[pos][0]
            h8_puerta = _sha256(normalizar(primera.url, primera.url_base or ""))[:8]
            ids_por_posicion[pos] = f"corr:{ids_por_posicion[corregida]}:{h8_puerta}"

    encargos: list[Encargo] = []
    no_obtenidos: list[dict] = []
    vinculos: list[dict] = []
    registros: list[dict] = []

    for ficha in fichas:
        campos = ficha["campos"]
        articulo_id = ids_por_posicion[campos["ID"]]
        puertas = puertas_por_posicion[campos["ID"]]
        registros.extend(
            _registro(articulo_id, campos["ID"], url) for _, url in ficha["enlaces"] if _es_registro(url)
        )

        relacion = _relacion(campos)
        if relacion:
            # Encargo no lleva relacion (N10): vive aquí. None si el literal no está
            # en Relacion («suplemento», «publicado en paralelo»; M30, M36)
            valor, relacionado = relacion
            vinculos.append(
                {
                    "articulo_id": articulo_id,
                    "relacionado_con": ids_por_posicion[relacionado],
                    "relacion": valor,
                    "literal": campos["RELACION"],
                }
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

        if articulo_id.startswith("corr:"):
            # 01 N10: autor y año del artículo corregido, con prefijo corr-
            corregida = por_posicion[relacion[1]]["campos"]
            etiqueta_base = f"corr-{slug(_primer_autor(corregida))}-{corregida['AÑO']}"
        else:
            etiqueta_base = f"{slug(_primer_autor(campos))}-{campos['AÑO']}"
        encargos.append(
            Encargo(
                encargo_id=articulo_id,
                modo="academico",
                solicitante=lote_id,
                puertas=puertas,
                cajon="papers",
                etiqueta=f"{etiqueta_base}__{_sha256(articulo_id)[:8]}",
                cruzar_vestibulos=True,
                grupo_alias=articulo_id,
                creado_en=ahora,
            )
        )

    datos = {
        "lote_id": lote_id,
        "archivo_origen": entrada.name,
        "sha256_archivo": sha256_archivo,
        "encargos": [e.model_dump(mode="json") for e in encargos],
        "no_obtenidos": no_obtenidos,
        "vinculos": vinculos,
        "registros": registros,
    }
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(encargos)} encargos, {len(no_obtenidos)} sin puertas → {salida}")


if __name__ == "__main__":
    typer.run(main)
