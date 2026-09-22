"""
Calcula para cada aviso la distancia a lugares de interés y las horas de sol
del 21 de junio, con los datos de data/osm/ (ver descargar_osm.py).

    python scripts/enriquecer_geo.py                 # según FUENTE_DATOS (.env)
    FUENTE_DATOS=demo python scripts/enriquecer_geo.py
    python scripts/enriquecer_geo.py --todos         # en Mongo, recalcula también los ya hechos
    python scripts/enriquecer_geo.py --edificios-demo   # demo: sol con la ciudad ficticia

- Demo: escribe data/demo/geo.csv (una fila por URL). No toca avisos.csv, así
  que regenerar la demo no borra el cálculo (las coordenadas son las mismas).
- MongoDB: guarda los campos en cada aviso. Por defecto solo los que no los
  tienen todavía (el sol de invierno no cambia de una semana a otra).
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))

import config  # noqa: E402
import geo  # noqa: E402
import repositorio  # noqa: E402
import sol  # noqa: E402

OSM = RAIZ / "data" / "osm"
GEO_DEMO = RAIZ / "data" / "demo" / "geo.csv"
CENTRO = (-36.83, -73.05)   # la trayectoria del sol casi no cambia dentro de la región


def cargar(edificios_demo: bool = False):
    pois_p = OSM / "pois.json"
    edif_p = RAIZ / "data" / "demo" / "edificios_demo.json" if edificios_demo else OSM / "edificios.json"
    if not pois_p.exists():
        sys.exit("Falta data/osm/pois.json. Corre primero:  python scripts/descargar_osm.py")
    pois = geo.indice_pois(json.loads(pois_p.read_text(encoding="utf-8")))
    if edif_p.exists():
        edificios = geo.indice_edificios(json.loads(edif_p.read_text(encoding="utf-8")))
    else:
        print(f"! Sin {edif_p.relative_to(RAIZ)}: se calcula solo la cercanía, no el sol.")
        edificios = None
    return pois, edificios


def metricas(a: dict, pois, edificios, tray) -> dict:
    lat, lon = a.get("latitud"), a.get("longitud")
    out = geo.cercania(lat, lon, pois)
    if edificios is not None:
        out.update(geo.sol_en_invierno(lat, lon, edificios, tray))
    return out


def main() -> None:
    demo_edif = "--edificios-demo" in sys.argv
    pois, edificios = cargar(demo_edif)
    tray = sol.trayectoria(geo.DIA_SOL, *CENTRO, geo.UTC_OFFSET_INVIERNO)
    cfg = config.cargar()
    repo = repositorio.crear(cfg)
    if demo_edif and repo.fuente != "demo":
        sys.exit("--edificios-demo es solo para la demo: los avisos reales van con edificios reales.")
    avisos = [a for a in repo.todos({}) if a.get("latitud") is not None and a.get("longitud") is not None]
    todos = "--todos" in sys.argv
    if repo.fuente == "mongo" and not todos:
        avisos = [a for a in avisos if "sol_calle" not in a and "dist_biotren" not in a]
    print(f"{len(avisos)} avisos con coordenadas por procesar ({repo.fuente})")

    t0, filas = time.time(), []
    for i, a in enumerate(avisos, 1):
        m = metricas(a, pois, edificios, tray)
        if edificios is not None:
            m["sol_fuente"] = "demo" if demo_edif else "osm"
        if repo.fuente == "mongo":
            repo._col.update_one({"url": a["url"]}, {"$set": m})
        else:
            filas.append({"url": a["url"], **m})
        if i % 250 == 0:
            print(f"   {i}/{len(avisos)} · {time.time() - t0:.0f} s", flush=True)

    if repo.fuente == "demo" and filas:
        campos = ["url"] + sorted({k for f in filas for k in f} - {"url"})
        with GEO_DEMO.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
            w.writeheader()
            w.writerows(filas)
        print(f"✓ {GEO_DEMO.relative_to(RAIZ)}")
    print(f"Listo en {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
