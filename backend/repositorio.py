"""
Acceso a los avisos, con dos implementaciones intercambiables:

- MongoRepositorio: la base que llena el scraper.
- DemoRepositorio:  un CSV incluido en el repo, cargado en memoria.

La API no sabe cuál está usando. Así el mismo código corre en tu máquina
con datos reales o en cualquier clon recién hecho con datos de demo.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Protocol

from analisis import numero, superficie

CAMPOS_NUMERICOS = ("precio_uf", "precio_clp")
ORDENES = ("reciente", "precio_asc", "precio_desc", "uf_m2_asc")


class Repositorio(Protocol):
    fuente: str

    def todos(self, filtro: dict[str, str]) -> list[dict]: ...
    def distintos(self, campo: str) -> list[str]: ...
    def contar(self) -> int: ...


def _uf_m2(a: dict) -> float:
    m2, uf = superficie(a), numero(a.get("precio_uf"))
    return uf / m2 if (m2 and uf) else float("inf")


def ordenar(avisos: list[dict], orden: str) -> list[dict]:
    if orden == "precio_asc":
        return sorted(avisos, key=lambda a: numero(a.get("precio_uf")) or float("inf"))
    if orden == "precio_desc":
        return sorted(avisos, key=lambda a: -(numero(a.get("precio_uf")) or 0))
    if orden == "uf_m2_asc":
        return sorted(avisos, key=_uf_m2)
    return sorted(avisos, key=lambda a: a.get("fecha_ultima_vista") or "", reverse=True)


class DemoRepositorio:
    fuente = "demo"

    def __init__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(
                f"No existe {path}. Genera la demo con:  python scripts/generar_demo.py"
            )
        with path.open(encoding="utf-8") as f:
            self._avisos = [self._tipar(r) for r in csv.DictReader(f)]

    @staticmethod
    def _tipar(fila: dict[str, str]) -> dict[str, Any]:
        a: dict[str, Any] = dict(fila)
        for c in CAMPOS_NUMERICOS:
            a[c] = numero(a.get(c))
        return a

    def todos(self, filtro: dict[str, str]) -> list[dict]:
        return [a for a in self._avisos if all(a.get(k) == v for k, v in filtro.items())]

    def distintos(self, campo: str) -> list[str]:
        return sorted({a[campo] for a in self._avisos if a.get(campo)})

    def contar(self) -> int:
        return len(self._avisos)


class MongoRepositorio:
    fuente = "mongo"

    def __init__(self, uri: str, db: str, coleccion: str):
        from pymongo import MongoClient

        self._col = MongoClient(uri, serverSelectionTimeoutMS=3000)[db][coleccion]

    def todos(self, filtro: dict[str, str]) -> list[dict]:
        return list(self._col.find(filtro, {"_id": 0}))

    def distintos(self, campo: str) -> list[str]:
        return sorted(v for v in self._col.distinct(campo) if v)

    def contar(self) -> int:
        return self._col.estimated_document_count()


def crear(cfg) -> Repositorio:
    if cfg.fuente == "mongo":
        return MongoRepositorio(cfg.mongo_uri, cfg.mongo_db, cfg.mongo_coleccion)
    if cfg.fuente == "demo":
        return DemoRepositorio(cfg.demo_path)
    raise ValueError(f"FUENTE_DATOS desconocida: {cfg.fuente!r} (usa 'demo' o 'mongo')")
