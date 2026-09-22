"""
Corre el scraper y guarda en MongoDB.

    python scraper.py                          # las 33 comunas
    python scraper.py concepcion talcahuano    # solo algunas (slugs)
"""

import sys

from scrapers import PortalInmobiliarioScraper

if __name__ == "__main__":
    PortalInmobiliarioScraper(comunas=sys.argv[1:] or None).scrape()
