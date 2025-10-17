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

# Padrões para normalização de habilidades
PADROES = {
    r"^activemq$": "Apache ActiveMQ",
    r"^active directory$": "Active Directory",
    r"^ad$": "Active Directory",
    r"^adfs$": "ADFS",
    r"^aiohttp$": "AIOHTTP",
    r"^ai$": "Inteligência Artificial",
    r"^alloydb$": "AlloyDB",
    r"^analise de riscos$": "Análise De Riscos",
    r"^angular cli$": "Angular CLI",
    r"^angular(js)?$": "Angular",
    r"^anydesk$": "AnyDesk",
    r"^api$": "API",
    r"^api rest$": "REST",
    r"^aplicacao desktop$": "Aplicação Desktop",
    r"^aplicacao mobile$": "Aplicação Mobile",
    r"^aplicacao web$": "Aplicação Web",
    r"^aprendizado de maquina$": "Machine Learning",
    r"^arquitetura de sistema$": "Arquitetura de Sistemas",
    r"^arquitetura de sistemas$": "Arquitetura de Sistemas",
    r"^arquitetura distribuida$": "Arquitetura Distribuída",
    r"^arvore de decisao$": "Árvore de Decisão",
    r"^asp classico$": "ASP Clássico",
    r"^asp\.net$": "ASP.NET",
    r"^aws$": "AWS",
    r"^aws firewall$": "AWS Firewall",
    r"^aws iam$": "AWS IAM",
    r"^aws shield$": "AWS Shield",
    r"^aws sqs$": "AWS SQS",
    r"^aws waf$": "AWS WAF",
    r"^azure$": "Azure",
    r"^azure ad$": "Azure AD",
    r"^azure ad connect$": "Azure AD Connect",
    r"^azure ai search$": "Azure AI Search",
    r"^azure devop$": "Azure DevOps",
    r"^azure openai$": "Azure OpenAI",
    r"^backend$": "Back-End",
    r"^balanceador de carga$": "Balanceador de Carga",
    r"^banco de dados$": "Banco de Dados",
    r"^banco de dados naorelacional$": "Banco de Dados Não Relacional",
    r"^banco de dados nao relacional$": "Banco de Dados Não Relacional",
    r"^banco de dados relacional$": "Banco de Dados Relacional",
    r"^Banco De Dados Nosql$": "NoSQL",
    r"^Banco De Dados sql$": "SQL",
    r"^bert$": "BERT",
    r"^bgp$": "BGP",
    r"^bsimm$": "BSIMM",
    r"^bi$": "PowerBI",
    r"^brute force$": "Brute Force",
    r"^bsimm$": "BSIMM",
    r"^burp$": "Burp Suite",
    r"^burp suite$": "Burp Suite",
    r"^burpsuite$": "Burp Suite",
    r"^busca semantica$": "Busca Semântica",
    r"^casb$": "CASB",
    r"^cdi$": "CDI",
    r"^ciberseguranca$": "Cibersegurança",
    r"^circuito de dados$": "Circuito de Dados",
    r"^cis$": "CIS Controls",
    r"^cisco$": "Cisco",
    r"^classificacao da informacao$": "Classificação da Informação",
    r"^cloud$": "Cloud Computing",
    r"^cloudbees$": "Cloudbees",
    r"^cobit$": "Cobit",
    r"^container$": "Container",
    r"^context api$": "Context API",
    r"^computacao em nuvem$": "Cloud Computing",
    r"^crm$": "Customer Relationship Management",
    r"^crowdstrike$": "CrowdStrike",
    r"^css$": "CSS",
    r"^css3$": "CSS",
    r"^cyberark$": "CyberArk",
    r"^cyberseguranca$": "Cibersegurança",
    r"^cybersecurity$": "Cibersegurança",
    r"^cybersecurity$": "Cibersegurança",
    r"^dast$": "DAST",
    r"^database migration service$": "AWS DMS",
    r"^db2$": "IBM Db2",
    r"^ddd$": "Domain-Driven Design",
    r"^ddns$": "DDNS",
    r"^defender for endpoint$": "Microsoft Defender for Endpoint",
    r"^devops$": "DevOps",
    r"^devsecops$": "DevSecOps",
    r"^dhcp$": "DHCP",
    r"^dkim$": "DKIM",
    r"^dmarc$": "DMARC",
    r"^dms$": "Document Management System",
    r"^docker$": "Docker",
    r"^dns$": "DNS",
    r"^documentdb$": "Amazon DocumentDB",
    r"^dotnet$": ".NET",
    r"^doubleclick studio$": "Google Web Designer",
    r"^dwdm$": "DWDM",
    r"^dynamodb$": "Amazon DynamoDB",
    r"^ec2$": "Amazon EC2",
    r"^ecmascript$": "ECMAScript",
    r"^eclipse$": "Eclipse IDE",
    r"^ecr$": "Amazon ECR",
    r"^edr$": "Endpoint Detection and Response",
    r"^ejb$": "Enterprise JavaBeans",
    r"^eks$": "Amazon EKS",
    r"^elasticsearch$": "Elasticsearch",
    r"^elt$": "ELT",
    r"^endpoint protection$": "Endpoint Security",
    r"^enfileiramento de mensagens$": "Enfileiramento de Mensagens",
    r"^equipamento de rede$": "Equipamentos de Rede",
    r"^erp$": "ERP",
    r"^es6$": "ECMAScript",
    r"^estatistica$": "Estatística",
    r"^etl$": "ETL",
    r"^exchange$": "Microsoft Exchange",
    r"^exchange online$": "Microsoft Exchange Online",
    r"^express$": "Express.js",
    r"^faiss$": "FAISS",
    r"^fastapi$": "FastAPI",
    r"^ferramenta de bi$": "PowerBI",
    r"^ferramenta de controle de versao$": "Controle de Versão de Software",
    r"^ferramenta de etl$": "ETL",
    r"^ferramenta de gestao de vulnerabilidade$": "Gestão de Vulnerabilidades",
    r"^ferramenta de ia$": "IA",
    r"^ferramenta de incidente$": "Gestão de Incidentes",
    r"^ferramenta de suporte remoto$": "Suporte Remoto",
    r"^ferramenta de teste$": "Automação de Teste",
    r"^ferramenta de versionamento$": "Versionamento",
    r"^ferramenta de visualizacao de dados$": "Visualização de Dados",
    r"^fibra optica$": "Fibra Óptica",
    r"^finetuning$": "Fine-tuning",
    r"^forca bruta$": "Brute Force",
    r"^forcabruta$": "Brute Force",
    r"^formatação de computadores$": "Formatação de Computadores",
    r"^formatacao de computador$": "Formatação de Computadores",
    r"^framework de persistencia$": "Frameworks de Persistência",
    r"^framework de seguranca da informacao$": "Segurança da Informação",
    r"^framework javascript$": "JavaScript",
    r"^frameworks de persistencia$": "Frameworks de Persistência",
    r"^frontend$": "Front-End",
    r"^ftp$": "FTP",
    r"^gcp$": "Google Cloud Platform",
    r"^gcs$": "Google Cloud Storage",
    r"^gdpr$": "Regulamento Geral sobre a Proteção de Dados",
    r"^gestao de acesso$": "Gestão de Acesso",
    r"^gestao de acessos$": "Gestão de Acesso",
    r"^gestao de ativos de ti$": "Gestão de Ativos de TI",
    r"^gestao de mudancas$": "Gestão de Mudanças",
    r"^gestao de riscos$": "Gestão de Riscos",
    r"^git$": "Git",
    r"^gitlab$": "GitLab",
    r"^glpi$": "GLPi",
    r"^go$": "GO",
    r"^golang$": "GO",
    r"^google cli$": "gcloud CLI",
    r"^google cloud cli$": "gcloud CLI",
    r"^google forms$": "Google Forms",
    r"^governanca de dados$": "Governança de Dados",
    r"^gpo$": "Group Policy Objects",
    r"^gpon$": "GPON",
    r"^graphql$": "GraphQL",
    r"^hadoop$": "Apache Hadoop",
    r"^hrms$": "Sistemas de Gestão de Recursos Humanos",
    r"^hrsd$": "Sistemas de Gestão de Recursos Humanos",
    r"^hsrp$": "HSRP",
    r"^html$": "HTML",
    r"^html5$": "HTML",
    r"^hybrid ad$": "Hybrid Azure AD Join",
    r"^hydra$": "Hydra Launcher",
    r"^hyper-v$": "Hyper-V",
    r"^ia$": "Inteligência Artificial",
    r"^ia generativa$": "IA Generativa",
    r"^iac$": "Infraestrutura como Código",
    r"^iis$": "Microsoft IIS",
    r"^imap$": "IMAP",
    r"^infrastructure as code$": "Infraestrutura como Código",
    r"^injeção de dependencia$": "Injeção de Dependência",
    r"^insightidr$": "InsightIDR",
    r"^intellij$": "Intellij IDEA",
    r"^intellij idea$": "Intellij IDEA",
    r"^intune$": "Microsoft Intune",
    r"^ios$": "IOS",
    r"^ip$": "IP Address",
    r"^ipsec$": "IPsec",
    r"^ips$": "Intrusion Prevention System",
    r"^iptables$": "iptables",
    r"^is-is$": "Intermediate System to Intermediate System",
    r"^isis$": "Intermediate System to Intermediate System",
    r"^iso$": "ISO",
    r"^iso 27000$": "ISO 27000",
    r"^iso 27001$": "ISO 27001",
    r"^iso 27002$": "ISO 27002",
    r"^iso 27701$": "ISO 27701",
    r"^iso/iec 27701$": "ISO 27701",
    r"^itil$": "ITIL",
    r"^itom$": "ITOM",
    r"^itsm$": "ITSM",
    r"^java ee$": "Java EE",
    r"^javascript$": "JavaScript",
    r"^javascript es6$": "JavaScript",
    r"^jd edwards$": "JD Edwards",
    r"^jmeter$": "Apache JMeter",
    r"^jpa$": "JPA",
    r"^json$": "JSON",
    r"^jsp$": "JavaServer Pages",
    r"^js$": "JavaScript",
    r"^juniper$": "Juniper Networks",
    r"^junit$": "JUnit",
    r"^jwt$": "JSON Web Token",
    r"^k8s$": "Kubernetes",
    r"^kafka$": "Apache Kafka",
    r"^kali$": "Kali Linux",
    r"^kmeans$": "k-means",
    r"^kpi$": "KPI",
    r"^l2vpn$": "L2VPN",
    r"^lacp$": "LACP",
    r"^lan$": "LAN",
    r"^langgraph$": "LangGraph",
    r"^layer 1$": "Modelo OSI",
    r"^layer 2$": "Modelo OSI",
    r"^layer 3$": "Modelo OSI",
    r"^layer 4$": "Modelo OSI",
    r"^layer 5$": "Modelo OSI",
    r"^layer 6$": "Modelo OSI",
    r"^layer 7$": "Modelo OSI",
    r"^lean it$": "Lean IT",
    r"^lei 137092018$": "Lei Geral de Proteção de Dados Pessoais",
    r"^lei geral de protecao de dados pessoais$": "Lei Geral de Proteção de Dados Pessoais",
    r"^less$": "LeSS",
    r"^lgpd$": "Lei Geral de Proteção de Dados Pessoais",
    r"^linter$": "Linter",
    r"^lint$": "Linter",
    r"^lists$": "Microsoft Lists",
    r"^litedb$": "LiteDB",
    r"^llamaindex$": "LlamaIndex",
    r"^llm$": "LLM",
    r"^logica de programacao$": "Lógica de Programação",
    r"^looker$": "Looker Studio",
    r"^looker studio$": "Looker Studio",
    r"^loop$": "Microsoft Loop",
    r"^macos$": "MacOS",
    r"^manageengine$": "ManageEngine",
    r"^mapeamento de dados$": "Mapeamento de Dados",
    r"^mapeamento de pastas$": "Mapeamento de Unidade de Rede",
    r"^mapeamento de tipos$": "Mapeamento de Processos",
    r"^mapeamento de unidade de rede$": "Mapeamento de Unidade de Rede",
    r"^marco civil da internet$": "Marco Civil da Internet",
    r"^mascara de rede$": "Máscara de Rede",
    r"^mascaramento de dados$": "Mascaramento de Dados",
    r"^material-ui$": "Material UI",
    r"^material ui$": "Material UI",
    r"^matriz de risco corporativa$": "Gestão de Riscos",
    r"^maven$": "Apache Maven",
    r"^mcp$": "MCP",
    r"^mcp model context protocol$": "MCP",
    r"^mdm$": "MDM",
    r"^meraki$": "Cisco Meraki",
    r"^metricstream$": "MetricStream",
    r"^microservico$": "Microsserviços",
    r"^microsservicos$": "Microsserviços",
    r"^microsoft 365$": "Microsoft 365",
    r"^microsoft ad$": "Active Directory",
    r"^microsoft office$": "Microsoft 365",
    r"^microsoft sdl$": "Microsoft SDL",
    r"^mikrotik$": "Mikrotik",
    r"^mitre att&ck$": "MITRE ATT&CK",
    r"^mitre attck$": "MITRE ATT&CK",
    r"^modelagem$": "Modelagem de Dados",
    r"^modelagem de ameaca$": "Modelagem de Ameaças",
    r"^modelo de dados$": "Modelagem de Dados",
    r"^modelo generativo$": "IA Generativa",
    r"^mongo(db)?$": "MongoDB",
    r"^mongoose$": "MongoDB",
    r"^monitoracao de dispositivos de rede$": "Monitoramento de Rede",
    r"^monitoramento$": "Monitoramento de Rede",
    r"^mpls$": "MPLS",
    r"^mq$": "Enfileiramento de Mensagens",
    r"^msft project$": "Microsoft Project",
    r"^msk$": "Amazon MSK",
    r"^ms project$": "Microsoft Project",
    r"^ms purview$": "Microsoft Purview",
    r"^mssql$": "SQL Server",
    r"^mysql$": "MySQL",
    r"^nac$": "Network Access Control",
    r"^nagios$": "Nagios",
    r"^nestjs$": "NestJS",
    r"^net$": ".NET",
    r"^net 6$": ".NET",
    r"^node ?js$": "Node.js",
    r"^node(js)?$": "Node.js",
    r"^no ?sql$": "NoSQL",
    r"^office$": "Microsoft 365",
    r"^ospf$": "OSPF",
    r"^pacote office$": "Microsoft 365",
    r"^postgres(q|ql)?$": "PostgreSQL",
    r"^postgre(sql)?$": "PostgreSQL",
    r"^powerbi$": "Power BI",
    r"^power bi$": "Power BI",
    r"^prtg$": "Paessler PRTG",
    r"^purview$": "Microsoft Purview",
    r"^python 3$": "Python",
    r"^python\d*$": "Python",
    r"^py$": "Python",
    r"^qos$": "QoS",
    r"^react(\.js)?$": "React",
    r"^reactjs$": "React",
    r"^regulamento geral sobre a protecao de dados$": "Regulamento Geral sobre a Proteção de Dados",
    r"^rest$": "REST",
    r"^roteamento$": "Roteamento",
    r"^roteador$": "Roteamento",
    r"^sistemas de gestao de recursos humanos$": "Sistemas de Gestão de Recursos Humanos",
    r"^sql$": "SQL",
    r"^sql server$": "SQL Server",
    r"^suporte remoto$": "Suporte Remoto",
    r"^tcp/?ip$": "TCP/IP",
    r"^ts$": "TypeScript",
    r"^typescript$": "TypeScript",
    r"^vlan$": "VLAN",
    r"^vue(\.js)?$": "Vue.js",
    r"^vpn$": "VPN",
    r"^zabbix$": "Zabbix",
    r"^airflow$": "Apache Airflow",
    r"^apache airflow$": "Apache Airflow",
    r"^athena$": "Amazon Athena",
    r"^amazon athena$": "Amazon Athena",
    r"^azure devops$": "Azure DevOps",
    r"^amazon cloudwatch$": "Amazon CloudWatch",
    r"^cloudwatch$": "Amazon CloudWatch",
    r"^cte$": "Common Table Expression",
    r"^dataops$": "DataOps",
    r"^amazon eventbridge$": "Amazon EventBridge",
    r"^eventbridge$": "Amazon EventBridge",
    r"^gitlab ci/cd$": "GitLab CI/CD",
    r"^gitlab ci$": "GitLab CI/CD",
    r"^aws glue$": "AWS Glue",
    r"^glue$": "AWS Glue",
    r"^great expectations( library)?$": "Great Expectations",
    r"^infrastructure as code$": "Infraestrutura como Código",
    r"^s3$": "AWS",
    r"^aws s3$": "AWS",
    r"^logging estruturado$": "Registro Estruturado",
    r"^modelagem de dados dimensional$": "Modelagem Dimensional",
    r"^nexus$": "Azure Operator Nexus",
    r"^nginx$": "NGINX",
    r"^ngrx$": "NgRx",
    r"^nifi$": "Apache NiFi",
    r"^nist$": "NIST",
    r"^nist csf$": "NIST",
    r"^nist cybersecurity framework$": "NIST",
    r"^nist privacy framework$": "NIST",
    r"^nist sp 800$": "NIST",
    r"^nlp$": "Processamento de Linguagem Natural",
    r"^noc$": "NOC",
    r"^norma iso 27001$": "ISO 27001",
    r"^nornir$": "Nornir Python",
    r"^nosql$": "NoSQL",
    r"^nuvem$": "Cloud Computing",
    r"^oauth 2\.0$": "OAuth 2.0",
    r"^oauth2$": "OAuth 2.0",
    r"^octane$": "ALM Octane",
    r"^oidc$": "OIDC",
    r"^olt$": "Terminal de Linha Óptica",
    r"^oms$": "Order Management System",
    r"^onedrive$": "Microsoft OneDrive",
    r"^onetrust$": "OneTrust",
    r"^ont$": "Terminal de Rede Óptica",
    r"^openapi$": "OpenAPI",
    r"^openid$": "OpenID",
    r"^openid connect$": "OIDC",
    r"^opensamm$": "OpenSAMM",
    r"^openshift$": "OpenShift",
    r"^oracle db$": "Oracle DB",
    r"^oracle$": "Oracle DB",
    r"^programacao orientada a objetos$": "Programação Orientada a Objetos",
    r"^orientacao a objetos$": "Programação Orientada a Objetos",
    r"^otimizacao de consultas sql$": "Otimização de Consultas SQL",
    r"^otimizacao de query$": "Otimização de Consultas SQL",
    r"^otimizacao de consultas$": "Otimização de Consultas SQL",
    r"^microsoft outlook$": "Microsoft Outlook",
    r"^outlook$": "Microsoft Outlook",
    r"^owasp$": "OWASP",
    r"^owasp mobile security$": "OWASP",
    r"^owasp testing guide$": "OWASP",
    r"^owasp top 10$": "OWASP",
    r"^owasp zap$": "OWASP",
    r"^padrao de arquitetura$": "Arquitetura de Software",
    r"^padroes de arquitetura$": "Arquitetura de Software",
    r"^padroes arquiteturais$": "Arquitetura de Software",
    r"^pam$": "Privileged Access Management",
    r"^parrot$": "Parrot OS",
    r"^pci$": "Peripheral Component Interconnect",
    r"^pci dss$": "PCI DSS",
    r"^pfsense$": "pfSense",
    r"^pipeline$": "Pipeline de Dados",
    r"^pipeline de ci/cd$": "Pipeline de CI/CD",
    r"^pipeline ci/cd$": "Pipeline de CI/CD",
    r"^planner$": "Microsoft Planner",
    r"^pl/sql$": "PL/SQL",
    r"^plsql$": "PL/SQL",
    r"^pmbok$": "PMBOK",
    r"^pmi$": "Project Management Institute",
    r"^pod$": "Kubernetes",
    r"^policy as code$": "Política como Código",
    r"^policy$": "Política de Segurança de TI",
    r"^pon$": "Rede Óptica Passiva",
    r"^pop$": "Procedimentos Operacionais Padrão",
    r"^power apps$": "Microsoft Power Apps",
    r"^power automate$": "Microsoft Power Automate",
    r"^power platform$": "Microsoft Power Platform",
    r"^power bi$": "Power BI",
    r"^powerpoint$": "PowerPoint",
    r"^powershell$": "PowerShell",
    r"^pppoe$": "PPPoE",
    r"^prince2$": "PRINCE2",
    r"^procedure$": "SQL",
    r"^processamento em batch$": "Processamento em Lote",
    r"^programacao funcional$": "Programação Funcional",
    r"^project management institute$": "Gerenciamento de Projetos",
    r"^project$": "Gerenciamento de Projetos",
    r"^project server$": "Microsoft Project Server",
    r"^promise$": "JavaScript",
    r"^protecao de dados$": "Proteção de Dados",
    r"^protocolo 802\.11$": "IEEE 802.11",
    r"^protocolo 80211$": "IEEE 802.11",
    r"^protocolo de rede$": "Protocolos de Rede",
    r"^protocolos de rede$": "Protocolos de Rede",
    r"^protocolo de seguranca$": "Protocolos de Segurança",
    r"^protocolos de seguranca$": "Protocolos de Segurança",
    r"^prtg$": "Paessler PRTG",
    r"^pseudonimizacao$": "Pseudonimização",
    r"^pub/sub$": "Pub/Sub",
    r"^pull request$": "GitHub",
    r"^pyspark$": "PySpark",
    r"^qos$": "Quality of Service",
    r"^quota$": "Quota Management",
    r"^rabbitmq$": "RabbitMQ",
    r"^rapid7 insightvm$": "InsightVM",
    r"^rds$": "Remote Desktop Services",
    r"^rede$": "Redes",
    r"^switch$": "Redes",
    r"^switching$": "Redes",
    r"^redundancia$": "Redes",
    r"^redundancia de rede$": "Redes",
    r"^rede de computador$": "Redes",
    r"^rede ip$": "IP Address",
    r"^redux saga$": "Redux",
    r"^regressao linear$": "Regressão Linear",
    r"^regressao logistica$": "Regressão Logística",
    r"^relatorio tecnico$": "Relatório Técnico",
    r"^remote desktop$": "Remote Desktop Services",
    r"^requisicao web$": "Requisições Web",
    r"^resolucao n 192024$": "ANPD",
    r"^responsabilidade legal$": "Lei Geral de Proteção de Dados Pessoais",
    r"^rest$": "REST",
    r"^restful$": "REST",
    r"^restassured$": "REST Assured",
    r"^restore$": "backup",
    r"^rf$": "Radiofrequência",
    r"^rfid$": "Radiofrequência",
    r"^ropa$": "Registro de Operações de Tratamento de Dados Pessoais",
    r"^routing$": "Roteamento",
    r"^rsa archer$": "RSA Archer",
    r"^rxjs$": "RxJS",
    r"^s/4hana$": "SAP S/4HANA",
    r"^saas$": "SaaS",
    r"^safe$": "Scaled Agile Framework",
    r"^samba$": "Servidor de Arquivos Samba",
    r"^saml$": "SAML",
    r"^sap$": "Sistema SAP",
    r"^sap ecc$": "Sistema SAP",
    r"^sap s/4hana$": "Sistema SAP",
    r"^sas$": "Software de Análise Estatística",
    r"^sast$": "SAST",
    r"^sca$": "Análise de Composição de Software",
    r"^scanner de vulnerabilidade$": "Scanner de Vulnerabilidade",
    r"^sccm$": "Microsoft SCCM",
    r"^scikit-learn$": "Scikit-Learn",
    r"^scripting$": "Script",
    r"^sass$": "SASS",
    r"^scss$": "SASS",
    r"^sd-wan$": "SD-WAN",
    r"^sdk$": "SDK",
    r"^seguranca de rede$": "Segurança de Rede",
    r"^seguranca perimetral$": "Segurança Perimetral",
    r"^seo$": "Otimização para Mecanismos de Busca",
    r"^servicenow$": "ServiceNow",
    r"^servicenow grc$": "ServiceNow",
    r"^servico de integracao$": "Serviços de Integração",
    r"^servico em nuvem$": "Cloud Computing",
    r"^servidor de aplicacao$": "Servidor de Aplicação",
    r"^servidor de arquivos$": "Servidor de Arquivos",
    r"^sftp$": "SSH File Transfer Protocol",
    r"^sharepoint$": "Microsoft SharePoint",
    r"^siem$": "SIEM",
    r"^single sign-on$": "Single Sign-On",
    r"^sistema autonomo$": "Sistema Autônomo",
    r"^sistemas contabeis$": "Sistemas Contábeis",
    r"^sistema contabil$": "Sistemas Contábeis",
    r"^sistemas de chamados$": "Sistemas de Chamados",
    r"^sistema de chamado$": "Sistemas de Chamados",
    r"^sistemas de monitoramento$": "Sistemas de Monitoramento",
    r"^sistema de monitoramento$": "Sistemas de Monitoramento",
    r"^sistemas de telefonia$": "Sistemas de Telefonia",
    r"^sistema de telefonia$": "Sistemas de Telefonia",
    r"^sistema distribuido$": "Sistema Distribuído",
    r"^sli$": "SLI",
    r"^slo$": "SLO",
    r"^smtp$": "SMTP",
    r"^snmp$": "SNMP",
    r"^soa$": "Arquitetura Orientada a Serviços",
    r"^soap$": "Simple Object Access Protocol",
    r"^soc$": "Centro de Operações de Segurança",
    r"^solarwinds$": "SolarWinds",
    r"^sonarqube$": "SonarQube",
    r"^sophos$": "Sophos",
    r"^sox$": "Lei Sarbanes-Oxley",
    r"^spa$": "Single Page Applications",
    r"^spacy$": "SpaCy",
    r"^spanning tree$": "Spanning Tree Protocol",
    r"^stp$": "Spanning Tree Protocol",
    r"^spark$": "Apache Spark",
    r"^spf$": "Sender Policy Framework",
    r"^spring framework$": "Spring",
    r"^sqlmap$": "SQLMAP",
    r"^ssg$": "Geração de Sites Estáticos",
    r"^ssl$": "Secure Sockets Layer",
    r"^ssr$": "Server-Side Rendering",
    r"^storefront api$": "Storefront API",
    r"^stream$": "Microsoft Clipchamp",
    r"^susep 638$": "Lei Geral de Proteção de Dados Pessoais",
    r"^svn$": "Apache Subversion",
    r"^sway$": "Microsoft Sway",
    r"^tag helper$": "ASP.NET",
    r"^tailwind css$": "Tailwind",
    r"^teams$": "Microsoft Teams",
    r"^teamviewer$": "TeamViewer",
    r"^telefonia ip$": "Telefonia IP",
    r"^termo de uso de dados$": "Termo de Uso de Dados",
    r"^teste de caixa-branca$": "Teste de Caixa-Branca",
    r"^teste de caixa-preta$": "Teste de Caixa-Preta",
    r"^teste de integracao$": "Teste de Integração",
    r"^teste de invasao$": "Pentest",
    r"^tls$": "Transport Layer Security",
    r"^to do$": "Microsoft To Do",
    r"^togaf$": "TOGAF",
    r"^tomcat$": "Apache Tomcat",
    r"^topologia de rede$": "Topologia de Rede",
    r"^totvs$": "TOTVS",
    r"^trace$": "Rastreamento de Atividades",
    r"^tracing$": "Rastreamento de Atividades",
    r"^transceiver$": "Transceptor",
    r"^tratamento de dados$": "Tratamento de Dados",
    r"^unifi$": "UniFi",
    r"^unit test$": "Teste de Unidade",
    r"^unittest$": "Teste de Unidade",
    r"^url filtering$": "URL filtering",
    r"^vb$": "Visual Basic",
    r"^velocloud$": "VeloCloud",
    r"^virtualizacao$": "Virtualização",
    r"^vision one$": "Trend Micro Vision One",
    r"^vm$": "Máquina Virtual",
    r"^voip$": "VoIP",
    r"^vpc$": "Virtual Private Cloud",
    r"^vrf$": "Roteamento e Encaminhamento Virtual",
    r"^vscode$": "Virtual Studio Code",
    r"^waf$": "Web Application Firewall",
    r"^wide area network$": "Wide Area Network",
    r"^waterfall$": "Método Cascata",
    r"^cascata$": "Método Cascata",
    r"^webgl$": "WebGL",
    r"^webservice$": "Web Service",
    r"^websocket$": "WebSocket",
    r"^wifi$": "Redes",
    r"^wi-fi$": "Redes",
    r"^wildfly$": "WildFly",
    r"^windows 10$": "Windows",
    r"^windows 7$": "Windows",
    r"^windows 8$": "Windows",
    r"^windows 11$": "Windows",
    r"^wlan$": "Wireless Local Area Network",
    r"^wms$": "WMS",
    r"^workfront$": "Adobe Workfront",
    r"^workspace one$": "Workspace ONE",
    r"^xdr$": "XDR",
    r"^xgboost$": "XGBoost",
    r"^xml$": "XML",
    r"^yaml$": "YAML",
    r"^ztna$": "ZTNA",
    r"^visao Computacional$": "Visão Computacional",
    
}

# lista de tuplas a partir do dicionário PADROES
PADROES_COMPILADOS = [(re.compile(p, re.IGNORECASE), v) for p, v in PADROES.items()]

# Normaliza uma habilidade conforme os padrões definidos
def normalizar_habilidade(habilidade: str) -> str:
    habilidade = habilidade.strip() # remove espaços em branco nas extremidades
    habilidade = re.sub(r'\s+', ' ', habilidade)[:60] # reduz múltiplos espaços e limita tamanho
    nfkd = unicodedata.normalize('NFKD', habilidade) # normaliza acentuação
    habilidade = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower() # remove acentos e converte para minúsculas
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala|windows)(\d{1,3}(?:\.\d+)*)\b', r'\1', habilidade) # remove versões
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala|windows)[ \-]+\d+(?:\.\d+){0,2}\b', r'\1', habilidade) # remove versões com hífen/espaço
    habilidade = re.sub(r'\b(c\+\+|c#)[ \-]*\d{1,2}\b', r'\1', habilidade) # remove versões de C++ e C#
    habilidade = re.sub(r'\b(dotnet|\.net)[ \-]*\d+(?:\.\d+){0,2}\b', r'dotnet', habilidade) # remove versões de .NET
    habilidade = habilidade.strip(' .;,-') # remove caracteres indesejados nas extremidades

    # Aplica padrões de normalização
    for regex, valor in PADROES_COMPILADOS:
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
