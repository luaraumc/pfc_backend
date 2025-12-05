from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cursoModels import Curso
from app.models.carreiraModels import Carreira
from app.models.habilidadeModels import Habilidade
from app.models.cursoConhecimentoModels import CursoConhecimento
from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria
from app.models.carreiraHabilidadeModels import  CarreiraHabilidade 


def carregar_listas_base(session: Session) -> Tuple[List[dict], List[dict]]:
    """Carrega listas de cursos e carreiras ordenadas alfabeticamente no formato {"id": int, "nome": str}"""
    cursos = [
        {"id": curso_id, "nome": curso_nome}
        for curso_id, curso_nome in session.query(Curso.id, Curso.nome)
        .order_by(Curso.nome.asc())
        .all()
    ]
    carreiras = [
        {"id": carreira_id, "nome": carreira_nome}
        for carreira_id, carreira_nome in session.query(Carreira.id, Carreira.nome)
        .order_by(Carreira.nome.asc())
        .all()
    ]
    return cursos, carreiras


def agregar_oferta_por_curso(session: Session) -> Dict[int, Dict[int, float]]:
    """Agrega oferta por curso somando pesos dos conhecimentos por categoria usando JOIN entre CursoConhecimento e ConhecimentoCategoria"""
    rows = (
        session.query(
            CursoConhecimento.curso_id.label("curso_id"),
            ConhecimentoCategoria.categoria_id.label("categoria_id"),
            func.sum(func.coalesce(ConhecimentoCategoria.peso, 0)).label("peso_sum"),
        )
        .join(
            ConhecimentoCategoria,
            ConhecimentoCategoria.conhecimento_id == CursoConhecimento.conhecimento_id,
        )
        .group_by(CursoConhecimento.curso_id, ConhecimentoCategoria.categoria_id)
        .all()
    )
    oferta: Dict[int, Dict[int, float]] = {}
    for r in rows:
        oferta.setdefault(r.curso_id, {})[r.categoria_id] = float(r.peso_sum)
    return oferta


def agregar_demanda_por_carreira(session: Session) -> Dict[int, Dict[int, float]]:
    """Agrega demanda por carreira somando frequências das habilidades por categoria usando JOIN entre CarreiraHabilidade e Habilidade"""
    rows = (
        session.query(
            CarreiraHabilidade.carreira_id.label("carreira_id"),
            Habilidade.categoria_id.label("categoria_id"),
            func.coalesce(func.sum(CarreiraHabilidade.frequencia), 0).label("freq_sum"),
        )
        .join(Habilidade, Habilidade.id == CarreiraHabilidade.habilidade_id)
        .group_by(CarreiraHabilidade.carreira_id, Habilidade.categoria_id)
        .all()
    )
    demanda: Dict[int, Dict[int, float]] = {}
    for r in rows:
        if r.categoria_id is None:
            continue
        demanda.setdefault(r.carreira_id, {})[r.categoria_id] = float(r.freq_sum)
    return demanda


def calcular_score(
    oferta_por_curso: Dict[int, Dict[int, float]],
    demanda_por_carreira: Dict[int, Dict[int, float]],
    curso_id: int,
    carreira_id: int,
) -> float:
    """Calcula score de compatibilidade entre curso e carreira usando média ponderada pela demanda: sum(oferta*demanda)/sum(demanda)"""
    oferta = oferta_por_curso.get(curso_id, {})
    demanda = demanda_por_carreira.get(carreira_id, {})
    numer = 0.0
    denom = 0.0
    for categoria_id, demanda_valor in demanda.items():
        oferta_valor = oferta.get(categoria_id, 0.0)
        numer += oferta_valor * demanda_valor
        denom += demanda_valor
    if denom <= 0:
        return 0.0
    return numer / denom


def montar_mapa(session: Session) -> dict:
    """Monta o mapa completo curso×carreira calculando scores de compatibilidade e organizando em estruturas bidirecionais ordenadas"""
    cursos, carreiras = carregar_listas_base(session)
    oferta_por_curso = agregar_oferta_por_curso(session)
    demanda_por_carreira = agregar_demanda_por_carreira(session)

    cursoToCarreiras: Dict[int, list] = {}
    for curso in cursos:
        relacoes: list = []
        for carreira in carreiras:
            score = calcular_score(oferta_por_curso, demanda_por_carreira, curso["id"], carreira["id"])
            if score > 0:
                relacoes.append({
                    "id": carreira["id"],
                    "nome": carreira["nome"],
                    "score": round(float(score), 6),
                })
        relacoes.sort(key=lambda x: x["score"], reverse=True)
        cursoToCarreiras[curso["id"]] = relacoes

    carreiraToCursos: Dict[int, list] = {}
    for carreira in carreiras:
        relacoes: list = []
        for curso in cursos:
            score = calcular_score(oferta_por_curso, demanda_por_carreira, curso["id"], carreira["id"])
            if score > 0:
                relacoes.append({
                    "id": curso["id"],
                    "nome": curso["nome"],
                    "score": round(float(score), 6),
                })
        relacoes.sort(key=lambda x: x["score"], reverse=True)
        carreiraToCursos[carreira["id"]] = relacoes

    return {
        "cursos": cursos,
        "carreiras": carreiras,
        "cursoToCarreiras": cursoToCarreiras,
        "carreiraToCursos": carreiraToCursos,
    }
