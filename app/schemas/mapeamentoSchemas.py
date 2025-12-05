from pydantic import BaseModel
from typing import List, Dict


class ItemSimples(BaseModel):
    id: int
    nome: str


class RelacaoScore(BaseModel):
    id: int
    nome: str
    score: float


class MapaOut(BaseModel):
    cursos: List[ItemSimples]
    carreiras: List[ItemSimples]
    cursoToCarreiras: Dict[int, List[RelacaoScore]]
    carreiraToCursos: Dict[int, List[RelacaoScore]]
