from dotenv import load_dotenv  # carregar variáveis de ambiente
import os  # interagir com o sistema operacional
from typing import List  # tipos para listas
from openai import OpenAI  # API OpenAI
from sqlalchemy.orm import Session  # sessões com o banco de dados
from app.models import Vaga, Habilidade, VagaHabilidade  # modelo de tabela definido no arquivo models.py
import json, re, unicodedata # manipulação de JSON, expressões regulares, normalização de strings

load_dotenv()

# Prompt base enviado ao modelo de linguagem
PROMPT_BASE = """
Extraia somente uma lista de habilidades (competências técnicas ou soft skills claras) do texto de descrição de vaga abaixo.
Responda apenas JSON válido no formato: {"habilidades": ["habilidade1", "habilidade2", ...]}
- Não invente habilidades que não estejam mencionadas.
- Use nomes curtos padronizados (ex: Java, Python, SQL, Git, Docker, Comunicação, Trabalho em equipe, Resolução de problemas).
- Não inclua níveis (júnior, pleno), nem anos de experiência, nem versões (ex: 'Java 17' => 'Java').
TEXTO:
"""

# Normaliza uma string de habilidade
def normalizar(habilidade: str) -> str:
    habilidade = habilidade.strip() # remove espaços em branco no início e fim
    habilidade = re.sub(r'\s+', ' ', habilidade) # re.sub encontra ocorrências de um determinado padrão numa string e substitui por uma nova string (substitui múltiplos espaços por um)
    return habilidade[:60] # limita a 60 caracteres

# Gera chave sem acento e minúscula para deduplicação
def deduplicar(habilidade: str) -> str:
    nfkd = unicodedata.normalize('NFKD', habilidade) # unicodedata.normalize normaliza a string para decompor caracteres acentuados / NFKD: Normalização de Compatibilidade de Decomposição
    sem_acento = ''.join(c for c in nfkd if not unicodedata.combining(c)) # unicodedata.combining verifica se o caractere é um caractere de combinação (tem acentos) e remove esses caracteres
    return sem_acento.lower() # converte para minúsculas

# Mapa de padrões (regex)
PADROES = {
    # Tecnologias / linguagens
    r"^python\d*$": "Python",
    r"^python 3$": "Python",
    r"^py$": "Python",
    r"^node(js)?$": "Node.js",
    r"^node ?js$": "Node.js",
    r"^javascript$": "JavaScript",
    r"^js$": "JavaScript",
    r"^ts$": "TypeScript",
    r"^typescript$": "TypeScript",
    r"^c\+$\+?$": "C++",
    r"^c ?sharp$": "C#",
    r"^csharp$": "C#",
    r"^react(\.js)?$": "React",
    r"^reactjs$": "React",
    r"^angular(js)?$": "Angular",
    r"^vue(\.js)?$": "Vue.js",
    r"^postgres(q|ql)?$": "PostgreSQL",
    r"^postgre(sql)?$": "PostgreSQL",
    r"^mongo(db)?$": "MongoDB",
    r"^git$": "Git",
    r"^docker$": "Docker",
    r"^k8s$": "Kubernetes",
    r"^kubernetes$": "Kubernetes",
    r"^aws$": "AWS",
    r"^gcp$": "GCP",
    r"^azure$": "Azure",
    r"^sql$": "SQL",
    r"^no ?sql$": "NoSQL",
    r"^ci/cd$": "CI/CD",
    r"^dotnet$": ".NET",
    r"^machine learning$": "Machine Learning",
    r"^ml$": "Machine Learning",
    r"^ia$": "Inteligência Artificial",
    r"^ai$": "Inteligência Artificial",
    # Soft skills
    r"^trabalho em equipe$": "Trabalho em equipe",
    r"^comunicac[aã]o$": "Comunicação",
    r"^boa comunicac[aã]o$": "Comunicação",
    r"^resolu[cç][aã]o de problemas$": "Resolução de problemas",
    r"^problem solving$": "Resolução de problemas",
    r"^pensamento cr[ií]tico$": "Pensamento crítico",
}

PADROES_COMPILADOS = [(re.compile(p, re.IGNORECASE), v) for p, v in PADROES.items()] # re.compile compila o padrão regex para uso repetido / re.IGNORECASE torna a busca case-insensitive

# Aplica regras de limpeza e mapeamento para obter a forma padrão da habilidade
def padronizar(habilidade: str) -> str:
    base = normalizar(habilidade) # remove espaços extras e limita tamanho
    minuscula = base.lower() # converte para minúsculas
    # 1. Remover versões acopladas sem espaço (ex: python311, node18, java17)
    minuscula = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala)(\d{1,3}(?:\.\d+)*)\b', r'\1', minuscula)
    # 2. Remover versões após espaço ou hífen (ex: python 3.11, java 17, node 18, go 1.22)
    minuscula = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala)[ \-]+\d+(?:\.\d+){0,2}\b', r'\1', minuscula)
    # 3. Remover versões após linguagens com sinais (c++ 20, c# 12)
    minuscula = re.sub(r'\b(c\+\+|c#)[ \-]*\d{1,2}\b', r'\1', minuscula)
    # 4. Normalizar ".net 8" / "dotnet 8" => dotnet / .net
    minuscula = re.sub(r'\b(dotnet|\.net)[ \-]*\d+(?:\.\d+){0,2}\b', r'dotnet', minuscula)
    # 5. Limpar pontuação periférica comum
    minuscula = minuscula.strip(' .;,-')
    # 6. Aplicar mapeamento
    for regex, valor in PADROES_COMPILADOS:
        if regex.match(minuscula): # .match verifica se a string corresponde ao padrão regex
            return valor
    # 7. Capitalização simples se for curta e não for sigla já em maiúsculas
    if len(base.split()) <= 3 and not re.search(r'[A-Z]{2,}', base): # .split() divide a string em uma lista de palavras / re.search procura por padrão regex na string
        base = ' '.join(p.capitalize() for p in base.split()) # join() junta a lista de palavras em uma string única separada por espaço / .capitalize() converte a primeira letra em maiúscula e o resto em minúscula
    return base # retorna a forma padronizada

# Extrai habilidades de um texto bruto de descrição de vaga
def extrair_habilidades_texto(texto: str) -> List[str]:
    cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # instancia cliente OpenAI com chave da variável de ambiente
    prompt = PROMPT_BASE + texto # concatena prompt base com o texto da vaga
    try:
        resposta = cliente.responses.create( # responses.create envia o prompt ao modelo e obtém a resposta
            model="gpt-4.1", # modelo de linguagem
            input=prompt, # prompt de entrada
            temperature=0.15, # controle de aleatoriedade (0 = respostas mais previsíveis, 1 = mais variadas)
            max_output_tokens=500 # limite de tokens na resposta
        )

        texto_completo = "" # armazenar o texto completo da resposta
        if hasattr(resposta, "output_text") and resposta.output_text: # hasattr verifica se o objeto tem o atributo / output_text contém o texto gerado
            texto_completo = resposta.output_text.strip() # monta o texto completo a partir do output_text removendo espaços em branco no início e fim
        else:
            blocos_puros = [] # lista para armazenar blocos de texto puros
            blocos = getattr(resposta, "output", []) or [] # getattr obtém o atributo 'output' do objeto resposta ou uma lista vazia se não existir
            for bloco in blocos:
                if getattr(bloco, "type", None) == "output_text": # verifica se o bloco é do tipo 'output_text'
                    blocos_puros.append(getattr(bloco, "text", "").strip()) # adiciona o texto do bloco à lista removendo espaços em branco no início e fim
            texto_completo = "\n".join(t for t in blocos_puros if t).strip() # junta os blocos de texto puros em uma única string

        habilidades_extraidas: List[str] = [] # lista para armazenar habilidades extraídas

        # tentar decodificar JSON de um segmento de texto
        def tentar_json(segmento: str):
            nonlocal habilidades_extraidas # permite modificar a variável do escopo externo
            try:
                data = json.loads(segmento) # json.loads tenta decodificar a string JSON
                if isinstance(data, dict) and isinstance(data.get("habilidades"), list): # verifica se o JSON é um dicionário com uma lista de habilidades
                    habilidades_extraidas = [
                        padronizar(h) for h in data["habilidades"] # aplica padronização a cada habilidade
                    ]
            except json.JSONDecodeError:
                pass

        # 1. Tenta JSON direto
        if texto_completo:
            tentar_json(texto_completo)

        # 2. Se falhou, tenta regex para isolar bloco JSON
        if not habilidades_extraidas:
            achado = re.search(r'\{.*"habilidades"\s*:\s*\[.*?\]\s*\}', texto_completo, re.DOTALL) # re.search procura por padrão regex na string / re.DOTALL faz o '.' corresponder a qualquer caractere, incluindo quebras de linha
            if achado:
                tentar_json(achado.group(0)) # tenta decodificar o bloco JSON encontrado

        # Deduplicação
        finais: List[str] = [] # lista para habilidades finais
        vistos = set() # conjunto para rastrear habilidades já vistas
        for hab in habilidades_extraidas:
            chave = deduplicar(hab) # gera chave para deduplicação
            if chave not in vistos:
                vistos.add(chave) # marca como vista
                finais.append(hab) # adiciona à lista final

        return finais
    except Exception as exc:
        return []

# Extrai habilidades da vaga pelo id criando registros em 'habilidade'
def extrair_habilidades_vaga(sessao: Session, vaga_id: int, criar_habilidades: bool = True, forcar_extracao: bool = False) -> dict:
    vaga = sessao.query(Vaga).filter(Vaga.id == vaga_id).first() # busca a vaga pelo id
    if not vaga:
        return {"erro": "Vaga não encontrada"}

    # Se não for para forçar, verificar cache
    if not forcar_extracao:
        habilidades_cache = (
            sessao.query(Habilidade)
            .join(VagaHabilidade, VagaHabilidade.habilidade_id == Habilidade.id)
            .filter(VagaHabilidade.vaga_id == vaga_id)
            .all()
        )
        if habilidades_cache:
            return {
                "vaga_id": vaga.id,
                "titulo": vaga.titulo,
                "habilidades_extraidas": [h.nome for h in habilidades_cache],
                "habilidades_criadas": [],
                "habilidades_ja_existiam": [h.nome for h in habilidades_cache],
                "fonte": "cache"
            }

    habilidades = extrair_habilidades_texto(vaga.descricao) # extrai habilidades do texto da descrição da vaga

    criadas: List[str] = [] # lista para habilidades criadas
    existentes: List[str] = [] # lista para habilidades que já existiam
    ids_relacionar: list[int] = []
    if criar_habilidades and habilidades:
        for nome in habilidades:
            existente = sessao.query(Habilidade).filter(Habilidade.nome.ilike(nome)).first() # ilike faz busca case-insensitive
            if existente:
                existentes.append(existente.nome) # adiciona o nome da habilidade existente à lista
                ids_relacionar.append(existente.id)
            else:
                nova = Habilidade(nome=nome) # cria nova habilidade
                sessao.add(nova) # adiciona à sessão
                sessao.flush()
                criadas.append(nome) # adiciona o nome da nova habilidade à lista
                ids_relacionar.append(nova.id)
        sessao.commit() # confirma as mudanças no banco de dados

    # Criar associações vaga_habilidade (evita duplicar com unique constraint)
    for hid in ids_relacionar:
        existente_rel = (
            sessao.query(VagaHabilidade)
            .filter_by(vaga_id=vaga_id, habilidade_id=hid)
            .first()
        )
        if not existente_rel:
            sessao.add(VagaHabilidade(vaga_id=vaga_id, habilidade_id=hid))
    sessao.commit()

    # Retorna informações sobre a vaga e as habilidades
    return {
        "vaga_id": vaga.id,
        "titulo": vaga.titulo,
        "habilidades_extraidas": habilidades,
        "habilidades_criadas": criadas,
        "habilidades_ja_existiam": existentes,
        "fonte": "modelo" if habilidades else "modelo_sem_resultados"
    }
