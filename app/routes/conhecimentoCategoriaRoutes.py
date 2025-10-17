from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import ConhecimentoCategoriaBase, ConhecimentoCategoriaOut
from app.dependencies import pegar_sessao, requer_admin

conhecimentoCategoriaRouter = APIRouter(prefix="/conhecimento-categoria", tags=["conhecimento_categoria"])

@conhecimentoCategoriaRouter.get("/{conhecimento_id}", response_model=list[ConhecimentoCategoriaOut])
def listar_por_conhecimento(conhecimento_id: int, session: Session = Depends(pegar_sessao)):
    from app.services.conhecimentoCategoria import listar_conhecimento_categorias
    return listar_conhecimento_categorias(session, conhecimento_id)

@conhecimentoCategoriaRouter.post("/", response_model=ConhecimentoCategoriaOut)
def criar(
    payload: ConhecimentoCategoriaBase,
    session: Session = Depends(pegar_sessao),
    usuario=Depends(requer_admin)
):
    from app.services.conhecimentoCategoria import criar_conhecimento_categoria
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
    from app.services.conhecimentoCategoria import remover_conhecimento_categoria
    rel = remover_conhecimento_categoria(session, conhecimento_id, categoria_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relação não encontrada")
    return {"status": "removida", "conhecimento_id": conhecimento_id, "categoria_id": categoria_id}
