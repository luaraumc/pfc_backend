from fastapi import APIRouter, Depends # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # cria sessões com o banco de dados
from app.schemas import MapaOut # schemas para validação de dados
from app.dependencies import pegar_sessao # pegar a sessão do banco de dados
from app.services.mapeamento import montar_mapa # serviço de mapeamento

# Inicializa o router
mapeamentoRouter = APIRouter(prefix="/mapa", tags=["mapeamento"])

# Obter o mapa completo curso × carreira
@mapeamentoRouter.get("/", response_model=MapaOut)
def obter_mapa(session: Session = Depends(pegar_sessao)):
    dados = montar_mapa(session=session)
    return dados
