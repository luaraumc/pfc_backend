from app.models import Vaga, Habilidade, VagaHabilidade, CarreiraHabilidade
from app.schemas import VagaBase, VagaOut
from sqlalchemy.orm import Session
from app.services.extracao import padronizar_descricao, extrair_habilidades_descricao, normalizar_habilidade, deduplicar

# ======================= CRUD =======================

def criar_vaga(session: Session, vaga_data: VagaBase) -> dict:
    """
    Cria uma nova vaga:
    - Padroniza descrição
    - Extrai habilidades
    - Cria habilidades novas
    - Associa habilidades à vaga e à carreira
    Retorna info detalhada para frontend
    """

    # Padroniza a descrição
    vaga_data.descricao = padronizar_descricao(vaga_data.descricao)

    # Cria a vaga
    nova_vaga = Vaga(**vaga_data.model_dump())
    session.add(nova_vaga)
    session.commit()
    session.refresh(nova_vaga)

    # Extrai habilidades
    habilidades_extraidas = extrair_habilidades_descricao(nova_vaga.descricao)

    vistos = set()
    finais = []
    for h in habilidades_extraidas:
        h_norm = normalizar_habilidade(h)
        chave = deduplicar(h_norm)
        if chave not in vistos:
            vistos.add(chave)
            finais.append(h_norm)

    habilidades_criadas = []
    habilidades_ja_existiam = []

    # Processa habilidades no banco
    for nome_padronizado in finais:
        # Verifica se já existe
        habilidade = session.query(Habilidade).filter(Habilidade.nome.ilike(nome_padronizado)).first()
        if not habilidade:
            habilidade = Habilidade(nome=nome_padronizado)
            session.add(habilidade)
            session.flush()
            habilidades_criadas.append(nome_padronizado)
        else:
            habilidades_ja_existiam.append(nome_padronizado)

        # Associa à vaga
        existe_rel_vaga = session.query(VagaHabilidade).filter_by(
            vaga_id=nova_vaga.id, habilidade_id=habilidade.id
        ).first()
        if not existe_rel_vaga:
            session.add(VagaHabilidade(vaga_id=nova_vaga.id, habilidade_id=habilidade.id))

        # Associa à carreira, se houver
        if nova_vaga.carreira_id:
            existe_rel_carreira = session.query(CarreiraHabilidade).filter_by(
                carreira_id=nova_vaga.carreira_id, habilidade_id=habilidade.id
            ).first()
            if not existe_rel_carreira:
                session.add(CarreiraHabilidade(carreira_id=nova_vaga.carreira_id, habilidade_id=habilidade.id))

    session.commit()
    session.refresh(nova_vaga)

    return {
        "id": nova_vaga.id,
        "titulo": nova_vaga.titulo,
        "descricao": nova_vaga.descricao,
        "carreira_id": nova_vaga.carreira_id,
        "carreira_nome": nova_vaga.carreira.nome if nova_vaga.carreira else None,
        "habilidades_extraidas": habilidades_extraidas,
        "habilidades_criadas": habilidades_criadas,
        "habilidades_ja_existiam": habilidades_ja_existiam
    }

# READ / GET - Lista todas as vagas
def listar_vagas(session: Session) -> list[VagaOut]:
    vagas = session.query(Vaga).order_by(Vaga.criado_em.desc()).all()
    return [VagaOut.model_validate(v) for v in vagas]

