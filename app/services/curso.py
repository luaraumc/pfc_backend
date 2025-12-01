from app.models.cursoModels import Curso
from app.schemas.cursoSchemas import CursoBase, CursoOut

def criar_curso(session, curso_data: CursoBase) -> CursoOut:
    """Cria um novo curso no banco de dados a partir dos dados do schema, salva e retorna como CursoOut"""
    novo_curso = Curso(**curso_data.model_dump())
    session.add(novo_curso)
    session.commit()
    session.refresh(novo_curso)
    return CursoOut.model_validate(novo_curso)

def listar_cursos(session) -> list[CursoOut]:
    """Busca todos os cursos no banco de dados e retorna uma lista convertida para CursoOut"""
    cursos = session.query(Curso).all()
    return [CursoOut.model_validate(curso) for curso in cursos]

def buscar_curso_por_id(session, id: int) -> CursoOut | None:
    """Busca um curso específico pelo ID no banco de dados e retorna como CursoOut ou None se não encontrado"""
    curso = session.query(Curso).filter(Curso.id == id).first()
    return CursoOut.model_validate(curso) if curso else None

def atualizar_curso(session, id: int, curso_data: CursoBase) -> CursoOut | None:
    """Busca um curso pelo ID, atualiza apenas os campos informados no schema, salva no banco e retorna como CursoOut"""
    curso = session.query(Curso).filter(Curso.id == id).first()
    if curso:
        for key, value in curso_data.model_dump(exclude_unset=True).items():
            setattr(curso, key, value)
        session.commit()
        session.refresh(curso)
        return CursoOut.model_validate(curso)
    return None

def deletar_curso(session, id: int) -> CursoOut | None:
    """Busca um curso pelo ID, remove do banco de dados e retorna os dados do curso removido como CursoOut"""
    curso = session.query(Curso).filter(Curso.id == id).first()
    if curso:
        session.delete(curso)
        session.commit()
        return CursoOut.model_validate(curso)
    return None