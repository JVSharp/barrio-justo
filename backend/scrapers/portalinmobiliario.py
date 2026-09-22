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

import re
import time

import requests

import comunas as comunas_mod
from .base import BaseScraper

BASE = "https://www.portalinmobiliario.com/api"
MAX_PAGINAS = 40
PAUSA_S = 1.0
_NUM = re.compile(r"(\d+(?:[.,]\d+)?)")


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
        error = None
        for _ in range(2):                 # mindicador.cl a veces tarda: un reintento
            try:
                r = self.http.get("https://mindicador.cl/api/uf", timeout=20)
                r.raise_for_status()
                return float(r.json()["serie"][0]["valor"])
            except Exception as e:  # noqa: BLE001
                error = e
        print(f"  ! No se pudo obtener la UF ({error}); precio_clp quedará vacío en avisos en UF")
        return None

    # ------------------------------------------------------------------
    # Lectura de un resultado. Desde 2026 el portal envuelve cada aviso en
    # una "polycard": results[i] = {id: 'POLYCARD', polycard: {metadata,
    # components: [pill, title, price, attributes_list]}}. Se mantiene el
    # formato antiguo (price/attributes/permalink en la raíz) por si vuelve.
    # ------------------------------------------------------------------

    @staticmethod
    def id_de(item: dict) -> str | None:
        meta = (item.get("polycard") or {}).get("metadata") or {}
        return meta.get("id") or (item.get("id") if item.get("permalink") else None)

    @staticmethod
    def _entero(texto: str) -> int | None:
        m = _NUM.search(texto or "")
        return int(float(m.group(1).replace(".", "").replace(",", "."))) if m else None

    @classmethod
    def _atributos(cls, textos: list[str]) -> dict:
        """['2 dormitorios', '2 baños', '65 m² útiles'] → dict normalizado."""
        out = {"superficie_m2": "", "dormitorios": "", "banos": ""}
        for t in textos or []:
            b = t.lower()
            if "m²" in b or "m2" in b:
                out["superficie_m2"] = out["superficie_m2"] or t
            elif "dorm" in b:
                out["dormitorios"] = cls._entero(t) or ""
            elif "baño" in b:
                out["banos"] = cls._entero(t) or ""
        return out

    def _leer_polycard(self, item: dict, url_prefix: str) -> dict | None:
        card = item.get("polycard") or {}
        meta = card.get("metadata") or {}
        comps = {c.get("type"): c for c in card.get("components") or []}
        precio = ((comps.get("price") or {}).get("price") or {})
        actual = precio.get("current_price") or {}
        if not meta.get("id") or not meta.get("url"):
            return None
        url = meta["url"]
        if not url.startswith("http"):
            url = (url_prefix or "https://") + url
        prefijo = ((precio.get("prefix") or {}).get("text") or "").lower()
        pill = (comps.get("pill") or {}).get("id") or ""
        textos = ((comps.get("attributes_list") or {}).get("attributes_list") or {}).get("texts") or []

        def coord(k):
            try:
                return float(meta.get(k))
            except (TypeError, ValueError):
                return None

        return {
            "id_aviso": meta["id"],
            "titulo": ((comps.get("title") or {}).get("title") or {}).get("text", ""),
            "monto": actual.get("value"),
            "moneda": actual.get("currency"),
            # Proyectos nuevos publican "Desde X UF" y rangos de m²: no es el
            # precio de una unidad concreta, así que el análisis los separa.
            "es_proyecto": pill == "project" or "desde" in prefijo,
            "latitud": coord("latitude"),
            "longitud": coord("longitude"),
            "url": url,
            **self._atributos(textos),
        }

    def _leer_antiguo(self, item: dict) -> dict | None:
        if not item.get("permalink"):
            return None
        attrs = item.get("attributes") or []

        def attr(*ids):
            for a in attrs:
                if a.get("id") in ids:
                    return a.get("value_name") or a.get("value") or ""
            return ""

        precio = item.get("price") or {}
        return {
            "id_aviso": item.get("id", ""), "titulo": item.get("title", ""),
            "monto": precio.get("amount"), "moneda": precio.get("currency_id"),
            "es_proyecto": False, "latitud": None, "longitud": None,
            "url": item["permalink"],
            "superficie_m2": attr("TOTAL_AREA", "COVERED_AREA"),
            "dormitorios": attr("BEDROOMS", "BEDROOMS_NUMBER"),
            "banos": attr("FULL_BATHROOMS", "BATHROOMS"),
        }

    def procesar(self, item: dict, comuna, operacion: str, tipo: str, uf: float | None,
                 url_prefix: str = "https://") -> dict | None:
        base = self._leer_polycard(item, url_prefix) if "polycard" in item else self._leer_antiguo(item)
        if not base:
            return None
        monto, moneda = base.pop("monto") or 0, base.pop("moneda")
        if moneda == "CLF":                              # UF
            precio_uf, precio_clp = monto, (round(monto * uf) if uf else None)
        else:                                            # CLP
            precio_clp, precio_uf = monto, (round(monto / uf, 1) if uf else None)
        return {
            **base,
            "tipo_operacion": operacion,
            "tipo_inmueble": tipo,
            "precio_uf": precio_uf,
            "precio_clp": precio_clp,
            "comuna": comuna.nombre,
            "provincia": comuna.provincia,
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
        print(f"[{self.fuente}] Listo: {self.nuevos} nuevos, {self.actualizados} actualizados "
              f"({self.cambios_de_precio} cambiaron de precio).")

    def _combinacion(self, comuna, op: str, tipo: str, uf: float | None) -> None:
        vistos: set[str] = set()
        for pagina in range(1, MAX_PAGINAS + 1):
            try:
                r = self.http.get(self.url(op, tipo, comuna.slug, len(vistos) + 1), timeout=15)
                r.raise_for_status()
                data = r.json()
            except Exception as e:  # noqa: BLE001
                print(f"  {comuna.nombre} · {tipo} · {op} · pág {pagina}: {e}")
                return
            resultados = data.get("results") or []
            url_prefix = (data.get("polycard_context") or {}).get("url_prefix") or "https://"
            avisos = [a for a in (self.procesar(i, comuna, op, tipo, uf, url_prefix) for i in resultados) if a]
            if resultados and not avisos:
                # Llegó algo, pero no son avisos: el portal cambió el formato o
                # respondió otra cosa. Mejor avisar que guardar 0 en silencio.
                raise RuntimeError(
                    f"Respuesta con formato inesperado en {comuna.nombre} ({tipo}, {op}). "
                    "Corre  python ../scripts/diagnostico_portal.py  y revisa qué devuelve.")
            ids = {a["id_aviso"] for a in avisos}
            if not avisos or ids <= vistos:          # vacía o puro repetido: fin
                break
            vistos |= ids
            for a in avisos:
                self.guardar(a)
            time.sleep(PAUSA_S)
        print(f"  {comuna.nombre:<22} {tipo:<12} {op:<8} {len(vistos):>5} avisos")
