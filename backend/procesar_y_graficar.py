# procesar_y_graficar.py

import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt

# Conexión a MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['propiedades']
collection = db['inmuebles']

# Consulta a MongoDB: obtén los datos
cursor = collection.find({}, {
    '_id': 0,
    'comuna': 1,
    'tipo_inmueble': 1,
    'tipo_operacion': 1,
    'precio_uf': 1,
    'precio_clp': 1,
})

# Convierte a DataFrame
df = pd.DataFrame(list(cursor))

# Elimina nulos
df = df.dropna(subset=['comuna', 'tipo_inmueble', 'tipo_operacion', 'precio_uf', 'precio_clp'])

# Agrupa por comuna y tipo de inmueble
agrupado = df.groupby(['comuna', 'tipo_inmueble', 'tipo_operacion']).agg(
    promedio_uf=('precio_uf', 'mean'),
    promedio_clp=('precio_clp', 'mean'),
    cantidad=('precio_uf', 'count')
).reset_index()

print("Resumen por comuna y tipo:")
print(agrupado)

# Gráfica ejemplo: Promedio UF por comuna para casas en venta
casas_venta = agrupado[
    (agrupado['tipo_inmueble'] == 'casa') &
    (agrupado['tipo_operacion'] == 'venta')
]

plt.figure(figsize=(12, 6))
plt.bar(casas_venta['comuna'], casas_venta['promedio_uf'])
plt.xticks(rotation=45, ha='right')
plt.ylabel('Precio promedio (UF)')
plt.title('Precio promedio de casas en venta por comuna')
plt.tight_layout()
plt.show()
