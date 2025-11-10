"""
Serviço de mapeamento curso × carreira.

Objetivo
========
Construir um "mapa" que relacione cursos e carreiras por um score de
preparação, calculado a partir de:

- Oferta do curso por categoria (derivada dos conhecimentos do curso e
    seus pesos por categoria).
- Demanda da carreira por categoria (derivada das habilidades
    requeridas pela carreira e sua frequência por categoria).

Fórmula do score (média ponderada pela demanda):

    score(curso, carreira) = sum(oferta[categoria_id] * demanda[categoria_id]) / sum(demanda[categoria_id])

onde categoria_id percorre as categorias presentes na demanda da carreira.

Estratégia
==========
1) Carregar listas base de cursos e carreiras (id, nome).
2) Agregar a oferta por curso via JOIN CursoConhecimento → ConhecimentoCategoria,
     agrupando por (curso_id, categoria_id) e somando os pesos.
3) Agregar a demanda por carreira via JOIN CarreiraHabilidade → Habilidade
     (para obter categoria_id), agrupando por (carreira_id, categoria_id) e
     somando as frequências.
4) Calcular o score para cada par (curso, carreira) usando a média
     ponderada pela demanda (ver fórmula acima).
5) Montar os dicionários cursoToCarreiras e carreiraToCursos, ordenando
    por score.

Notas
=====
- Peso pode ser 0 (zero) e deve ser respeitado: valores nulos de peso
    viram 0, mas 0 permanece 0 na soma.
- Frequência 0 ou NULL contam como 0 (não contribuem para a soma/ponderação).
- O score não é globalmente normalizado; ele depende da escala da
    oferta/demanda construída pelos seus dados de base.
- O retorno é um dicionário serializável compatível com a resposta Pydantic
    definida na rota.
"""

from typing import Dict, List, Tuple  # Tipagens auxiliares
from sqlalchemy.orm import Session  # Sessão do SQLAlchemy para executar consultas
from sqlalchemy import func  # Funções SQL (sum, coalesce)
from app.models.cursoModels import Curso
from app.models.carreiraModels import Carreira
from app.models.habilidadeModels import Habilidade
from app.models.cursoConhecimentoModels import CursoConhecimento
from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria
from app.models.carreiraHabilidadeModels import  CarreiraHabilidade 

# Carrega as listas de cursos e carreiras
def carregar_listas_base(session: Session) -> Tuple[List[dict], List[dict]]:
    """
    Retorna as listas no formato {"id": int, "nome": str}
    """
    cursos = [
        {"id": curso_id, "nome": curso_nome}  # Monta dicionário
        for curso_id, curso_nome in session.query(Curso.id, Curso.nome)  # Seleciona as colunas específicas
        .order_by(Curso.nome.asc()) # Ordena alfabeticamente por nome do curso
        .all() # Executa a consulta e retorna lista de tuplas
    ]
    carreiras = [
        {"id": carreira_id, "nome": carreira_nome}  # Monta dicionário
        for carreira_id, carreira_nome in session.query(Carreira.id, Carreira.nome)  # Seleciona as colunas específicas
        .order_by(Carreira.nome.asc())  # Ordena alfabeticamente por nome da carreira
        .all() # Executa a consulta e retorna lista de tuplas
    ]
    return cursos, carreiras # Retorna as duas listas

# Quanto cada curso oferece de cada categoria com base nos conhecimentos
def agregar_oferta_por_curso(session: Session) -> Dict[int, Dict[int, float]]:
    """
    Faz um JOIN entre CursoConhecimento e ConhecimentoCategoria e para cada par (curso_id, categoria_id) soma os pesos.
    """
    rows = (
        session.query(
            CursoConhecimento.curso_id.label("curso_id"), # id do curso na relção curso-conhecimento
            ConhecimentoCategoria.categoria_id.label("categoria_id"), # id da categoria na relação conhecimento-categoria
            func.sum(func.coalesce(ConhecimentoCategoria.peso, 0)).label("peso_sum"), # soma de pesos por (curso, categoria) / se null vira 0
        )
        .join(
            ConhecimentoCategoria,
            ConhecimentoCategoria.conhecimento_id == CursoConhecimento.conhecimento_id,  # junção por id do conhecimento
        )
        .group_by(CursoConhecimento.curso_id, ConhecimentoCategoria.categoria_id)  # agrega por curso e categoria
        .all()  # executa a consulta
    )
    oferta: Dict[int, Dict[int, float]] = {}  # Estrutura: {curso_id: {categoria_id: soma_peso}}
    # Para cada linha agregada, popula o mapa
    for r in rows:
        oferta.setdefault(r.curso_id, {})[r.categoria_id] = float(r.peso_sum) # garante dicionario para o curso e atribui o peso somado
    return oferta  # Retorna o mapa de oferta por curso

# Quanto cada carreira demanda de cada categoria com base nas habilidades
def agregar_demanda_por_carreira(session: Session) -> Dict[int, Dict[int, float]]:
    """
    Faz um JOIN entre CarreiraHabilidade e Habilidade para obter categoria_id e somar as frequências.
    """
    rows = (
        session.query(
            CarreiraHabilidade.carreira_id.label("carreira_id"), # id da carreira na relação carreira-habilidade
            Habilidade.categoria_id.label("categoria_id"), # id da categoria na tabela habilidade
            func.coalesce(func.sum(CarreiraHabilidade.frequencia), 0).label("freq_sum"), # soma a frequência tratando soma total NULL como 0
        )
        .join(Habilidade, Habilidade.id == CarreiraHabilidade.habilidade_id)  # associa para obter categoria_id
        .group_by(CarreiraHabilidade.carreira_id, Habilidade.categoria_id)  # agrega por carreira e categoria
        .all()  # executa a consulta
    )
    demanda: Dict[int, Dict[int, float]] = {}  # Estrutura: {carreira_id: {categoria_id: soma_freq}}
    for r in rows:
        # ignora registros de habilidade sem categoria definida
        if r.categoria_id is None:
            continue
        # Para cada linha agregada, popula o mapa
        demanda.setdefault(r.carreira_id, {})[r.categoria_id] = float(r.freq_sum) # garante dicionario para a carreira e atribui a frequência somada
    return demanda  # Retorna o mapa de demanda por carreira

# Calcula o score para um par (curso, carreira)
def calcular_score(
    oferta_por_curso: Dict[int, Dict[int, float]], # oferta agregada por curso
    demanda_por_carreira: Dict[int, Dict[int, float]], # demanda agregada por carreira
    curso_id: int, # identificador do curso
    carreira_id: int, # identificador da carreira
) -> float:
    """
    Média ponderada das “ofertas” do curso, onde os “pesos” são as “demandas” da carreira:
        numer = Σ oferta * demanda
        denom = Σ demanda
        score = numer / denom

    Exemplo:
        Oferta do curso por categoria: A=5, B=2, C=8
        Demanda da carreira por categoria: A=3, B=0, C=1
        Numerador = 5×3 + 2×0 + 8×1 = 23
        Denominador = 3 + 0 + 1 = 4
        Score = 23 / 4 = 5,75

    Observação:
    - Se uma categoria demandada não tiver oferta no curso, considera 0.
    """
    oferta = oferta_por_curso.get(curso_id, {}) # mapa categoria→peso ofertado pelo curso
    demanda = demanda_por_carreira.get(carreira_id, {}) # mapa categoria→frequencia demandada pela carreira
    numer = 0.0 # acumulador do numerador
    denom = 0.0 # acumulador do denominador
    for categoria_id, demanda_valor in demanda.items(): # percorre apenas categorias demandadas
        oferta_valor = oferta.get(categoria_id, 0.0) # oferta do curso para a categoria (0 se inexistente)
        numer += oferta_valor * demanda_valor # oferta×demanda
        denom += demanda_valor # soma das demandas
    if denom <= 0:
        return 0.0 # proteção contra divisão por zero
    return numer / denom # média ponderada pela demanda

# Monta o mapa completo curso × carreira
def montar_mapa(
    session: Session, # sessão do banco
) -> dict:
    """
    Monta o mapa completo consolidando as listas base, agregações e scores.
    """
    cursos, carreiras = carregar_listas_base(session) # listas base
    oferta_por_curso = agregar_oferta_por_curso(session) # oferta agregada
    demanda_por_carreira = agregar_demanda_por_carreira(session) # demanda agregada

    cursoToCarreiras: Dict[int, list] = {}  # Mapa de curso → lista de carreiras com score
    for curso in cursos:
        relacoes: list = []  # acumula relações para o curso atual
        for carreira in carreiras:
            score = calcular_score(oferta_por_curso, demanda_por_carreira, curso["id"], carreira["id"])  # score(curso,carreira)
            if score > 0:  # descarta scores 0
                relacoes.append({
                    "id": carreira["id"],
                    "nome": carreira["nome"],
                    "score": round(float(score), 6),  # arredonda para 6 casas por consistência
                })
        relacoes.sort(key=lambda x: x["score"], reverse=True)  # ordena do maior para o menor
        cursoToCarreiras[curso["id"]] = relacoes  # salva lista para o curso

    carreiraToCursos: Dict[int, list] = {}  # Mapa de carreira → lista de cursos com score
    for carreira in carreiras:
        relacoes: list = []  # acumula relações para a carreira atual
        for curso in cursos:
            score = calcular_score(oferta_por_curso, demanda_por_carreira, curso["id"], carreira["id"])  # score(curso,carreira)
            if score > 0:
                relacoes.append({
                    "id": curso["id"],
                    "nome": curso["nome"],
                    "score": round(float(score), 6),
                })
        relacoes.sort(key=lambda x: x["score"], reverse=True)  # ordena do maior para o menor
        carreiraToCursos[carreira["id"]] = relacoes  # salva lista para a carreira

    # Retorna o pacote consolidado pronto para serialização
    return {
        "cursos": cursos,
        "carreiras": carreiras,
        "cursoToCarreiras": cursoToCarreiras,
        "carreiraToCursos": carreiraToCursos,
    }
