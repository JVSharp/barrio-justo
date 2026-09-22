"""Revisa rápido qué hay en MongoDB.   python scripts/check_db.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from pymongo import MongoClient  # noqa: E402

import config  # noqa: E402

cfg = config.cargar()
col = MongoClient(cfg.mongo_uri, serverSelectionTimeoutMS=3000)[cfg.mongo_db][cfg.mongo_coleccion]
print(f"Avisos en {cfg.mongo_db}.{cfg.mongo_coleccion}: {col.count_documents({})}")
for fila in col.aggregate([{"$group": {"_id": "$comuna", "n": {"$sum": 1}}}, {"$sort": {"n": -1}}]):
    print(f"  {fila['_id']:<22} {fila['n']:>6}")
