from fastapi import APIRouter, Depends, HTTPException
from app.services.compatibilidade import criar_compatibilidade, listar_compatibilidades, buscar_compatibilidade_por_id, atualizar_compatibilidade, deletar_compatibilidade
from sqlalchemy.orm import sessionmaker, Session
from app.models import Compatibilidade
from app.dependencies import pegar_sessao
from app.main import bcrypt_context
from app.schemas import CompatibilidadeBase, CompatibilidadeOut # rotas POST, PUT e DELETE usam CompatibilidadeBase, rota GET usa CompatibilidadeOut

compatibilidadeRouter = APIRouter(prefix="/compatibilidade", tags=["compatibilidade"])