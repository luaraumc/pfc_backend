import pytest
from pydantic import ValidationError

from app.schemas.mapeamentoSchemas import ItemSimples, RelacaoScore, MapaOut
from tests.schemas.utils_test_schemas import rel


def test_item_simples_valido_com_coercao():
	"""Valida coerção de id (str→int) e nome (int→str) em ItemSimples."""
	m = ItemSimples(id="1", nome=123)
	assert m.id == 1
	assert isinstance(m.id, int)
	assert m.nome == "123"
	assert isinstance(m.nome, str)


def test_item_simples_campos_obrigatorios_e_none():
	"""Garante obrigatoriedade de id e nome e rejeição de None."""
	with pytest.raises(ValidationError):
		ItemSimples(nome="x")

	with pytest.raises(ValidationError):
		ItemSimples(id=1)

	with pytest.raises(ValidationError):
		ItemSimples(id=None, nome="x")

	with pytest.raises(ValidationError):
		ItemSimples(id=1, nome=None)

def test_relacao_score_valida_com_coercao():
	"""Valida coerção de id/nome e score str→float em RelacaoScore."""
	m = RelacaoScore(id="2", nome=456, score="0.75")
	assert m.id == 2
	assert m.nome == "456"
	assert isinstance(m.score, float)
	assert m.score == 0.75


def test_relacao_score_score_int_vira_float():
	"""Confere que score int é convertido para float automaticamente."""
	m = RelacaoScore(id=3, nome="ABC", score=1)
	assert isinstance(m.score, float)
	assert m.score == 1.0


def test_relacao_score_campos_obrigatorios_e_none():
	"""Garante obrigatoriedade de todos os campos e rejeição de None."""
	with pytest.raises(ValidationError):
		RelacaoScore(nome="x", score=0.1)

	with pytest.raises(ValidationError):
		RelacaoScore(id=1, score=0.1)

	with pytest.raises(ValidationError):
		RelacaoScore(id=1, nome="x")

	with pytest.raises(ValidationError):
		RelacaoScore(id=None, nome="x", score=0.1)

	with pytest.raises(ValidationError):
		RelacaoScore(id=1, nome=None, score=0.1)

	with pytest.raises(ValidationError):
		RelacaoScore(id=1, nome="x", score=None)

def test_mapa_out_valido_estrutura_basica():
	"""Valida estrutura básica de MapaOut com listas e relações coerentes."""
	dado = {
		"cursos": [{"id": 1, "nome": "ADS"}],
		"carreiras": [{"id": 2, "nome": "Engenharia"}],
		"cursoToCarreiras": {1: [rel(2, "Engenharia", 0.9)]},
		"carreiraToCursos": {2: [rel(1, "ADS", 0.9)]},
	}

	m = MapaOut(**dado)

	assert len(m.cursos) == 1 and m.cursos[0].id == 1 and m.cursos[0].nome == "ADS"
	assert len(m.carreiras) == 1 and m.carreiras[0].id == 2 and m.carreiras[0].nome == "Engenharia"
	assert set(m.cursoToCarreiras.keys()) == {1}
	assert m.cursoToCarreiras[1][0].id == 2 and m.cursoToCarreiras[1][0].score == 0.9
	assert set(m.carreiraToCursos.keys()) == {2}
	assert m.carreiraToCursos[2][0].id == 1 and m.carreiraToCursos[2][0].nome == "ADS"


def test_mapa_out_coercao_chaves_dict_e_aninhados():
	"""Confere coerção de chaves str→int e itens aninhados nas relações."""
	dado = {
		"cursos": [{"id": "10", "nome": 111}],
		"carreiras": [{"id": "20", "nome": 222}],
		"cursoToCarreiras": {
			"10": [
				{"id": "20", "nome": 333, "score": "0.8"},
			]
		},
		"carreiraToCursos": {
			"20": [
				{"id": "10", "nome": 444, "score": 1},
			]
		},
	}

	m = MapaOut(**dado)

	assert m.cursos[0].id == 10 and m.cursos[0].nome == "111"
	assert m.carreiras[0].id == 20 and m.carreiras[0].nome == "222"

	assert set(m.cursoToCarreiras.keys()) == {10}
	assert set(m.carreiraToCursos.keys()) == {20}

	rel1 = m.cursoToCarreiras[10][0]
	assert rel1.id == 20 and rel1.nome == "333" and rel1.score == 0.8

	rel2 = m.carreiraToCursos[20][0]
	assert rel2.id == 10 and rel2.nome == "444" and rel2.score == 1.0


def test_mapa_out_aceita_colecoes_vazias():
	"""Aceita coleções vazias em todas as estruturas de MapaOut."""
	m = MapaOut(cursos=[], carreiras=[], cursoToCarreiras={}, carreiraToCursos={})
	assert m.cursos == []
	assert m.carreiras == []
	assert m.cursoToCarreiras == {}
	assert m.carreiraToCursos == {}


def test_mapa_out_item_invalido_dispara_erro():
	"""Dispara erro quando uma relação obrigatória está incompleta (sem score)."""
	dado = {
		"cursos": [{"id": 1, "nome": "A"}],
		"carreiras": [{"id": 2, "nome": "B"}],
		"cursoToCarreiras": {1: [{"id": 2, "nome": "B"}]},
		"carreiraToCursos": {2: [{"id": 1, "nome": "A", "score": 0.5}]},
	}

	with pytest.raises(ValidationError):
		MapaOut(**dado)

