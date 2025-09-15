from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from app.services.usuario import atualizar_usuario, buscar_usuario_por_id # serviços relacionados ao usuário
from app.services.usuarioHabilidade import criar_usuario_habilidade, listar_habilidades_usuario, remover_usuario_habilidade # serviços para manipular habilidades do usuário
from app.models import Habilidade, UsuarioHabilidade # modelo de tabela definido no arquivo models.py
from sqlalchemy.orm import Session# cria sessões com o banco de dados
from app.models import Usuario # modelo de tabela definido no arquivo models.py
from app.dependencies import pegar_sessao, verificar_token # pegar a sessão do banco de dados e verificar o token
from app.config import bcrypt_context # configuração de criptografia
from app.schemas import UsuarioBase, UsuarioOut, AtualizarUsuarioSchema, AtualizarSenhaSchema, UsuarioHabilidadeBase, UsuarioHabilidadeOut, HabilidadeOut # schemas para validação de dados

# Inicializa o router
usuarioRouter = APIRouter(prefix="/usuario", tags=["usuario"])

# Buscar usuário por ID
@usuarioRouter.get("/{usuario_id}", response_model=UsuarioOut) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_usuario(usuario_id: int, session: Session = Depends(pegar_sessao)):
    usuario = buscar_usuario_por_id(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

# Atualizar dados de usuário - AUTENTICADA
@usuarioRouter.put("/atualizar/{usuario_id}")
async def atualizar_usuario_route(
    usuario_id: int,
    usuario_data: AtualizarUsuarioSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario_atualizado = atualizar_usuario(session, usuario_id, usuario_data)
    return usuario_atualizado

# Atualizar senha do usuário - AUTENTICADA
@usuarioRouter.put("/atualizar-senha/{usuario_id}")
async def atualizar_senha(
    usuario_id: int,
    nova_senha: AtualizarSenhaSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario_db.senha = bcrypt_context.hash(nova_senha.nova_senha)
    atualizar_usuario(session, usuario_db)
    return usuario_db

# Deletar usuário - AUTENTICADA
@usuarioRouter.delete("/deletar/{usuario_id}", response_model=UsuarioOut)
async def deletar_usuario(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    deletar_usuario(session, usuario_db)
    return usuario_db

# ======================= HABILIDADES DO USUÁRIO =======================

# Listar habilidades do usuário - AUTENTICADA
@usuarioRouter.get("/{usuario_id}/habilidades", response_model=list[UsuarioHabilidadeOut])
async def listar_habilidades_usuario_route(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return listar_habilidades_usuario(session, usuario_id)

# Listar habilidades faltantes para o usuário - AUTENTICADA
@usuarioRouter.get("/{usuario_id}/habilidades-faltantes", response_model=list[HabilidadeOut])
async def listar_habilidades_faltantes(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    todas_habilidades = session.query(Habilidade).all()
    habilidades_usuario = session.query(Habilidade).join(UsuarioHabilidade).filter(UsuarioHabilidade.usuario_id == usuario_id).all()
    faltantes = [h for h in todas_habilidades if h not in habilidades_usuario]
    return [HabilidadeOut.model_validate(h) for h in faltantes]

# Adicionar habilidade ao usuário - AUTENTICADA
@usuarioRouter.post("/{usuario_id}/adicionar-habilidade/{habilidade_id}", response_model=UsuarioHabilidadeOut)
async def adicionar_habilidade_usuario_route(
    usuario_id: int,
    habilidade_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    existe = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id, habilidade_id=habilidade_id).first()
    if existe:
        raise HTTPException(status_code=400, detail="Habilidade já adicionada ao usuário")
    usuario_habilidade_data = UsuarioHabilidadeBase(usuario_id=usuario_id, habilidade_id=habilidade_id)
    return criar_usuario_habilidade(session, usuario_habilidade_data)

# Remover habilidade do usuário - AUTENTICADA
@usuarioRouter.delete("/{usuario_id}/remover-habilidade/{habilidade_id}", response_model=UsuarioHabilidadeOut)
async def remover_habilidade_usuario_route(
    usuario_id: int,
    habilidade_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    resultado = remover_usuario_habilidade(session, usuario_id, habilidade_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Relação usuário-habilidade não encontrada")
    return resultado
