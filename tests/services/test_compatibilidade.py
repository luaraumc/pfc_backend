import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Variáveis mínimas de ambiente para evitar erros nas imports
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
    Usuario,
    Carreira,
    Categoria,
    Habilidade,
    UsuarioHabilidade,
    CarreiraHabilidade,
)
from app.services.compatibilidade import (
    calcular_compatibilidade_usuario_carreira,
    compatibilidade_carreiras_por_usuario,
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


# Helpers para criar dados
def cria_usuario(session, nome="Usu", email="u@test.com") -> Usuario:
    u = Usuario(nome=nome, email=email, senha="Senha1!")
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def cria_carreira(session, nome="Carreira") -> Carreira:
    c = Carreira(nome=nome)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def cria_categoria(session, nome="Cat") -> Categoria:
    cat = Categoria(nome=nome)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return cat


def cria_habilidade(session, nome: str, categoria_id: int) -> Habilidade:
    h = Habilidade(nome=nome, categoria_id=categoria_id)
    session.add(h)
    session.commit()
    session.refresh(h)
    return h


def vincula_usuario_habilidade(session, usuario_id: int, habilidade_id: int) -> UsuarioHabilidade:
    uh = UsuarioHabilidade(usuario_id=usuario_id, habilidade_id=habilidade_id)
    session.add(uh)
    session.commit()
    session.refresh(uh)
    return uh


def vincula_carreira_habilidade(session, carreira_id: int, habilidade_id: int, frequencia: int) -> CarreiraHabilidade:
    ch = CarreiraHabilidade(carreira_id=carreira_id, habilidade_id=habilidade_id, frequencia=frequencia)
    session.add(ch)
    session.commit()
    session.refresh(ch)
    return ch


# =========================
# Testes para calcular_compatibilidade_usuario_carreira
# =========================

def test_carreira_inexistente(session):
    usuario = cria_usuario(session)
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira_id=999)
    assert res["percentual"] == 0.0
    assert res["carreira_nome"] is None
    assert res["peso_total"] == 0


def test_carreira_sem_relacoes(session):
    usuario = cria_usuario(session)
    carreira = cria_carreira(session, "Engenharia")
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id)
    assert res["percentual"] == 0.0
    assert res["peso_total"] == 0
    assert res["habilidades_cobertas"] == []


def test_compatibilidade_parcial_sem_filtros(session):
    usuario = cria_usuario(session)
    cat = cria_categoria(session)
    carreira = cria_carreira(session, "Dados")

    h1 = cria_habilidade(session, "Python", cat.id)
    h2 = cria_habilidade(session, "SQL", cat.id)

    # Carreira: Python (3), SQL (2)
    vincula_carreira_habilidade(session, carreira.id, h1.id, 3)
    vincula_carreira_habilidade(session, carreira.id, h2.id, 2)

    # Usuário possui apenas Python
    vincula_usuario_habilidade(session, usuario.id, h1.id)

    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id)
    # percentual = 100 * 3 / (3+2) = 60.0
    assert res["percentual"] == 60.0
    assert res["peso_coberto"] == 3.0
    assert res["peso_total"] == 5.0
    assert res["habilidades_cobertas"] == ["Python"]


def test_min_freq_filtra_habilidades(session):
    usuario = cria_usuario(session)
    cat = cria_categoria(session)
    carreira = cria_carreira(session, "Infra")

    h1 = cria_habilidade(session, "Docker", cat.id)
    h2 = cria_habilidade(session, "K8s", cat.id)

    vincula_carreira_habilidade(session, carreira.id, h1.id, 2)
    vincula_carreira_habilidade(session, carreira.id, h2.id, 5)

    # usuário tem apenas Docker (freq 2)
    vincula_usuario_habilidade(session, usuario.id, h1.id)

    # com min_freq=3 Docker deve ser ignorado -> percentual 0
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id, min_freq=3)
    assert res["percentual"] == 0.0
    assert res["peso_total"] == 5.0

    # sem min_freq, percentual = 100 * 2/(2+5) = 28.57 -> arredondado para 2 casas
    res2 = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id, min_freq=None)
    assert res2["percentual"] == round(100.0 * (2.0 / 7.0), 2)


def test_taxa_cobertura_usa_nucleo(session):
    usuario = cria_usuario(session)
    cat = cria_categoria(session)
    carreira = cria_carreira(session, "Fullstack")

    h1 = cria_habilidade(session, "React", cat.id)
    h2 = cria_habilidade(session, "Node", cat.id)
    h3 = cria_habilidade(session, "Postgres", cat.id)

    # pesos: React 5, Node 3, Postgres 2 -> total 10
    vincula_carreira_habilidade(session, carreira.id, h1.id, 5)
    vincula_carreira_habilidade(session, carreira.id, h2.id, 3)
    vincula_carreira_habilidade(session, carreira.id, h3.id, 2)

    # usuário possui Node e Postgres (3+2)
    vincula_usuario_habilidade(session, usuario.id, h2.id)
    vincula_usuario_habilidade(session, usuario.id, h3.id)

    # taxa_cobertura = 0.6 -> núcleo precisa 6.0 peso. Ordenando: 5,3,2 -> núcleo {React,Node} -> peso núcleo = 8
    # usuário possui Node (3) dentro do núcleo -> percentual = 100 * 3 / 8 = 37.5
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id, taxa_cobertura=0.6)
    assert res["peso_total"] == 10.0
    assert res["peso_coberto"] == 3.0
    assert res["percentual"] == round(100.0 * (3.0 / 8.0), 2)


# =========================
# Testes para compatibilidade_carreiras_por_usuario
# =========================

def test_compatibilidade_carreiras_por_usuario_ordenacao(session):
    usuario = cria_usuario(session)
    cat = cria_categoria(session)

    c1 = cria_carreira(session, "A")
    c2 = cria_carreira(session, "B")

    h1 = cria_habilidade(session, "H1", cat.id)
    h2 = cria_habilidade(session, "H2", cat.id)

    # Carreira A: H1(5) ; Carreira B: H1(2), H2(2)
    vincula_carreira_habilidade(session, c1.id, h1.id, 5)
    vincula_carreira_habilidade(session, c2.id, h1.id, 2)
    vincula_carreira_habilidade(session, c2.id, h2.id, 2)

    # usuário tem apenas H1 -> compat A = 100; compat B = 100 * 2/4 = 50
    vincula_usuario_habilidade(session, usuario.id, h1.id)

    resultados = compatibilidade_carreiras_por_usuario(session, usuario.id)
    assert len(resultados) == 2
    assert resultados[0]["carreira_nome"] == "A"
    assert resultados[1]["carreira_nome"] == "B"
