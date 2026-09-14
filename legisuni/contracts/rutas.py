"""Validación anti-traversal de cajón y etiqueta (docs/05 criterio 17, M18).

Módulo auxiliar: no es un contrato nuevo, no añade ni cambia campos de N10.
Único lugar donde viven los patrones seguros de nombre de archivo. `Encargo`
los usa para el rechazo "de verdad" al construirse; `descargador/paths.py`
los reutiliza como cinturón y tirantes, la última línea antes de escribir a
disco (M17). Si divergieran, la validación mentiría.
"""

import re

_ETIQUETA_SEGURA = re.compile(r"^[a-z0-9._-]+$")
_CAJON_SEGURO = re.compile(r"^[a-z0-9._/-]+$")


def validar_cajon(cajon: str) -> None:
    if cajon.startswith("/") or ".." in cajon.split("/") or not _CAJON_SEGURO.match(cajon):
        raise ValueError(f"cajon inseguro: {cajon!r}")


def validar_etiqueta(etiqueta: str) -> None:
    if ".." in etiqueta or not _ETIQUETA_SEGURA.match(etiqueta):
        raise ValueError(f"etiqueta insegura: {etiqueta!r}")
