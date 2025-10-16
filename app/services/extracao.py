from dotenv import load_dotenv # variáveis de ambiente de um arquivo .env
import os # manipulação do sistema operacional
from typing import List # tipos para listas
from openai import OpenAI # cliente OpenAI para chamadas à API
import json, re, unicodedata # manipulação de JSON, expressões regulares e normalização de texto

load_dotenv() # carrega chave da API do arquivo .env

# Instrução para o modelo
PROMPT_BASE = """
Você é um extrator de habilidades técnicas.
Objetivo: a partir do texto da vaga abaixo, extraia SOMENTE hard skills presentes literalmente no texto e retorne APENAS um JSON válido.

Instruções de saída:
- Retorne exatamente: {"habilidades": ["..."]} — sem markdown, sem comentários, sem texto extra.

Critérios de inclusão:
- Inclua quaisquer competências técnicas literalmente citadas, abrangendo todas as áreas de TI: linguagens, runtimes, frameworks, bibliotecas, bancos de dados, dados/analytics, backend, frontend, mobile, cloud, DevOps, segurança, redes/infraestrutura, protocolos, padrões de API, sistemas operacionais e ferramentas.
- Não inclua soft skills, cargos/funções, níveis (júnior/pleno/sênior), anos de experiência e idiomas.
- Não inclua nomes de certificações/certificados.

Precisão:
- Não invente. Se não houver habilidades técnicas, retorne {"habilidades": []}.

Padronização de nomes:
- Use nomes canônicos quando aplicável (lista não exaustiva — não limite a esta lista): Java, Python, JavaScript, TypeScript, Node.js, React, Angular, Vue.js, .NET, C#, C++, SQL, NoSQL, PostgreSQL, MySQL, MongoDB, Git, Docker, Kubernetes, AWS, GCP, Azure, Linux, Redis, GraphQL, Kafka, Jenkins, Terraform.
- Retorne cada habilidade no singular canônico quando aplicável (ex.: switches → switch, roteadores → roteador, firewalls → firewall, backups → backup, APIs → API, bancos de dados → banco de dados).

Normalização adicional:
- Não repita itens; a lista deve conter valores únicos.

Exemplos de saída válida:
{"habilidades": ["Python", "Django", "PostgreSQL", "Docker", "AWS"]}
{"habilidades": ["Java", "Spring Boot", "SQL", "Kafka", "Kubernetes"]}
{"habilidades": ["Next.js", "Node.js", "MongoDB"]}

Texto da vaga:
"""

# Padrões para normalização de habilidades
PADROES = {
    # Tecnologias e linguagens
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
    r"^aprendizado de maquina$": "Machine Learning",
    r"^ia$": "Inteligência Artificial",
    r"^ai$": "Inteligência Artificial",

    # Protocolos / siglas amplamente usadas
    r"^rest$": "REST",
    r"^http$": "HTTP",
    r"^tcp/?ip$": "TCP/IP",
    r"^ospf$": "OSPF",
    r"^bgp$": "BGP",
    r"^vpn$": "VPN",
    r"^vlan$": "VLAN",
    r"^qos$": "QoS",

    # Ferramentas/tecnologias comuns (sem limitar a infra)
    r"^zabbix$": "Zabbix",
    r"^prtg$": "PRTG",
    r"^nagios$": "Nagios",
    r"^cisco$": "Cisco",
    r"^fortinet$": "Fortinet",
    r"^mikrotik$": "Mikrotik",
    r"^active directory$": "Active Directory",
    r"^azure ad$": "Azure AD",

    # ETL e BI
    r"^etl$": "ETL",
    r"^ferramenta de etl$": "ETL",
    r"^ferramenta de bi$": "PowerBI",
    r"^bi$": "PowerBI",
    r"^powerbi$": "PowerBI",
    r"^power bi$": "PowerBI",
    # Banco de Dados não relacional
    r"^banco de dados nao relacional$": "Banco de Dados não relacional",
    r"^banco de dados naorelacional$": "Banco de Dados não relacional",
}

# lista de tuplas a partir do dicionário PADROES
PADROES_COMPILADOS = [(re.compile(p, re.IGNORECASE), v) for p, v in PADROES.items()]

# Normaliza uma habilidade conforme os padrões definidos
def normalizar_habilidade(habilidade: str) -> str:
    habilidade = habilidade.strip() # remove espaços em branco nas extremidades
    habilidade = re.sub(r'\s+', ' ', habilidade)[:60] # reduz múltiplos espaços e limita tamanho
    nfkd = unicodedata.normalize('NFKD', habilidade) # normaliza acentuação
    habilidade = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower() # remove acentos e converte para minúsculas
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala)(\d{1,3}(?:\.\d+)*)\b', r'\1', habilidade) # remove versões
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala)[ \-]+\d+(?:\.\d+){0,2}\b', r'\1', habilidade) # remove versões com hífen/espaço
    habilidade = re.sub(r'\b(c\+\+|c#)[ \-]*\d{1,2}\b', r'\1', habilidade) # remove versões de C++ e C#
    habilidade = re.sub(r'\b(dotnet|\.net)[ \-]*\d+(?:\.\d+){0,2}\b', r'dotnet', habilidade) # remove versões de .NET
    habilidade = habilidade.strip(' .;,-') # remove caracteres indesejados nas extremidades

    # Aplica padrões de normalização
    for regex, valor in PADROES_COMPILADOS:
        if regex.fullmatch(habilidade):
            return valor

    # Transforma o primeiro caractere de uma string em maiúsculo
    if len(habilidade.split()) <= 3 and not re.search(r'[A-Z]{2,}', habilidade):
        habilidade = ' '.join(p.capitalize() for p in habilidade.split())

    return habilidade

# Padroniza a descrição da vaga para facilitar a extração
def padronizar_descricao(descricao: str) -> str:
    descricao = unicodedata.normalize('NFD', descricao) # normaliza acentuação
    descricao = descricao.encode('ascii', 'ignore').decode('utf-8') # remove acentos
    descricao = descricao.lower() # converte para minúsculas
    descricao = re.sub(r'[^a-z0-9\s]', '', descricao) # remove caracteres especiais
    descricao = re.sub(r'\s+', ' ', descricao).strip() # reduz múltiplos espaços e remove espaços nas extremidades
    return descricao

# Elimina cópias redundantes
def deduplicar(hab: str) -> str:
    hab = hab.strip().lower() # remove espaços e converte para minúsculas
    hab = unicodedata.normalize('NFD', hab) # normaliza acentuação
    hab = ''.join(c for c in hab if not unicodedata.combining(c)) # remove acentos
    hab = re.sub(r'[^a-z0-9]', '', hab) # remove caracteres especiais
    return hab

# Extrai habilidades da descrição usando a API do OpenAI
def extrair_habilidades_descricao(descricao: str) -> List[str]:
    cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # inicializa o cliente com a chave da API
    prompt = PROMPT_BASE + descricao # cria o prompt completo
    try:
        resposta = cliente.responses.create(
            model="gpt-4.1",
            input=prompt,
            temperature=0.15, # baixo para respostas mais consistentes
            max_output_tokens=500
        )
        texto_completo = ""
        # Extrai o texto da resposta
        if hasattr(resposta, "output_text") and resposta.output_text:
            texto_completo = resposta.output_text.strip() # resposta direta
        else:
            blocos_puros = [] # lista para armazenar blocos de texto
            blocos = getattr(resposta, "output", []) or [] # resposta em blocos
            for bloco in blocos:
                if getattr(bloco, "type", None) == "output_text": # verifica o tipo do bloco
                    blocos_puros.append(getattr(bloco, "text", "").strip()) # adiciona texto do bloco
            texto_completo = "\n".join(t for t in blocos_puros if t).strip() # junta blocos de texto

        # Extrai habilidades do JSON na resposta
        habilidades_extraidas: List[str] = []

        # Função auxiliar para tentar interpretar um segmento como JSON
        def tentar_json(segmento: str):
            nonlocal habilidades_extraidas # permite modificar a variável externa
            try:
                data = json.loads(segmento) # tenta carregar o JSON
                # Verifica se o JSON contém a chave "habilidades"
                if isinstance(data, dict) and isinstance(data.get("habilidades"), list):
                    habilidades_extraidas = [
                        normalizar_habilidade(h) for h in data["habilidades"]
                    ]
            except json.JSONDecodeError:
                pass

        # Tenta interpretar o texto completo como JSON
        if texto_completo:
            tentar_json(texto_completo)

        # Se não conseguiu, tenta encontrar um trecho JSON no texto
        if not habilidades_extraidas:
            achado = re.search(r'\{.*"habilidades"\s*:\s*\[.*?\]\s*\}', texto_completo, re.DOTALL)
            if achado:
                tentar_json(achado.group(0))

        finais: List[str] = [] # lista final de habilidades deduplicadas
        vistos = set() # conjunto para rastrear habilidades já vistas

        # Deduplica habilidades extraídas
        for hab in habilidades_extraidas:
            chave = deduplicar(hab)
            if chave not in vistos:
                vistos.add(chave)
                finais.append(hab)
        return finais
    
    # Em caso de erro, retorna lista vazia
    except Exception as exc:
        return []
