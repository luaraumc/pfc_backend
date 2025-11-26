import os
import pytest
from datetime import datetime, timezone, timedelta

os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.services.logExclusao import gerar_email_hash, registrar_exclusao_usuario
from app.models import LogExclusao
from tests.services.utils_test_services import session as session


def test_gerar_email_hash_normaliza():
	"""Gera hash estável independentemente de espaços e caixa do e-mail."""
	h1 = gerar_email_hash("  USER@Email.COM  ")
	h2 = gerar_email_hash("user@email.com")
	assert h1 == h2
	assert len(h1) == 64
	assert all(c in "0123456789abcdef" for c in h1)


def test_registrar_exclusao_usuario_cria_registro(session):
	"""Registra exclusão de usuário e valida dados e timestamp persistido."""
	email = "pessoa@exemplo.com"
	antes = datetime.now(timezone.utc)
	out = registrar_exclusao_usuario(session, email)
	depois = datetime.now(timezone.utc)

	assert out.id is not None
	assert out.email_hash == gerar_email_hash(email)
	assert out.acao == "exclusao definitiva"
	assert out.responsavel == "usuario"
	assert out.motivo == "pedido do titular"
	assert out.data_hora_exclusao is not None
	dt = out.data_hora_exclusao
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	assert antes - timedelta(seconds=2) <= dt <= depois + timedelta(seconds=2)
	db_item = session.query(LogExclusao).filter(LogExclusao.id == out.id).first()
	assert db_item is not None
	assert db_item.email_hash == out.email_hash


def test_registrar_exclusao_usuario_varias_entradas_mesmo_email(session):
	"""Permite múltiplos registros para o mesmo e-mail (sem unicidade)."""
	email = "duplicado@exemplo.com"
	out1 = registrar_exclusao_usuario(session, email)
	out2 = registrar_exclusao_usuario(session, email)
	assert out1.email_hash == out2.email_hash
	total = session.query(LogExclusao).filter(LogExclusao.email_hash == out1.email_hash).count()
	assert total == 2

