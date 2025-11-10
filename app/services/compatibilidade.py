from typing import Any, Dict, List, Set, Tuple # tipos para anotações
from sqlalchemy.orm import Session # sessões para interagir com o banco
from app.models.usuarioHabilidadeModels import UsuarioHabilidade
from app.models.carreiraHabilidadeModels import CarreiraHabilidade
from app.models.carreiraModels import Carreira
from app.models.habilidadeModels import Habilidade 

# Configuração padrão centralizada para evitar duplicação de literais
DEFAULT_MIN_FREQ: int | None = 3  # filtra habilidades com frequência >= 3 (exclui as que aparecem apenas 1 vez)
DEFAULT_TAXA_COBERTURA: float = 1.0 #proporção do núcleo da carreira (100%)

# Conjunto de IDs de habilidades que o usuário possui
def _ids_habilidades_do_usuario(session: Session, usuario_id: int) -> Set[int]:
    linhas = (
        session.query(UsuarioHabilidade.habilidade_id)
        .filter(UsuarioHabilidade.usuario_id == usuario_id)
        .all()
    )
    return {habilidade_id for (habilidade_id,) in linhas} # extrai apenas os IDs das tuplas retornadas

# Calcula a compatibilidade do usuário para uma carreira específica
def calcular_compatibilidade_usuario_carreira(
    session: Session,
    usuario_id: int,
    carreira_id: int,
    *,
    min_freq: int | None = DEFAULT_MIN_FREQ, # frequência mínima de CarreiraHabilidade a considerar
    taxa_cobertura: float | None = DEFAULT_TAXA_COBERTURA, # proporção do núcleo da carreira a considerar (padrão 80%)
) -> Dict[str, Any]:
    
    """
    Calcula a compatibilidade (0 a 100) do usuário para uma carreira específica, ponderando pelas frequências de CarreiraHabilidade.

    percentual = 100 * soma(freq das habilidades da carreira que o usuário possui) / soma(freq de todas as habilidades da carreira)

    Retorna um dicionário com:
    - carreira_id, carreira_nome
    - percentual (float 0>100 com 2 casas)
    - peso_coberto (int), peso_total (int)
    - habilidades_cobertas (lista de nomes)
    """

    # Busca a carreira
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

    # Coleta habilidades do usuário
    habilidades_usuario = _ids_habilidades_do_usuario(session, usuario_id)

    # Coleta frequências da carreira
    relacoes: List[Tuple[int, int]] = (
        session.query(CarreiraHabilidade.habilidade_id, CarreiraHabilidade.frequencia)
        .filter(CarreiraHabilidade.carreira_id == carreira.id)
        .all()
    )

    # Aplica filtro por frequência mínima e transforma pesos
    def calcular_peso(frequencia_valor: int) -> float:
        # Como a frequência no banco já representa a importância, usamos diretamente o valor sem transformações.
        return float(frequencia_valor)

    # Lista de tuplas (habilidade_id, peso_transformado) após filtro
    habilidades_consideradas: List[Tuple[int, float]] = []
    for habilidade_id, frequencia in relacoes:
        frequencia_int = int(frequencia) # garante que é inteiro
        if min_freq is not None and frequencia_int < int(min_freq): # aplica filtro de frequência mínima
            continue
        habilidades_consideradas.append((habilidade_id, calcular_peso(frequencia_int))) # adiciona após filtro e transformação em peso

    # Soma total considerando filtro/transformação
    peso_total_considerado = sum(peso for _, peso in habilidades_consideradas)

    # Define o denominador com base na taxa_cobertura (núcleo da carreira)
    ids_nucleo: Set[int] = set()
    denominador = peso_total_considerado
    # Calcula o núcleo baseado na taxa_cobertura
    if (
        taxa_cobertura is not None
        and isinstance(taxa_cobertura, (int, float)) # garante que é numérico
        and 0 < float(taxa_cobertura) < 1 # entre 0 e 1
        and peso_total_considerado > 0 # evita divisão por zero
    ):
        alvo = float(taxa_cobertura) * peso_total_considerado # alvo de peso para o núcleo
        ordenadas = sorted(habilidades_consideradas, key=lambda t: t[1], reverse=True) # ordena por peso decrescente
        acumulado = 0.0 # acumula peso até atingir o alvo
        for habilidade_id, peso in ordenadas:
            ids_nucleo.add(habilidade_id) # adiciona ao núcleo
            acumulado += peso # acumula peso
            if acumulado >= alvo: # atingiu o alvo
                break
        denominador = acumulado # redefine denominador para o peso do núcleo
    else:
        ids_nucleo = {habilidade_id for habilidade_id, _ in habilidades_consideradas} # todo o conjunto

    # Peso coberto apenas do núcleo
    peso_coberto = sum(
        peso # soma pesos
        for habilidade_id, peso in habilidades_consideradas # considera apenas núcleo
        if habilidade_id in ids_nucleo and habilidade_id in habilidades_usuario # usuário possui
    )

    # Evita divisão por zero
    percentual = 0.0 if denominador <= 0 else round(100.0 * (peso_coberto / float(denominador)), 2)

    # Busca nomes das habilidades cobertas
    habilidades_nomes: List[str] = []
    ids_cobertos = [
        habilidade_id for habilidade_id, _ in habilidades_consideradas if habilidade_id in ids_nucleo and habilidade_id in habilidades_usuario
    ]
    # Busca nomes apenas se houver habilidades cobertas
    if ids_cobertos:
        nomes_habilidades = (
            session.query(Habilidade.nome)
            .filter(Habilidade.id.in_(ids_cobertos))
            .all()
        )
        habilidades_nomes = [nome for (nome,) in nomes_habilidades]

    # Retorna o resultado como dicionário
    return {
        "carreira_id": carreira.id,
        "carreira_nome": carreira.nome,
        "percentual": percentual,
        "peso_coberto": round(float(peso_coberto), 4),
        "peso_total": round(float(peso_total_considerado), 4),
        "habilidades_cobertas": habilidades_nomes,
    }

# Retorna compatibilidade com todas as carreiras para um usuário (ponderada por frequência)
def compatibilidade_carreiras_por_usuario(
    session: Session,
    usuario_id: int,
    *,
    min_freq: int | None = DEFAULT_MIN_FREQ, # frequência mínima de CarreiraHabilidade a considerar
    taxa_cobertura: float | None = DEFAULT_TAXA_COBERTURA, # proporção do núcleo da carreira a considerar
) -> List[Dict[str, Any]]:

    # Busca todas as carreiras e calcula compatibilidade
    carreiras = session.query(Carreira).all()
    resultados: List[Dict[str, Any]] = []
    for carreira_item in carreiras:
        resultado = calcular_compatibilidade_usuario_carreira(
            session,
            usuario_id,
            carreira_item.id,
            min_freq=min_freq,
            taxa_cobertura=taxa_cobertura,
        )
        resultados.append(resultado)

    # Ordena resultados
    resultados.sort(
        key=lambda r: (
            r.get("percentual", 0.0),
            r.get("peso_coberto", 0),
            r.get("peso_total", 0),
            (r.get("carreira_nome") or "").lower(),
        ),
        reverse=True, # ordem decrescente
    )
    return resultados
