"""
Configuración por variables de entorno (o un archivo .env en la raíz).

    FUENTE_DATOS   demo | mongo     (por defecto: demo)
    MONGO_URI      mongodb://localhost:27017
    MONGO_DB       propiedades
    MONGO_COLECCION inmuebles
    DEMO_PATH      data/demo/avisos.csv
    CORS_ORIGINS   lista separada por comas

El modo demo existe para que cualquiera pueda clonar el repo y ver el
dashboard funcionando sin instalar MongoDB ni correr el scraper.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

try:  # python-dotenv es opcional
    from dotenv import load_dotenv

    load_dotenv(RAIZ / ".env")
except ImportError:  # pragma: no cover
    pass


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip()]


@dataclass(frozen=True)
class Config:
    fuente: str = field(default_factory=lambda: os.getenv("FUENTE_DATOS", "demo").lower())
    mongo_uri: str = field(default_factory=lambda: os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    mongo_db: str = field(default_factory=lambda: os.getenv("MONGO_DB", "propiedades"))
    mongo_coleccion: str = field(default_factory=lambda: os.getenv("MONGO_COLECCION", "inmuebles"))
    demo_path: Path = field(
        default_factory=lambda: Path(os.getenv("DEMO_PATH") or RAIZ / "data" / "demo" / "avisos.csv")
    )
    comunas_path: Path = RAIZ / "data" / "comunas_biobio.csv"
    cors_origins: list[str] = field(
        default_factory=lambda: _lista(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
            )
        )
    )


def cargar() -> Config:
    return Config()
