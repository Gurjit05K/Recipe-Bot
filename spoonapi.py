import requests

SPOONACULAR_API_KEY = "fc1e7aa72afe4c139e6f05e6485e16d3"
ingredient = "tomato"

url = f"https://api.spoonacular.com/recipes/complexSearch?query={ingredient}&apiKey={SPOONACULAR_API_KEY}"
response = requests.get(url)

print(f"Status Code: {response.status_code}")
print(f"Response JSON: {response.json()}")
