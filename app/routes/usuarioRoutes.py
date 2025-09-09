from fastapi import APIRouter, Depends, HTTPException
from app.services.usuario import atualizar_usuario, buscar_usuario_por_id
from app.models import Habilidade, UsuarioHabilidade
from sqlalchemy.orm import Session
from app.models import Usuario
from app.dependencies import pegar_sessao, verificar_token
from app.main import bcrypt_context
from app.schemas import UsuarioBase, UsuarioOut, AtualizarUsuarioSchema, AtualizarSenhaSchema, UsuarioHabilidadeBase, UsuarioHabilidadeOut, HabilidadeOut

usuarioRouter = APIRouter(prefix="/usuario", tags=["usuario"])

# Buscar usuário por ID
@usuarioRouter.get("/{usuario_id}", response_model=UsuarioOut) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_usuario(usuario_id: int, session: Session = Depends(pegar_sessao)):
    usuario = buscar_usuario_por_id(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

# Atualizar dados de usuário
@usuarioRouter.put("/atualizar/{usuario_id}")
async def atualizar_usuario(usuario_id: int, usuario_data: AtualizarUsuarioSchema, session: Session = Depends(pegar_sessao)):
    usuario = buscar_usuario_por_id(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario = atualizar_usuario(session, usuario, usuario_data)
    return usuario

# Atualizar senha do usuário
@usuarioRouter.put("/atualizar-senha/{usuario_id}")
async def atualizar_senha(usuario_id: int, nova_senha: AtualizarSenhaSchema, session: Session = Depends(pegar_sessao)):
    usuario = buscar_usuario_por_id(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.senha = bcrypt_context.hash(nova_senha.nova_senha)
    atualizar_usuario(session, usuario)
    return usuario

# Deletar usuário
@usuarioRouter.delete("/deletar/{usuario_id}", response_model=UsuarioOut) # response_model para retornar os dados do usuário deletado para mostrar ao usuário o que foi removido
async def deletar_usuario(usuario_id: int, session: Session = Depends(pegar_sessao)):
    usuario = buscar_usuario_por_id(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    deletar_usuario(session, usuario)
    return usuario

# Listar habilidades do usuário
@usuarioRouter.get("/{usuario_id}/habilidades", response_model=list[HabilidadeOut])
async def listar_habilidades_usuario(usuario_id: int, session: Session = Depends(pegar_sessao)):
    usuario = buscar_usuario_por_id(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    habilidades = session.query(Habilidade).join(UsuarioHabilidade).filter(UsuarioHabilidade.usuario_id == usuario_id).all() # Consulta no banco todas as habilidades relacionadas ao usuário através da tabela relacional
    return [HabilidadeOut.model_validate(h) for h in habilidades] # Converte cada habilidade do banco para o schema HabilidadeOut

# Listar habilidades faltantes para o usuário
@usuarioRouter.get("/{usuario_id}/habilidades-faltantes", response_model=list[HabilidadeOut])
async def listar_habilidades_faltantes(usuario_id: int, session: Session = Depends(pegar_sessao)):
    todas_habilidades = session.query(Habilidade).all() # Busca todas as habilidades no banco
    habilidades_usuario = session.query(Habilidade).join(UsuarioHabilidade).filter(UsuarioHabilidade.usuario_id == usuario_id).all() # Consulta no banco as habilidades que o usuário já possui
    faltantes = [h for h in todas_habilidades if h not in habilidades_usuario] # Filtra as habilidades que o usuário ainda não possui
    return [HabilidadeOut.model_validate(h) for h in faltantes] # Converte cada habilidade faltante para o schema HabilidadeOut

# Adicionar habilidade ao usuário
@usuarioRouter.post("/{usuario_id}/adicionar-habilidade/{habilidade_id}", response_model=UsuarioHabilidadeOut)
async def adicionar_habilidade_usuario(usuario_id: int, habilidade_id: int, session: Session = Depends(pegar_sessao)):
    existe = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id, habilidade_id=habilidade_id).first() # Verifica se a relação entre usuário e habilidade já existe
    if existe:
        raise HTTPException(status_code=400, detail="Habilidade já adicionada ao usuário")
    nova = UsuarioHabilidade(usuario_id=usuario_id, habilidade_id=habilidade_id) # Cria uma nova relação entre usuário e habilidade
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return UsuarioHabilidadeOut.model_validate(nova) # Retorna o vínculo criado no formato do schema

# Remover habilidade do usuário
@usuarioRouter.delete("/{usuario_id}/remover-habilidade/{habilidade_id}", response_model=UsuarioHabilidadeOut)
async def remover_habilidade_usuario(usuario_id: int, habilidade_id: int, session: Session = Depends(pegar_sessao)):
    relacao = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id, habilidade_id=habilidade_id).first() # Verifica se a relação entre usuário e habilidade existe
    if not relacao:
        raise HTTPException(status_code=404, detail="Relação usuário-habilidade não encontrada")
    session.delete(relacao) # Remove a relação do banco de dados
    session.commit()
    return UsuarioHabilidadeOut.model_validate(relacao) # Retorna o vínculo removido no formato do schema