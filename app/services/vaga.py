from app.models import Vaga, Habilidade, VagaHabilidade, CarreiraHabilidade, Categoria # modelos de tabela definidos no arquivo models.py
from app.schemas import VagaBase, VagaOut # schema de entrada e saída
from sqlalchemy.orm import Session # manipular sessões do banco de dados
from sqlalchemy.exc import IntegrityError
from app.services.extracao import padronizar_descricao, extrair_habilidades_descricao, normalizar_habilidade, deduplicar # funções de extração e padronização

# ======================= CRUD =======================

# DELETE / DELETE - Exclui a vaga decrementando frequências das habilidades na carreira
def excluir_vaga_decrementando(session: Session, vaga_id: int) -> bool:
    """
    Exclui a vaga e ajusta a frequência das habilidades associadas à carreira da vaga.
    - Decrementa 1 na frequência das relações CarreiraHabilidade correspondentes às habilidades da vaga.
    - Remove a relação CarreiraHabilidade quando a frequência atingir 0.
    - Remove a vaga (e suas relações VagaHabilidade por cascata, se configurado) ao final.
    Retorna True se excluiu, False se a vaga não existe.
    """
    vaga = session.query(Vaga).filter(Vaga.id == vaga_id).first()
    if not vaga:
        return False

    # Coleta habilidades associadas à vaga
    rels_vh = session.query(VagaHabilidade.habilidade_id).filter(
        VagaHabilidade.vaga_id == vaga_id
    ).all()
    habilidade_ids = [hid for (hid,) in rels_vh] if rels_vh else []

    # Ajusta frequências na carreira relacionada
    if vaga.carreira_id and habilidade_ids:
        rels_ch = session.query(CarreiraHabilidade).filter(
            CarreiraHabilidade.carreira_id == vaga.carreira_id,
            CarreiraHabilidade.habilidade_id.in_(habilidade_ids)
        ).all()
        for rel in rels_ch:
            atual = rel.frequencia or 0
            nova = max(0, atual - 1)
            if nova == 0:
                # zera e remove a relação (para não impactar contagens futuras)
                session.delete(rel)
            else:
                rel.frequencia = nova

    # Exclui a vaga (relações VagaHabilidade devem ser removidas por CASCADE se mapeado)
    session.delete(vaga)
    session.commit()
    return True

# CREATE (básico) / POST - Cria a vaga sem processar habilidades (prévia)
def criar_vaga_basica(session: Session, vaga_data: VagaBase) -> VagaOut:
    """
    Cria um registro de vaga com título/descrição/carreira padronizando a descrição,
    sem processar habilidades ainda (usado para o fluxo em duas etapas com preview).
    """
    # Padroniza descrição antes de salvar
    vaga_data.descricao = padronizar_descricao(vaga_data.descricao)
    nova_vaga = Vaga(**vaga_data.model_dump())
    session.add(nova_vaga)
    try:
        session.commit()
    except IntegrityError as e:
        # Trata duplicidade de descrição (constraint unique)
        session.rollback()
        msg = str(getattr(e, "orig", e)).lower()
        if "uq_vaga_descricao" in msg or ("unique" in msg and "descricao" in msg) or "duplicate key" in msg:
            # Use um ValueError sem acoplar ao FastAPI aqui; a rota converterá para HTTP 409
            raise ValueError("DUPLICATE_VAGA_DESCRICAO")
        # Propaga outros erros de integridade
        raise
    session.refresh(nova_vaga)
    return VagaOut.model_validate({
        "id": nova_vaga.id,
        "titulo": nova_vaga.titulo,
        "descricao": nova_vaga.descricao,
        "carreira_id": nova_vaga.carreira_id,
        "carreira_nome": nova_vaga.carreira.nome if nova_vaga.carreira else None,
    })

# PREVIEW - Extrai habilidades da descrição da vaga sem salvar
def extrair_habilidades_vaga(session: Session, vaga_id: int) -> list[str]:
    vaga = session.query(Vaga).filter(Vaga.id == vaga_id).first()
    if not vaga:
        return []
    # usa a versão atual da extração que aceita sessão e retorna apenas os nomes para o preview
    itens = extrair_habilidades_descricao(vaga.descricao, session=session)
    nomes = []
    vistos = set()
    for item in itens:
        nome = item.get("nome") if isinstance(item, dict) else str(item)
        chave = deduplicar(nome)
        if chave not in vistos:
            vistos.add(chave)
            nomes.append(nome)
    return nomes

# CONFIRMAR - Confirma lista final de habilidades para a vaga e associa/incrementa na carreira
def confirmar_habilidades_vaga(session: Session, vaga_id: int, habilidades_finais: list[str]) -> dict:
    vaga = session.query(Vaga).filter(Vaga.id == vaga_id).first()
    if not vaga:
        raise ValueError("Vaga não encontrada")

    # Obtem sugestões de categoria da IA para esta descrição (mapeadas por chave dedup)
    itens_sugeridos = extrair_habilidades_descricao(vaga.descricao, session=session)
    categoria_por_chave: dict[str, str | None] = {}
    for item in itens_sugeridos:
        nome = item.get("nome") if isinstance(item, dict) else str(item)
        cat_sug = item.get("categoria_sugerida") if isinstance(item, dict) else None
        chave = deduplicar(normalizar_habilidade(nome, session=session))
        if chave not in categoria_por_chave:
            categoria_por_chave[chave] = cat_sug

    # Normaliza e deduplica conforme lógica atual (usando session e deduplicação)
    vistos = set()
    finais_norm = []
    for h in habilidades_finais:
        h_norm = normalizar_habilidade(h, session=session)
        chave = deduplicar(h_norm)
        if chave not in vistos:
            vistos.add(chave)
            finais_norm.append(h_norm)

    habilidades_criadas = []
    habilidades_ja_existiam = []

    for nome_padronizado in finais_norm:
        # Verifica se já existe (case-insensitive)
        habilidade = session.query(Habilidade).filter(Habilidade.nome.ilike(nome_padronizado)).first()
        if not habilidade:
            # Usa a categoria sugerida pela IA para esta habilidade; se ausente, "categoria pendente"
            chave = deduplicar(nome_padronizado)
            categoria_sugerida = categoria_por_chave.get(chave)
            categoria_nome = categoria_sugerida or "categoria pendente"
            # busca ou cria a categoria pelo nome definido
            categoria = session.query(Categoria).filter(Categoria.nome.ilike(categoria_nome)).first()
            if not categoria:
                categoria = Categoria(nome=categoria_nome)
                session.add(categoria)
                session.flush()
            habilidade = Habilidade(nome=nome_padronizado, categoria_id=categoria.id)
            session.add(habilidade)
            session.flush()
            habilidades_criadas.append(nome_padronizado)
        else:
            habilidades_ja_existiam.append(nome_padronizado)

        # Associa à vaga (se ainda não existe a relação)
        existe_rel_vaga = session.query(VagaHabilidade).filter_by(
            vaga_id=vaga.id, habilidade_id=habilidade.id
        ).first()
        if not existe_rel_vaga:
            session.add(VagaHabilidade(vaga_id=vaga.id, habilidade_id=habilidade.id))

        # Associa/incrementa na carreira conforme lógica atual (frequência)
        if vaga.carreira_id:
            rel_carreira = session.query(CarreiraHabilidade).filter_by(
                carreira_id=vaga.carreira_id, habilidade_id=habilidade.id
            ).first()
            if rel_carreira:
                rel_carreira.frequencia += 1
            else:
                rel_carreira = CarreiraHabilidade(
                    carreira_id=vaga.carreira_id,
                    habilidade_id=habilidade.id,
                    frequencia=1
                )
                session.add(rel_carreira)

    session.commit()
    session.refresh(vaga)

    return {
        "id": vaga.id,
        "titulo": vaga.titulo,
        "descricao": vaga.descricao,
        "carreira_id": vaga.carreira_id,
        "carreira_nome": vaga.carreira.nome if vaga.carreira else None,
        "habilidades_criadas": habilidades_criadas,
        "habilidades_ja_existiam": habilidades_ja_existiam,
    }

# CREATE / POST - Cria uma nova vaga e processa habilidades
def criar_vaga(session: Session, vaga_data: VagaBase) -> dict:

    # Padroniza a descrição
    vaga_data.descricao = padronizar_descricao(vaga_data.descricao)

    # Cria a vaga
    nova_vaga = Vaga(**vaga_data.model_dump())
    session.add(nova_vaga)
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        msg = str(getattr(e, "orig", e)).lower()
        if "uq_vaga_descricao" in msg or ("unique" in msg and "descricao" in msg) or "duplicate key" in msg:
            # Mapeie para ValueError para a rota responder 409
            raise ValueError("DUPLICATE_VAGA_DESCRICAO")
        raise
    session.refresh(nova_vaga)

    # Extrai habilidades
    itens_extraidos = extrair_habilidades_descricao(nova_vaga.descricao, session=session)

    # Deduplica mantendo sugestão de categoria por nome normalizado
    vistos = set()
    finais = []  # nomes normalizados finais
    categoria_por_chave: dict[str, str | None] = {}
    for item in itens_extraidos:
        nome = item.get("nome") if isinstance(item, dict) else str(item)
        cat_sug = item.get("categoria_sugerida") if isinstance(item, dict) else None
        h_norm = normalizar_habilidade(nome, session=session)
        chave = deduplicar(h_norm)
        if chave not in vistos:
            vistos.add(chave)
            finais.append(h_norm)
            categoria_por_chave[chave] = cat_sug

    habilidades_criadas = []
    habilidades_ja_existiam = []

    # Processa habilidades no banco
    for nome_padronizado in finais:
        # Verifica se já existe
        habilidade = session.query(Habilidade).filter(Habilidade.nome.ilike(nome_padronizado)).first()
        # Cria se não existir
        if not habilidade:
            # Usa sugestão da IA; se ausente, usa "categoria pendente" (sem heurística)
            chave = deduplicar(nome_padronizado)
            categoria_sugerida = categoria_por_chave.get(chave)
            categoria_nome = categoria_sugerida or "categoria pendente"
            categoria = session.query(Categoria).filter(Categoria.nome.ilike(categoria_nome)).first()
            if not categoria:
                categoria = Categoria(nome=categoria_nome)
                session.add(categoria)
                session.flush()
            habilidade = Habilidade(nome=nome_padronizado, categoria_id=categoria.id)
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

    # Retorna nomes de habilidades extraídas para compatibilidade com schema
    habilidades_extraidas_nomes = [item.get("nome") if isinstance(item, dict) else str(item) for item in itens_extraidos]

    return {
        "id": nova_vaga.id,
        "titulo": nova_vaga.titulo,
        "descricao": nova_vaga.descricao,
        "carreira_id": nova_vaga.carreira_id,
        "carreira_nome": nova_vaga.carreira.nome if nova_vaga.carreira else None,
        "habilidades_extraidas": habilidades_extraidas_nomes,
        "habilidades_criadas": habilidades_criadas,
        "habilidades_ja_existiam": habilidades_ja_existiam
    }

# READ / GET - Lista todas as vagas
def listar_vagas(session: Session) -> list[VagaOut]:
    vagas = session.query(Vaga).order_by(Vaga.criado_em.desc()).all()
    # Precisa montar carreira_nome manualmente, pois o ORM não possui esse atributo diretamente
    resultado: list[VagaOut] = []
    for v in vagas:
        item = {
            "id": v.id,
            "titulo": v.titulo,
            "descricao": v.descricao,
            "carreira_id": v.carreira_id,
            "carreira_nome": v.carreira.nome if getattr(v, "carreira", None) else None,
        }
        resultado.append(VagaOut.model_validate(item))
    return resultado

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
