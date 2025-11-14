import os
import pytest

os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

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
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import (
    cria_usuario,
    cria_carreira,
    cria_categoria,
    cria_habilidade,
    vincula_usuario_habilidade,
    vincula_carreira_habilidade,
)

def test_carreira_inexistente(session):
    """Retorna 0% de compatibilidade quando a carreira não existe."""
    usuario = cria_usuario(session)
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira_id=999)
    assert res["percentual"] == 0.0
    assert res["carreira_nome"] is None
    assert res["peso_total"] == 0


def test_carreira_sem_relacoes(session):
    """Retorna 0% quando a carreira não possui relacionamentos de habilidades."""
    usuario = cria_usuario(session)
    carreira = cria_carreira(session, "Engenharia")
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id)
    assert res["percentual"] == 0.0
    assert res["peso_total"] == 0
    assert res["habilidades_cobertas"] == []


def test_compatibilidade_parcial_sem_filtros(session):
    """Calcula compatibilidade parcial sem filtro de frequência mínimo."""
    usuario = cria_usuario(session)
    cat = cria_categoria(session)
    carreira = cria_carreira(session, "Dados")

    h1 = cria_habilidade(session, "Python", cat.id)
    h2 = cria_habilidade(session, "SQL", cat.id)

    vincula_carreira_habilidade(session, carreira.id, h1.id, 3)
    vincula_carreira_habilidade(session, carreira.id, h2.id, 2)
    vincula_usuario_habilidade(session, usuario.id, h1.id)
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id, min_freq=None)
    assert res["percentual"] == 60.0
    assert res["peso_coberto"] == 3.0
    assert res["peso_total"] == 5.0
    assert res["habilidades_cobertas"] == ["Python"]


def test_min_freq_filtra_habilidades(session):
    """Aplica min_freq para filtrar habilidades de baixa frequência no cálculo."""
    usuario = cria_usuario(session)
    cat = cria_categoria(session)
    carreira = cria_carreira(session, "Infra")

    h1 = cria_habilidade(session, "Docker", cat.id)
    h2 = cria_habilidade(session, "K8s", cat.id)

    vincula_carreira_habilidade(session, carreira.id, h1.id, 2)
    vincula_carreira_habilidade(session, carreira.id, h2.id, 5)

    vincula_usuario_habilidade(session, usuario.id, h1.id)
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id, min_freq=3)
    assert res["percentual"] == 0.0
    assert res["peso_total"] == 5.0
    res2 = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id, min_freq=None)
    assert res2["percentual"] == round(100.0 * (2.0 / 7.0), 2)


def test_taxa_cobertura_usa_nucleo(session):
    """Utiliza taxa de cobertura para restringir cálculo ao núcleo de habilidades."""
    usuario = cria_usuario(session)
    cat = cria_categoria(session)
    carreira = cria_carreira(session, "Fullstack")

    h1 = cria_habilidade(session, "React", cat.id)
    h2 = cria_habilidade(session, "Node", cat.id)
    h3 = cria_habilidade(session, "Postgres", cat.id)

    vincula_carreira_habilidade(session, carreira.id, h1.id, 5)
    vincula_carreira_habilidade(session, carreira.id, h2.id, 3)
    vincula_carreira_habilidade(session, carreira.id, h3.id, 2)
    vincula_usuario_habilidade(session, usuario.id, h2.id)
    vincula_usuario_habilidade(session, usuario.id, h3.id)
    res = calcular_compatibilidade_usuario_carreira(session, usuario.id, carreira.id, taxa_cobertura=0.6, min_freq=None)
    assert res["peso_total"] == 10.0
    assert res["peso_coberto"] == 3.0
    assert res["percentual"] == round(100.0 * (3.0 / 8.0), 2)


def test_compatibilidade_carreiras_por_usuario_ordenacao(session):
    """Ordena carreiras por compatibilidade decrescente para um usuário."""
    usuario = cria_usuario(session)
    cat = cria_categoria(session)

    c1 = cria_carreira(session, "A")
    c2 = cria_carreira(session, "B")

    h1 = cria_habilidade(session, "H1", cat.id)
    h2 = cria_habilidade(session, "H2", cat.id)

    vincula_carreira_habilidade(session, c1.id, h1.id, 5)
    vincula_carreira_habilidade(session, c2.id, h1.id, 2)
    vincula_carreira_habilidade(session, c2.id, h2.id, 2)
    vincula_usuario_habilidade(session, usuario.id, h1.id)
    resultados = compatibilidade_carreiras_por_usuario(session, usuario.id, min_freq=None)
    assert len(resultados) == 2
    assert resultados[0]["carreira_nome"] == "A"
    assert resultados[1]["carreira_nome"] == "B"
