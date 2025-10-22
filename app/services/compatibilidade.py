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
