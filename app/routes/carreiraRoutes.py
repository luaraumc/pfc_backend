from fastapi import APIRouter, HTTPException, Depends # cria dependências e exceções HTTP
from app.services.carreira import criar_carreira, listar_carreiras, buscar_carreira_por_id, atualizar_carreira, deletar_carreira # serviços relacionados a carreira
from app.services.carreiraHabilidade import criar_carreira_habilidade, listar_carreira_habilidades, remover_carreira_habilidade # serviços relacionados a habilidade da carreira
from app.schemas import CarreiraBase, CarreiraOut, CarreiraHabilidadeBase, CarreiraHabilidadeOut  # schemas para validação de dados
from app.dependencies import pegar_sessao, requer_admin # pegar a sessão do banco de dados, verificar o token e requerer admin
from sqlalchemy.orm import Session # cria sessões com o banco de dados
from app.models import Carreira # modelo de tabela definido no arquivo models.py

# Inicializa o router
carreiraRouter = APIRouter(prefix="/carreira", tags=["carreira"])

# Listar todas as carreiras
@carreiraRouter.get("/", response_model=list[CarreiraOut]) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_carreiras(session: Session = Depends(pegar_sessao)):
    return listar_carreiras(session)

# Buscar carreira por ID
@carreiraRouter.get("/{carreira_id}", response_model=CarreiraOut) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_carreira(carreira_id: int, session: Session = Depends(pegar_sessao)):
    carreira = buscar_carreira_por_id(session, carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return carreira

# Cadastrar carreira - AUTENTICADA
@carreiraRouter.post("/cadastro")
async def cadastro(
    carreira_schema: CarreiraBase, # passa como parametro os dados que o usuário tem que inserir ao acessar a rota
    usuario: dict = Depends(requer_admin), # verifica se é um usuário permitido (admin)
    session: Session = Depends(pegar_sessao) # pega a sessão do banco de dados
):
    carreira = session.query(Carreira).filter(Carreira.nome == carreira_schema.nome).first() # verifica se a carreira já existe no banco de dados
    if carreira:
        raise HTTPException(status_code=400, detail="Carreira já cadastrada")
    nova_carreira = criar_carreira(session, carreira_schema) # se não existir, cria a carreira
    return {"message": f"Carreira cadastrada com sucesso: {nova_carreira.nome}"}

# Atualizar carreira - AUTENTICADA
@carreiraRouter.put("/atualizar/{carreira_id}")
async def atualizar(
    carreira_id: int, # ID da carreira a ser atualizada
    carreira_schema: CarreiraBase, # passa como parametro os dados que o usuário tem que inserir ao acessar a rota
    usuario: dict = Depends(requer_admin), # verifica se é um usuário permitido (admin)
    session: Session = Depends(pegar_sessao) # pega a sessão do banco de dados
):
    carreira = atualizar_carreira(session, carreira_id, carreira_schema) # chama a função de serviço para atualizar a carreira
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return {"message": f"Carreira atualizada com sucesso: {carreira.nome}"}

# Deletar carreira - AUTENTICADA
@carreiraRouter.delete("/deletar/{carreira_id}")
async def deletar(
    carreira_id: int, # ID da carreira a ser deletada
    usuario: dict = Depends(requer_admin), # verifica se é um usuário permitido (admin)
    session: Session = Depends(pegar_sessao) # pega a sessão do banco de dados
):
    carreira = deletar_carreira(session, carreira_id) # chama a função de serviço para deletar a carreira
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return {"message": f"Carreira deletada com sucesso: {carreira.nome}"}    

# ======================= HABILIDADES DA CARREIRA =======================

# Listar habilidades da carreira
@carreiraRouter.get("/{carreira_id}/habilidades", response_model=list[CarreiraHabilidadeOut])
async def listar_habilidades_carreira_route(
    carreira_id: int,
    session: Session = Depends(pegar_sessao)
):
    return listar_carreira_habilidades(session, carreira_id)

# Remover habilidade da carreira - AUTENTICADA
@carreiraRouter.delete("/{carreira_id}/remover-habilidade/{habilidade_id}", response_model=CarreiraHabilidadeOut)
async def remover_habilidade_carreira_route(
    carreira_id: int,
    habilidade_id: int,
    usuario: dict = Depends(requer_admin), # verifica se é um usuário permitido (admin)
    session: Session = Depends(pegar_sessao)
):
    resultado = remover_carreira_habilidade(session, carreira_id, habilidade_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Relação carreira-habilidade não encontrada")
    return resultado

# Adicionar habilidade à carreira - AUTENTICADA
@carreiraRouter.post("/{carreira_id}/adicionar-habilidade", response_model=CarreiraHabilidadeOut)
async def adicionar_habilidade_carreira_route(
    carreira_id: int,
    payload: CarreiraHabilidadeBase,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    # Força o carreira_id do path
    data = payload.model_copy(update={"carreira_id": carreira_id, "frequencia": 1})
    # Service cuida de incrementar se já existir
    return criar_carreira_habilidade(session, data)

# Adicionar habilidade por nome (cria habilidade se não existir) - AUTENTICADA
@carreiraRouter.post("/{carreira_id}/adicionar-habilidade-por-nome", response_model=CarreiraHabilidadeOut)
async def adicionar_habilidade_por_nome_route(
    carreira_id: int,
    body: dict,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    nome = (body.get("nome") or "").strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Nome da habilidade é obrigatório")
    from app.models import Habilidade
    existente = session.query(Habilidade).filter(Habilidade.nome == nome).first()
    if not existente:
        # cria habilidade
        nova = Habilidade(nome=nome)
        session.add(nova)
        session.commit()
        session.refresh(nova)
        habilidade_id = nova.id
    else:
        habilidade_id = existente.id
    data = CarreiraHabilidadeBase(carreira_id=carreira_id, habilidade_id=habilidade_id, frequencia=1)
    return criar_carreira_habilidade(session, data)
    
