from fastapi import APIRouter, Depends, HTTPException
from app.services.conhecimento import criar_compatibilidade, listar_compatibilidades, buscar_compatibilidade_por_id, atualizar_compatibilidade, deletar_compatibilidade
from sqlalchemy.orm import sessionmaker, Session
from app.models import Conhecimento
from app.dependencies import pegar_sessao
from app.main import bcrypt_context
from app.schemas import ConhecimentoBase, ConhecimentoOut # rotas POST, PUT e DELETE usam ConhecimentoBase, rota GET usa ConhecimentoOut

conhecimentoRouter = APIRouter(prefix="/conhecimento", tags=["conhecimento"])