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
    "proyecto": "Proyecto nuevo: publica precio 'desde', no el de una unidad",
}

_NUM = re.compile(r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)")


def numero(valor: Any) -> float | None:
    """'120 m²' → 120.0 · '1.200 m²' → 1200.0 · '45,5' → 45.5 · '' / None → None."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    m = _NUM.search(str(valor))
    if not m:
        return None
    t = m.group(1)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", t):   # "1.200" o "1.200,5": punto de miles
        t = t.replace(".", "")
    return float(t.replace(",", "."))


def superficie(aviso: dict) -> float | None:
    m2 = numero(aviso.get("superficie_m2"))
    if m2 is None or not (SUPERFICIE_MIN_M2 <= m2 <= SUPERFICIE_MAX_M2):
        return None
    return m2


def motivo_exclusion(aviso: dict) -> str | None:
    """Código del motivo por el que el aviso no entra al análisis, o None."""
    if str(aviso.get("es_proyecto")).lower() in ("true", "1"):
        return "proyecto"
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


# ---------------------------------------------------------------------------
# v3 · ¿Este aviso está caro? · rentabilidad bruta · historial de precio
# ---------------------------------------------------------------------------

MIN_REFERENCIA = 10   # avisos con superficie necesarios para opinar sobre un grupo

Clave = tuple  # (comuna, tipo_operacion, tipo_inmueble)


def uf_m2(aviso: dict) -> float | None:
    m2, uf = superficie(aviso), numero(aviso.get("precio_uf"))
    return uf / m2 if (m2 and uf) else None


def clave(aviso: dict) -> Clave:
    return (aviso.get("comuna"), aviso.get("tipo_operacion"), aviso.get("tipo_inmueble"))


def referencias(avisos: Iterable[dict]) -> dict[Clave, dict[str, float]]:
    """p25 / mediana / p75 de UF/m² por grupo, solo con avisos válidos y
    solo para grupos con al menos MIN_REFERENCIA avisos con superficie."""
    validos, _ = limpiar(avisos)
    por_grupo: dict[Clave, list[float]] = defaultdict(list)
    for a in validos:
        v = uf_m2(a)
        if v:
            por_grupo[clave(a)].append(v)
    return {
        k: {"p25": percentil(v, .25), "mediana": percentil(v, .5), "p75": percentil(v, .75), "n": len(v)}
        for k, v in por_grupo.items() if len(v) >= MIN_REFERENCIA
    }


POSICIONES = {
    "bajo": "Bajo el mercado",
    "en_rango": "En rango",
    "sobre": "Sobre el mercado",
    "sin_referencia": "Sin referencia",
}


def posicion(aviso: dict, refs: dict[Clave, dict[str, float]]) -> dict[str, Any]:
    """Dónde cae la UF/m² del aviso respecto de su comuna.

    bajo = bajo el p25 · en_rango = entre p25 y p75 · sobre = sobre el p75.
    Sin superficie, excluido del análisis o grupo chico → sin_referencia.
    """
    ref = refs.get(clave(aviso))
    v = uf_m2(aviso)
    if not ref or v is None or motivo_exclusion(aviso):
        return {"codigo": "sin_referencia", "etiqueta": POSICIONES["sin_referencia"], "vs_mediana_pct": None}
    codigo = "bajo" if v < ref["p25"] else "sobre" if v > ref["p75"] else "en_rango"
    return {
        "codigo": codigo,
        "etiqueta": POSICIONES[codigo],
        "vs_mediana_pct": round((v / ref["mediana"] - 1) * 100),
    }


def rentabilidad(avisos: Iterable[dict]) -> list[dict[str, Any]]:
    """Rentabilidad bruta anual estimada por comuna y tipo:
    (mediana UF/m² de arriendo mensual × 12) / mediana UF/m² de venta.

    Es una aproximación gruesa: no descuenta gastos, contribuciones ni
    vacancia, y compara medianas de avisos distintos.
    """
    refs = referencias(avisos)
    filas = []
    for (comuna, op, tipo), venta in refs.items():
        if op != "venta":
            continue
        arriendo = refs.get((comuna, "arriendo", tipo))
        if not arriendo:
            continue
        filas.append({
            "comuna": comuna,
            "tipo_inmueble": tipo,
            "venta_uf_m2": round(venta["mediana"], 1),
            "arriendo_uf_m2_mes": round(arriendo["mediana"], 3),
            "rentabilidad_bruta_pct": round(arriendo["mediana"] * 12 / venta["mediana"] * 100, 1),
            "n_venta": venta["n"],
            "n_arriendo": arriendo["n"],
        })
    filas.sort(key=lambda f: -f["rentabilidad_bruta_pct"])
    return filas


def _fecha(s: Any):
    from datetime import date
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def historial(aviso: dict) -> dict[str, Any]:
    """Días publicado y cambio de precio desde la primera vez que se vio."""
    ini, fin = _fecha(aviso.get("fecha_primera_vista")), _fecha(aviso.get("fecha_ultima_vista"))
    dias = (fin - ini).days if (ini and fin and fin >= ini) else None
    puntos = aviso.get("historial_precios") or []
    if isinstance(puntos, str):          # demo en CSV: "2026-06-01:3200|2026-08-01:3050"
        puntos = [{"fecha": p.split(":")[0], "precio_uf": numero(p.split(":")[1])}
                  for p in puntos.split("|") if ":" in p]
    cambio = None
    if puntos:
        primero = numero(puntos[0].get("precio_uf"))
        actual = numero(aviso.get("precio_uf"))
        if primero and actual and primero != actual:
            cambio = round((actual / primero - 1) * 100, 1)
    return {"dias_publicado": dias, "cambio_precio_pct": cambio, "cambios_de_precio": max(0, len(puntos) - 1)}


def enriquecer(aviso: dict, refs: dict[Clave, dict[str, float]]) -> dict[str, Any]:
    """Lo que la API agrega a cada aviso: UF/m², motivo de exclusión,
    posición frente a su comuna e historial. Lo usan la API y la demo estática."""
    m = motivo_exclusion(aviso)
    v = uf_m2(aviso)
    return {
        **{k: val for k, val in aviso.items() if k != "_id"},
        "uf_m2": round(v, 2) if v else None,
        "motivo_exclusion": MOTIVOS[m] if m else None,
        "posicion": posicion(aviso, refs),
        **historial(aviso),
    }


# ---------------------------------------------------------------------------
# v4 · Mapa: celdas de ~500 m con la mediana de UF/m²
# ---------------------------------------------------------------------------

TAMANO_CELDA = 0.005      # grados (~550 m × 450 m a la latitud de Concepción)
MIN_CELDA = 3             # una celda con 1-2 avisos no es "el precio de la zona"
# Caja generosa alrededor de la Región del Biobío: coordenadas fuera de esto
# son errores de geocodificación del portal, no avisos en otra parte.
CAJA_BIOBIO = (-38.6, -36.3, -74.0, -71.0)   # lat mín, lat máx, lon mín, lon máx


def coordenada(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def celdas(avisos: Iterable[dict], tamano: float = TAMANO_CELDA, minimo: int = MIN_CELDA) -> dict[str, Any]:
    """Agrupa los avisos válidos con coordenadas y superficie en una grilla
    lat/lon, y devuelve una fila por celda con su mediana de UF/m²."""
    import math

    validos, _ = limpiar(avisos)
    lat_min, lat_max, lon_min, lon_max = CAJA_BIOBIO
    grupos: dict[tuple[int, int], list[tuple[float, str]]] = defaultdict(list)
    con_coord = 0
    for a in validos:
        lat, lon, v = coordenada(a.get("latitud")), coordenada(a.get("longitud")), uf_m2(a)
        if lat is None or lon is None or not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            continue
        con_coord += 1
        if v:
            grupos[(math.floor(lat / tamano), math.floor(lon / tamano))].append((v, a.get("comuna") or ""))

    filas = []
    for (i, j), vals in grupos.items():
        if len(vals) < minimo:
            continue
        precios = [v for v, _ in vals]
        comunas = [c for _, c in vals]
        filas.append({
            "lat": round((i + 0.5) * tamano, 5),
            "lon": round((j + 0.5) * tamano, 5),
            "n": len(vals),
            "mediana_uf_m2": round(percentil(precios, .5), 2),
            "p25_uf_m2": round(percentil(precios, .25), 2),
            "p75_uf_m2": round(percentil(precios, .75), 2),
            "comuna": max(set(comunas), key=comunas.count),
        })
    filas.sort(key=lambda f: -f["n"])
    return {"tamano_grados": tamano, "minimo_por_celda": minimo,
            "avisos_validos": len(validos), "avisos_con_coordenadas": con_coord, "celdas": filas}
