from dotenv import load_dotenv # variáveis de ambiente de um arquivo .env
import os # manipulação do sistema operacional
from typing import List # tipos para listas
from sqlalchemy.orm import Session
from openai import OpenAI # cliente OpenAI para chamadas à API
import json, re, unicodedata # manipulação de JSON, expressões regulares e normalização de texto
from app.models import Normalizacao # modelo de tabela definido no arquivo models.py

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
{"habilidades": ["Python", "Django", "PostgreSQL", "Docker", "AWS"]}
{"habilidades": ["Java", "Spring Boot", "SQL", "Kafka", "Kubernetes"]}
{"habilidades": ["Next.js", "Node.js", "MongoDB"]}

Texto da vaga:
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

# Categorias por habilidade normalizada
CATEGORIA_POR_HABILIDADE = {
    # API/Web
    "API": "Web/API",
    "REST": "Web/API",
    "OpenAPI": "Web/API",
    "Web Service": "Web/API",
    "WebSocket": "Web/API",
    "GraphQL": "Web/API",
    "Storefront API": "Web/API",
    "Context API": "Web/API",
    "Single Page Applications": "Web/Frontend",
    "Server-Side Rendering": "Web/Frontend",
    "Geração de Sites Estáticos": "Web/Frontend",
    "WebGL": "Web/Frontend",

    # Frontend/UI
    "Angular": "Web/Frontend",
    "Angular CLI": "Web/Frontend",
    "React": "Web/Frontend",
    "Vue.js": "Web/Frontend",
    "Material UI": "Web/Frontend",
    "Tailwind": "Web/Frontend",
    "NgRx": "Web/Frontend",
    "RxJS": "Web/Frontend",

    # Backend/Frameworks
    ".NET": "Backend/Framework",
    "ASP.NET": "Backend/Framework",
    "ASP Clássico": "Backend/Framework",
    "Express.js": "Backend/Framework",
    "FastAPI": "Backend/Framework",
    "Spring": "Backend/Framework",
    "NestJS": "Backend/Framework",
    "JavaServer Pages": "Backend/Framework",
    "Enterprise JavaBeans": "Backend/Framework",
    "Servidor de Aplicação": "Backend/Execução",
    "Apache Tomcat": "Backend/Execução",
    "WildFly": "Backend/Execução",
    "NGINX": "Backend/Execução",
    "Microsoft IIS": "Backend/Execução",

    # Linguagens e formatos
    "JavaScript": "Linguagens",
    "TypeScript": "Linguagens",
    "Python": "Linguagens",
    "GO": "Linguagens",
    "Visual Basic": "Linguagens",
    "SQL": "Linguagens",
    "PL/SQL": "Linguagens",
    "JSON": "Linguagens",
    "XML": "Linguagens",
    "YAML": "Linguagens",
    "ECMAScript": "Linguagens",

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
    "Apache Airflow": "Dados/Big Data",
    "AWS Glue": "Dados/Big Data",
    "DataOps": "Dados/Big Data",
    "ETL": "Dados/Big Data",
    "ELT": "Dados/Big Data",
    "Looker Studio": "Dados/Analytics",
    "Power BI": "Dados/Analytics",
    "PowerBI": "Dados/Analytics",
    "Modelagem Dimensional": "Dados/Modelagem",
    "Modelagem de Dados": "Dados/Modelagem",
    "Common Table Expression": "Dados/SQL",
    "Otimização de Consultas SQL": "Dados/SQL",
    "Registro Estruturado": "Observabilidade/Logs",

    # Bancos de dados
    "PostgreSQL": "Banco de Dados/Relacional",
    "MySQL": "Banco de Dados/Relacional",
    "SQL Server": "Banco de Dados/Relacional",
    "IBM Db2": "Banco de Dados/Relacional",
    "Oracle DB": "Banco de Dados/Relacional",
    "AlloyDB": "Banco de Dados/Relacional",
    "MongoDB": "Banco de Dados/NoSQL",
    "Amazon DynamoDB": "Banco de Dados/NoSQL",
    "Amazon DocumentDB": "Banco de Dados/NoSQL",
    "LiteDB": "Banco de Dados/NoSQL",
    "Banco de Dados": "Banco de Dados/Conceitos",
    "Banco de Dados Relacional": "Banco de Dados/Conceitos",
    "Banco de Dados Não Relacional": "Banco de Dados/Conceitos",
    "NoSQL": "Banco de Dados/Conceitos",

    # Mensageria/Eventos/Streaming
    "Apache Kafka": "Mensageria/Streaming",
    "RabbitMQ": "Mensageria/Filas",
    "Apache ActiveMQ": "Mensageria/Filas",
    "Amazon MSK": "Mensageria/Streaming",
    "AWS SQS": "Mensageria/Filas",
    "Amazon EventBridge": "Mensageria/Eventos",
    "Pub/Sub": "Mensageria/Eventos",
    "Enfileiramento de Mensagens": "Mensageria/Conceitos",

    # DevOps/CI-CD/Contêineres
    "DevOps": "DevOps/Práticas",
    "Git": "DevOps/SCM",
    "GitLab": "DevOps/SCM",
    "GitHub": "DevOps/SCM",
    "GitLab CI/CD": "DevOps/CI-CD",
    "Azure DevOps": "DevOps/CI-CD",
    "Docker": "DevOps/Contêineres",
    "Kubernetes": "DevOps/Contêineres",
    "Express.js": "Backend/Framework",
    "SonarQube": "DevOps/Qualidade",

    # Cloud (geral e provedores)
    "Cloud Computing": "Cloud/Conceitos",
    "AWS": "Cloud/AWS",
    "Amazon EC2": "Cloud/AWS",
    "Amazon EKS": "Cloud/AWS",
    "Amazon ECR": "Cloud/AWS",
    "Amazon CloudWatch": "Cloud/AWS",
    "Amazon Athena": "Cloud/AWS",
    "AWS IAM": "Cloud/AWS",
    "AWS WAF": "Cloud/AWS",
    "AWS Shield": "Cloud/AWS",
    "AWS Firewall": "Cloud/AWS",
    "AWS DMS": "Cloud/AWS",
    "Azure": "Cloud/Azure",
    "Azure AD": "Cloud/Azure",
    "Azure AD Connect": "Cloud/Azure",
    "Azure AI Search": "Cloud/Azure",
    "Azure OpenAI": "Cloud/Azure",
    "Azure Operator Nexus": "Cloud/Azure",
    "Microsoft Purview": "Cloud/Azure",
    "Google Cloud Platform": "Cloud/GCP",
    "Google Cloud Storage": "Cloud/GCP",
    "gcloud CLI": "Cloud/GCP",

    # Segurança da Informação / AppSec / Identidade
    "Cibersegurança": "Segurança/InfoSec",
    "Segurança da Informação": "Segurança/InfoSec",
    "Gestão de Vulnerabilidades": "Segurança/InfoSec",
    "Scanner de Vulnerabilidade": "Segurança/InfoSec",
    "SIEM": "Segurança/InfoSec",
    "Centro de Operações de Segurança": "Segurança/InfoSec",
    "XDR": "Segurança/Endpoint",
    "Endpoint Detection and Response": "Segurança/Endpoint",
    "Endpoint Security": "Segurança/Endpoint",
    "SAST": "Segurança/AppSec",
    "DAST": "Segurança/AppSec",
    "OWASP": "Segurança/AppSec",
    "MITRE ATT&CK": "Segurança/Referenciais",
    "NIST": "Segurança/Referenciais",
    "CIS Controls": "Segurança/Referenciais",
    "BSIMM": "Segurança/Referenciais",
    "OpenSAMM": "Segurança/Referenciais",
    "PCI DSS": "Segurança/Compliance",
    "ISO": "Segurança/Normas",
    "ISO 27000": "Segurança/Normas",
    "ISO 27001": "Segurança/Normas",
    "ISO 27002": "Segurança/Normas",
    "ISO 27701": "Segurança/Normas",
    "Lei Geral de Proteção de Dados Pessoais": "Segurança/Privacidade",
    "Regulamento Geral sobre a Proteção de Dados": "Segurança/Privacidade",
    "ANPD": "Segurança/Privacidade",
    "Proteção de Dados": "Segurança/Privacidade",
    "Pseudonimização": "Segurança/Privacidade",
    "Mascaramento de Dados": "Segurança/Privacidade",
    "Registro de Operações de Tratamento de Dados Pessoais": "Segurança/Privacidade",
    "OneTrust": "Segurança/Privacidade",
    "Microsoft Defender for Endpoint": "Segurança/Endpoint",
    "CrowdStrike": "Segurança/Endpoint",
    "Sophos": "Segurança/Endpoint",
    "CyberArk": "Segurança/Identidade",
    "Privileged Access Management": "Segurança/Identidade",
    "Single Sign-On": "Segurança/Identidade",
    "OAuth 2.0": "Segurança/Identidade",
    "OIDC": "Segurança/Identidade",
    "OpenID": "Segurança/Identidade",
    "SAML": "Segurança/Identidade",
    "SSL": "Segurança/AppSec",
    "Transport Layer Security": "Segurança/AppSec",
    "Web Application Firewall": "Segurança/AppSec",
    "Burp Suite": "Segurança/AppSec",
    "REST Assured": "Segurança/Testes",
    "SQLMAP": "Segurança/Testes",
    "Pentest": "Segurança/Testes",
    "Brute Force": "Segurança/Conceitos",
    "Hydra Launcher": "Segurança/Testes",
    "URL filtering": "Segurança/Rede",
    "ZTNA": "Segurança/Rede",

    # Redes e Protocolos
    "Redes": "Redes/Conceitos",
    "Protocolos de Rede": "Redes/Conceitos",
    "Protocolos de Segurança": "Redes/Conceitos",
    "Roteamento": "Redes/Conceitos",
    "Topologia de Rede": "Redes/Conceitos",
    "Equipamentos de Rede": "Redes/Conceitos",
    "IP Address": "Redes/Protocolos",
    "TCP/IP": "Redes/Protocolos",
    "IEEE 802.11": "Redes/Protocolos",
    "DNS": "Redes/Protocolos",
    "DHCP": "Redes/Protocolos",
    "IMAP": "Redes/Protocolos",
    "SMTP": "Redes/Protocolos",
    "SNMP": "Redes/Protocolos",
    "IPsec": "Redes/Protocolos",
    "QoS": "Redes/Protocolos",
    "Quality of Service": "Redes/Protocolos",
    "LAN": "Redes/Protocolos",
    "VLAN": "Redes/Protocolos",
    "WAN": "Redes/Protocolos",
    "Wireless Local Area Network": "Redes/Protocolos",
    "LACP": "Redes/Protocolos",
    "L2VPN": "Redes/Protocolos",
    "HSRP": "Redes/Protocolos",
    "OSPF": "Redes/Roteamento",
    "BGP": "Redes/Roteamento",
    "MPLS": "Redes/Infraestrutura",
    "PPPoe": "Redes/Protocolos",
    "VRF": "Redes/Infraestrutura",
    "VPN": "Redes/Segurança",
    "Telefonia IP": "Redes/Telefonia",
    "VoIP": "Redes/Telefonia",
    "Wi-Fi": "Redes/Sem Fio",
    "Wireless Local Area Network": "Redes/Sem Fio",
    "Wide Area Network": "Redes/Protocolos",
    "Fibra Óptica": "Redes/Infraestrutura",
    "GPON": "Redes/Infraestrutura",
    "Terminal de Linha Óptica": "Redes/Infraestrutura",
    "Terminal de Rede Óptica": "Redes/Infraestrutura",
    "Transceptor": "Redes/Infraestrutura",
    "Circuito de Dados": "Redes/Infraestrutura",
    "Redundância": "Redes/Infraestrutura",
    "Redundância de Rede": "Redes/Infraestrutura",
    "Switch": "Redes/Dispositivos",
    "Rastreamento de Atividades": "Observabilidade/Tracing",
    "Tracing": "Observabilidade/Tracing",
    "Trace": "Observabilidade/Tracing",
    "NOC": "Redes/Operações",
    "Zabbix": "Observabilidade/Monitoramento",
    "Nagios": "Observabilidade/Monitoramento",
    "Paessler PRTG": "Observabilidade/Monitoramento",
    "SolarWinds": "Observabilidade/Monitoramento",

    # Infraestrutura / Sistemas / Virtualização
    "Hyper-V": "Infra/Virtualização",
    "Virtualização": "Infra/Virtualização",
    "Máquina Virtual": "Infra/Virtualização",
    "Virtual Private Cloud": "Infra/Redes (Cloud)",
    "Servidor de Arquivos": "Infra/Servidores",
    "Servidor de Arquivos Samba": "Infra/Servidores",
    "Remote Desktop Services": "Infra/Acesso Remoto",
    "TeamViewer": "Infra/Acesso Remoto",
    "AnyDesk": "Infra/Acesso Remoto",
    "pfSense": "Infra/Firewall",
    "Mikrotik": "Infra/Rede",
    "Cisco": "Infra/Rede",
    "Juniper Networks": "Infra/Rede",
    "Cisco Meraki": "Infra/Rede",
    "UniFi": "Infra/Rede",
    "VeloCloud": "Infra/Rede",
    "Windows": "Sistemas Operacionais",
    "MacOS": "Sistemas Operacionais",

    # Microsoft 365 / Produtividade
    "Microsoft 365": "Produtividade/Microsoft 365",
    "Microsoft Teams": "Produtividade/Microsoft 365",
    "Microsoft Outlook": "Produtividade/Microsoft 365",
    "Microsoft SharePoint": "Produtividade/Microsoft 365",
    "Microsoft OneDrive": "Produtividade/Microsoft 365",
    "Microsoft Planner": "Produtividade/Microsoft 365",
    "Microsoft To Do": "Produtividade/Microsoft 365",
    "Microsoft Sway": "Produtividade/Microsoft 365",
    "Microsoft Loop": "Produtividade/Microsoft 365",
    "Microsoft Clipchamp": "Produtividade/Microsoft 365",
    "Microsoft Power Apps": "Produtividade/Power Platform",
    "Microsoft Power Automate": "Produtividade/Power Platform",
    "Microsoft Power Platform": "Produtividade/Power Platform",

    # Ferramentas de desenvolvimento/IDE/Qualidade
    "Virtual Studio Code": "Dev/Ferramentas",
    "Eclipse IDE": "Dev/Ferramentas",
    "Intellij IDEA": "Dev/Ferramentas",
    "Apache JMeter": "Dev/Testes",
    "Apache Maven": "Dev/Build",
    "JUnit": "Dev/Testes",
    "Linter": "Dev/Qualidade",

    # Arquitetura/Práticas/Metodologias/Gestão
    "Arquitetura de Sistemas": "Arquitetura/Conceitos",
    "Arquitetura Distribuída": "Arquitetura/Conceitos",
    "Arquitetura de Software": "Arquitetura/Conceitos",
    "Padrões de Arquitetura": "Arquitetura/Conceitos",
    "Padrões Arquiteturais": "Arquitetura/Conceitos",
    "Microsserviços": "Arquitetura/Estilos",
    "Domain-Driven Design": "Arquitetura/Práticas",
    "Programação Orientada a Objetos": "Arquitetura/Práticas",
    "Programação Funcional": "Arquitetura/Práticas",
    "Injeção de Dependência": "Arquitetura/Práticas",
    "Back-End": "Arquitetura/Camadas",
    "Front-End": "Arquitetura/Camadas",
    "Container": "Arquitetura/Execução",
    "Política como Código": "Governança/Políticas",
    "Política de Segurança de TI": "Governança/Políticas",
    "Gestão de Riscos": "Governança/Riscos",
    "Análise De Riscos": "Governança/Riscos",
    "Matriz de Risco Corporativa": "Governança/Riscos",
    "Gestão de Mudanças": "Governança/Processos",
    "Procedimentos Operacionais Padrão": "Governança/Processos",
    "Governança de Dados": "Governança/Dados",
    "COBIT": "Governança/Frameworks",
    "ITIL": "Governança/Frameworks",
    "ITSM": "Governança/Processos",
    "ITOM": "Governança/Processos",
    "Lean IT": "Governança/Melhoria Contínua",
    "LeSS": "Governança/Metodologias Ágeis",
    "TOGAF": "Governança/Arquitetura",
    "PMBOK": "Gestão/Projetos",
    "PRINCE2": "Gestão/Projetos",
    "Gerenciamento de Projetos": "Gestão/Projetos",
    "Project Management Institute": "Gestão/Projetos",
    "Microsoft Project": "Gestão/Projetos",
    "Microsoft Project Server": "Gestão/Projetos",

    # Identidade/Microsoft/Intune/MDM
    "Microsoft Intune": "Endpoint/MDM",
    "MDM": "Endpoint/MDM",
    "Workspace ONE": "Endpoint/MDM",
    "Active Directory": "Identidade/AD",
    "Hybrid Azure AD Join": "Identidade/AD",

    # Serviços/Aplicações de Negócio
    "ERP": "Aplicações de Negócio",
    "Customer Relationship Management": "Aplicações de Negócio",
    "Microsoft Exchange": "Infra/Mensageria",
    "Microsoft Exchange Online": "Infra/Mensageria",
    "Sistema SAP": "Aplicações de Negócio",
    "SAP S/4HANA": "Aplicações de Negócio",
    "Sistemas de Gestão de Recursos Humanos": "Aplicações de Negócio",
    "Order Management System": "Aplicações de Negócio",
    "WMS": "Aplicações de Negócio",
    "Adobe Workfront": "Gestão/Projetos",
    "ServiceNow": "ITSM",
    "ServiceNow GRC": "GRC",
    "RSA Archer": "GRC",
    "MetricStream": "GRC",

    # Privacidade/Regulação/Leis
    "Marco Civil da Internet": "Compliance/Leis",
    "Lei Sarbanes-Oxley": "Compliance/Leis",
    "Termo de Uso de Dados": "Compliance/Privacidade",

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
    "Automação de Teste": "Qualidade/Testes",
    "Teste Unitário": "Qualidade/Testes",
    "Teste de Unidade": "Qualidade/Testes",
    "Teste de Caixa-Branca": "Qualidade/Testes",
    "Teste de Caixa-Preta": "Qualidade/Testes",
    "Teste de Integração": "Qualidade/Testes",
    "Relatório Técnico": "Qualidade/Documentação",

    # Ferramentas/Outros
    "Google Web Designer": "Ferramentas",
    "ManageEngine": "Ferramentas",
    "GLPi": "Ferramentas/ITSM",
    "Microsoft SCCM": "Ferramentas/Endpoint",
    "TeamViewer": "Infra/Acesso Remoto",
    "AnyDesk": "Infra/Acesso Remoto",
    "gcloud CLI": "Cloud/GCP",
    "Google Forms": "Produtividade/Formulários",

    # Conceitos diversos
    "Aplicação Web": "Conceitos/Aplicações",
    "Aplicação Mobile": "Conceitos/Aplicações",
    "Aplicação Desktop": "Conceitos/Aplicações",
    "Controle de Versão de Software": "Conceitos/Dev",
    "Versionamento": "Conceitos/Dev",
    "Visualização de Dados": "Conceitos/Dados",
    "Formatação de Computadores": "Conceitos/Suporte",
    "Frameworks de Persistência": "Conceitos/Desenvolvimento",
    "Segurança de Rede": "Conceitos/Segurança",
    "Segurança Perimetral": "Conceitos/Segurança",
    "Gestão de Incidentes": "Conceitos/ITSM",
    "Suporte Remoto": "Conceitos/Suporte",
    "Serviços de Integração": "Conceitos/Integração",
    "Processamento em Lote": "Conceitos/Dados",
    "Requisições Web": "Conceitos/Web",
    "Busca Semântica": "Conceitos/IA",
    "Lógica de Programação": "Conceitos/Programação",
    "Mapeamento de Dados": "Conceitos/Dados",
    "Mapeamento de Unidade de Rede": "Conceitos/Rede",
    "Mapeamento de Processos": "Conceitos/Processos",
    "Máscara de Rede": "Conceitos/Rede",
    "Programação Orientada a Objetos": "Arquitetura/Práticas",
    "Java EE": "Backend/Plataforma",
    "Modelo OSI": "Redes/Conceitos",
    "Lean IT": "Governança/Melhoria Contínua",
    "Hybrid Azure AD Join": "Identidade/AD",
    "Policy": "Governança/Políticas",
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

# Mapeia uma habilidade normalizada para sua categoria (a partir do dicionário criado acima)
DEFAULT_CATEGORIA = "Outros"

def obter_categoria(habilidade_normalizada: str) -> str:
    return CATEGORIA_POR_HABILIDADE.get(habilidade_normalizada, DEFAULT_CATEGORIA)

# Mapeia uma habilidade normalizada para sua categoria (a partir do dicionário criado acima)
DEFAULT_CATEGORIA = "Outros"

def obter_categoria(habilidade_normalizada: str) -> str:
    return CATEGORIA_POR_HABILIDADE.get(habilidade_normalizada, DEFAULT_CATEGORIA)

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
def extrair_habilidades_descricao(descricao: str, session: Session | None = None) -> List[str]:
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
                        normalizar_habilidade(h, session=session) for h in data["habilidades"]
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

        # Deduplica e filtra habilidades extraídas
        for hab in habilidades_extraidas:
            chave = deduplicar(hab)
            # ignora marcas, periféricos e palavras genéricas
            if chave not in vistos:
                vistos.add(chave)
                finais.append(hab)
        return finais
    
    # Em caso de erro, retorna lista vazia
    except Exception as exc:
        return []
