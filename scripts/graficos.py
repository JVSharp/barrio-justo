"""
Genera los gráficos del README en docs/img/.

    python scripts/graficos.py                  # con la fuente de .env (demo por defecto)
    FUENTE_DATOS=mongo python scripts/graficos.py

Cada gráfico indica en el pie de dónde salen los datos, para que nunca se
confunda la demo con una medición real.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import analisis  # noqa: E402
import config  # noqa: E402
import repositorio  # noqa: E402

SALIDA = RAIZ / "docs" / "img"
TEAL, TEAL_CLARO, GRIS, TEXTO = "#0f766e", "#99cfc9", "#a8a29e", "#292524"
MIN_MUESTRA = 10


def slug(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return t.lower().strip().replace(" ", "-")


with (RAIZ / "data" / "comunas_biobio.csv").open(encoding="utf-8") as _f:
    NOMBRES = {r["slug"]: r["nombre"] for r in csv.DictReader(_f)}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10.5, "axes.edgecolor": "#d6d3d1",
    "axes.labelcolor": TEXTO, "xtick.color": "#57534e", "ytick.color": TEXTO,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100,
})


def pie(fig, texto: str) -> None:
    fig.text(0.01, 0.012, texto, fontsize=8.5, color="#78716c", ha="left")


def fmt(n: float, d: int = 0) -> str:
    return f"{n:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def uf_m2_por_comuna(avisos: list[dict], origen: str) -> Path:
    deptos = [a for a in avisos if a.get("tipo_operacion") == "venta"
              and a.get("tipo_inmueble") == "departamento"]
    validos, _ = analisis.limpiar(deptos)
    por_comuna: dict[str, list[float]] = defaultdict(list)
    for a in validos:
        m2 = analisis.superficie(a)
        if m2:
            por_comuna[a["comuna"]].append(analisis.numero(a["precio_uf"]) / m2)
    filas = sorted(
        ((c, analisis.percentil(v, .5), analisis.percentil(v, .25), analisis.percentil(v, .75), len(v))
         for c, v in por_comuna.items() if len(v) >= MIN_MUESTRA),
        key=lambda f: f[1],
    )
    fig, ax = plt.subplots(figsize=(10, 0.46 * len(filas) + 1.6))
    y = range(len(filas))
    ax.hlines(y, [f[2] for f in filas], [f[3] for f in filas], color=TEAL_CLARO, lw=7, zorder=1)
    ax.scatter([f[1] for f in filas], y, color=TEAL, s=46, zorder=2)
    for i, f in enumerate(filas):
        ax.text(f[3] + 1, i, f"{fmt(f[1], 1)}  (n={f[4]})", va="center", fontsize=9.5, color="#44403c")
    ax.set_yticks(list(y), [f[0] for f in filas])
    ax.set_xlabel("UF por m²  ·  punto = mediana, barra = rango típico (p25–p75)")
    ax.set_title("Departamentos en venta: precio por m² según comuna", loc="left",
                 fontsize=13, fontweight="bold", color=TEXTO, pad=12)
    ax.set_xlim(left=0, right=max(f[3] for f in filas) * 1.22)
    ax.grid(axis="x", color="#f0efed")
    pie(fig, origen)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return guardar(fig, "uf-m2-por-comuna.png")


def promedio_vs_mediana(avisos: list[dict], origen: str) -> Path:
    """Por qué el análisis usa mediana y limpieza: el promedio crudo se va lejos."""
    casas = [a for a in avisos if a.get("tipo_operacion") == "venta" and a.get("tipo_inmueble") == "casa"]
    crudo: dict[str, list[float]] = defaultdict(list)
    for a in casas:
        v = analisis.numero(a.get("precio_uf"))
        if v:
            crudo[a["comuna"]].append(v)
    validos, _ = analisis.limpiar(casas)
    limpio: dict[str, list[float]] = defaultdict(list)
    for a in validos:
        limpio[a["comuna"]].append(analisis.numero(a["precio_uf"]))
    comunas = sorted((c for c in limpio if len(limpio[c]) >= 40),
                     key=lambda c: -analisis.percentil(limpio[c], .5))[:8]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = range(len(comunas))
    w = 0.38
    ax.bar([i - w / 2 for i in x], [mean(crudo[c]) for c in comunas], w, color=GRIS, label="Promedio de los datos crudos")
    ax.bar([i + w / 2 for i in x], [analisis.percentil(limpio[c], .5) for c in comunas], w, color=TEAL,
           label="Mediana después de limpiar")
    ax.set_xticks(list(x), comunas, rotation=20, ha="right")
    ax.set_ylabel("UF")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: fmt(v)))
    ax.set_title("Casas en venta: promedio de datos crudos vs. mediana limpia", loc="left", fontsize=13,
                 fontweight="bold", color=TEXTO, pad=12)
    ax.legend(frameon=False, loc="upper right")
    ax.grid(axis="y", color="#f0efed")
    ax.set_axisbelow(True)
    pie(fig, origen)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return guardar(fig, "promedio-vs-mediana.png")


def avisos_por_comuna_snapshot() -> Path:
    """Este sí es real: conteo de avisos del snapshot de scraping de 2025."""
    conteo: dict[str, int] = defaultdict(int)
    with (RAIZ / "data" / "snapshot_2025_resumen_por_comuna.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            conteo[NOMBRES.get(slug(r["comuna"]), r["comuna"])] += int(r["cantidad"])
    filas = sorted(conteo.items(), key=lambda kv: kv[1])[-15:]
    fig, ax = plt.subplots(figsize=(10, 0.4 * len(filas) + 1.5))
    ax.barh([c for c, _ in filas], [n for _, n in filas], color=TEAL, height=0.62)
    for i, (_, n) in enumerate(filas):
        ax.text(n + 8, i, fmt(n), va="center", fontsize=9.5, color="#44403c")
    ax.set_title("Avisos capturados por comuna", loc="left", fontsize=13, fontweight="bold",
                 color=TEXTO, pad=12)
    ax.set_xlabel("avisos (venta y arriendo, casas y departamentos)")
    ax.grid(axis="x", color="#f0efed")
    ax.set_axisbelow(True)
    pie(fig, "Fuente: scraping real de PortalInmobiliario, snapshot de 2025 (las 15 comunas con más avisos).")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return guardar(fig, "avisos-por-comuna.png")


def guardar(fig, nombre: str) -> Path:
    SALIDA.mkdir(parents=True, exist_ok=True)
    p = SALIDA / nombre
    fig.savefig(p, dpi=160, facecolor="white")
    plt.close(fig)
    return p


def main() -> None:
    cfg = config.cargar()
    repo = repositorio.crear(cfg)
    avisos = repo.todos({})
    origen = ("Datos de demostración: cantidades reales por comuna (snapshot 2025), precios y superficies ficticios."
              if repo.fuente == "demo" else "Fuente: avisos de PortalInmobiliario guardados por el scraper.")
    for p in (uf_m2_por_comuna(avisos, origen), promedio_vs_mediana(avisos, origen),
              avisos_por_comuna_snapshot()):
        print("  ✓", p.relative_to(RAIZ))


if __name__ == "__main__":
    main()
