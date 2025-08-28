from fastapi import APIRouter, HTTPException


homeRouter = APIRouter(prefix="/home", tags=["home"])

@homeRouter.get("/")
async def informacoes():
    # funcionalidade para exibir cursos
    # funcionalidade para exibir carreiras
    # funcionalidade para exibir a relação entre os cursos e carreiras
    return {"curso": "lista de cursos", "carreira": "lista de carreiras", "compatibilidade": "relação entre cursos e carreiras"}