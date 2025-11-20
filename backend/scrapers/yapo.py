import requests
import time
from bs4 import BeautifulSoup
from .base import BaseScraper

class YapoScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.source_name = "Yapo"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }
        self.comunas = [
            'concepcion', 'chiguayante', 'coronel', 'hualpen', 'lota',
            'penco', 'san-pedro-de-la-paz', 'talcahuano', 'tome'
        ]
        self.base_url = "https://www.yapo.cl"

    def parse_listing_html(self, html_content):
        """Parse the HTML content returned by AJAX to extract property listings"""
        soup = BeautifulSoup(html_content, 'html.parser')
        listings = []
        
        # Find all listing items
        items = soup.find_all('div', class_='listing_thumbs')
        
        for item in items:
            try:
                # Extract title and URL
                title_elem = item.find('a', class_='title')
                if not title_elem:
                    continue
                    
                titulo = title_elem.get_text(strip=True)
                url = self.base_url + title_elem.get('href', '')
                
                # Extract price
                price_elem = item.find('div', class_='price')
                precio_text = price_elem.get_text(strip=True) if price_elem else "0"
                precio_clp = self.parse_price(precio_text)
                
                # Extract location
                location_elem = item.find('div', class_='data_location')
                direccion = location_elem.get_text(strip=True) if location_elem else ""
                
                # Extract details (bedrooms, bathrooms, m2)
                details = item.find('div', class_='data_details')
                dormitorios = ""
                baños = ""
                superficie_m2 = ""
                
                if details:
                    detail_text = details.get_text()
                    # Try to extract numbers from detail text
                    if 'dorm' in detail_text.lower():
                        parts = detail_text.split('|')
                        for part in parts:
                            if 'dorm' in part.lower():
                                dormitorios = ''.join(filter(str.isdigit, part))
                            elif 'baño' in part.lower():
                                baños = ''.join(filter(str.isdigit, part))
                            elif 'm²' in part or 'm2' in part:
                                superficie_m2 = ''.join(filter(str.isdigit, part))
                
                listing = {
                    'titulo': titulo,
                    'precio_clp': precio_clp,
                    'precio_uf': int(precio_clp / 37000) if precio_clp > 0 else 0,  # Approximate UF
                    'direccion': direccion,
                    'dormitorios': dormitorios,
                    'baños': baños,
                    'superficie_m2': superficie_m2,
                    'url': url,
                    'tipo_operacion': 'venta',  # Default, can be refined
                    'tipo_inmueble': 'casa',  # Default, can be refined
                    'comuna': ''  # Will be set by caller
                }
                listings.append(listing)
            except Exception as e:
                print(f"    Error parsing item: {e}")
                continue
        
        return listings

    def parse_price(self, price_text):
        """Extract numeric price from text like '$150.000.000' or 'UF 5.000'"""
        try:
            # Remove currency symbols and convert to number
            price_text = price_text.replace('$', '').replace('.', '').replace(',', '').replace('UF', '').strip()
            if price_text:
                return int(price_text)
        except:
            pass
        return 0

    def scrape(self):
        print(f"[{self.source_name}] Starting scrape...")
        
        for comuna in self.comunas:
            print(f"[{self.source_name}] Scraping {comuna}")
            
            # Yapo uses region-based URLs
            region_slug = f"biobio-{comuna}"
            
            for page in range(1, 5):  # Limit to 4 pages per comuna
                url = f"{self.base_url}/chile-es/ajax/bienes-raices-venta-de-propiedades?regionslug={region_slug}&list=categoryregion"
                if page > 1:
                    url += f"&page={page}"
                
                try:
                    resp = requests.get(url, headers=self.headers, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # The AJAX response contains HTML in the 'listing' field
                    if 'listing' in data and data['listing']:
                        listings = self.parse_listing_html(data['listing'])
                        
                        if not listings:
                            break
                        
                        for listing in listings:
                            listing['comuna'] = comuna.replace('-', ' ').title()
                            self.save_aviso(listing)
                        
                        print(f"    Page {page}: Found {len(listings)} listings")
                    else:
                        break
                        
                except Exception as e:
                    print(f"    Error on page {page}: {e}")
                    break
                
                time.sleep(1)
        
        print(f"[{self.source_name}] Scraping completed.")
