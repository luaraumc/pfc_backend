from dotenv import load_dotenv # variáveis de ambiente de um arquivo .env
import os # manipulação do sistema operacional
from typing import List # tipos para listas
from sqlalchemy.orm import Session
from openai import OpenAI # cliente OpenAI para chamadas à API
import json, re, unicodedata # manipulação de JSON, expressões regulares e normalização de texto
from app.models import Normalizacao, Categoria # modelos de tabela definidos no arquivo models.py

load_dotenv() # carrega chave da API do arquivo .env

# Instrução para o modelo
PROMPT_BASE = """
Você é um extrator de habilidades técnicas.
Objetivo: a partir do texto da vaga abaixo, extraia SOMENTE hard skills presentes literalmente no texto e retorne APENAS um JSON válido.

Instruções de saída:
- Retorne exatamente: {"habilidades": [{"nome": "...", "categoria": "<uma das categorias listadas>"}, ...]} — sem markdown, sem comentários, sem texto extra.
- A categoria deve ser escolhida EXCLUSIVAMENTE da lista de categorias permitidas abaixo.

Critérios de inclusão:
- Inclua quaisquer competências técnicas literalmente citadas, abrangendo todas as áreas de TI: linguagens, runtimes, frameworks, bibliotecas, bancos de dados, dados/analytics, backend, frontend, mobile, cloud, DevOps, segurança, redes/infraestrutura, protocolos, padrões de API, sistemas operacionais e ferramentas.
- Não inclua soft skills, cargos/funções, níveis (júnior/pleno/sênior), anos de experiência e idiomas.
- Não inclua nomes de certificações/certificados.

Critérios de exclusão adicionais:
- Ignore marcas comerciais e nomes de empresas (ex.: HP, Dell, Samsung, Apple, Huawei, IBM, Nokia...).
- Ignore periféricos/hardware de uso geral (ex.: monitor, teclado, mouse, impressora...).
- Ignore palavras genéricas isoladas que não caracterizam uma tecnologia específica (ex.: monitoramento, protocolo, relatório, segurança, serviço, servidor, sinônimo, software, storage, task, voz, vulnerabilidade, web).

Precisão:
- Não invente. Se não houver habilidades técnicas, retorne {"habilidades": []}.
- Considere e corrija erros de digitação evidentes quando o termo técnico for inequívoco (ex.: "Pyhton" → "Python").
- Toda habilidade deve ser associada a uma categoria, mesmo que o texto não a especifique.

Padronização de nomes:
- Use nomes canônicos quando aplicável (lista não exaustiva — não limite a esta lista): Java, Python, JavaScript, TypeScript, Node.js, React, Angular, Vue.js, .NET, C#, C++, SQL, NoSQL, PostgreSQL, MySQL, MongoDB, Git, Docker, Kubernetes, AWS, GCP, Azure, Linux, Redis, GraphQL, Kafka, Jenkins, Terraform.
- Retorne cada habilidade no singular canônico quando aplicável (ex.: switches → switch, roteadores → roteador, firewalls → firewall, backups → backup, APIs → API, bancos de dados → banco de dados).

Normalização adicional:
- Não repita itens; a lista deve conter valores únicos.

Abreviações:
- Normalize abreviações comuns para seus nomes canônicos quando aplicável (ex.: "Ms Project"/"Msft Project" → "Microsoft Project").

Exemplos de saída válida:
{"habilidades": [{"nome": "Python", "categoria": "Linguagens"}, {"nome": "Django", "categoria": "Backend/Framework"}]}
{"habilidades": [{"nome": "Java", "categoria": "Linguagens"}, {"nome": "Spring Boot", "categoria": "Backend/Framework"}]}

Categorias permitidas (escolha exata de um destes nomes):
 - Aplicações de Negócio
 - Arquitetura
 - Backend
 - Banco de Dados
 - Bibliotecas/SDKs
 - Cloud
 - Compliance
 - Conceitos
 - Dados
 - Desenvolvimento
 - DevOps
 - Ferramentas
 - Governança e Gestão
 - IA/ML
 - Identidade
 - Identidade/MDM
 - Infraestrutura
 - ITSM
 - Linguagens e formatos
 - Mensageria
 - Modelos de Entrega
 - Observabilidade
 - Produtividade
 - Qualidade
 - Redes
 - Segurança
 - Sistemas Operacionais
 - Web
"""

# Carrega padrões de normalização da base de dados
def carregar_padroes_db(session: Session | None) -> list[tuple[re.Pattern, str]]:
    if session is None:
        return []
    try:
        regras = session.query(Normalizacao).order_by(Normalizacao.id.asc()).all()
        return [(re.compile(r.nome, re.IGNORECASE), r.nome_padronizado) for r in regras]
    except Exception:
        return []

# Lista os nomes de categorias existentes no banco (para orientar o modelo)
def listar_categorias_db(session: Session | None) -> list[str]:
    if session is None:
        return []
    try:
        categorias = session.query(Categoria).order_by(Categoria.nome.asc()).all()
        return [c.nome for c in categorias]
    except Exception:
        return []

# Normaliza uma habilidade conforme os padrões definidos
def normalizar_habilidade(habilidade: str, session: Session | None = None) -> str:
    habilidade = habilidade.strip() # remove espaços em branco nas extremidades
    habilidade = re.sub(r'[\-_\/]+', ' ', habilidade) # normaliza hífen/underscore/"/" em espaço
    habilidade = re.sub(r'\s+', ' ', habilidade)[:60] # reduz múltiplos espaços e limita tamanho
    nfkd = unicodedata.normalize('NFKD', habilidade) # normaliza acentuação
    habilidade = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower() # remove acentos e converte para minúsculas
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala|windows)(\d{1,3}(?:\.\d+)*)\b', r'\1', habilidade) # remove versões
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala|windows)[ \-]+\d+(?:\.\d+){0,2}\b', r'\1', habilidade) # remove versões com hífen/espaço
    habilidade = re.sub(r'\b(c\+\+|c#)[ \-]*\d{1,2}\b', r'\1', habilidade) # remove versões de C++ e C#
    habilidade = re.sub(r'\b(dotnet|\.net)[ \-]*\d+(?:\.\d+){0,2}\b', r'dotnet', habilidade) # remove versões de .NET
    habilidade = habilidade.strip(' .;,-') # remove caracteres indesejados nas extremidades

    # Aplica padrões de normalização
    # 1) Tenta com padrões vindos do banco
    for regex, valor in carregar_padroes_db(session) or []:
        if regex.fullmatch(habilidade):
            return valor  # valor já está com acento e capitalização correta

    # Se não encontrou no padrão, capitaliza a primeira letra de cada palavra
    habilidade_cap = ' '.join(p.capitalize() for p in habilidade.split())
    return habilidade_cap

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
def extrair_habilidades_descricao(descricao: str, session: Session | None = None) -> List[dict]:
    cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # inicializa o cliente com a chave da API
    categorias_lista = listar_categorias_db(session)
    categorias_texto = "\n".join(f"- {nome}" for nome in categorias_lista) if categorias_lista else ""
    prompt = f"{PROMPT_BASE}\n{categorias_texto}\n\nTexto da vaga:\n" + descricao # cria o prompt completo com categorias
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
        habilidades_extraidas: List[dict] = []  # cada item: {"nome": str, "categoria_sugerida": Optional[str]}

        # Função auxiliar para tentar interpretar um segmento como JSON
        def _validar_categoria_sugerida(cat: str | None) -> str | None:
            if not cat:
                return None
            if not categorias_lista:
                return None
            # faz comparação case-insensitive e retorna o nome com a capitalização correta do banco
            for c in categorias_lista:
                if c.strip().lower() == str(cat).strip().lower():
                    return c
            return None

        def tentar_json(segmento: str):
            nonlocal habilidades_extraidas # permite modificar a variável externa
            try:
                data = json.loads(segmento) # tenta carregar o JSON
                # Verifica se o JSON contém a chave "habilidades"
                if isinstance(data, dict) and isinstance(data.get("habilidades"), list):
                    coletadas: list[dict] = []
                    for item in data["habilidades"]:
                        if isinstance(item, str):
                            nome_norm = normalizar_habilidade(item, session=session)
                            coletadas.append({"nome": nome_norm, "categoria_sugerida": None})
                        elif isinstance(item, dict):
                            nome_bruto = item.get("nome") or item.get("habilidade") or item.get("skill")
                            cat_bruta = item.get("categoria") or item.get("categoria_sugerida")
                            if isinstance(nome_bruto, str) and nome_bruto.strip():
                                nome_norm = normalizar_habilidade(nome_bruto, session=session)
                                cat_ok = _validar_categoria_sugerida(cat_bruta)
                                coletadas.append({"nome": nome_norm, "categoria_sugerida": cat_ok})
                    habilidades_extraidas = coletadas
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

        finais: List[dict] = [] # lista final deduplicada de objetos
        vistos = set() # conjunto para rastrear habilidades já vistas

        # Deduplica e filtra habilidades extraídas
        for item in habilidades_extraidas:
            nome = item.get("nome") if isinstance(item, dict) else str(item)
            cat_sug = item.get("categoria_sugerida") if isinstance(item, dict) else None
            chave = deduplicar(nome)
            if chave not in vistos and nome:
                vistos.add(chave)
                finais.append({"nome": nome, "categoria_sugerida": _validar_categoria_sugerida(cat_sug)})
        return finais

    # Em caso de erro, retorna lista vazia
    except Exception as exc:
        return []
