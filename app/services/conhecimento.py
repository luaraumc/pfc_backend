from app.models.conhecimentoModels import Conhecimento
from app.schemas.conhecimentoSchemas import ConhecimentoBase, ConhecimentoOut

def criar_conhecimento(session, conhecimento_data: ConhecimentoBase) -> ConhecimentoOut:
    """Cria um novo conhecimento no banco de dados a partir dos dados do schema, salva e retorna como ConhecimentoOut"""
    novo_conhecimento = Conhecimento(**conhecimento_data.model_dump())
    session.add(novo_conhecimento)
    session.commit()
    session.refresh(novo_conhecimento)
    return ConhecimentoOut.model_validate(novo_conhecimento)

def listar_conhecimentos(session) -> list[ConhecimentoOut]:
    """Busca todos os conhecimentos no banco de dados e retorna uma lista convertida para ConhecimentoOut"""
    conhecimentos = session.query(Conhecimento).all()
    return [ConhecimentoOut.model_validate(conhecimento) for conhecimento in conhecimentos]

def buscar_conhecimento_por_id(session, id: int) -> ConhecimentoOut | None:
    """Busca um conhecimento específico pelo ID no banco de dados e retorna como ConhecimentoOut ou None se não encontrado"""
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()
    return ConhecimentoOut.model_validate(conhecimento) if conhecimento else None

def atualizar_conhecimento(session, id: int, conhecimento_data: ConhecimentoBase) -> ConhecimentoOut | None:
    """Busca um conhecimento pelo ID, atualiza apenas os campos informados no schema, salva no banco e retorna como ConhecimentoOut"""
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()
    if conhecimento:
        for key, value in conhecimento_data.model_dump(exclude_unset=True).items():
            setattr(conhecimento, key, value)
        session.commit()
        session.refresh(conhecimento)
        return ConhecimentoOut.model_validate(conhecimento)
    return None

def deletar_conhecimento(session, id: int) -> ConhecimentoOut | None:
    """Busca um conhecimento pelo ID, remove do banco de dados e retorna os dados do conhecimento removido como ConhecimentoOut"""
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()
    if conhecimento:
        session.delete(conhecimento)
        session.commit()
        return ConhecimentoOut.model_validate(conhecimento)
    return None
