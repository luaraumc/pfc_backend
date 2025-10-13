from app.models import Vaga, Habilidade, VagaHabilidade, CarreiraHabilidade # modelos de tabela definidos no arquivo models.py
from app.schemas import VagaBase, VagaOut # schema de entrada e saída
from sqlalchemy.orm import Session # manipular sessões do banco de dados
from app.services.extracao import padronizar_descricao, extrair_habilidades_descricao, normalizar_habilidade, deduplicar # funções de extração e padronização

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova vaga e processa habilidades
def criar_vaga(session: Session, vaga_data: VagaBase) -> dict:

    """
    Cria uma nova vaga:
    - Padroniza descrição
    - Extrai habilidades
    - Cria habilidades novas
    - Associa habilidades à vaga e à carreira
    - Incrementa frequência das habilidades na carreira
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

    vistos = set() # conjunto para rastrear habilidades já vistas
    finais = [] # lista final de habilidades deduplicadas

    # Deduplica habilidades extraídas
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
        # Cria se não existir
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
        # Cria nova associação se não existir
        if not existe_rel_vaga:
            session.add(VagaHabilidade(vaga_id=nova_vaga.id, habilidade_id=habilidade.id))
        # Associa à carreira
        if nova_vaga.carreira_id:
            rel_carreira = session.query(CarreiraHabilidade).filter_by(
                carreira_id=nova_vaga.carreira_id, habilidade_id=habilidade.id
            ).first()
            # Incrementa frequência se já existir
            if rel_carreira:
                rel_carreira.frequencia += 1
            # Cria nova associação com frequência inicial 1
            else:
                rel_carreira = CarreiraHabilidade(
                    carreira_id=nova_vaga.carreira_id,
                    habilidade_id=habilidade.id,
                    frequencia=1
                )
                session.add(rel_carreira)
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
<<<<<<< HEAD
=======

# DELETE / DELETE - Remove a relação vaga-habilidade
def remover_relacao_vaga_habilidade(session, vaga_id: int, habilidade_id: int) -> bool:
    relacao = (
        session.query(VagaHabilidade)
        .filter_by(vaga_id=vaga_id, habilidade_id=habilidade_id)
        .first()
    )
    if not relacao:
        return False
    session.delete(relacao)
    session.commit()
    return True
>>>>>>> fb21101de33e1a7ccbf9bf911c04c85d1a1b802b
