import os
import pytest
from datetime import datetime, timezone, timedelta
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
from app.services.logExclusao import gerar_email_hash, registrar_exclusao_usuario
from app.models import LogExclusao


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


def test_gerar_email_hash_normaliza():
	h1 = gerar_email_hash("  USER@Email.COM  ")
	h2 = gerar_email_hash("user@email.com")
	assert h1 == h2
	# hashes SHA-256 têm 64 chars hex
	assert len(h1) == 64
	assert all(c in "0123456789abcdef" for c in h1)


def test_registrar_exclusao_usuario_cria_registro(session):
	email = "pessoa@exemplo.com"
	antes = datetime.now(timezone.utc)
	out = registrar_exclusao_usuario(session, email)
	depois = datetime.now(timezone.utc)

	assert out.id is not None
	assert out.email_hash == gerar_email_hash(email)
	# Defaults do modelo
	assert out.acao == "exclusao definitiva"
	assert out.responsavel == "usuario"
	assert out.motivo == "pedido do titular"
	assert out.data_hora_exclusao is not None

	# Verifica que timestamp está entre antes e depois (tolerância de segundos)
	dt = out.data_hora_exclusao
	if dt.tzinfo is None:
		# converter naive para UTC para comparação
		dt = dt.replace(tzinfo=timezone.utc)
	assert antes - timedelta(seconds=2) <= dt <= depois + timedelta(seconds=2)

	# Confere que persistiu no banco
	db_item = session.query(LogExclusao).filter(LogExclusao.id == out.id).first()
	assert db_item is not None
	assert db_item.email_hash == out.email_hash


def test_registrar_exclusao_usuario_varias_entradas_mesmo_email(session):
	email = "duplicado@exemplo.com"
	out1 = registrar_exclusao_usuario(session, email)
	out2 = registrar_exclusao_usuario(session, email)
	assert out1.email_hash == out2.email_hash
	# Não há constraint de unicidade; devem existir 2 registros
	total = session.query(LogExclusao).filter(LogExclusao.email_hash == out1.email_hash).count()
	assert total == 2

