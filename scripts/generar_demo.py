"""
Genera data/demo/avisos.csv: avisos FICTICIOS para probar el dashboard.

Qué es real y qué no:
- La cantidad de avisos por comuna, tipo y operación sale del snapshot real
  de 2025 (data/snapshot_2025_resumen_por_comuna.csv).
- Los precios, superficies y títulos son inventados. Se generan alrededor
  de un precio por m² de referencia por comuna, con dispersión realista.
  NO sirven como análisis del mercado.
- Se agrega a propósito un ~4 % de avisos "sucios" (ventas publicadas como
  arriendo, precios en cero, duplicados) para que se vea la limpieza.
- Las URLs apuntan a example.invalid: ninguna lleva a un aviso real.

    python scripts/generar_demo.py
"""

from __future__ import annotations

import csv
import random
import unicodedata
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = RAIZ / "data" / "snapshot_2025_resumen_por_comuna.csv"
COMUNAS = RAIZ / "data" / "comunas_biobio.csv"
SALIDA = RAIZ / "data" / "demo" / "avisos.csv"

UF_CLP = 39_500          # valor fijo, solo para la demo
HOY = date(2026, 9, 1)   # fijo: la demo sale siempre igual

# UF/m² de referencia para departamentos en venta (inventado, orden de
# magnitud razonable). Casas: ×0.75. Arriendo: ~0,45 % mensual del valor.
REF_UF_M2 = {
    "concepcion": 62, "san-pedro-de-la-paz": 58, "chiguayante": 50,
    "hualpen": 44, "talcahuano": 42, "penco": 40, "tome": 36, "coronel": 34,
    "los-angeles": 42, "lota": 26, "hualqui": 28, "florida": 24,
    "santa-juana": 22, "cabrero": 24, "arauco": 26, "canete": 25,
    "negrete": 20, "santa-barbara": 21,
}
ARRIENDO_TASA = 0.0045
COLUMNAS = ["id_aviso", "fuente", "tipo_operacion", "tipo_inmueble", "titulo",
            "precio_uf", "precio_clp", "comuna", "provincia", "superficie_m2",
            "dormitorios", "banos", "url", "fecha_primera_vista", "fecha_ultima_vista"]


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return t.lower().strip().replace(" ", "-")


def superficie(tipo: str, rnd: random.Random) -> int:
    if tipo == "departamento":
        return int(rnd.triangular(32, 140, 62))
    return int(rnd.triangular(55, 320, 110))


def main() -> None:
    rnd = random.Random(2026)
    comunas = {r["slug"]: r for r in csv.DictReader(COMUNAS.open(encoding="utf-8"))}
    filas = []
    n = 0
    for s in csv.DictReader(SNAPSHOT.open(encoding="utf-8")):
        c = comunas[slug(s["comuna"])]
        tipo, op = s["tipo_inmueble"], s["tipo_operacion"]
        base = REF_UF_M2.get(c["slug"], 22) * (0.75 if tipo == "casa" else 1.0)
        for _ in range(int(s["cantidad"])):
            n += 1
            m2 = superficie(tipo, rnd)
            uf_m2 = base * rnd.lognormvariate(0, 0.22)
            precio = m2 * uf_m2 if op == "venta" else m2 * uf_m2 * ARRIENDO_TASA
            precio = round(precio, 1 if op == "arriendo" else 0)
            dorm = max(1, min(6, round(m2 / (28 if tipo == "departamento" else 35))))
            banos = max(1, min(4, round(dorm * 0.6)))

            # Ruido de carga deliberado, para ver la limpieza en acción.
            r = rnd.random()
            if r < 0.012 and op == "arriendo":
                precio = round(m2 * base * rnd.uniform(0.8, 1.2))    # venta publicada como arriendo
            elif r < 0.020:
                precio = 0                                           # sin precio
            elif r < 0.028 and op == "venta":
                precio = round(precio / 100)                         # cero de menos
            superficie_txt = f"{m2} m²" if rnd.random() > 0.18 else ""  # ~18 % sin superficie

            primera = HOY - timedelta(days=rnd.randint(0, 120))
            ultima = min(HOY, primera + timedelta(days=rnd.randint(0, 60)))
            tipo_txt = "Depto" if tipo == "departamento" else "Casa"
            filas.append({
                "id_aviso": f"DEMO-{n:05d}",
                "fuente": "demo",
                "tipo_operacion": op,
                "tipo_inmueble": tipo,
                "titulo": f"{tipo_txt} {dorm}D {banos}B en {c['nombre']}",
                "precio_uf": precio,
                "precio_clp": round(precio * UF_CLP),
                "comuna": c["nombre"],
                "provincia": c["provincia"],
                "superficie_m2": superficie_txt,
                "dormitorios": dorm,
                "banos": banos,
                "url": f"https://example.invalid/demo/{n:05d}",
                "fecha_primera_vista": primera.isoformat(),
                "fecha_ultima_vista": ultima.isoformat(),
            })

    # Un puñado de duplicados exactos (el mismo aviso visto dos veces).
    for f in rnd.sample(filas, 25):
        filas.append(dict(f))
    rnd.shuffle(filas)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"Demo lista: {len(filas)} avisos ficticios en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
