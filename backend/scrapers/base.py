from abc import ABC, abstractmethod
from pymongo import MongoClient
from datetime import datetime

class BaseScraper(ABC):
    def __init__(self, db_name='propiedades', collection_name='inmuebles', mongo_uri='mongodb://localhost:27017'):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.source_name = "generic"

    @abstractmethod
    def scrape(self):
        """
        Main method to execute the scraping logic.
        """
        pass

    def save_aviso(self, aviso_data):
        """
        Saves or updates an ad in the database.
        aviso_data must contain a 'url' field to check for duplicates.
        """
        if not aviso_data.get("url"):
            print("Error: Aviso sin URL, no se puede guardar.")
            return

        # Ensure source is set
        aviso_data['source'] = self.source_name
        aviso_data['fecha_scraping'] = datetime.utcnow().isoformat()

        # Check if exists
        existing = self.collection.find_one({"url": aviso_data["url"]})
        if not existing:
            self.collection.insert_one(aviso_data)
            # print(f"[{self.source_name}] Guardado: {aviso_data.get('titulo', 'Sin titulo')}")
        else:
            # Optional: Update if needed, for now just skip
            pass
