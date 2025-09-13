import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4MzkwNDY1fQ.X3F-ZUZqT_HXEzGdZ869DwLQoauEMoaC06lwKhHI0M0"
}

requisicao = requests.get('http://127.0.0.1:8000/auth/refresh', headers=headers)
print(requisicao)
print(requisicao.json())