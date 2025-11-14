import os
import sys
from contextlib import contextmanager
from typing import Generator, Iterable, List, Optional, Tuple, Union


def _set_env_defaults() -> None:
    os.environ.setdefault("KEY_CRYPT", "k")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    # Vars de DB apenas para evitar falha em imports que constroem engine não usado
    os.environ.setdefault("DB_USER", "u")
    os.environ.setdefault("DB_PASSWORD", "p")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    os.environ.setdefault("DB_NAME", "db")


def _fresh_imports():
    # Garante que env está aplicado antes dos imports
    for m in ("app.main", "app.models", "app.dependencies"):
        sys.modules.pop(m, None)


@contextmanager
def app_client_context(
    override_admin: bool = False,
    patch_email_modules: Optional[Iterable[str]] = None,
):
    """
    Prepara app FastAPI com SQLite em memória, session override, e opções adicionais.

    - override_admin: quando True, libera rotas protegidas por admin.
    - patch_email_modules: nomes de módulos a receberem um enviar_email fake que
      captura (dest, code) numa lista.

    Yield:
      (client, TestingSessionLocal) ou (client, TestingSessionLocal, captured_codes)
    """
    _set_env_defaults()
    _fresh_imports()

    # Cria engine in-memory com FKs habilitados
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models import Base  # noqa: WPS433

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", lambda dbapi_conn, _: dbapi_conn.execute("PRAGMA foreign_keys=ON"))

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    from app.main import app  # noqa: WPS433
    from app.dependencies import pegar_sessao  # noqa: WPS433

    # Override sessão
    def _override_session():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[pegar_sessao] = _override_session

    # Admin
    if override_admin:
        from app.dependencies import requer_admin  # noqa: WPS433

        app.dependency_overrides[requer_admin] = lambda: {"admin": True}

    # Patch de envio de email
    captured_codes: Optional[List[Tuple[str, str]]] = None
    if patch_email_modules:
        captured_codes = []

        def _mk_fake(captured):
            def _fake(dest, code):
                captured.append((dest, code))
                return {"id": "fake"}

            return _fake

        for modname in patch_email_modules:
            mod = sys.modules.get(modname)
            if mod is None:
                mod = __import__(modname, fromlist=["*"])
            setattr(mod, "enviar_email", _mk_fake(captured_codes))

    # Cria client
    from fastapi.testclient import TestClient  # noqa: WPS433

    client = TestClient(app)

    try:
        if captured_codes is None:
            yield client, TestingSessionLocal
        else:
            yield client, TestingSessionLocal, captured_codes
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


# -------------- Helpers de seed/criação comuns --------------

def seed_carreira_curso(SessionLocal) -> Tuple[int, int]:
    from app.models import Carreira, Curso

    db = SessionLocal()
    try:
        car = Carreira(nome="Dados", descricao="Desc")
        cur = Curso(nome="Ciência de Dados", descricao="Desc")
        db.add_all([car, cur])
        db.commit()
        db.refresh(car)
        db.refresh(cur)
        return car.id, cur.id
    finally:
        db.close()


def criar_carreira(SessionLocal, nome: str = "Carreira X", desc: str = "desc") -> int:
    from app.models import Carreira

    db = SessionLocal()
    try:
        c = Carreira(nome=nome, descricao=desc)
        db.add(c)
        db.commit()
        db.refresh(c)
        return c.id
    finally:
        db.close()


def criar_curso(SessionLocal, nome: str = "ADS", desc: str = "desc") -> int:
    from app.models import Curso

    db = SessionLocal()
    try:
        c = Curso(nome=nome, descricao=desc)
        db.add(c)
        db.commit()
        db.refresh(c)
        return c.id
    finally:
        db.close()


def criar_conhecimento(SessionLocal, nome: str = "Python") -> int:
    from app.models import Conhecimento

    db = SessionLocal()
    try:
        c = Conhecimento(nome=nome)
        db.add(c)
        db.commit()
        db.refresh(c)
        return c.id
    finally:
        db.close()


def criar_categoria(SessionLocal, nome: str = "Backend") -> int:
    from app.models import Categoria

    db = SessionLocal()
    try:
        c = Categoria(nome=nome)
        db.add(c)
        db.commit()
        db.refresh(c)
        return c.id
    finally:
        db.close()


def criar_habilidade(SessionLocal, nome: str = "Python", categoria_id: Optional[int] = None) -> int:
    from app.models import Habilidade

    if categoria_id is None:
        raise AssertionError("categoria_id é obrigatório para criar habilidade")
    db = SessionLocal()
    try:
        h = Habilidade(nome=nome, categoria_id=categoria_id)
        db.add(h)
        db.commit()
        db.refresh(h)
        return h.id
    finally:
        db.close()


def buscar_carreira_habilidade(SessionLocal, carreira_id: int, habilidade_id: int):
    from app.models import CarreiraHabilidade

    db = SessionLocal()
    try:
        return (
            db.query(CarreiraHabilidade)
            .filter_by(carreira_id=carreira_id, habilidade_id=habilidade_id)
            .first()
        )
    finally:
        db.close()


def relacionar_carreira_habilidade(SessionLocal, carreira_id: int, habilidade_id: int, frequencia: int = 1) -> None:
    from app.models import CarreiraHabilidade

    db = SessionLocal()
    try:
        rel = CarreiraHabilidade(
            carreira_id=carreira_id,
            habilidade_id=habilidade_id,
            frequencia=frequencia,
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)
    finally:
        db.close()


def add_usuario_habilidade(SessionLocal, usuario_id: int, habilidade_id: int) -> int:
    from app.models import UsuarioHabilidade

    db = SessionLocal()
    try:
        rel = UsuarioHabilidade(usuario_id=usuario_id, habilidade_id=habilidade_id)
        db.add(rel)
        db.commit()
        db.refresh(rel)
        return rel.id
    finally:
        db.close()


def seed_conhecimento_categoria(SessionLocal) -> Tuple[int, int]:
    """Cria (Conhecimento, Categoria) com sufixos para evitar UNIQUE."""
    from app.models import Conhecimento, Categoria

    db = SessionLocal()
    try:
        count = db.query(Categoria).count() if hasattr(db, "query") else 0
        suf = count + 1
        con = Conhecimento(nome=f"Python{suf}")
        cat = Categoria(nome=f"Backend{suf}")
        db.add_all([con, cat])
        db.commit()
        db.refresh(con)
        db.refresh(cat)
        return con.id, cat.id
    finally:
        db.close()


def seed_usuario(
    SessionLocal,
    nome: str = "Fulano",
    email: str = "f@e.com",
    senha: str = "hash",
    carreira_id: Optional[int] = None,
    curso_id: Optional[int] = None,
    admin: bool = False,
) -> int:
    from app.models import Usuario

    db = SessionLocal()
    try:
        u = Usuario(
            nome=nome,
            email=email,
            senha=senha,
            admin=admin,
            carreira_id=carreira_id,
            curso_id=curso_id,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id
    finally:
        db.close()


def find_habilidade_by_id(SessionLocal, habilidade_id: int) -> Tuple[Optional[int], Optional[str]]:
    from app.models import Habilidade

    db = SessionLocal()
    try:
        name = db.query(Habilidade.nome).filter(Habilidade.id == habilidade_id).scalar()
        return habilidade_id, name
    finally:
        db.close()


def find_habilidade_by_name(SessionLocal, name: str) -> Optional[int]:
    from app.models import Habilidade

    db = SessionLocal()
    try:
        return db.query(Habilidade.id).filter(Habilidade.nome == name).scalar()
    finally:
        db.close()
