import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# --- Infra compartilhada: engine/sessão limpa para cada módulo de teste ---
@pytest.fixture(scope="module")
def session_factory():
    # Env mínimos para que app.dependencies não falhe em imports
    os.environ.setdefault("KEY_CRYPT", "k")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    os.environ.setdefault("DB_USER", "u")
    os.environ.setdefault("DB_PASSWORD", "p")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    os.environ.setdefault("DB_NAME", "db")

    # Reimport limpo para evitar cache entre módulos
    sys.modules.pop("app.models", None)
    sys.modules.pop("app.dependencies", None)

    from app.models import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# --- Helpers compartilhados (pequenos e expressivos) ---

def _criar_categoria(db, nome: str = "Backend"):
    from app.models.categoriaModels import Categoria

    c = Categoria(nome=nome)
    db.add(c)
    db.flush()
    return c


def _criar_habilidade(db, nome: str = "Python", categoria=None):
    from app.models.habilidadeModels import Habilidade

    if categoria is None:
        categoria = _criar_categoria(db)
    h = Habilidade(nome=nome, categoria_id=categoria.id)
    db.add(h)
    db.flush()
    return h


def _criar_carreira(db, nome: str = "Desenvolvedor", descricao: Optional[str] = None):
    from app.models.carreiraModels import Carreira

    c = Carreira(nome=nome, descricao=descricao)
    db.add(c)
    db.flush()
    return c


def _criar_curso(db, nome: str = "Python 101", descricao: str = "Curso introdutório"):
    from app.models.cursoModels import Curso

    c = Curso(nome=nome, descricao=descricao)
    db.add(c)
    db.flush()
    return c


def _criar_vaga(db, titulo: str = "Dev", descricao: str = "Descricao Unica", carreira_id: Optional[int] = None):
    from app.models.vagaModels import Vaga

    v = Vaga(titulo=titulo, descricao=descricao, carreira_id=carreira_id)
    db.add(v)
    db.flush()
    return v


def _criar_conhecimento(db, nome: str = "POO"):
    from app.models.conhecimentoModels import Conhecimento

    k = Conhecimento(nome=nome)
    db.add(k)
    db.flush()
    return k


def _criar_conhecimento_categoria(db, conhecimento_id: int, categoria_id: int, peso: Optional[int] = None):
    from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria

    kc = ConhecimentoCategoria(
        conhecimento_id=conhecimento_id,
        categoria_id=categoria_id,
        peso=peso,
    )
    db.add(kc)
    db.flush()
    return kc


def _criar_curso_conhecimento(db, curso_id: int, conhecimento_id: int):
    from app.models.cursoConhecimentoModels import CursoConhecimento

    ck = CursoConhecimento(curso_id=curso_id, conhecimento_id=conhecimento_id)
    db.add(ck)
    db.flush()
    return ck


def _criar_usuario(
    db,
    nome: str = "Alice",
    email: str = "alice@example.com",
    senha: str = "hash",
    carreira_id: Optional[int] = None,
    curso_id: Optional[int] = None,
    admin: Optional[bool] = None,
):
    from app.models.usuarioModels import Usuario

    kwargs = dict(nome=nome, email=email, senha=senha, carreira_id=carreira_id, curso_id=curso_id)
    if admin is not None:
        kwargs["admin"] = admin
    u = Usuario(**kwargs)
    db.add(u)
    db.flush()
    return u


def _criar_usuario_habilidade(db, usuario_id: int, habilidade_id: int):
    from app.models.usuarioHabilidadeModels import UsuarioHabilidade

    uh = UsuarioHabilidade(usuario_id=usuario_id, habilidade_id=habilidade_id)
    db.add(uh)
    db.flush()
    return uh


def _criar_vaga_habilidade(db, vaga_id: int, habilidade_id: int):
    from app.models.vagaHabilidadeModels import VagaHabilidade

    vh = VagaHabilidade(vaga_id=vaga_id, habilidade_id=habilidade_id)
    db.add(vh)
    db.flush()
    return vh


def _criar_carreira_habilidade(db, carreira_id: int, habilidade_id: int, frequencia: Optional[int] = None):
    from app.models.carreiraHabilidadeModels import CarreiraHabilidade

    ch = CarreiraHabilidade(
        carreira_id=carreira_id,
        habilidade_id=habilidade_id,
        frequencia=frequencia,
    )
    db.add(ch)
    db.flush()
    return ch


def _criar_codigo(
    db,
    usuario_id: int,
    codigo: str = "ABC123",
    expira_em=None,
    motivo: Optional[str] = None,
):
    from app.models.codigoAutenticacaoModels import CodigoAutenticacao

    if expira_em is None:
        expira_em = datetime.utcnow() + timedelta(minutes=30)

    kwargs = dict(
        usuario_id=usuario_id,
        codigo_recuperacao=codigo,
        codigo_expira_em=expira_em,
    )
    # Se motivo for None, omitimos o campo para permitir server_default do banco preencher
    if motivo is not None:
        kwargs["motivo"] = motivo

    ca = CodigoAutenticacao(**kwargs)
    db.add(ca)
    db.flush()
    return ca


def _criar_log(db, email_hash: str = "hash123", **overrides):
    from app.models.logExclusaoModels import LogExclusao

    log = LogExclusao(email_hash=email_hash, **overrides)
    db.add(log)
    db.flush()
    return log
