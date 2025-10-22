# test_api.py 
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

print("Testing E-Commerce Backend APIs")
print("=" * 50)

# Root endpoint
print("\n1. Testing root endpoint...")
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print(" Root endpoint working!")
except Exception as e:
    print(f" Error: {e}")

# Simple search
print("\n2. Testing simple search...")
try:
    response = requests.get(f"{BASE_URL}/products/search", params={"query": "laptop", "limit": 2})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} products")
        for product in data:
            print(f"  - {product['name']}: ${product['price']}")
        print(" Search working!")
    else:
        print(f" Error: {response.text}")
except Exception as e:
    print(f" Error: {e}")

# Fuzzy search
print("\n3. Testing fuzzy search (typo: 'leptop')...")
try:
    response = requests.get(f"{BASE_URL}/products/search", params={"query": "leptop", "limit": 2})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} products despite typo")
        for product in data:
            print(f"  - {product['name']}")
        print(" Fuzzy search working!")
    else:
        print(f" Error: {response.text}")
except Exception as e:
    print(f" Error: {e}")

# User orders
print("\n4. Testing user orders...")
try:
    user_id = "653b6f8f9e6d7f001a1b2d01"
    response = requests.get(f"{BASE_URL}/users/{user_id}/orders")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} orders")
        print(" User orders working!")
    else:
        print(f" Error: {response.text}")
except Exception as e:
    print(f" Error: {e}")

# Product reviews
print("\n5. Testing product reviews...")
try:
    product_id = "653b6f8f9e6d7f001a1b2c01"
    response = requests.get(f"{BASE_URL}/products/{product_id}/reviews")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} reviews")
        print(" Product reviews working!")
    else:
        print(f" Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Analytics
print("\n6. Testing analytics (top products)...")
try:
    response = requests.get(f"{BASE_URL}/analytics/top-products", params={"days": 365, "limit": 5})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} top products")
        for product in data:
            print(f"  - {product['name']}: {product['purchase_count']} purchases")
        print(" Analytics working!")
    else:
        print(f" Error: {response.text}")
except Exception as e:
    print(f" Error: {e}")

print("\n" + "=" * 50)
print("Testing complete!")
