"""
Descarga de OpenStreetMap los lugares de interés y los edificios de las
zonas urbanas del Biobío, vía la API pública de Overpass.

    python scripts/descargar_osm.py              # lugares + edificios
    python scripts/descargar_osm.py --solo-pois  # solo lugares (rápido)
    python scripts/descargar_osm.py --pois       # vuelve a bajar los lugares

Si se corta (Overpass suele saturarse), vuelve a correrlo: las teselas ya
descargadas quedan en data/osm/teselas/ y no se piden de nuevo.

Salida:
    data/osm/pois.json        (liviano; se versiona)
    data/osm/edificios.json   (pesado; queda fuera de git)

Datos © colaboradores de OpenStreetMap, licencia ODbL.
Overpass es un servicio compartido y gratuito: el script pide de a un
recuadro por vez, espera entre pedidos y se identifica. Corre una vez y
reutiliza los archivos; no hace falta bajarlos en cada corrida del scraper.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "osm"
# Servidores públicos de Overpass: si uno está saturado se prueba el siguiente.
SERVIDORES = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
CACHE = SALIDA / "teselas"          # una respuesta por tesela: permite retomar si se corta
PAUSA_S = 4
UA = {"User-Agent": "barrio-justo/5.0 (proyecto educativo; github.com/JVSharp/barrio-justo)"}

# (sur, oeste, norte, este) de las zonas urbanas con más avisos.
ZONAS = {
    "gran_concepcion": (-37.12, -73.20, -36.60, -72.90),
    "los_angeles": (-37.52, -72.42, -37.42, -72.30),
}
TESELA = 0.04   # grados: los edificios se piden en recuadros chicos para no saturar Overpass

CONSULTA_POIS = """
[out:json][timeout:180];
(
  nwr["railway"~"^(station|halt)$"]({b});
  nwr["amenity"~"^(bus_station)$"]({b});
  nwr["amenity"~"^(university|college)$"]({b});
  nwr["amenity"="school"]({b});
  nwr["amenity"~"^(hospital|clinic)$"]({b});
  nwr["shop"="supermarket"]({b});
  nwr["leisure"~"^(park|garden)$"]["access"!="private"]({b});
);
out center tags;
"""

CONSULTA_EDIFICIOS = """
[out:json][timeout:180];
way["building"]({b});
out tags geom;
"""


def categoria(tags: dict) -> str | None:
    if tags.get("railway") in ("station", "halt") or tags.get("amenity") == "bus_station":
        return "biotren"
    a = tags.get("amenity")
    if a in ("university", "college"):
        return "universidad"
    if a == "school":
        return "colegio"
    if a in ("hospital", "clinic"):
        return "salud"
    if tags.get("shop") == "supermarket":
        return "supermercado"
    if tags.get("leisure") in ("park", "garden"):
        return "parque"
    return None


_NUM = re.compile(r"(\d+(?:[.,]\d+)?)")


def altura(tags: dict) -> tuple[float, int]:
    """(altura en m, 1 si viene de un dato explícito / 0 si es supuesta)."""
    for clave in ("height", "building:height"):
        m = _NUM.search(tags.get(clave, ""))
        if m:
            return float(m.group(1).replace(",", ".")), 1
    m = _NUM.search(tags.get("building:levels", ""))
    if m:
        return float(m.group(1).replace(",", ".")) * 3.0 + 1.0, 1
    return 6.0, 0      # sin dato: 2 pisos


def pedir(consulta: str, bbox: tuple[float, float, float, float]) -> list[dict]:
    """Pide a Overpass con reintentos: respeta Retry-After (429) y rota servidor."""
    b = ",".join(f"{v:.5f}" for v in bbox)
    for intento in range(10):
        url = SERVIDORES[intento % len(SERVIDORES)]
        try:
            r = requests.post(url, data={"data": consulta.format(b=b)}, headers=UA, timeout=240)
            if r.status_code == 200:
                return r.json().get("elements", [])
            estado = r.status_code
            espera = int(r.headers.get("Retry-After", 0)) or min(15 * (intento + 1), 120)
        except (requests.RequestException, ValueError) as e:
            estado, espera = type(e).__name__, min(15 * (intento + 1), 120)
        host = url.split("/")[2]
        print(f"   {host} respondió {estado}; reintento en {espera} s", flush=True)
        time.sleep(espera)
    raise RuntimeError(f"Overpass no respondió para {bbox} (lo ya descargado quedó guardado)")


def coordenadas_de_avisos() -> list[tuple[float, float]]:
    """Coordenadas de la demo y, si está configurado, de MongoDB."""
    import csv
    import os

    puntos = []
    demo = RAIZ / "data" / "demo" / "avisos.csv"
    if demo.exists():
        with demo.open(encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                try:
                    puntos.append((float(fila["latitud"]), float(fila["longitud"])))
                except (KeyError, TypeError, ValueError):
                    pass
    if os.getenv("FUENTE_DATOS", "").lower() == "mongo" or (RAIZ / ".env").exists():
        try:
            sys.path.insert(0, str(RAIZ / "backend"))
            import config
            from pymongo import MongoClient

            cfg = config.cargar()
            if cfg.fuente == "mongo":
                col = MongoClient(cfg.mongo_uri, serverSelectionTimeoutMS=2000)[cfg.mongo_db][cfg.mongo_coleccion]
                for d in col.find({"latitud": {"$ne": None}}, {"latitud": 1, "longitud": 1, "_id": 0}):
                    if d.get("latitud") is not None and d.get("longitud") is not None:
                        puntos.append((float(d["latitud"]), float(d["longitud"])))
        except Exception as e:  # noqa: BLE001 — sin Mongo, basta la demo
            print(f"   (MongoDB no disponible: {type(e).__name__}; se usan solo las coordenadas de la demo)")
    return puntos


def con_avisos(t, puntos, margen=0.002) -> bool:
    """¿Hay algún aviso dentro de la tesela o a menos de ~200 m de su borde?"""
    s, w, n, e = t
    return any(s - margen <= la <= n + margen and w - margen <= lo <= e + margen for la, lo in puntos)


def teselas(bbox):
    s, w, n, e = bbox
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            yield (lat, lon, min(lat + TESELA, n), min(lon + TESELA, e))
            lon += TESELA
        lat += TESELA


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    pois: dict[str, list] = {}
    if (SALIDA / "pois.json").exists() and "--pois" not in sys.argv:
        pois = json.loads((SALIDA / "pois.json").read_text(encoding="utf-8"))
        print("Lugares de interés: ya descargados (usa --pois para bajarlos de nuevo)")
    for nombre, bbox in ({} if pois else ZONAS).items():
        print(f"Lugares de interés · {nombre}")
        for el in pedir(CONSULTA_POIS, bbox):
            tags = el.get("tags", {})
            cat = categoria(tags)
            lat = el.get("lat") or (el.get("center") or {}).get("lat")
            lon = el.get("lon") or (el.get("center") or {}).get("lon")
            if cat and lat and lon:
                pois.setdefault(cat, []).append([round(lat, 6), round(lon, 6), tags.get("name", "")])
        time.sleep(3)
    (SALIDA / "pois.json").write_text(json.dumps(pois, ensure_ascii=False), encoding="utf-8")
    print("✓ data/osm/pois.json · " + ", ".join(f"{k}: {len(v)}" for k, v in sorted(pois.items())))

    if "--solo-pois" in sys.argv:
        return

    CACHE.mkdir(parents=True, exist_ok=True)
    puntos = coordenadas_de_avisos()
    print(f"Edificios · solo teselas con avisos cerca ({len(puntos)} avisos con coordenadas)")
    edificios, conocidos = [], 0
    for nombre, bbox in ZONAS.items():
        lista = [t for t in teselas(bbox) if con_avisos(t, puntos)]
        for i, t in enumerate(lista, 1):
            archivo = CACHE / f"{nombre}_{t[0]:.3f}_{t[1]:.3f}.json"
            if archivo.exists():
                els = json.loads(archivo.read_text(encoding="utf-8"))
                origen = "guardada"
            else:
                els = pedir(CONSULTA_EDIFICIOS, t)
                archivo.write_text(json.dumps(els, separators=(",", ":")), encoding="utf-8")
                origen = "descargada"
                time.sleep(PAUSA_S)
            for el in els:
                geom = el.get("geometry") or []
                if len(geom) < 3:
                    continue
                h, conocida = altura(el.get("tags", {}))
                conocidos += conocida
                edificios.append([round(h, 1), conocida,
                                  [[round(p["lat"], 6), round(p["lon"], 6)] for p in geom[:-1]]])
            print(f"   {nombre} {i}/{len(lista)} · {len(els)} edificios ({origen})", flush=True)
    (SALIDA / "edificios.json").write_text(json.dumps(edificios, separators=(",", ":")), encoding="utf-8")
    pct = 100 * conocidos / max(1, len(edificios))
    print(f"✓ data/osm/edificios.json · {len(edificios)} edificios · {pct:.0f} % con altura conocida")


if __name__ == "__main__":
    main()
