"""Las 33 comunas de la Región del Biobío, desde data/comunas_biobio.csv."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from config import RAIZ


@dataclass(frozen=True)
class Comuna:
    slug: str       # como aparece en las URLs del portal
    nombre: str     # como se muestra (con tildes)
    provincia: str


def cargar(path: Path = RAIZ / "data" / "comunas_biobio.csv") -> list[Comuna]:
    with path.open(encoding="utf-8") as f:
        return [Comuna(**fila) for fila in csv.DictReader(f)]
