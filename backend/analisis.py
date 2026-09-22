"""
Limpieza y estadística de avisos.

La versión anterior promediaba precios crudos, y un par de avisos mal
cargados bastaban para mover el promedio de una comuna completa (una venta
publicada como arriendo, un precio escrito en pesos en vez de UF). Acá:

1. Cada aviso pasa por reglas de plausibilidad explícitas. Los que fallan
   no se borran: quedan fuera del cálculo con un motivo legible, y la API
   los sigue mostrando marcados.
2. Se usa la mediana y el rango intercuartil (p25–p75) en vez del
   promedio, porque no se mueven con un solo valor extremo.
3. El precio por m² solo se calcula cuando la superficie es creíble.
"""

from __future__ import annotations

import re
from collections import defaultdict
from statistics import median
from typing import Any, Iterable

# Rangos plausibles, en UF. Son deliberadamente amplios: la idea es atrapar
# errores de carga, no opinar sobre qué propiedad está cara.
VENTA_MIN_UF = 300
VENTA_MAX_UF = 100_000
ARRIENDO_MIN_UF = 3
ARRIENDO_MAX_UF = 300          # sobre esto casi siempre es una venta mal clasificada
SUPERFICIE_MIN_M2 = 15
SUPERFICIE_MAX_M2 = 5_000

MOTIVOS = {
    "sin_precio": "Sin precio publicado",
    "venta_baja": f"Precio de venta bajo {VENTA_MIN_UF} UF (probable error de carga)",
    "venta_alta": f"Precio de venta sobre {VENTA_MAX_UF:,} UF".replace(",", "."),
    "arriendo_alto": f"Arriendo sobre {ARRIENDO_MAX_UF} UF: probable venta mal clasificada",
    "arriendo_bajo": f"Arriendo bajo {ARRIENDO_MIN_UF} UF",
    "duplicado": "Aviso duplicado (misma URL)",
}

_NUM = re.compile(r"(\d+(?:[.,]\d+)?)")


def numero(valor: Any) -> float | None:
    """'120 m²' → 120.0 · '3' → 3.0 · '' / None / 'n/a' → None."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    m = _NUM.search(str(valor))
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def superficie(aviso: dict) -> float | None:
    m2 = numero(aviso.get("superficie_m2"))
    if m2 is None or not (SUPERFICIE_MIN_M2 <= m2 <= SUPERFICIE_MAX_M2):
        return None
    return m2


def motivo_exclusion(aviso: dict) -> str | None:
    """Código del motivo por el que el aviso no entra al análisis, o None."""
    uf = numero(aviso.get("precio_uf"))
    if not uf or uf <= 0:
        return "sin_precio"
    op = aviso.get("tipo_operacion")
    if op == "venta":
        if uf < VENTA_MIN_UF:
            return "venta_baja"
        if uf > VENTA_MAX_UF:
            return "venta_alta"
    elif op == "arriendo":
        if uf > ARRIENDO_MAX_UF:
            return "arriendo_alto"
        if uf < ARRIENDO_MIN_UF:
            return "arriendo_bajo"
    return None


def limpiar(avisos: Iterable[dict]) -> tuple[list[dict], list[dict]]:
    """Separa (válidos, excluidos). Los excluidos llevan 'motivo'."""
    validos, excluidos, vistos = [], [], set()
    for a in avisos:
        url = a.get("url")
        if url and url in vistos:
            excluidos.append({**a, "motivo": "duplicado"})
            continue
        if url:
            vistos.add(url)
        m = motivo_exclusion(a)
        if m:
            excluidos.append({**a, "motivo": m})
        else:
            validos.append(a)
    return validos, excluidos


def percentil(valores: list[float], p: float) -> float:
    """Percentil con interpolación lineal (igual que numpy por defecto)."""
    if not valores:
        raise ValueError("lista vacía")
    s = sorted(valores)
    k = (len(s) - 1) * p
    i = int(k)
    if i + 1 >= len(s):
        return s[-1]
    return s[i] + (s[i + 1] - s[i]) * (k - i)


def estadisticas(avisos: list[dict]) -> dict[str, Any]:
    """Resumen robusto de un grupo de avisos ya limpios."""
    precios = [numero(a["precio_uf"]) for a in avisos]
    precios = [p for p in precios if p]
    por_m2 = []
    for a in avisos:
        m2 = superficie(a)
        uf = numero(a.get("precio_uf"))
        if m2 and uf:
            por_m2.append(uf / m2)
    if not precios:
        return {"cantidad": 0}
    return {
        "cantidad": len(precios),
        "mediana_uf": round(median(precios), 1),
        "p25_uf": round(percentil(precios, 0.25), 1),
        "p75_uf": round(percentil(precios, 0.75), 1),
        "mediana_uf_m2": round(median(por_m2), 2) if por_m2 else None,
        "con_superficie": len(por_m2),
    }


def resumen_por(avisos: Iterable[dict], claves: tuple[str, ...]) -> list[dict]:
    """Limpia y agrupa. Devuelve una fila por grupo con stats + excluidos."""
    validos, excluidos = limpiar(avisos)
    grupos: dict[tuple, list[dict]] = defaultdict(list)
    for a in validos:
        grupos[tuple(a.get(k) for k in claves)].append(a)
    fuera: dict[tuple, int] = defaultdict(int)
    for a in excluidos:
        fuera[tuple(a.get(k) for k in claves)] += 1

    filas = []
    for clave in set(grupos) | set(fuera):
        fila = dict(zip(claves, clave))
        fila.update(estadisticas(grupos.get(clave, [])))
        fila["excluidos"] = fuera.get(clave, 0)
        filas.append(fila)
    filas.sort(key=lambda f: (-(f.get("cantidad") or 0), str(f.get(claves[0]))))
    return filas


def calidad(avisos: Iterable[dict]) -> dict[str, Any]:
    validos, excluidos = limpiar(avisos)
    conteo: dict[str, int] = defaultdict(int)
    for a in excluidos:
        conteo[a["motivo"]] += 1
    total = len(validos) + len(excluidos)
    return {
        "total": total,
        "validos": len(validos),
        "excluidos": len(excluidos),
        "por_motivo": [
            {"motivo": m, "descripcion": MOTIVOS[m], "cantidad": n}
            for m, n in sorted(conteo.items(), key=lambda kv: -kv[1])
        ],
    }
