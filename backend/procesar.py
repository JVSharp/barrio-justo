import pandas as pd
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['propiedades']
collection = db['inmuebles']

df = pd.DataFrame(list(collection.find()))

# Normalización
df['precio_uf'] = pd.to_numeric(df['precio_uf'], errors='coerce')
df['precio_clp'] = pd.to_numeric(df['precio_clp'], errors='coerce')
df = df[df['precio_uf'].between(20, 200_000, inclusive='both')]
df = df[df['precio_clp'].between(500_000, 10_000_000_000, inclusive='both')]
df['dormitorios'] = pd.to_numeric(df['dormitorios'], errors='coerce').fillna(0).astype(int)
df['baños'] = pd.to_numeric(df['baños'], errors='coerce').fillna(0).astype(int)
df = df.dropna(subset=['comuna', 'tipo_inmueble', 'tipo_operacion'])
df = df.drop_duplicates(subset=['url'])

# Resumen
agrupado = df.groupby(['comuna', 'tipo_inmueble', 'tipo_operacion']).agg(
    promedio_uf=('precio_uf', 'mean'),
    promedio_clp=('precio_clp', 'mean'),
    cantidad=('url', 'count')
).reset_index()

print(agrupado)
agrupado.to_csv("resumen_comunas_limpio.csv", index=False)
