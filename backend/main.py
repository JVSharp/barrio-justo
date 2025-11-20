from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient('mongodb://localhost:27017')
db = client['propiedades']
collection = db['inmuebles']

# Endpoint: Propiedades filtradas y paginadas
@app.get("/propiedades/")
def get_propiedades(
    comuna: str = Query(None),
    tipo_operacion: str = Query(None, regex="^(venta|arriendo)?$"),
    tipo_inmueble: str = Query(None, regex="^(casa|departamento)?$"),
    skip: int = 0,
    limit: int = 50,
):
    query = {}
    if comuna:
        query["comuna"] = comuna.replace('_', ' ').title()
    if tipo_operacion:
        query["tipo_operacion"] = tipo_operacion
    if tipo_inmueble:
        query["tipo_inmueble"] = tipo_inmueble

    resultados = list(collection.find(query, {'_id': 0}).skip(skip).limit(limit))
    return resultados

# Endpoint: Resumen por comuna
@app.get("/resumen/{comuna}")
def resumen_comuna(comuna: str):
    pipeline = [
        {"$match": {"comuna": comuna.replace('_', ' ').title()}},
        {"$group": {
            "_id": "$comuna",
            "promedio_precio_uf": {"$avg": "$precio_uf"},
            "promedio_precio_clp": {"$avg": "$precio_clp"},
            "cantidad": {"$sum": 1}
        }}
    ]
    resumen = list(collection.aggregate(pipeline))
    return resumen[0] if resumen else {}

# Endpoint: Resumen de todas las comunas
@app.get("/resumen")
def resumen_todas_comunas():
    pipeline = [
        {"$group": {
            "_id": "$comuna",
            "promedio_precio_uf": {"$avg": "$precio_uf"},
            "promedio_precio_clp": {"$avg": "$precio_clp"},
            "cantidad": {"$sum": 1}
        }},
        {"$sort": {"cantidad": -1}}
    ]
    return list(collection.aggregate(pipeline))

# Endpoint: Lista de comunas (para filtros frontend)
@app.get("/comunas")
def get_comunas():
    comunas = collection.distinct("comuna")
    return sorted(comunas)

# Endpoint: Lista de tipos de inmueble
@app.get("/tipos_inmueble")
def get_tipos_inmueble():
    return collection.distinct("tipo_inmueble")

# Endpoint: Lista de tipos de operación
@app.get("/tipos_operacion")
def get_tipos_operacion():
    return collection.distinct("tipo_operacion")
