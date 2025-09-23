# Documentação - Módulo de Vagas

## Visão Geral
O módulo de Vagas permite:
- Cadastro de vagas (admin)
- Associação opcional a uma carreira (carreira_id) ou sugestão automática baseada no título
- Extração de habilidades da descrição usando OpenAI
- Criação (opcional) das habilidades inexistentes
- Cache de habilidades por vaga via tabela relacional vaga_habilidade para evitar reprocessamento
- Reextração forçada quando necessário
- Listagem e remoção de associações vaga → habilidade

## Modelos Envolvidos
- Vaga(id, titulo, descricao, carreira_id, criado_em, atualizado_em)
- Habilidade(id, nome)
- VagaHabilidade(id, vaga_id, habilidade_id)  (chave única composta vaga_id + habilidade_id)

## Migrações relevantes
- 006_cria_tabela_vaga.py
- 007_cria_tabela_vaga_habilidade.py
- 008_add_coluna_carreira_id_em_vaga.py

## Fluxo de Cadastro de Vaga
1. Admin chama POST /vaga/vaga/cadastro
2. Se carreira_id vier no payload → usa direto
3. Se não vier → serviço tenta sugerir carreira por palavra‑chave no título (ex: “backend”, “dados”)
4. Vaga armazenada

## Extração de Habilidades
Rota: POST /vaga/{vaga_id}/extrair-habilidades  
Parâmetros (query):
- criar_habilidades (bool, padrão true): cria no banco habilidades ausentes
- forcar_extracao (bool, padrão false): ignora cache e chama OpenAI novamente

Processo:
1. Se não for forçar, busca habilidades já associadas (cache)
2. Se existir cache → retorna fonte=cache
3. Caso contrário:
   - Monta prompt (sem versões, níveis, anos)
   - Chama OpenAI
   - Lê JSON {"habilidades":[...]}
   - Normaliza (regex + remoção de versões + capitalização controlada + deduplicação por chave sem acento)
   - Cria habilidades (se habilitado)
   - Cria relações em vaga_habilidade
   - Retorna fonte=modelo (ou modelo_sem_resultados)

## Cache (vaga_habilidade)
- Evita chamadas repetidas ao modelo
- Pode ser invalidado usando forcar_extracao=true
- Pode remover manualmente relações via DELETE (ver abaixo)

## Endpoints Principais

### Listar vagas
GET /vaga/  
Resposta: lista de VagaOut (inclui carreira_id e carreira_nome)

### Criar vaga
POST /vaga/vaga/cadastro (admin)  
Body exemplo:
{
  "titulo": "Desenvolvedor Backend Python",
  "descricao": "Responsável por APIs, Docker, Git, PostgreSQL...",
  "carreira_id": null
}

Resposta inclui carreira sugerida se não enviada.

### Extrair habilidades
POST /vaga/{vaga_id}/extrair-habilidades?criar_habilidades=true&forcar_extracao=false

Resposta exemplo:
{
  "vaga_id": 1,
  "titulo": "Desenvolvedor Backend Python",
  "habilidades_extraidas": ["Python","Docker","Git","PostgreSQL","Comunicação"],
  "habilidades_criadas": ["Comunicação"],
  "habilidades_ja_existiam": ["Python","Docker","Git","PostgreSQL"],
  "fonte": "modelo"
}

Fonte pode ser:
- cache
- modelo
- modelo_sem_resultados

### Listar habilidades associadas (cache)
GET /vaga/{vaga_id}/habilidades  
Resposta: ["Python","Docker","Git"]

### Remover uma relação vaga-habilidade
DELETE /vaga/{vaga_id}/habilidades/{habilidade_id} (admin)  
Resposta:
{"status":"removido"}

## Exemplo curl (Windows PowerShell)
$token = "SEU_TOKEN_ADMIN"
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/vaga/vaga/cadastro" `
  -Headers @{Authorization="Bearer $token";"Content-Type"="application/json"} `
  -Body '{"titulo":"Desenvolvedor Backend Python","descricao":"Experiência com Python, Docker, Git, PostgreSQL, comunicação e trabalho em equipe."}'

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/vaga/1/extrair-habilidades?criar_habilidades=true" `
  -Headers @{Authorization="Bearer $token"}

Invoke-RestMethod -Method Get -Uri "http://localhost:8000/vaga/1/habilidades"

## Lógica de Normalização de Habilidades (resumo)
1. Limpa espaços / limita tamanho
2. Remove versões (python3.11 → python, node18 → node)
3. Normaliza variações via regex (ex: py → Python, reactjs → React)
4. Remove acentos para deduplicação
5. Capitaliza somente se:
   - Até 3 palavras
   - Não contém siglas 2+ maiúsculas (preserva API, SQL, CI/CD)
6. Deduplicação final (case/acento-insensitive)

## Quando usar forcar_extracao=true
- Atualizou a descrição da vaga
- Ajustou regras de normalização
- Modelo OpenAI anterior retornou incompleto
- Adicionou novos padrões de mapeamento

## Boas Práticas
- Rodar extração somente após descrição final
- Evitar descrições excessivamente longas ou genéricas
- Revisar habilidades antes de mostrar para candidato
- Usar forcar_extracao com moderação (custo de API)

## Possíveis Extensões Futuras
- Persistir snapshot JSON das habilidades na própria vaga
- Peso/score por habilidade
- Sugestão de carreira baseada em similaridade de habilidades
- Lista de “habilidades essenciais” por carreira
- Paginação em /vaga/

## Erros Comuns
404 Vaga não encontrada → ID inválido  
Resposta vazia / fonte=modelo_sem_resultados → descrição fraca ou não reconhecida  
Nenhuma habilidade criada → já existiam ou criar_habilidades=false

## Dependências Necessárias
- openai instalado (pip install openai)
- Variável OPENAI_API_KEY definida (.env)
- Migrações aplicadas (alembic upgrade head)

## Checklist Rápido
[ ] Executar alembic upgrade head  
[ ] Definir OPENAI_API_KEY  
[ ] Criar vaga (admin)  
[ ] Extrair habilidades  
[ ] Ver fonte=cache na segunda extração  

---
