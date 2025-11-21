from fastapi import APIRouter, Depends, HTTPException
from app.services.usuario import buscar_usuario_por_id
from app.services.usuarioHabilidade import criar_usuario_habilidade, listar_habilidades_usuario, remover_usuario_habilidade
from app.services.compatibilidade import compatibilidade_carreiras_por_usuario, calcular_compatibilidade_usuario_carreira
from app.models.usuarioHabilidadeModels import UsuarioHabilidade
from app.models.carreiraHabilidadeModels import CarreiraHabilidade
from app.models.habilidadeModels import Habilidade 
from app.models.usuarioModels import Usuario 
from sqlalchemy.orm import Session
from app.dependencies import pegar_sessao, verificar_token
from app.schemas.usuarioHabilidadeSchemas import UsuarioHabilidadeBase, UsuarioHabilidadeOut

usuarioHabilidadeRouter = APIRouter(prefix="/usuario", tags=["usuario"])

@usuarioHabilidadeRouter.get("/{usuario_id}/habilidades", response_model=list[UsuarioHabilidadeOut])
async def listar_habilidades_usuario_route(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """Lista todas as habilidades associadas a um usuário específico com autenticação obrigatória"""
    # Garante que o usuário autenticado só acesse as próprias habilidades
    if usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="Acesso negado: você só pode listar suas próprias habilidades")
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return listar_habilidades_usuario(session, usuario_id)

@usuarioHabilidadeRouter.get("/{usuario_id}/habilidades-faltantes", response_model=list[dict])
async def listar_habilidades_faltantes_route(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao),
):
    """Lista habilidades requeridas pela carreira do usuário que ele ainda não possui, ordenadas por frequência"""
    # Busca usuário
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if not usuario_db.carreira_id:
        raise HTTPException(status_code=400, detail="Usuário não possui carreira definida")

    # Habilidades que o usuário já possui
    habs_usuario = session.query(UsuarioHabilidade.habilidade_id).filter(UsuarioHabilidade.usuario_id == usuario_id).all()
    ids_usuario = {hid for (hid,) in habs_usuario}

    # Habilidades requeridas pela carreira do usuário (com frequência)
    rows = (
        session.query(Habilidade.id, Habilidade.nome, CarreiraHabilidade.frequencia)
        .join(CarreiraHabilidade, CarreiraHabilidade.habilidade_id == Habilidade.id)
        .filter(CarreiraHabilidade.carreira_id == usuario_db.carreira_id)
        .all()
    )

    # Filtra apenas as habilidades que o usuário não possui
    faltantes = [
        {
            "id": hid,
            "nome": nome,
            "frequencia": int(freq) if freq is not None else 0, # converte para int e trata None
        }
        for (hid, nome, freq) in rows
        if hid not in ids_usuario
    ]

    faltantes.sort(key=lambda x: x["frequencia"], reverse=True) # ordena por frequência decrescente
    return faltantes

@usuarioHabilidadeRouter.get("/{usuario_id}/compatibilidade/top", response_model=list[dict])
async def top_carreiras_usuario_route(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao),
):
    """Calcula compatibilidade do usuário com todas as carreiras ponderada por frequência das habilidades"""
    # Busca usuário
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Calcula compatibilidade para todas as carreiras
    resultados = compatibilidade_carreiras_por_usuario(session, usuario_id)
    return resultados

@usuarioHabilidadeRouter.get("/{usuario_id}/compatibilidade/carreira/{carreira_id}", response_model=dict)
async def compatibilidade_usuario_carreira_route(
    usuario_id: int,
    carreira_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao),
):
    """Calcula compatibilidade do usuário com uma carreira específica"""
    # Busca usuário
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Calcula compatibilidade para a carreira específica
    resultado = calcular_compatibilidade_usuario_carreira(session, usuario_id, carreira_id)
    return resultado

@usuarioHabilidadeRouter.post("/{usuario_id}/adicionar-habilidade/{habilidade_id}", response_model=UsuarioHabilidadeOut)
async def adicionar_habilidade_usuario_route(
    usuario_id: int,
    habilidade_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """Adiciona uma habilidade ao usuário verificando duplicatas com autenticação obrigatória"""
    # Garante que o usuário autenticado só cadastre habilidades para si próprio
    if usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="Acesso negado: você só pode cadastrar habilidades para sua própria conta")
    # Verifica se a relação já existe
    existe = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id, habilidade_id=habilidade_id).first()
    if existe:
        raise HTTPException(status_code=400, detail="Habilidade já adicionada ao usuário")
    # Adiciona a habilidade
    usuario_habilidade_data = UsuarioHabilidadeBase(usuario_id=usuario_id, habilidade_id=habilidade_id)
    return criar_usuario_habilidade(session, usuario_habilidade_data)

@usuarioHabilidadeRouter.delete("/{usuario_id}/remover-habilidade/{habilidade_id}", response_model=UsuarioHabilidadeOut)
async def remover_habilidade_usuario_route(
    usuario_id: int,
    habilidade_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """Remove uma habilidade do usuário com autenticação obrigatória"""
    # Garante que o usuário autenticado só remova habilidades da própria conta
    if usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="Acesso negado: você só pode remover habilidades da sua própria conta")
    # Remove a habilidade
    resultado = remover_usuario_habilidade(session, usuario_id, habilidade_id)
    # Verifica se a relação existia
    if not resultado:
        raise HTTPException(status_code=404, detail="Relação usuário-habilidade não encontrada")
    return resultado
