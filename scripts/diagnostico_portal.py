"""
Muestra la FORMA de la respuesta del portal (no los datos) para una búsqueda.

    python scripts/diagnostico_portal.py [comuna] [operacion] [tipo]

Imprime código HTTP, tipo de contenido, las claves del JSON y las claves del
primer resultado. Sirve para saber si el endpoint cambió de formato.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import requests  # noqa: E402

from scrapers.portalinmobiliario import PortalInmobiliarioScraper  # noqa: E402

comuna, op, tipo = (sys.argv[1:] + ["concepcion", "venta", "departamento"][len(sys.argv[1:]):])[:3]
s = object.__new__(PortalInmobiliarioScraper)
url = s.url(op, tipo, comuna)
r = requests.get(url, timeout=20, headers={"User-Agent": "barrio-justo/2.0 (proyecto educativo)",
                                           "Accept": "application/json"})
print("URL         ", url)
print("HTTP        ", r.status_code, "→", r.url if r.url != url else "(sin redirección)")
print("Content-Type", r.headers.get("content-type"))
print("Tamaño      ", len(r.content), "bytes")
try:
    data = r.json()
except ValueError:
    print("No es JSON. Primeros 300 caracteres:\n", r.text[:300])
    sys.exit()


def forma(x, nivel=0):
    if isinstance(x, dict):
        return {k: forma(v, nivel + 1) if nivel < 1 else type(v).__name__ for k, v in list(x.items())[:25]}
    if isinstance(x, list):
        return f"lista[{len(x)}]"
    return type(x).__name__


print("Claves      ", json.dumps(forma(data), ensure_ascii=False, indent=2))
res = data.get("results") if isinstance(data, dict) else None
if isinstance(res, list) and res:
    print(f"results: {len(res)} elementos. Claves del primero:")
    print("  ", sorted(res[0].keys()) if isinstance(res[0], dict) else type(res[0]).__name__)

    # Estructura de la tarjeta, sin valores: solo nombres de claves y tipos.
    # Se muestran literales únicamente en campos estructurales ('type', 'id',
    # 'currency', 'state'), que dicen qué es cada pieza pero no son datos del aviso.
    VISIBLES = {"type", "currency", "currency_id", "state", "id"}

    def esqueleto(x, nivel=0, clave=""):
        if nivel > 9:
            return "…"
        if isinstance(x, dict):
            return {k: esqueleto(v, nivel + 1, k) for k, v in x.items()}
        if isinstance(x, list):
            if not x:
                return []
            if all(isinstance(e, dict) and "type" in e for e in x):   # componentes: todos distintos
                return [esqueleto(e, nivel + 1, clave) for e in x[:15]]
            return [esqueleto(x[0], nivel + 1, clave)] + ([f"…×{len(x)}"] if len(x) > 1 else [])
        if clave in VISIBLES and isinstance(x, str):
            return f"'{x[:30]}'"
        return type(x).__name__

    ids = [r.get("id") for r in res if isinstance(r, dict)]
    print(f"\nids distintos en esta página: {len(set(ids))} de {len(ids)}")
    print("formato de id (enmascarado):", {str(i)[:3] + "…" for i in ids[:5]})
    print("url_prefix del contexto:", "presente" if (data.get("polycard_context") or {}).get("url_prefix") else "no")
    print("\nEsqueleto de results[0]:")
    print(json.dumps(esqueleto(res[0]), ensure_ascii=False, indent=2))
    comps = ((res[0].get("polycard") or {}).get("components") or [])
    if comps:
        print("\nTipos de componente en la tarjeta:", [c.get("type") for c in comps])
