from app.models import Vaga # modelo de tabela definido no arquivo models.py
from app.schemas import VagaBase, VagaOut # schema de entrada e saída
from sqlalchemy.orm import Session

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova vaga
def criar_vaga(session, vaga_data: VagaBase) -> VagaOut:
    nova_vaga = Vaga(**vaga_data.model_dump())
    session.add(nova_vaga)
    session.commit()
    session.refresh(nova_vaga)
    return VagaOut.model_validate(nova_vaga)

# READ / GET - Lista todas as vagas
def listar_vagas(session) -> list[VagaOut]:
    vagas = session.query(Vaga).order_by(Vaga.criado_em.desc()).all()
    return [VagaOut.model_validate(v) for v in vagas]

MAPEAMENTO_CARREIRA_PALAVRAS = {
    "dados": "Analista de Dados",
    "cientista": "Cientista de Dados",
    "backend": "Desenvolvedor Backend",
    "frontend": "Desenvolvedor Frontend",
    "full": "Desenvolvedor Fullstack",
    "segurança": "Analista de Segurança da Informação",
    "rede": "Analista de Redes",
    "infra": "Analista de Infraestrutura",
}

# Sugere uma carreira com base no título da vaga
def sugerir_carreira_por_titulo(titulo: str, sessao: Session):
    t = titulo.lower()
    from app.models import Carreira
    for chave, nome in MAPEAMENTO_CARREIRA_PALAVRAS.items():
        if chave in t:
            carreira = sessao.query(Carreira).filter(Carreira.nome == nome).first()
            if carreira:
                return carreira.id
    return None
