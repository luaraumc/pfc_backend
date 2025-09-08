from fastapi import APIRouter, Depends, HTTPException
from app.services.habilidade import criar_habilidade, listar_habilidades, buscar_habilidade_por_id, atualizar_habilidade, deletar_habilidade
from sqlalchemy.orm import sessionmaker, Session
from app.models import Habilidade
from app.dependencies import pegar_sessao
from app.main import bcrypt_context
from app.schemas import HabilidadeBase, HabilidadeOut # rotas POST, PUT e DELETE usam HabilidadeBase, rota GET usa HabilidadeOut

habilidadeRouter = APIRouter(prefix="/habilidade", tags=["habilidade"])