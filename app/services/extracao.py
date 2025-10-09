from dotenv import load_dotenv
import os
from typing import List
from openai import OpenAI
import json, re, unicodedata
from app.models import Habilidade, CarreiraHabilidade

load_dotenv()

PROMPT_BASE = """
Extraia somente uma lista de habilidades (competências técnicas ou soft skills claras) do texto de descrição de vaga abaixo.
Responda apenas JSON válido no formato: {"habilidades": ["habilidade1", "habilidade2", ...]}
- Não invente habilidades que não estejam mencionadas.
- Use nomes curtos padronizados (ex: Java, Python, SQL, Git, Docker, Comunicação, Trabalho em equipe, Resolução de problemas).
- Não inclua níveis (júnior, pleno), nem anos de experiência, nem versões (ex: 'Java 17' => 'Java').
TEXTO:
"""

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

PADROES_COMPILADOS = [(re.compile(p, re.IGNORECASE), v) for p, v in PADROES.items()]


def normalizar_habilidade(habilidade: str) -> str:
    habilidade = habilidade.strip()
    habilidade = re.sub(r'\s+', ' ', habilidade)[:60]
    nfkd = unicodedata.normalize('NFKD', habilidade)
    habilidade = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala)(\d{1,3}(?:\.\d+)*)\b', r'\1', habilidade)
    habilidade = re.sub(r'\b(python|node|java|go|ruby|php|rust|scala)[ \-]+\d+(?:\.\d+){0,2}\b', r'\1', habilidade)
    habilidade = re.sub(r'\b(c\+\+|c#)[ \-]*\d{1,2}\b', r'\1', habilidade)
    habilidade = re.sub(r'\b(dotnet|\.net)[ \-]*\d+(?:\.\d+){0,2}\b', r'dotnet', habilidade)
    habilidade = habilidade.strip(' .;,-')

    for regex, valor in PADROES_COMPILADOS:
        if regex.fullmatch(habilidade):
            return valor

    if len(habilidade.split()) <= 3 and not re.search(r'[A-Z]{2,}', habilidade):
        habilidade = ' '.join(p.capitalize() for p in habilidade.split())

    return habilidade


def padronizar_descricao(descricao: str) -> str:
    descricao = unicodedata.normalize('NFD', descricao)
    descricao = descricao.encode('ascii', 'ignore').decode('utf-8')
    descricao = descricao.lower()
    descricao = re.sub(r'[^a-z0-9\s]', '', descricao)
    descricao = re.sub(r'\s+', ' ', descricao).strip()
    return descricao


def deduplicar(hab: str) -> str:
    hab = hab.strip().lower()
    hab = unicodedata.normalize('NFD', hab)
    hab = ''.join(c for c in hab if not unicodedata.combining(c))
    hab = re.sub(r'[^a-z0-9]', '', hab)
    return hab


def extrair_habilidades_descricao(descricao: str) -> List[str]:
    cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = PROMPT_BASE + descricao
    try:
        resposta = cliente.responses.create(
            model="gpt-4.1",
            input=prompt,
            temperature=0.15,
            max_output_tokens=500
        )

        texto_completo = ""
        if hasattr(resposta, "output_text") and resposta.output_text:
            texto_completo = resposta.output_text.strip()
        else:
            blocos_puros = []
            blocos = getattr(resposta, "output", []) or []
            for bloco in blocos:
                if getattr(bloco, "type", None) == "output_text":
                    blocos_puros.append(getattr(bloco, "text", "").strip())
            texto_completo = "\n".join(t for t in blocos_puros if t).strip()

        habilidades_extraidas: List[str] = []

        def tentar_json(segmento: str):
            nonlocal habilidades_extraidas
            try:
                data = json.loads(segmento)
                if isinstance(data, dict) and isinstance(data.get("habilidades"), list):
                    habilidades_extraidas = [
                        normalizar_habilidade(h) for h in data["habilidades"]
                    ]
            except json.JSONDecodeError:
                pass

        if texto_completo:
            tentar_json(texto_completo)

        if not habilidades_extraidas:
            achado = re.search(r'\{.*"habilidades"\s*:\s*\[.*?\]\s*\}', texto_completo, re.DOTALL)
            if achado:
                tentar_json(achado.group(0))

        finais: List[str] = []
        vistos = set()
        for hab in habilidades_extraidas:
            chave = deduplicar(hab)
            if chave not in vistos:
                vistos.add(chave)
                finais.append(hab)

        return finais
    except Exception as exc:
        return []


