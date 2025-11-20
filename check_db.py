from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['propiedades']
collection = db['inmuebles']

count = collection.count_documents({})
print(f"Total documents in 'inmuebles': {count}")

# Print a sample if exists
if count > 0:
    print("Sample document:")
    print(collection.find_one())
