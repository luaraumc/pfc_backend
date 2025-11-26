from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaBase, ConhecimentoCategoriaOut, ConhecimentoCategoriaAtualizar
from app.dependencies import pegar_sessao, requer_admin
from app.services.conhecimentoCategoria import (
    listar_conhecimento_categorias,
    criar_conhecimento_categoria,
    remover_conhecimento_categoria,
    atualizar_conhecimento_categoria
)

conhecimentoCategoriaRouter = APIRouter(prefix="/conhecimento-categoria", tags=["conhecimento_categoria"])

@conhecimentoCategoriaRouter.get("/{conhecimento_id}", response_model=list[ConhecimentoCategoriaOut])
def listar_por_conhecimento(conhecimento_id: int, session: Session = Depends(pegar_sessao)):
    """Lista todas as categorias associadas a um conhecimento específico"""
    return listar_conhecimento_categorias(session, conhecimento_id)

@conhecimentoCategoriaRouter.post("/", response_model=ConhecimentoCategoriaOut)
def criar(
    payload: ConhecimentoCategoriaBase,
    session: Session = Depends(pegar_sessao),
    usuario=Depends(requer_admin)
):
    """Cria uma nova associação entre conhecimento e categoria, disponível apenas para administradores"""
    try:
        return criar_conhecimento_categoria(session, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@conhecimentoCategoriaRouter.delete("/{conhecimento_id}/{categoria_id}")
def remover(
    conhecimento_id: int,
    categoria_id: int,
    session: Session = Depends(pegar_sessao),
    usuario=Depends(requer_admin)
):
    """Remove a associação entre um conhecimento e uma categoria específica, disponível apenas para administradores"""
    rel = remover_conhecimento_categoria(session, conhecimento_id, categoria_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relação não encontrada")
    return {"status": "removida", "conhecimento_id": conhecimento_id, "categoria_id": categoria_id}

@conhecimentoCategoriaRouter.put("/{relacao_id}", response_model=ConhecimentoCategoriaOut)
def atualizar(
    relacao_id: int,
    payload: ConhecimentoCategoriaAtualizar,
    session: Session = Depends(pegar_sessao),
    usuario=Depends(requer_admin)
):
    """Atualiza uma relação existente entre conhecimento e categoria, disponível apenas para administradores"""
    try:
        rel = atualizar_conhecimento_categoria(session, relacao_id, payload)
        if not rel:
            raise HTTPException(status_code=404, detail="Relação não encontrada")
        return rel
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
