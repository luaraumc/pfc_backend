# Sistema de Apoio à Decisão para Escolha de Carreira em Tecnologia

![Badge de Python](https://img.shields.io/badge/Python-3670A0?style=flat&logo=python&logoColor=white)
![Badge de FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Badge de React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Badge de Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white)
![Badge de PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)

---

## 🔗 Repositórios Originais
Este repositório é uma cópia do projeto original desenvolvido em colaboração:  
- [Frontend Original](https://github.com/luaraumc/pfc_frontend.git)  
- [Backend Original](https://github.com/luaraumc/pfc_backend.git)

---

## 🎯 Objetivo do Projeto
Desenvolver um **sistema web responsivo** para auxiliar estudantes e ingressantes na área de Tecnologia na escolha de cursos de bacharelado, baseado nas Diretrizes Curriculares Nacionais, e fornecer **orientações personalizadas de profissionalização** de acordo com os requisitos das vagas mais recentes do mercado de trabalho brasileiro.  

O sistema integra a **OpenAI API** para extração automatizada de competências e qualificações das descrições de vagas e fornece **feedback automatizado personalizado** com base no perfil de habilidades e carreira escolhida pelo usuário.

---

## 🛠 Tecnologias Utilizadas

### Banco de Dados
- **PostgreSQL**: banco relacional robusto, com suporte a transações e integridade referencial.  
- **SQLAlchemy**: ORM para abstração das operações no backend Python.

### Frontend
- **React.js**: construção da interface do usuário (SPA).  
- **React Router**: navegação entre páginas.  
- **Axios**: consumo de APIs.  
- **Tailwind CSS**: estilização moderna e responsiva.

### Backend
- **Python com FastAPI**: criação de API REST, suporte a rotinas assíncronas (`async/await`).  
- Middleware para:  
  - Autenticação JWT  
  - Tratamento de erros  
  - Validação de entrada

### API Externa
- **OpenAI API**: extração automatizada de habilidades e sumarização de requisitos das vagas.  

### Arquitetura
- **Camadas**: separação entre apresentação (frontend), lógica de negócio (backend) e persistência (PostgreSQL).  
- **Comunicação**: REST API entre frontend e backend.  
- **Hospedagem**:  
  - Frontend: Vercel  
  - Backend: Railway  
  - Banco de Dados: PostgreSQL na nuvem (Supabase)  

---

## ⚙️ Funcionalidades Principais
- CRUD de usuário, cursos e carreiras  
- Upload e ingestão de vagas  
- Extração automática de habilidades das vagas via API de IA  
- Gerenciamento do progresso do usuário  
- Mapeamento habilidades genéricas ↔ habilidades específicas  
- Mapeamento cursos ↔ carreiras  
- Recomendações e feedback automático de compatibilidade com carreiras

---

## 🤝 Contribuição

Projeto em desenvolvimento por **Elisa Mostafa** e **Luara Meissner**.  
Este repositório é mantido como **cópia do projeto original**
