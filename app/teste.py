import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4MDU0MDEwfQ.J2XI9K1EvwVFgVcL1TNbYCNaOGrPwB1oSg8a0Giac8A"
}

requisicao = requests.get('http://127.0.0.1:8000/auth/refresh', headers=headers)
print(requisicao)
print(requisicao.json())