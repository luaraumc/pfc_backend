from typing import Any, Dict, List, Set, Tuple
import math

from sqlalchemy.orm import Session

from app.models import (
    Compatibilidade,  # modelo/tabela
    UsuarioHabilidade,
    CarreiraHabilidade,
    Carreira,
    Habilidade,
)
from app.schemas import CompatibilidadeBase, CompatibilidadeOut # schema de entrada e saída

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE - Cria uma nova compatibilidade
def criar_compatibilidade(session, compatibilidade_data: CompatibilidadeBase) -> CompatibilidadeOut:
    nova_compatibilidade = Compatibilidade(**compatibilidade_data.model_dump()) # Cria um objeto Compatibilidade a partir dos dados do schema
    session.add(nova_compatibilidade)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(nova_compatibilidade) # Atualiza o objeto com dados do banco
    return CompatibilidadeOut.model_validate(nova_compatibilidade) # Converte o modelo SQLAlchemy para o schema de saída (CompatibilidadeOut)

# READ - Lista todas as compatibilidades
def listar_compatibilidades(session) -> list[CompatibilidadeOut]:
    compatibilidades = session.query(Compatibilidade).all()  # Busca todas as compatibilidades no banco
    return [CompatibilidadeOut.model_validate(c) for c in compatibilidades] # Converte cada compatibilidade para o schema de saída

# READ - Busca uma compatibilidade pelo id
def buscar_compatibilidade_por_id(session, id: int) -> CompatibilidadeOut | None:
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()  # Busca a compatibilidade pelo id
    return CompatibilidadeOut.model_validate(compatibilidade) if compatibilidade else None # Se encontrada converte para schema de saída, senão retorna None

# UPDATE - Atualiza os dados de uma compatibilidade existente usando schema
def atualizar_compatibilidade(session, id: int, compatibilidade_data: CompatibilidadeBase) -> CompatibilidadeOut | None:
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()  # Busca a compatibilidade pelo id
    if compatibilidade:
        # Atualiza os campos da compatibilidade com os dados recebidos
        for key, value in compatibilidade_data.model_dump(exclude_unset=True).items():
            setattr(compatibilidade, key, value)
        session.commit()
        session.refresh(compatibilidade)
        return CompatibilidadeOut.model_validate(compatibilidade) # Retorna a compatibilidade atualizada como schema de saída
    return None

# DELETE - Remove uma compatibilidade pelo id
def deletar_compatibilidade(session, id: int) -> CompatibilidadeOut | None:
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()  # Busca a compatibilidade pelo id
    if compatibilidade:
        session.delete(compatibilidade)  # Remove do banco
        session.commit()
        return CompatibilidadeOut.model_validate(compatibilidade) # Retorna a compatibilidade removida como schema de saída
    return None
    
# ======================= CÁLCULO EM TEMPO REAL =======================

def _ids_habilidades_do_usuario(session: Session, usuario_id: int) -> Set[int]:
    """Retorna o conjunto de IDs de habilidades que o usuário possui."""
    linhas = (
        session.query(UsuarioHabilidade.habilidade_id)
        .filter(UsuarioHabilidade.usuario_id == usuario_id)
        .all()
    )
    return {habilidade_id for (habilidade_id,) in linhas}


def calcular_compatibilidade_usuario_carreira(
    session: Session,
    usuario_id: int,
    carreira_id: int,
    *,
    min_freq: int | None = None,
    coverage_ratio: float | None = 0.8,
) -> Dict[str, Any]:
    """
    Calcula a compatibilidade (0 a 100) do usuário para uma carreira específica,
    ponderando pelas frequências de CarreiraHabilidade.

    Fórmula:
    percentual = 100 * soma(freq das habilidades da carreira que o usuário possui) / soma(freq de todas as habilidades da carreira)

    Retorna um dicionário com:
    - carreira_id, carreira_nome
    - percentual (float 0..100 com 2 casas)
    - peso_coberto (int), peso_total (int)
    - habilidades_cobertas (lista de nomes)
    """
    carreira = session.query(Carreira).filter(Carreira.id == carreira_id).first()
    if not carreira:
        return {
            "carreira_id": carreira_id,
            "carreira_nome": None,
            "percentual": 0.0,
            "peso_coberto": 0,
            "peso_total": 0,
            "habilidades_cobertas": [],
        }

    habilidades_usuario = _ids_habilidades_do_usuario(session, usuario_id)

    # Coleta frequências da carreira
    relacoes: List[Tuple[int, int]] = (
        session.query(CarreiraHabilidade.habilidade_id, CarreiraHabilidade.frequencia)
        .filter(CarreiraHabilidade.carreira_id == carreira.id)
        .all()
    )

    # Aplica filtro por freq mínima (se configurado) e transforma pesos
    def calcular_peso(frequencia_valor: int) -> float:
        """Retorna o peso real (frequência bruta) da habilidade."""
        # Como a frequência no banco já representa a importância,
        # usamos diretamente o valor sem transformações.
        return float(frequencia_valor)

    habilidades_consideradas: List[Tuple[int, float]] = []  # (habilidade_id, peso_transformado)
    for habilidade_id, frequencia in relacoes:
        frequencia_int = int(frequencia)
        if min_freq is not None and frequencia_int < int(min_freq):
            continue
        habilidades_consideradas.append((habilidade_id, calcular_peso(frequencia_int)))

    # Soma total considerando filtro/transformação
    peso_total_considerado = sum(peso for _, peso in habilidades_consideradas)

    # Define o denominador com base no coverage_ratio (núcleo da carreira)
    ids_nucleo: Set[int] = set()
    denominador = peso_total_considerado
    if (
        coverage_ratio is not None
        and isinstance(coverage_ratio, (int, float))
        and 0 < float(coverage_ratio) < 1
        and peso_total_considerado > 0
    ):
        alvo = float(coverage_ratio) * peso_total_considerado
        # Ordena por peso decrescente
        ordenadas = sorted(habilidades_consideradas, key=lambda t: t[1], reverse=True)
        acumulado = 0.0
        for habilidade_id, peso in ordenadas:
            ids_nucleo.add(habilidade_id)
            acumulado += peso
            if acumulado >= alvo:
                break
        denominador = acumulado
    else:
        ids_nucleo = {habilidade_id for habilidade_id, _ in habilidades_consideradas}

    # Peso coberto apenas do núcleo
    peso_coberto = sum(
        peso
        for habilidade_id, peso in habilidades_consideradas
        if habilidade_id in ids_nucleo and habilidade_id in habilidades_usuario
    )

    # Evita divisão por zero
    percentual = 0.0 if denominador <= 0 else round(100.0 * (peso_coberto / float(denominador)), 2)

    # Busca nomes das habilidades cobertas (núcleo intersect usuário)
    habilidades_nomes: List[str] = []
    ids_cobertos = [
        habilidade_id for habilidade_id, _ in habilidades_consideradas if habilidade_id in ids_nucleo and habilidade_id in habilidades_usuario
    ]
    if ids_cobertos:
        nomes_habilidades = (
            session.query(Habilidade.nome)
            .filter(Habilidade.id.in_(ids_cobertos))
            .all()
        )
        habilidades_nomes = [nome for (nome,) in nomes_habilidades]

    return {
        "carreira_id": carreira.id,
        "carreira_nome": carreira.nome,
        "percentual": percentual,
        "peso_coberto": round(float(peso_coberto), 4),
        "peso_total": round(float(peso_total_considerado), 4),
        "habilidades_cobertas": habilidades_nomes,
    }


def top_n_carreiras_por_usuario(
    session: Session,
    usuario_id: int,
    n: int | None = None,
    *,
    min_freq: int | None = None,
    coverage_ratio: float | None = 0.8,
) -> List[Dict[str, Any]]:
    """
    Retorna o Top N de carreiras para um usuário com base na fórmula ponderada.
    Se n for None, retorna todas as carreiras ordenadas.
    Ordena por:
      1) percentual desc
      2) peso_coberto desc
      3) peso_total desc
      4) carreira_nome asc (para desempate determinístico)
    """
    carreiras = session.query(Carreira).all()
    resultados: List[Dict[str, Any]] = []
    for carreira_item in carreiras:
        resultado = calcular_compatibilidade_usuario_carreira(
            session,
            usuario_id,
            carreira_item.id,
            min_freq=min_freq,
            coverage_ratio=coverage_ratio,
        )
        resultados.append(resultado)

    resultados.sort(
        key=lambda r: (
            r.get("percentual", 0.0),
            r.get("peso_coberto", 0),
            r.get("peso_total", 0),
            (r.get("carreira_nome") or "").lower(),
        ),
        reverse=True,
    )
    if n is None:
        return resultados
    return resultados[: max(0, n)]
