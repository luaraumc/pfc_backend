from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from datetime import datetime # para comparar expiração de códigos
from app.services.usuario import atualizar_usuario, buscar_usuario_por_id, deletar_usuario, atualizar_senha # serviços relacionados ao usuário
from app.services.logExclusao import registrar_exclusao_usuario # serviço para auditoria de exclusões
from app.services.usuarioHabilidade import criar_usuario_habilidade, listar_habilidades_usuario, remover_usuario_habilidade # serviços para manipular habilidades do usuário
from app.services.compatibilidade import compatibilidade_carreiras_por_usuario, calcular_compatibilidade_usuario_carreira # serviços de compatibilidade
from app.routes.authRoutes import enviar_email, _gerar_codigo # enviar email e gerar código de verificação
from app.models import UsuarioHabilidade, CodigoAutenticacao # modelo de tabela definido no arquivo models.py
from app.models import CarreiraHabilidade, Habilidade # para consultar habilidades da carreira
from sqlalchemy.orm import Session# cria sessões com o banco de dados
from app.models import Usuario # modelo de tabela definido no arquivo models.py
from app.dependencies import pegar_sessao, verificar_token # pegar a sessão do banco de dados e verificar o token
from app.config import bcrypt_context # configuração de criptografia
from app.schemas import UsuarioOut, AtualizarUsuarioSchema, UsuarioHabilidadeBase, UsuarioHabilidadeOut, ConfirmarNovaSenhaSchema, ConfirmarCodigoSchema, SolicitarCodigoSchema # schemas para validação de dados

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

# Solicitar código de verificação por email (motivo: atualizar_senha)
@usuarioRouter.post("/solicitar-codigo/atualizar-senha")
async def solicitar_codigo_atualizar(payload: SolicitarCodigoSchema, session: Session = Depends(pegar_sessao)):
    usuario = session.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    _gerar_codigo(session, usuario, "atualizar_senha")
    return {"message": "Código enviado para atualização de senha"}

# Confirmar código + atualizar senha - AUTENTICADA
@usuarioRouter.put("/atualizar-senha/{usuario_id}")
async def atualizar_senha_route(
    usuario_id: int,
    dados: ConfirmarNovaSenhaSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
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

# Solicitar código de verificação por email (motivo: exclusao_conta)
@usuarioRouter.post("/solicitar-codigo/exclusao-conta")
async def solicitar_codigo_exclusao(payload: SolicitarCodigoSchema, session: Session = Depends(pegar_sessao)):
    usuario = session.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    _gerar_codigo(session, usuario, "exclusao_conta")
    return {"message": "Código enviado para exclusão de conta"}

# Confirmar código + deletar usuário - AUTENTICADA
@usuarioRouter.delete("/deletar/{usuario_id}")
async def deletar_usuario_route(
    usuario_id: int,
    dados: ConfirmarCodigoSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
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
    return {"message": f"Usuário deletado com sucesso e registrado em auditoria"}

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
@usuarioRouter.get("/{usuario_id}/habilidades-faltantes", response_model=list[dict])
async def listar_habilidades_faltantes_route(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao),
):
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

# Todas as carreiras por compatibilidade (ponderada por frequência) - AUTENTICADA
@usuarioRouter.get("/{usuario_id}/compatibilidade/top", response_model=list[dict])
async def top_carreiras_usuario_route(
    usuario_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao),
):
    # Busca usuário
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Calcula compatibilidade para todas as carreiras
    resultados = compatibilidade_carreiras_por_usuario(
        session,
        usuario_id,
        min_freq=None,
        taxa_cobertura=0.8,
    )
    return resultados

# Compatibilidade do usuário para uma carreira específica - AUTENTICADA
@usuarioRouter.get("/{usuario_id}/compatibilidade/carreira/{carreira_id}", response_model=dict)
async def compatibilidade_usuario_carreira_route(
    usuario_id: int,
    carreira_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao),
):
    # Busca usuário
    usuario_db = buscar_usuario_por_id(session, usuario_id)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Calcula compatibilidade para a carreira específica
    resultado = calcular_compatibilidade_usuario_carreira(
        session,
        usuario_id,
        carreira_id,
        min_freq=None,
        taxa_cobertura=0.8,
    )
    return resultado

# Adicionar habilidade ao usuário - AUTENTICADA
@usuarioRouter.post("/{usuario_id}/adicionar-habilidade/{habilidade_id}", response_model=UsuarioHabilidadeOut)
async def adicionar_habilidade_usuario_route(
    usuario_id: int,
    habilidade_id: int,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    # Verifica se a relação já existe
    existe = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id, habilidade_id=habilidade_id).first()
    if existe:
        raise HTTPException(status_code=400, detail="Habilidade já adicionada ao usuário")
    # Adiciona a habilidade
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
    # Remove a habilidade
    resultado = remover_usuario_habilidade(session, usuario_id, habilidade_id)
    # Verifica se a relação existia
    if not resultado:
        raise HTTPException(status_code=404, detail="Relação usuário-habilidade não encontrada")
    return resultado
