from fastapi import APIRouter, Depends, HTTPException, Body
from datetime import datetime
from app.services.usuario import atualizar_usuario, buscar_usuario_por_id, deletar_usuario, atualizar_senha
from app.services.logExclusao import registrar_exclusao_usuario
from app.routes.authRoutes import _gerar_codigo
from app.models.codigoAutenticacaoModels import CodigoAutenticacao 
from app.models.usuarioModels import Usuario 
from sqlalchemy.orm import Session
from app.dependencies import pegar_sessao, verificar_token
from app.config import bcrypt_context
from app.schemas.usuarioSchemas import UsuarioOut, AtualizarUsuarioSchema
from app.schemas.authSchemas import ConfirmarNovaSenhaSchema, ConfirmarCodigoSchema, SolicitarCodigoSchema
from pydantic import ValidationError
from app.utils.errors import raise_validation_http_exception

usuarioRouter = APIRouter(prefix="/usuario", tags=["usuario"])

@usuarioRouter.get("/{usuario_id}", response_model=UsuarioOut)
async def get_usuario(usuario_id: int, session: Session = Depends(pegar_sessao)):
    """Busca um usuário específico pelo ID ou retorna erro 404 se não encontrado"""
    usuario = buscar_usuario_por_id(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

@usuarioRouter.put("/atualizar/{usuario_id}")
async def atualizar_usuario_route(
    usuario_id: int,
    usuario_data: AtualizarUsuarioSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """Atualiza os dados de um usuário existente pelo ID com autenticação obrigatória"""
    # Garante que o usuário autenticado só atualize seus próprios dados
    if usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="Acesso negado: você só pode atualizar seus próprios dados")
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario_atualizado = atualizar_usuario(session, usuario_id, usuario_data)
    return {"message": "Usuário atualizado com sucesso: " + usuario_atualizado.nome}

@usuarioRouter.post("/solicitar-codigo/atualizar-senha")
async def solicitar_codigo_atualizar(payload: SolicitarCodigoSchema, session: Session = Depends(pegar_sessao)):
    """Envia código de verificação por email para atualização de senha"""
    usuario = session.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    _gerar_codigo(session, usuario, "atualizar_senha")
    return {"message": "Código enviado para atualização de senha."}

@usuarioRouter.put("/atualizar-senha/{usuario_id}")
async def atualizar_senha_route(
    usuario_id: int,
    dados_payload: dict = Body(...),
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """Valida código de verificação e atualiza senha do usuário com autenticação obrigatória"""
    # Garante que o usuário autenticado só atualize a própria senha
    if usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="Acesso negado: você só pode atualizar sua própria senha")
    # valida payload usando Pydantic para capturar mensagens legíveis
    try:
        dados = ConfirmarNovaSenhaSchema.model_validate(dados_payload)
    except ValidationError as e:
        raise_validation_http_exception(e)

    usuario_db = buscar_usuario_por_id(session, usuario_id) # busca usuário no banco de dados
    if not usuario_db or usuario_db.email != dados.email:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Busca último código válido para motivos de senha
    rec = (
        session.query(CodigoAutenticacao)
        .filter(CodigoAutenticacao.usuario_id == usuario_db.id, CodigoAutenticacao.motivo.in_(["atualizar_senha"])) # filtra por motivo de atualização de senha
        .order_by(CodigoAutenticacao.id.desc())
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Nenhum código de verificação gerado para este email")
    if rec.codigo_expira_em < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código expirado")
    if not bcrypt_context.verify(dados.codigo, rec.codigo_recuperacao):
        raise HTTPException(status_code=400, detail="Código inválido")

    nova_hash = bcrypt_context.hash(dados.nova_senha)
    atualizar_senha(session, usuario_id, nova_hash)
    session.delete(rec)
    session.commit()
    return {"message": f"Senha atualizada com sucesso para o usuário: {usuario_db.nome}"}

@usuarioRouter.post("/solicitar-codigo/exclusao-conta")
async def solicitar_codigo_exclusao(payload: SolicitarCodigoSchema, session: Session = Depends(pegar_sessao)):
    """Envia código de verificação por email para exclusão de conta"""
    usuario = session.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    _gerar_codigo(session, usuario, "exclusao_conta")
    return {"message": "Código enviado para exclusão de conta."}

@usuarioRouter.delete("/deletar/{usuario_id}")
async def deletar_usuario_route(
    usuario_id: int,
    dados: ConfirmarCodigoSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """Valida código de verificação e exclui conta do usuário com registro de auditoria"""

    # Garante que o usuário autenticado só exclua a própria conta
    if usuario.id != usuario_id:
        raise HTTPException(status_code=403, detail="Acesso negado: você só pode excluir a sua própria conta")
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db or usuario_db.email != dados.email:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if dados.motivo != "exclusao_conta":
        raise HTTPException(status_code=400, detail="Motivo inválido para exclusão")
    # Busca último código válido para motivos de exclusão de conta
    rec = (
        session.query(CodigoAutenticacao)
        .filter(CodigoAutenticacao.usuario_id == usuario_db.id, CodigoAutenticacao.motivo == "exclusao_conta") # filtra por motivo de exclusão de conta
        .order_by(CodigoAutenticacao.id.desc())
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Nenhum código de verificação gerado")
    if rec.codigo_expira_em < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código expirado")
    if not bcrypt_context.verify(dados.codigo, rec.codigo_recuperacao):
        raise HTTPException(status_code=400, detail="Código inválido")

    # Remove todos os códigos do usuário antes de deletá-lo (evita erro por UPDATE de FK -> NULL)
    session.query(CodigoAutenticacao).filter(CodigoAutenticacao.usuario_id == usuario_db.id).delete(synchronize_session=False)
    session.flush()
    # Deleta o usuário e registra auditoria
    email_para_hash = usuario_db.email
    deletar_usuario(session, usuario_id)
    registrar_exclusao_usuario(session, email_para_hash)
    session.commit()
    return {"message": f"Usuário deletado com sucesso e registrado em auditoria."}
