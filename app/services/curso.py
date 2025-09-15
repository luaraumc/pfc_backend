from app.models import Curso # modelo de tabela definido no arquivo models.py
from app.dependencies import setup_database # conexão do banco de dados
from app.schemas import CursoBase, CursoOut # schema de entrada e saída

# Inicializa a conexão com o banco de dados
engine, SessionLocal, Base = setup_database()

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria um novo curso usando schema
def criar_curso(session, curso_data: CursoBase) -> CursoOut:
    novo_curso = Curso(**curso_data.model_dump()) # Cria um objeto Curso a partir dos dados do schema
    session.add(novo_curso)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(novo_curso) # Atualiza o objeto com dados do banco
    return CursoOut.model_validate(novo_curso) # Converte o modelo SQLAlchemy para o schema de saída (CursoOut)

# READ / GET - Lista todos os cursos
def listar_cursos(session) -> list[CursoOut]:
    cursos = session.query(Curso).all()  # Busca todos os cursos
    return [CursoOut.model_validate(curso) for curso in cursos] # Converte cada curso para o schema de saída

# READ / GET - Busca um curso pelo id
def buscar_curso_por_id(session, id: int) -> CursoOut | None:
    curso = session.query(Curso).filter(Curso.id == id).first()  # Busca o curso pelo id
    return CursoOut.model_validate(curso) if curso else None # Se encontrado converte para schema de saída, senão retorna None

# UPDATE / PUT - Atualiza os dados de um curso existente usando schema
def atualizar_curso(session, id: int, curso_data: CursoBase) -> CursoOut | None:
    curso = session.query(Curso).filter(Curso.id == id).first()  # Busca o curso pelo id
    if curso:
        # Atualiza os campos do curso com os dados recebidos
        for key, value in curso_data.model_dump(exclude_unset=True).items():
            setattr(curso, key, value)
        session.commit()
        session.refresh(curso)
        return CursoOut.model_validate(curso) # Retorna o curso atualizado como schema de saída
    return None

# DELETE / DELETE - Remove um curso pelo id
def deletar_curso(session, id: int) -> CursoOut | None:
    curso = session.query(Curso).filter(Curso.id == id).first()  # Busca curso pelo id
    if curso:
        session.delete(curso)  # Remove do banco
        session.commit()
        return CursoOut.model_validate(curso) # Retorna o curso removido como schema de saída
    return None

