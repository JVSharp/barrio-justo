from scrapers import PortalInmobiliarioScraper

if __name__ == "__main__":
    # Aquí se pueden instanciar y ejecutar múltiples scrapers
    scrapers = [
        PortalInmobiliarioScraper(),
        # FutureScraper(),
    ]

    for scraper in scrapers:
        scraper.scrape()

