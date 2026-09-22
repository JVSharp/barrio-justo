"""
Scraper de PortalInmobiliario.

Usa el endpoint JSON que alimenta la vista de mapa del portal. Antes de
correrlo, revisa los términos de uso del sitio: esto es un proyecto de
aprendizaje, pide una página por segundo y no guarda datos personales.

Cambios respecto de la v1:
- La paginación antes agregaba `#N` a la URL. Todo lo que va después de `#`
  se queda en el cliente y nunca llega al servidor, así que cada "página"
  devolvía los mismos resultados. Ahora se usa el offset `_Desde_N` (el
  formato de las URLs de listado del portal), avanzando según cuántos
  avisos distintos llegaron, sin suponer un tamaño de página fijo.
- La lista de comunas sale de data/comunas_biobio.csv (antes faltaban
  algunas y 'Nacimiento' tenía mayúscula, así que esa URL no existía).
- Si no se puede obtener el valor de la UF, el precio en pesos queda vacío
  en vez de calcularse con un valor inventado.
"""

from __future__ import annotations

import time

import requests

import comunas as comunas_mod
from .base import BaseScraper

BASE = "https://www.portalinmobiliario.com/api"
MAX_PAGINAS = 40
PAUSA_S = 1.0


class PortalInmobiliarioScraper(BaseScraper):
    fuente = "PortalInmobiliario"
    operaciones = ("venta", "arriendo")
    tipos = ("casa", "departamento")

    def __init__(self, *args, comunas: list[str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        todas = comunas_mod.cargar()
        self.comunas = [c for c in todas if not comunas or c.slug in comunas]
        self.http = requests.Session()
        self.http.headers.update({"User-Agent": "comuna-dash/2.0 (proyecto educativo)",
                                  "Accept": "application/json"})

    def valor_uf(self) -> float | None:
        try:
            r = self.http.get("https://mindicador.cl/api/uf", timeout=8)
            r.raise_for_status()
            return float(r.json()["serie"][0]["valor"])
        except Exception as e:  # noqa: BLE001
            print(f"  ! No se pudo obtener la UF ({e}); precio_clp quedará vacío en avisos en UF")
            return None

    @staticmethod
    def _attr(attrs: list[dict], ids: tuple[str, ...]) -> str:
        for a in attrs:
            if a.get("id") in ids:
                return a.get("value_name") or a.get("value") or ""
        return ""

    def procesar(self, item: dict, comuna, operacion: str, tipo: str, uf: float | None) -> dict:
        precio = item.get("price") or {}
        monto = precio.get("amount") or 0
        if precio.get("currency_id") == "CLF":        # UF
            precio_uf = monto
            precio_clp = round(monto * uf) if uf else None
        else:                                           # CLP
            precio_clp = monto
            precio_uf = round(monto / uf, 1) if uf else None
        attrs = item.get("attributes") or []
        return {
            "id_aviso": item.get("id", ""),
            "tipo_operacion": operacion,
            "tipo_inmueble": tipo,
            "titulo": item.get("title", ""),
            "precio_uf": precio_uf,
            "precio_clp": precio_clp,
            "comuna": comuna.nombre,
            "provincia": comuna.provincia,
            "superficie_m2": self._attr(attrs, ("TOTAL_AREA", "COVERED_AREA")),
            "dormitorios": self._attr(attrs, ("BEDROOMS", "BEDROOMS_NUMBER")),
            "banos": self._attr(attrs, ("FULL_BATHROOMS", "BATHROOMS")),
            "url": item.get("permalink", ""),
        }

    def url(self, operacion: str, tipo: str, slug: str, desde: int = 1) -> str:
        offset = "" if desde <= 1 else f"_Desde_{desde}"
        return f"{BASE}/{operacion}/{tipo}/{slug}-biobio/{offset}_DisplayType_M"

    def scrape(self) -> None:
        uf = self.valor_uf()
        if uf:
            print(f"[{self.fuente}] UF de hoy: ${uf:,.0f}".replace(",", "."))
        for comuna in self.comunas:
            for op in self.operaciones:
                for tipo in self.tipos:
                    self._combinacion(comuna, op, tipo, uf)
        print(f"[{self.fuente}] Listo: {self.nuevos} nuevos, {self.actualizados} actualizados.")

    def _combinacion(self, comuna, op: str, tipo: str, uf: float | None) -> None:
        vistos: set[str] = set()
        for pagina in range(1, MAX_PAGINAS + 1):
            try:
                r = self.http.get(self.url(op, tipo, comuna.slug, len(vistos) + 1), timeout=15)
                r.raise_for_status()
                resultados = r.json().get("results") or []
            except Exception as e:  # noqa: BLE001
                print(f"  {comuna.nombre} · {tipo} · {op} · pág {pagina}: {e}")
                return
            ids = {i.get("id") for i in resultados}
            if not resultados or ids <= vistos:     # vacía o puro repetido: fin
                break
            vistos |= ids
            for item in resultados:
                self.guardar(self.procesar(item, comuna, op, tipo, uf))
            time.sleep(PAUSA_S)
        print(f"  {comuna.nombre:<22} {tipo:<12} {op:<8} {len(vistos):>5} avisos")
