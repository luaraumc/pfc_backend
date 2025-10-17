"""seed habilidades a partir do dicionario CATEGORIA_POR_HABILIDADE

Revision ID: 018_seed_habilidades_from_const
Revises: 017_seed_categorias
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018_seed_habilidades_from_const'
down_revision = '017_seed_categorias'
branch_labels = None
depends_on = None


# Snapshot do dicionário CATEGORIA_POR_HABILIDADE em tempo de migração
HABILIDADE_PARA_CATEGORIA = {
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
}

def upgrade() -> None:
    conn = op.get_bind()

    # Pré-carregar mapa nome_categoria -> id
    categorias = conn.execute(sa.text("SELECT id, nome FROM categoria")).fetchall()
    nome_to_id = {row[1]: row[0] for row in categorias}

    insert_stmt = sa.text(
        """
        INSERT INTO habilidade (nome, categoria_id)
        VALUES (:nome, :categoria_id)
        ON CONFLICT (nome) DO NOTHING
        """
    )

    # Inserir cada habilidade usando o categoria_id pelo nome
    for habilidade, nome_categoria in HABILIDADE_PARA_CATEGORIA.items():
        categoria_id = nome_to_id.get(nome_categoria)
        if categoria_id is None:
            # se a categoria não existir (diferença de acento/capitalização), tenta case-insensitive
            res = conn.execute(
                sa.text("SELECT id FROM categoria WHERE lower(nome) = lower(:nome)"),
                {"nome": nome_categoria},
            ).fetchone()
            categoria_id = res[0] if res else None

        if categoria_id is not None:
            conn.execute(insert_stmt, {"nome": habilidade, "categoria_id": categoria_id})


def downgrade() -> None:
    conn = op.get_bind()
    # Remove apenas as habilidades que não estão relacionadas em tabelas de junção
    delete_stmt = sa.text(
        """
        DELETE FROM habilidade h
        WHERE h.nome = :nome
          AND NOT EXISTS (SELECT 1 FROM carreira_habilidade ch WHERE ch.habilidade_id = h.id)
          AND NOT EXISTS (SELECT 1 FROM conhecimento_habilidade kh WHERE kh.habilidade_id = h.id)
          AND NOT EXISTS (SELECT 1 FROM usuario_habilidade uh WHERE uh.habilidade_id = h.id)
          AND NOT EXISTS (SELECT 1 FROM vaga_habilidade vh WHERE vh.habilidade_id = h.id)
        """
    )
    for habilidade in HABILIDADE_PARA_CATEGORIA.keys():
        conn.execute(delete_stmt, {"nome": habilidade})
