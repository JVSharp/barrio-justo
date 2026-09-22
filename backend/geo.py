"""
Métricas geográficas por aviso: distancia a lugares de interés y horas de sol.

Los insumos vienen de OpenStreetMap (scripts/descargar_osm.py):

    data/osm/pois.json        {"categoria": [[lat, lon, "nombre"], ...], ...}
    data/osm/edificios.json   [[altura_m, altura_conocida (0/1), [[lat, lon], ...]], ...]

Todo en Python puro, con una grilla simple como índice espacial.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from typing import Any, Iterable

import sol

CATEGORIAS = {
    "biotren": "Estación de Biotren o terminal de buses",
    "universidad": "Universidad o instituto",
    "colegio": "Colegio",
    "salud": "Hospital o clínica",
    "supermercado": "Supermercado",
    "parque": "Parque o plaza",
}

DIA_SOL = date(2026, 6, 21)        # el día más corto del año en Chile
UTC_OFFSET_INVIERNO = -4           # hora de invierno de Chile continental
PISOS = {"calle": 1.5, "p3": 7.5, "p6": 16.5, "p10": 28.5}   # altura de los ojos, en m
RADIO_M = 150
CELDA = 0.002                       # ~200 m: tamaño de la grilla del índice


def distancia_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    x, y = sol.a_metros(lat1, lon1, lat2, lon2)
    return math.hypot(x, y)


class Indice:
    """Grilla lat/lon para buscar elementos cercanos sin recorrer todos."""

    def __init__(self, elementos: Iterable[tuple[float, float, Any]]):
        self.celdas: dict[tuple[int, int], list] = defaultdict(list)
        for lat, lon, dato in elementos:
            self.celdas[self._c(lat, lon)].append((lat, lon, dato))

    @staticmethod
    def _c(lat: float, lon: float) -> tuple[int, int]:
        return (math.floor(lat / CELDA), math.floor(lon / CELDA))

    def cerca(self, lat: float, lon: float, radio_m: float):
        anillos = int(radio_m / 180) + 1
        ci, cj = self._c(lat, lon)
        for i in range(ci - anillos, ci + anillos + 1):
            for j in range(cj - anillos, cj + anillos + 1):
                yield from self.celdas.get((i, j), ())

    def mas_cercano(self, lat: float, lon: float, max_m: float = 5000) -> tuple[float, Any] | None:
        mejor = None
        radio = 400
        while radio <= max_m * 1.5:
            for la, lo, dato in self.cerca(lat, lon, radio):
                d = distancia_m(lat, lon, la, lo)
                if mejor is None or d < mejor[0]:
                    mejor = (d, dato)
            if mejor and mejor[0] <= radio:
                return mejor
            radio *= 2
        return mejor if mejor and mejor[0] <= max_m else None


def indice_pois(pois: dict[str, list]) -> dict[str, Indice]:
    return {cat: Indice((p[0], p[1], p[2] if len(p) > 2 else "") for p in lista)
            for cat, lista in pois.items() if cat in CATEGORIAS}


def indice_edificios(edificios: list) -> Indice:
    """Indexa cada edificio por su primer vértice (basta para radios de 150 m)."""
    return Indice((e[2][0][0], e[2][0][1], e) for e in edificios if e[2])


def cercania(lat: float, lon: float, indices: dict[str, Indice]) -> dict[str, Any]:
    out = {}
    for cat, ind in indices.items():
        r = ind.mas_cercano(lat, lon)
        out[f"dist_{cat}"] = round(r[0]) if r else None
        out[f"cerca_{cat}"] = r[1] if r else None
    return out


def sol_en_invierno(lat: float, lon: float, ind_edificios: Indice,
                    trayecto: list[tuple[float, float]] | None = None) -> dict[str, Any]:
    """Horas de sol directo el 21 de junio, a nivel calle y en pisos 3, 6 y 10."""
    trayecto = trayecto or sol.trayectoria(DIA_SOL, lat, lon, UTC_OFFSET_INVIERNO)
    cercanos, conocidos = [], 0
    for la, lo, (altura, conocida, verts) in ind_edificios.cerca(lat, lon, RADIO_M + 60):
        pol = [sol.a_metros(lat, lon, v[0], v[1]) for v in verts]
        dmin = min(math.hypot(x, y) for x, y in pol)
        if dmin > RADIO_M:
            continue
        if sol.dentro(0.0, 0.0, pol):
            continue           # el propio edificio del aviso no se tapa a sí mismo
        cercanos.append((altura, pol))
        conocidos += conocida
    horas_luz = round(len(trayecto) * 10 / 60, 1)
    out: dict[str, Any] = {"sol_horas_luz": horas_luz, "sol_edificios": len(cercanos),
                           "sol_calidad": round(conocidos / len(cercanos), 2) if cercanos else None}
    for clave, altura_obs in PISOS.items():
        out[f"sol_{clave}"] = sol.horas_de_sol(trayecto, sol.horizonte(cercanos, altura_obs))
    return out
