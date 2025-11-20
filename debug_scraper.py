import requests

url = "https://www.portalinmobiliario.com/api/venta/casa/concepcion-biobio/_DisplayType_M"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept": "application/json"}

print(f"Fetching {url}...")
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print("Response Headers:", resp.headers)
    print("Response Content Preview (first 500 chars):")
    print(resp.text[:500])
    
    data = resp.json()
    print("JSON decode successful")
except Exception as e:
    print(f"Error: {e}")
