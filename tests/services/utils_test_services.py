import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Garantir variáveis mínimas exigidas por app.dependencies
os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.dependencies import Base
from app.models import (
    Categoria,
    Carreira,
    Habilidade,
    Usuario,
    Curso,
    Conhecimento,
    CursoConhecimento,
    ConhecimentoCategoria,
    UsuarioHabilidade,
    CarreiraHabilidade,
    Vaga,
    VagaHabilidade,
    Normalizacao,
)
from app.schemas import (
    UsuarioBase,
    CarreiraBase,
    ConhecimentoBase,
    CursoBase,
)

@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def cria_categoria(session, nome: str = "Tecnologia") -> Categoria:
    c = Categoria(nome=nome)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def cria_carreira(session, nome: str = "Backend", descricao: str | None = None) -> Carreira:
    car = Carreira(nome=nome, descricao=descricao)
    session.add(car)
    session.commit()
    session.refresh(car)
    return car


def cria_habilidade(session, nome: str, categoria_id: int) -> Habilidade:
    h = Habilidade(nome=nome, categoria_id=categoria_id)
    session.add(h)
    session.commit()
    session.refresh(h)
    return h


def cria_usuario(session, nome: str, email: str, senha: str = "Senha1!") -> Usuario:
    u = Usuario(nome=nome, email=email, senha=senha)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def cria_curso(session, nome: str, descricao: str = "Descricao do curso") -> Curso:
    c = Curso(nome=nome, descricao=descricao)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def cria_conhecimento(session, nome: str = "Python") -> Conhecimento:
    k = Conhecimento(nome=nome)
    session.add(k)
    session.commit()
    session.refresh(k)
    return k


def criar_vaga_raw(session, titulo: str, descricao: str, carreira_id: int | None = None) -> Vaga:
    v = Vaga(titulo=titulo, descricao=descricao, carreira_id=carreira_id)
    session.add(v)
    session.commit()
    session.refresh(v)
    return v


def vincula_curso_conhecimento(session, curso_id: int, conhecimento_id: int) -> CursoConhecimento:
    cc = CursoConhecimento(curso_id=curso_id, conhecimento_id=conhecimento_id)
    session.add(cc)
    session.commit()
    session.refresh(cc)
    return cc


def vincula_conhecimento_categoria(session, conhecimento_id: int, categoria_id: int, peso: int | None) -> ConhecimentoCategoria:
    kc = ConhecimentoCategoria(conhecimento_id=conhecimento_id, categoria_id=categoria_id, peso=peso)
    session.add(kc)
    session.commit()
    session.refresh(kc)
    return kc


def vincula_usuario_habilidade(session, usuario_id: int, habilidade_id: int) -> UsuarioHabilidade:
    uh = UsuarioHabilidade(usuario_id=usuario_id, habilidade_id=habilidade_id)
    session.add(uh)
    session.commit()
    session.refresh(uh)
    return uh


def vincula_carreira_habilidade(session, carreira_id: int, habilidade_id: int, frequencia: int | None) -> CarreiraHabilidade:
    ch = CarreiraHabilidade(carreira_id=carreira_id, habilidade_id=habilidade_id, frequencia=frequencia)
    session.add(ch)
    session.commit()
    session.refresh(ch)
    return ch


def adiciona_padrao(session, regex: str, padronizado: str) -> Normalizacao:
    n = Normalizacao(nome=regex, nome_padronizado=padronizado)
    session.add(n)
    session.commit()
    session.refresh(n)
    return n


def fake_openai_factory(payload):
    """Retorna uma classe substituta de OpenAI que devolve `payload` ao chamar `responses.create()`."""
    class DummyResponses:
        def create(self, **kwargs):
            return payload

    class DummyClient:
        def __init__(self, api_key=None):
            self.responses = DummyResponses()

    return DummyClient


def usuario_payload(
    nome: str = "Usuário Teste",
    email: str = "user@test.com",
    senha: str = "Senha1!",
    admin: bool = False,
    carreira_id: int | None = None,
    curso_id: int | None = None,
) -> UsuarioBase:
    return UsuarioBase(
        nome=nome,
        email=email,
        senha=senha,
        admin=admin,
        carreira_id=carreira_id,
        curso_id=curso_id,
    )


def carreira_payload(
    nome: str = "Desenvolvedor(a) Backend",
    descricao: str = "Atua com APIs e serviços",
) -> CarreiraBase:
    return CarreiraBase(nome=nome, descricao=descricao)


def conhecimento_payload(nome: str = "Python") -> ConhecimentoBase:
    return ConhecimentoBase(nome=nome)


def curso_payload(nome: str = "Curso A", descricao: str = "Descricao A") -> CursoBase:
    return CursoBase(nome=nome, descricao=descricao)
