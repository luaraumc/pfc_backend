import hashlib # para hashing de emails
from datetime import datetime # para timestamps
from sqlalchemy.orm import Session # para interagir com o banco de dados
from app.models import LogExclusao # modelo da tabela de log de exclusões
from app.schemas import LogExclusaoBase, LogExclusaoOut # schemas para validação e saída

# Gera um hash SHA-256 irreversível do email
def gerar_email_hash(email: str) -> str:
    email_normalizado = email.strip().lower() # normaliza email (removendo espaços e convertendo para minúsculas)
    return hashlib.sha256(email_normalizado.encode('utf-8')).hexdigest() # gera hash

# Registra a exclusão definitiva de um usuário na tabela de log
def registrar_exclusao_usuario(session: Session, email: str) -> LogExclusaoOut:
    email_hash = gerar_email_hash(email) # gera hash do email
    log_data = LogExclusaoBase(email_hash=email_hash) # cria dados do log
    log_model = LogExclusao(**log_data.model_dump()) # instancia o modelo
    if not log_model.data_hora_exclusao: 
        log_model.data_hora_exclusao = datetime.utcnow() # garante timestamp
    session.add(log_model) # adiciona à sessão
    session.commit() # salva no banco
    session.refresh(log_model) # atualiza o modelo com dados do banco
    return LogExclusaoOut.model_validate(log_model) # retorna dados validados do log
