from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from app.services.usuario import atualizar_usuario, buscar_usuario_por_id, deletar_usuario, atualizar_senha # serviços relacionados ao usuário
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
    return {"message": "Usuário atualizado com sucesso: " + usuario_atualizado.nome}

# Atualizar senha do usuário - AUTENTICADA
@usuarioRouter.put("/atualizar-senha/{usuario_id}")
async def atualizar_senha_route(
    usuario_id: int,
    nova_senha: AtualizarSenhaSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario_db.senha = bcrypt_context.hash(nova_senha.nova_senha)
    atualizar_senha(session, usuario_id, usuario_db.senha)
    return {"message": "Senha atualizada com sucesso para o usuário: " + usuario_db.nome}

# Deletar usuário - AUTENTICADA
@usuarioRouter.delete("/deletar/{usuario_id}")
async def deletar_usuario_route(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    email_para_hash = usuario_db.email # pega email antes de excluir para gerar hash
    deletar_usuario(session, usuario_id)
    registrar_exclusao_usuario(session, email_para_hash) # gera hash e registra na tabela de log
    return {"message": f"Usuário deletado com sucesso e registrado em auditoria: {usuario_db.nome}"}

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
############### FAZER APÓS CRIAR COMPARAÇÃO ###############

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
