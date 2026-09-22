"""
Edificios FICTICIOS para calcular el sol de la demo.

La demo tiene coordenadas inventadas, así que calcular su sol con los
edificios reales de OpenStreetMap no tendría sentido. Este script arma una
"ciudad de demostración" alrededor de los avisos: manzanas de ~100 m con
calles entremedio, torres más probables cerca del centro de cada comuna y
casas hacia los bordes.

El cálculo del sol que se hace después (enriquecer_geo.py) es el real; lo
único inventado son estos edificios.

    python scripts/generar_edificios_demo.py
    python scripts/enriquecer_geo.py --edificios-demo
"""

from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from generar_demo import CENTROS  # noqa: E402  (mismos centros que las coordenadas)

AVISOS = RAIZ / "data" / "demo" / "avisos.csv"
SALIDA = RAIZ / "data" / "demo" / "edificios_demo.json"
MANZANA_M = 110           # distancia entre centros de manzana (incluye la calle)
LADO_M = 88               # lado construido de la manzana; el resto es calle
M_LAT = 110_540.0


def m_lon(lat: float) -> float:
    return 111_320.0 * math.cos(math.radians(lat))


def main() -> None:
    rnd = random.Random(2126)
    # Manzanas que tienen algún aviso a menos de ~200 m.
    manzanas: set[tuple[int, int]] = set()
    with AVISOS.open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            try:
                lat, lon = float(fila["latitud"]), float(fila["longitud"])
            except (KeyError, ValueError):
                continue
            i, j = round(lat * M_LAT / MANZANA_M), round(lon * m_lon(lat) / MANZANA_M)
            for di in range(-2, 3):
                for dj in range(-2, 3):
                    manzanas.add((i + di, j + dj))

    centros = [(la, lo, d) for la, lo, d in CENTROS.values()]
    edificios = []
    for i, j in manzanas:
        clat = i * MANZANA_M / M_LAT
        clon = j * MANZANA_M / m_lon(clat)
        # Qué tan "centro" es esta manzana: 1 en el centro de su comuna, ~0 lejos.
        cercania = max(math.exp(-(((clat - la) ** 2 + (clon - lo) ** 2) ** 0.5) / (d * 1.2)) for la, lo, d in centros)
        n = rnd.randint(3, 6)
        ancho = LADO_M / n
        for k in range(n):
            # Frente de edificios a lo largo de la manzana, con patio atrás.
            x0 = -LADO_M / 2 + k * ancho + rnd.uniform(1, 3)
            w = ancho - rnd.uniform(2, 6)
            fondo = rnd.uniform(18, 40) if rnd.random() < 0.6 else LADO_M * 0.9
            lado_norte = rnd.random() < 0.5
            y0 = (LADO_M / 2 - fondo) if lado_norte else -LADO_M / 2
            torre = rnd.random() < 0.45 * cercania ** 1.5
            h = rnd.uniform(30, 75) if torre else (rnd.uniform(9, 16) if rnd.random() < 0.4 * cercania else rnd.uniform(5, 8))
            conocida = 1 if rnd.random() < 0.7 else 0
            verts = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + fondo), (x0, y0 + fondo)]
            edificios.append([round(h, 1), conocida,
                              [[round(clat + y / M_LAT, 6), round(clon + x / m_lon(clat), 6)] for x, y in verts]])

    SALIDA.write_text(json.dumps(edificios, separators=(",", ":")), encoding="utf-8")
    torres = sum(1 for e in edificios if e[0] >= 30)
    print(f"✓ {SALIDA.relative_to(RAIZ)} · {len(edificios)} edificios ficticios ({torres} torres) "
          f"en {len(manzanas)} manzanas")


if __name__ == "__main__":
    main()
