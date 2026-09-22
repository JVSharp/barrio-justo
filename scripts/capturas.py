"""
Toma las capturas del dashboard para el README, con los datos de demo.

Levanta la API y el frontend, abre un navegador headless y guarda las
imágenes en docs/img/. Después apaga todo.

Requisitos (una sola vez):
    pip install -r backend/requirements-dev.txt
    python -m playwright install chromium
    (cd comuna-frontend && npm install)

Uso:
    python scripts/capturas.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

RAIZ = Path(__file__).resolve().parent.parent
FRONT = RAIZ / "comuna-frontend"
DESTINO = RAIZ / "docs" / "img"
API_PUERTO, WEB_PUERTO = 8765, 4173
NPM = "npm.cmd" if os.name == "nt" else "npm"
NPX = "npx.cmd" if os.name == "nt" else "npx"

CAPTURAS = [
    # archivo, hash de la vista, alto de la ventana
    ("dashboard-mercado.png", "mercado", 1500),
    ("dashboard-avisos.png", "avisos", 1100),
    ("dashboard-mapa.png", "mapa", 900),
]
# El mapa baja teselas de OpenFreeMap: necesita más tiempo que el resto.
ESPERA_MS = {"mapa": 6000}


def esperar(url: str, segundos: int = 60) -> None:
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            with urlopen(url, timeout=2):
                return
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    sys.exit(f"No respondió {url}")


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Falta Playwright:  pip install playwright && python -m playwright install chromium")
    if not (RAIZ / "data" / "demo" / "avisos.csv").exists():
        subprocess.run([sys.executable, str(RAIZ / "scripts" / "generar_demo.py")], check=True)

    print("Compilando el frontend…")
    env_build = {**os.environ, "VITE_API_URL": f"http://127.0.0.1:{API_PUERTO}"}
    subprocess.run([NPM, "run", "build"], cwd=FRONT, env=env_build, check=True,
                   stdout=subprocess.DEVNULL)

    env_api = {**os.environ, "FUENTE_DATOS": "demo"}
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", str(API_PUERTO), "--log-level", "warning"],
        cwd=RAIZ / "backend", env=env_api)
    # --host explícito: en macOS "localhost" resuelve a IPv6 (::1) y vite
    # preview no queda escuchando en 127.0.0.1, que es donde lo esperamos.
    web = subprocess.Popen([NPX, "vite", "preview", "--host", "127.0.0.1",
                            "--port", str(WEB_PUERTO), "--strictPort"],
                           cwd=FRONT, stdout=subprocess.DEVNULL)
    try:
        esperar(f"http://127.0.0.1:{API_PUERTO}/salud")
        esperar(f"http://127.0.0.1:{WEB_PUERTO}/")
        DESTINO.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            nav = p.chromium.launch()
            for archivo, vista, alto in CAPTURAS:
                pag = nav.new_page(viewport={"width": 1280, "height": alto}, device_scale_factor=2)
                pag.goto(f"http://127.0.0.1:{WEB_PUERTO}/#{vista}", wait_until="networkidle")
                pag.wait_for_timeout(ESPERA_MS.get(vista, 800))
                pag.screenshot(path=str(DESTINO / archivo))
                pag.close()
                print(f"  ✓ docs/img/{archivo}")
            nav.close()
    finally:
        for proc in (api, web):
            proc.terminate()
    print("Listo. Revisa las imágenes antes de hacer commit.")


if __name__ == "__main__":
    main()
