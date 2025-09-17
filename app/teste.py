import requests

headers = {
    "Authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4MTE3MTAxfQ.kwooQd67AnrVIhPbGY_w5RsOwmov0414ISjdhPqnxUI"
}

requisicao = requests.get("http://127.0.0.1:8000/auth/refresh", headers=headers)
print(requisicao.json())
print(requisicao)


