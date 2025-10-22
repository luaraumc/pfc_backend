from app.models import Vaga, Habilidade, VagaHabilidade, CarreiraHabilidade, Categoria # modelos de tabela definidos no arquivo models.py
from app.schemas import VagaBase, VagaOut # schema de entrada e saída
from sqlalchemy.orm import Session # manipular sessões do banco de dados
from sqlalchemy.exc import IntegrityError # capturar erros de integridade do banco de dados
from app.services.extracao import padronizar_descricao, extrair_habilidades_descricao, normalizar_habilidade, deduplicar # funções de extração e padronização

# ======================= CRUD =======================

# CREATE / POST - Cria a vaga sem processar habilidades
def criar_vaga(session: Session, vaga_data: VagaBase) -> VagaOut:
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
def extrair_habilidades_vaga(session: Session, vaga_id: int) -> list[dict]:
    vaga = session.query(Vaga).filter(Vaga.id == vaga_id).first()
    if not vaga:
        return []
    # usa a versão atual da extração que aceita sessão e retorna apenas os nomes para o preview
    itens = extrair_habilidades_descricao(vaga.descricao, session=session)
    finais: list[dict] = []
    vistos = set()
    for item in itens:
        nome = item.get("nome") if isinstance(item, dict) else str(item)
        cat_sug = item.get("categoria_sugerida") if isinstance(item, dict) else None
        chave = deduplicar(nome)
        if chave not in vistos and nome:
            vistos.add(chave)
            # Verifica se a habilidade já existe no banco
            habilidade_db = session.query(Habilidade).filter(Habilidade.nome.ilike(nome)).first()
            habilidade_id = habilidade_db.id if habilidade_db else ""
            # Se existir no banco, preferir a categoria atual do banco
            if habilidade_db and habilidade_db.categoria_id:
                categoria_id = habilidade_db.categoria_id
                categoria_nome = session.query(Categoria.nome).filter(Categoria.id == habilidade_db.categoria_id).scalar() or ""
            else:
                # Caso contrário, tenta casar sugestão com categoria existente
                categoria_id = ""
                categoria_nome = ""
                if cat_sug:
                    cat_db = session.query(Categoria).filter(Categoria.nome.ilike(cat_sug)).first()
                    if cat_db:
                        categoria_id = cat_db.id
                        categoria_nome = cat_db.nome
            finais.append({
                "nome": nome,
                "habilidade_id": habilidade_id,
                "categoria_sugerida": cat_sug,
                "categoria_id": categoria_id,
                "categoria_nome": categoria_nome,
                "categoria": categoria_nome,
            })
    return finais

# CONFIRMAR - Confirma lista final de habilidades para a vaga e associa na carreira
def confirmar_habilidades_vaga(session: Session, vaga_id: int, habilidades_finais: list) -> dict:
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
    # Agora aceitamos objetos com nome, categoria_id e habilidade_id
    vistos = set()
    finais_norm: list[dict] = []  # cada item: { nome_norm, categoria_id?, habilidade_id? }
    for h in habilidades_finais:
        if isinstance(h, dict):
            nome_raw = h.get("nome") or h.get("name") or ""
            categoria_id_raw = h.get("categoria_id") or h.get("category_id") or ""
            habilidade_id_raw = h.get("habilidade_id") or h.get("skill_id") or ""
        else:
            nome_raw = str(h)
            categoria_id_raw = ""
            habilidade_id_raw = ""
        nome_norm = normalizar_habilidade(nome_raw, session=session)
        chave = deduplicar(nome_norm)
        if chave in vistos:
            continue
        vistos.add(chave)
        finais_norm.append({
            "nome": nome_norm,
            "categoria_id": categoria_id_raw,
            "habilidade_id": habilidade_id_raw,
        })

    habilidades_criadas = []
    habilidades_ja_existiam = []

    for item in finais_norm:
        nome_padronizado = item["nome"]
        categoria_id_informada = item.get("categoria_id")
        habilidade_id_informada = item.get("habilidade_id")

        habilidade = None
        if habilidade_id_informada:
            habilidade = session.query(Habilidade).filter(Habilidade.id == habilidade_id_informada).first()
        if not habilidade:
            # Verifica por nome (case-insensitive)
            habilidade = session.query(Habilidade).filter(Habilidade.nome.ilike(nome_padronizado)).first()

        if not habilidade:
            # Usa a categoria sugerida pela IA para esta habilidade; se ausente, "categoria pendente"
            chave = deduplicar(nome_padronizado)
            categoria_sugerida = categoria_por_chave.get(chave)
            categoria = None
            if categoria_id_informada:
                categoria = session.query(Categoria).filter(Categoria.id == categoria_id_informada).first()
            if not categoria and categoria_sugerida:
                categoria = session.query(Categoria).filter(Categoria.nome.ilike(categoria_sugerida)).first()
            if not categoria:
                # fallback estrito: não criar novas categorias com o nome sugerido; usar/garantir 'categoria pendente'
                categoria = session.query(Categoria).filter(Categoria.nome.ilike("categoria pendente")).first()
                if not categoria:
                    categoria = Categoria(nome="categoria pendente")
                    session.add(categoria)
                    session.flush()
            habilidade = Habilidade(nome=nome_padronizado, categoria_id=categoria.id)
            session.add(habilidade)
            session.flush()
            habilidades_criadas.append(nome_padronizado)
        else:
            # Atualiza nome/categoria se informado
            if habilidade.nome.lower() != nome_padronizado.lower():
                conflito = session.query(Habilidade).filter(Habilidade.nome.ilike(nome_padronizado)).first()
                if conflito and conflito.id != habilidade.id:
                    raise ValueError(f"Já existe uma habilidade com o nome '{nome_padronizado}'.")
                habilidade.nome = nome_padronizado
            # Atualizar categoria se fornecida e existir
            if categoria_id_informada:
                categoria_db = session.query(Categoria).filter(Categoria.id == categoria_id_informada).first()
                if categoria_db:
                    habilidade.categoria_id = categoria_db.id
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
