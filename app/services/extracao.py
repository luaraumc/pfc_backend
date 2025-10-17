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

# Categorias por habilidade normalizada
CATEGORIA_POR_HABILIDADE = {
    # API/Web
    "API": "Web",
    "REST": "Web",
    "OpenAPI": "Web",
    "Web Service": "Web",
    "WebSocket": "Web",
    "GraphQL": "Web",
    "Storefront API": "Web",
    "Context API": "Web",
    "Single Page Applications": "Web",
    "Server-Side Rendering": "Web",
    "Geração de Sites Estáticos": "Web",
    "WebGL": "Web",

    # Frontend/UI
    "Angular": "Web",
    "Angular CLI": "Web",
    "React": "Web",
    "Vue.js": "Web",
    "Material UI": "Web",
    "Tailwind": "Web",
    "NgRx": "Web",
    "RxJS": "Web",

    # Backend/Frameworks
    ".NET": "Backend",
    "ASP.NET": "Backend",
    "ASP Clássico": "Backend",
    "Express.js": "Backend",
    "FastAPI": "Backend",
    "Spring": "Backend",
    "NestJS": "Backend",
    "JavaServer Pages": "Backend",
    "Enterprise JavaBeans": "Backend",
    "Servidor de Aplicação": "Backend",
    "Apache Tomcat": "Backend",
    "WildFly": "Backend",
    "NGINX": "Backend",
    "Microsoft IIS": "Backend",
    "Express.js": "Backend",

    # Linguagens e formatos
    "JavaScript": "Linguagens e formatos",
    "TypeScript": "Linguagens e formatos",
    "Python": "Linguagens e formatos",
    "GO": "Linguagens e formatos",
    "Visual Basic": "Linguagens e formatos",
    "SQL": "Linguagens e formatos",
    "PL/SQL": "Linguagens e formatos",
    "JSON": "Linguagens e formatos",
    "XML": "Linguagens e formatos",
    "YAML": "Linguagens e formatos",
    "ECMAScript": "Linguagens e formatos",

    # Bibliotecas/SDKs
    "AIOHTTP": "Bibliotecas/SDKs",
    "FAISS": "Bibliotecas/SDKs",
    "Great Expectations": "Bibliotecas/SDKs",
    "Scikit-Learn": "Bibliotecas/SDKs",
    "SpaCy": "Bibliotecas/SDKs",
    "PySpark": "Bibliotecas/SDKs",
    "JWT": "Bibliotecas/SDKs",
    "Redux": "Bibliotecas/SDKs",
    "SDK": "Bibliotecas/SDKs",
    "JPA": "Bibliotecas/SDKs",

    # Dados/Big Data/ETL/Analytics
    "Apache Airflow": "Dados",
    "AWS Glue": "Dados",
    "DataOps": "Dados",
    "ETL": "Dados",
    "ELT": "Dados",
    "Looker Studio": "Dados",
    "Power BI": "Dados",
    "Modelagem Dimensional": "Dados",
    "Modelagem de Dados": "Dados",
    "Common Table Expression": "Dados",
    "Otimização de Consultas SQL": "Dados",

    # Bancos de dados
    "PostgreSQL": "Banco de Dados",
    "MySQL": "Banco de Dados",
    "SQL Server": "Banco de Dados",
    "IBM Db2": "Banco de Dados",
    "Oracle DB": "Banco de Dados",
    "AlloyDB": "Banco de Dados",
    "MongoDB": "Banco de Dados",
    "Amazon DynamoDB": "Banco de Dados",
    "Amazon DocumentDB": "Banco de Dados",
    "LiteDB": "Banco de Dados",
    "Banco de Dados": "Banco de Dados",
    "Banco de Dados Relacional": "Banco de Dados",
    "Banco de Dados Não Relacional": "Banco de Dados",
    "NoSQL": "Banco de Dados",

    # Mensageria/Eventos/Streaming
    "Apache Kafka": "Mensageria",
    "RabbitMQ": "Mensageria",
    "Apache ActiveMQ": "Mensageria",
    "Amazon MSK": "Mensageria",
    "AWS SQS": "Mensageria",
    "Amazon EventBridge": "Mensageria",
    "Pub/Sub": "Mensageria",
    "Enfileiramento de Mensagens": "Mensageria",

    # DevOps/CI-CD/Contêineres
    "DevOps": "DevOps",
    "Git": "DevOps",
    "GitLab": "DevOps",
    "GitHub": "DevOps",
    "GitLab CI/CD": "DevOps",
    "Azure DevOps": "DevOps",
    "Docker": "DevOps",
    "Kubernetes": "DevOps",
    "SonarQube": "DevOps",

    # Cloud
    "Cloud Computing": "Cloud",
    "AWS": "Cloud",
    "Amazon EC2": "Cloud",
    "Amazon EKS": "Cloud",
    "Amazon ECR": "Cloud",
    "Amazon CloudWatch": "Cloud",
    "Amazon Athena": "Cloud",
    "AWS IAM": "Cloud",
    "AWS WAF": "Cloud",
    "AWS Shield": "Cloud",
    "AWS Firewall": "Cloud",
    "AWS DMS": "Cloud",
    "Azure": "Cloud",
    "Azure AD": "Cloud",
    "Azure AD Connect": "Cloud",
    "Azure AI Search": "Cloud",
    "Azure OpenAI": "Cloud",
    "Azure Operator Nexus": "Cloud",
    "Microsoft Purview": "Cloud",
    "Google Cloud Platform": "Cloud",
    "Google Cloud Storage": "Cloud",
    "gcloud CLI": "Cloud",

    # Segurança da Informação / AppSec / Identidade
    "Cibersegurança": "Segurança",
    "Segurança da Informação": "Segurança",
    "Gestão de Vulnerabilidades": "Segurança",
    "Scanner de Vulnerabilidade": "Segurança",
    "SIEM": "Segurança",
    "Centro de Operações de Segurança": "Segurança",
    "XDR": "Segurança",
    "Endpoint Detection and Response": "Segurança",
    "Endpoint Security": "Segurança",
    "SAST": "Segurança",
    "DAST": "Segurança",
    "OWASP": "Segurança",
    "MITRE ATT&CK": "Segurança",
    "NIST": "Segurança",
    "CIS Controls": "Segurança",
    "BSIMM": "Segurança",
    "OpenSAMM": "Segurança",
    "PCI DSS": "Segurança",
    "ISO": "Segurança",
    "ISO 27000": "Segurança",
    "ISO 27001": "Segurança",
    "ISO 27002": "Segurança",
    "ISO 27701": "Segurança",
    "Lei Geral de Proteção de Dados Pessoais": "Segurança",
    "Regulamento Geral sobre a Proteção de Dados": "Segurança",
    "ANPD": "Segurança",
    "Proteção de Dados": "Segurança",
    "Pseudonimização": "Segurança",
    "Mascaramento de Dados": "Segurança",
    "Registro de Operações de Tratamento de Dados Pessoais": "Segurança",
    "OneTrust": "Segurança",
    "Microsoft Defender for Endpoint": "Segurança",
    "CrowdStrike": "Segurança",
    "Sophos": "Segurança",
    "CyberArk": "Segurança",
    "Privileged Access Management": "Segurança",
    "Single Sign-On": "Segurança",
    "OAuth 2.0": "Segurança",
    "OIDC": "Segurança",
    "OpenID": "Segurança",
    "SAML": "Segurança",
    "SSL": "Segurança",
    "Transport Layer Security": "Segurança",
    "Web Application Firewall": "Segurança",
    "Burp Suite": "Segurança",
    "REST Assured": "Segurança",
    "SQLMAP": "Segurança",
    "Pentest": "Segurança",
    "Brute Force": "Segurança",
    "Hydra Launcher": "Segurança",
    "URL filtering": "Segurança",
    "ZTNA": "Segurança",

    # Redes
    "Redes": "Redes",
    "Protocolos de Rede": "Redes",
    "Protocolos de Segurança": "Redes",
    "Roteamento": "Redes",
    "Topologia de Rede": "Redes",
    "Equipamentos de Rede": "Redes",
    "IP Address": "Redes",
    "TCP/IP": "Redes",
    "IEEE 802.11": "Redes",
    "DNS": "Redes",
    "DHCP": "Redes",
    "IMAP": "Redes",
    "SMTP": "Redes",
    "SNMP": "Redes",
    "IPsec": "Redes",
    "QoS": "Redes",
    "Quality of Service": "Redes",
    "LAN": "Redes",
    "VLAN": "Redes",
    "WAN": "Redes",
    "Wireless Local Area Network": "Redes",
    "LACP": "Redes",
    "L2VPN": "Redes",
    "HSRP": "Redes",
    "OSPF": "Redes",
    "BGP": "Redes",
    "MPLS": "Redes",
    "PPPoe": "Redes",
    "VRF": "Redes",
    "VPN": "Redes",
    "Telefonia IP": "Redes",
    "VoIP": "Redes",
    "Wi-Fi": "Redes",
    "Wireless Local Area Network": "Redes",
    "Wide Area Network": "Redes",
    "Fibra Óptica": "Redes",
    "GPON": "Redes",
    "Terminal de Linha Óptica": "Redes",
    "Terminal de Rede Óptica": "Redes",
    "Transceptor": "Redes",
    "Circuito de Dados": "Redes",
    "Redundância": "Redes",
    "Redundância de Rede": "Redes",
    "Switch": "Redes",

    # Observabilidade
    "Registro Estruturado": "Observabilidade",
    "Rastreamento de Atividades": "Observabilidade",
    "Tracing": "Observabilidade",
    "Trace": "Observabilidade",
    "NOC": "Redes",
    "Zabbix": "Observabilidade",
    "Nagios": "Observabilidade",
    "Paessler PRTG": "Observabilidade",
    "SolarWinds": "Observabilidade",

    # Infraestrutura / Sistemas / Virtualização
    "Hyper-V": "Infraestrutura",
    "Virtualização": "Infraestrutura",
    "Máquina Virtual": "Infraestrutura",
    "Virtual Private Cloud": "Infraestrutura",
    "Servidor de Arquivos": "Infraestrutura",
    "Servidor de Arquivos Samba": "Infraestrutura",
    "Remote Desktop Services": "Infraestrutura",
    "TeamViewer": "Infraestrutura",
    "AnyDesk": "Infraestrutura",
    "pfSense": "Infraestrutura",
    "Mikrotik": "Infraestrutura",
    "Cisco": "Infraestrutura",
    "Juniper Networks": "Infraestrutura",
    "Cisco Meraki": "Infraestrutura",
    "UniFi": "Infraestrutura",
    "VeloCloud": "Infraestrutura",
    "TeamViewer": "Infraestrutura",
    "AnyDesk": "Infraestrutura",
    "Windows": "Sistemas Operacionais",
    "MacOS": "Sistemas Operacionais",

    # Produtividade
    "Microsoft 365": "Produtividade",
    "Microsoft Teams": "Produtividade",
    "Microsoft Outlook": "Produtividade",
    "Microsoft SharePoint": "Produtividade",
    "Microsoft OneDrive": "Produtividade",
    "Microsoft Planner": "Produtividade",
    "Microsoft To Do": "Produtividade",
    "Microsoft Sway": "Produtividade",
    "Microsoft Loop": "Produtividade",
    "Microsoft Clipchamp": "Produtividade",
    "Microsoft Power Apps": "Produtividade",
    "Microsoft Power Automate": "Produtividade",
    "Microsoft Power Platform": "Produtividade",
    "Google Forms": "Produtividade",

    # Desenvolvimento/IDE/Qualidade
    "Virtual Studio Code": "Desenvolvimento",
    "Eclipse IDE": "Desenvolvimento",
    "Intellij IDEA": "Desenvolvimento",
    "Apache JMeter": "Desenvolvimento",
    "Apache Maven": "Desenvolvimento",
    "JUnit": "Desenvolvimento",
    "Linter": "Desenvolvimento",

    # Arquitetura/Práticas
    "Arquitetura de Sistemas": "Arquitetura",
    "Arquitetura Distribuída": "Arquitetura",
    "Arquitetura de Software": "Arquitetura",
    "Padrões de Arquitetura": "Arquitetura",
    "Padrões Arquiteturais": "Arquitetura",
    "Microsserviços": "Arquitetura",
    "Domain-Driven Design": "Arquitetura",
    "Programação Orientada a Objetos": "Arquitetura",
    "Programação Funcional": "Arquitetura",
    "Injeção de Dependência": "Arquitetura",
    "Back-End": "Arquitetura",
    "Front-End": "Arquitetura",
    "Container": "Arquitetura",

    # Gestão/Metodologias
    "Política como Código": "Governança e Gestão",
    "Política de Segurança de TI": "Governança e Gestão",
    "Gestão de Riscos": "Governança e Gestão",
    "Análise De Riscos": "Governança e Gestão",
    "Matriz de Risco Corporativa": "Governança e Gestão",
    "Gestão de Mudanças": "Governança e Gestão",
    "Procedimentos Operacionais Padrão": "Governança e Gestão",
    "Governança de Dados": "Governança e Gestão",
    "COBIT": "Governança e Gestão",
    "ITIL": "Governança e Gestão",
    "ITSM": "Governança e Gestão",
    "ITOM": "Governança e Gestão",
    "Lean IT": "Governança e Gestão",
    "LeSS": "Governança e Gestão",
    "TOGAF": "Governança e Gestão",
    "PMBOK": "Governança e Gestão",
    "PRINCE2": "Governança e Gestão",
    "Gerenciamento de Projetos": "Governança e Gestão",
    "Project Management Institute": "Governança e Gestão",
    "Microsoft Project": "Governança e Gestão",
    "Microsoft Project Server": "Governança e Gestão",
    "Adobe Workfront": "Governança e Gestão",
    "ServiceNow": "Governança e Gestão",
    "ServiceNow GRC": "Governança e Gestão",
    "RSA Archer": "Governança e Gestão",
    "MetricStream": "Governança e Gestão",

    # Identidade/Intune/MDM
    "Microsoft Intune": "Identidade",
    "MDM": "Identidade",
    "Workspace ONE": "Identidade",
    "Active Directory": "Identidade",
    "Hybrid Azure AD Join": "Identidade",

    # Serviços/Aplicações de Negócio
    "ERP": "Aplicações de Negócio",
    "Customer Relationship Management": "Aplicações de Negócio",
    "Microsoft Exchange": "Mensageria",
    "Microsoft Exchange Online": "Mensageria",
    "Sistema SAP": "Aplicações de Negócio",
    "SAP S/4HANA": "Aplicações de Negócio",
    "Sistemas de Gestão de Recursos Humanos": "Aplicações de Negócio",
    "Order Management System": "Aplicações de Negócio",
    "WMS": "Aplicações de Negócio",

    # Privacidade/Regulação/Leis
    "Marco Civil da Internet": "Compliance",
    "Lei Sarbanes-Oxley": "Compliance",
    "Termo de Uso de Dados": "Compliance",

    # AI/ML/Data Science
    "Inteligência Artificial": "IA/ML",
    "IA": "IA/ML",
    "IA Generativa": "IA/ML",
    "LLM": "IA/ML",
    "LlamaIndex": "IA/ML",
    "LangGraph": "IA/ML",
    "BERT": "IA/ML",
    "k-means": "IA/ML",
    "Processamento de Linguagem Natural": "IA/ML",
    "Visão Computacional": "IA/ML",
    "Fine-tuning": "IA/ML",
    "Estatística": "IA/ML",
    "Regressão Linear": "IA/ML",
    "Regressão Logística": "IA/ML",
    "Apache Spark": "IA/ML",
    "XGBoost": "IA/ML",

    # Qualidade/Testes/Automação
    "Automação de Teste": "Qualidade",
    "Teste Unitário": "Qualidade",
    "Teste de Unidade": "Qualidade",
    "Teste de Caixa-Branca": "Qualidade",
    "Teste de Caixa-Preta": "Qualidade",
    "Teste de Integração": "Qualidade",
    "Relatório Técnico": "Qualidade",

    # Ferramentas
    "Google Web Designer": "Ferramentas",
    "ManageEngine": "Ferramentas",
    "GLPi": "Ferramentas",
    "Microsoft SCCM": "Ferramentas",
    
    # Conceitos diversos
    "Aplicação Web": "Conceitos",
    "Aplicação Mobile": "Conceitos",
    "Aplicação Desktop": "Conceitos",
    "Controle de Versão de Software": "Conceitos",
    "Versionamento": "Conceitos",
    "Visualização de Dados": "Conceitos",
    "Formatação de Computadores": "Conceitos",
    "Frameworks de Persistência": "Conceitos",
    "Segurança de Rede": "Conceitos",
    "Segurança Perimetral": "Conceitos",
    "Gestão de Incidentes": "Conceitos",
    "Suporte Remoto": "Conceitos",
    "Serviços de Integração": "Conceitos",
    "Processamento em Lote": "Conceitos",
    "Requisições Web": "Conceitos",
    "Busca Semântica": "Conceitos",
    "Lógica de Programação": "Conceitos",
    "Mapeamento de Dados": "Conceitos",
    "Mapeamento de Unidade de Rede": "Conceitos",
    "Mapeamento de Processos": "Conceitos",
    "Máscara de Rede": "Conceitos",
    "Programação Orientada a Objetos": "Arquitetura",
    "Java EE": "Backend",
    "Modelo OSI": "Redes",
    "Lean IT": "Governança e Gestão",
    "Hybrid Azure AD Join": "Identidade/MDM",
    "Policy": "Governança e Gestão",
    "SaaS": "Modelos de Entrega",
    "ServiceNow": "ITSM",
    "Order Management System": "Aplicações de Negócio",
    "WMS": "Aplicações de Negócio",
}

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
