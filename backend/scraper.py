from scrapers import PortalInmobiliarioScraper, YapoScraper

if __name__ == "__main__":
    # Aquí se pueden instanciar y ejecutar múltiples scrapers
    scrapers = [
        PortalInmobiliarioScraper(),
        YapoScraper(),
    ]

    for scraper in scrapers:
        scraper.scrape()

