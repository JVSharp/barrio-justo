import requests
import time
from .base import BaseScraper

class PortalInmobiliarioScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.source_name = "PortalInmobiliario"
        self.headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        self.comunas = [
            'alto-biobio', 'antuco', 'arauco', 'cabrero', 'canete', 'chiguayante',
            'concepcion', 'contulmo', 'coronel', 'florida', 'hualpen', 'hualqui',
            'lebu', 'los-alamos', 'los-angeles', 'lota', 'mulchen', 'Nacimiento',
            'negrete', 'penco', 'quilleco', 'quilaco', 'quillon', 'san-pedro-de-la-paz',
            'san-rosendo', 'santa-barbara', 'santa-juana', 'talcahuano', 'tome'
        ]
        self.operaciones = ['venta', 'arriendo']
        self.tipos_inmueble = ['casa', 'departamento']

    def get_uf_value(self):
        try:
            r = requests.get("https://mindicador.cl/api", timeout=5)
            r.raise_for_status()
            return r.json()["uf"]["valor"]
        except Exception as e:
            print(f"No se pudo obtener UF: {e}")
            return 37000

    def get_attr(self, attrs, ids):
        if isinstance(ids, str):
            ids = [ids]
        for attr in attrs:
            if attr.get("id") in ids:
                return attr.get("value_name") or attr.get("value") or ""
        return ""

    def process_item(self, item, comuna, tipo_operacion, tipo_inmueble, uf):
        p = item.get("price", {})
        precio_uf = p.get("amount", 0)
        precio_clp = int(precio_uf * uf) if p.get("currency_id") == "CLF" else precio_uf
        attrs = item.get("attributes", [])
        
        aviso = {
            "id_aviso": item.get("id", ""),
            "tipo_operacion": tipo_operacion,
            "tipo_inmueble": tipo_inmueble,
            "titulo": item.get("title", ""),
            "precio_uf": precio_uf,
            "precio_clp": precio_clp,
            "direccion": item.get("location", ""),
            "comuna": comuna.replace("-", " ").title(),
            "superficie_m2": self.get_attr(attrs, ["TOTAL_AREA", "COVERED_AREA"]),
            "dormitorios": self.get_attr(attrs, ["BEDROOMS", "BEDROOMS_NUMBER"]),
            "baños": self.get_attr(attrs, ["FULL_BATHROOMS", "BATHROOMS"]),
            "url": item.get("permalink", ""),
        }
        return aviso

    def scrape(self):
        uf_val = self.get_uf_value()
        print(f"[{self.source_name}] UF actual: {uf_val:,.0f} CLP")

        for comuna in self.comunas:
            for operacion in self.operaciones:
                for tipo_inmueble in self.tipos_inmueble:
                    print(f"[{self.source_name}] Scrapeando {comuna} | {tipo_inmueble} | {operacion}")
                    pagina = 1
                    prev_ids = set()
                    repeticiones = 0
                    
                    while pagina < 50:
                        url = f"https://www.portalinmobiliario.com/api/{operacion}/{tipo_inmueble}/{comuna}-biobio/_DisplayType_M"
                        if pagina > 1:
                            url += f"#{pagina}"
                        
                        try:
                            resp = requests.get(url, headers=self.headers, timeout=10)
                            resp.raise_for_status()
                            data = resp.json()
                        except Exception as e:
                            print(f"    Error: {e}")
                            break

                        results = data.get("results", [])
                        if not results:
                            break

                        ids = set(item.get("id") for item in results)
                        if ids == prev_ids:
                            repeticiones += 1
                            if repeticiones > 2:
                                break
                        else:
                            repeticiones = 0

                        for itm in results:
                            aviso = self.process_item(itm, comuna, operacion, tipo_inmueble, uf_val)
                            self.save_aviso(aviso)

                        prev_ids = ids
                        pagina += 1
                        time.sleep(1)
        print(f"[{self.source_name}] Scraping completado.")
