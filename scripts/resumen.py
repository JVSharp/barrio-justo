"""
Imprime el análisis en la terminal, sin levantar la API ni el dashboard.

    python scripts/resumen.py                 # usa FUENTE_DATOS del .env
    FUENTE_DATOS=demo python scripts/resumen.py

Muestra: calidad (qué quedó fuera y por qué), y por cada operación × tipo,
la mediana, el rango p25–p75 y la UF/m² de cada comuna.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import analisis  # noqa: E402
import config  # noqa: E402
import repositorio  # noqa: E402


def f(v, d=0):
    return "—" if v is None else f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


repo = repositorio.crear(config.cargar())
avisos = repo.todos({})
cal = analisis.calidad(avisos)
print(f"Fuente: {repo.fuente} · {f(cal['total'])} avisos · {f(cal['excluidos'])} fuera del análisis")
for m in cal["por_motivo"]:
    print(f"   {m['cantidad']:>6}  {m['descripcion']}")

for op in ("venta", "arriendo"):
    d = 1 if op == "arriendo" else 0
    for tipo in ("departamento", "casa"):
        grupo = [a for a in avisos if a.get("tipo_operacion") == op and a.get("tipo_inmueble") == tipo]
        if not grupo:
            continue
        print(f"\n{tipo.upper()} EN {op.upper()}")
        print(f"   {'comuna':<22}{'n':>6}{'mediana UF':>13}{'p25–p75':>19}{'UF/m²':>9}{'fuera':>7}")
        for r in analisis.resumen_por(grupo, ("comuna",)):
            rango = f"{f(r.get('p25_uf'), d)} – {f(r.get('p75_uf'), d)}" if r.get("cantidad") else "—"
            print(f"   {r['comuna']:<22}{r.get('cantidad', 0):>6}{f(r.get('mediana_uf'), d):>13}"
                  f"{rango:>19}{f(r.get('mediana_uf_m2'), 2 if d else 1):>9}{r['excluidos']:>7}")
