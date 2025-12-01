import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.logExclusaoModels import LogExclusao
from app.schemas.logExclusaoSchemas import LogExclusaoBase, LogExclusaoOut

def gerar_email_hash(email: str) -> str:
    """Gera um hash SHA-256 irreversível do email normalizado para armazenamento seguro"""
    email_normalizado = email.strip().lower()
    return hashlib.sha256(email_normalizado.encode('utf-8')).hexdigest()

def registrar_exclusao_usuario(session: Session, email: str) -> LogExclusaoOut:
    """Registra a exclusão definitiva de um usuário na tabela de log usando hash do email para auditoria"""
    email_hash = gerar_email_hash(email)
    log_data = LogExclusaoBase(email_hash=email_hash)
    log_model = LogExclusao(**log_data.model_dump())
    if not log_model.data_hora_exclusao: 
        log_model.data_hora_exclusao = datetime.utcnow()
    session.add(log_model)
    session.commit()
    session.refresh(log_model)
    return LogExclusaoOut.model_validate(log_model)
