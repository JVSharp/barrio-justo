"""
Exporta la demo a un JSON para publicar el dashboard sin backend
(GitHub Pages). Lo corre el workflow de Pages antes del build.

    python scripts/exportar_estatico.py

Siempre usa la DEMO, nunca MongoDB: la demo pública no debe llevar datos
reales. Las cifras salen de las mismas funciones que responde la API, así
que el modo estático y el modo con API muestran exactamente lo mismo.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ["FUENTE_DATOS"] = "demo"          # antes de importar config
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))

import main  # noqa: E402

SALIDA = RAIZ / "comuna-frontend" / "public" / "demo" / "datos.json"

# Solo lo que usa el frontend; el resto del aviso no viaja.
CAMPOS = ("titulo", "comuna", "tipo_operacion", "tipo_inmueble", "precio_uf", "precio_clp",
          "superficie_m2", "dormitorios", "banos", "url", "uf_m2", "motivo_exclusion",
          "fecha_ultima_vista", "posicion", "dias_publicado", "cambio_precio_pct")


def main_() -> None:
    repo = main.obtener_repo()
    salud = main.salud(repo)
    if salud["fuente"] != "demo":
        sys.exit("Abortado: la exportación estática solo se hace con la demo.")

    # Igual que /propiedades antes de filtrar y ordenar: mismo orden de origen,
    # así los empates se resuelven igual en el navegador que en Python.
    refs = main.refs_de(repo)
    enriquecidos = [main.analisis.enriquecer(a, refs) for a in repo.todos({})]
    datos = {
        "salud": salud,
        "comunas": main.comunas(repo),
        "tipos_inmueble": main.tipos_inmueble(repo),
        "tipos_operacion": main.tipos_operacion(repo),
        "calidad": main.calidad(repo),
        "rentabilidad": main.rentabilidad(repo),
        "resumen": {
            f"{op}|{tipo}": main.resumen(repo, tipo_operacion=op, tipo_inmueble=tipo)
            for op in ("venta", "arriendo") for tipo in ("departamento", "casa")
        },
        # En el orden del repositorio (el mismo que usa la API antes de ordenar).
        "avisos": [{k: a.get(k) for k in CAMPOS} for a in enriquecidos],
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"✓ {SALIDA.relative_to(RAIZ)} · {len(datos['avisos'])} avisos · "
          f"{SALIDA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main_()
