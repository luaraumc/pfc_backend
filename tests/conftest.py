# Garante que o pacote "app" seja importável em qualquer rootdir do pytest
import sys
from pathlib import Path

tests_dir = Path(__file__).resolve().parent
candidatos = [
    tests_dir.parent,           # pfc_backend/
    tests_dir.parent / "src",   # pfc_backend/src (se usar layout src/)
    tests_dir.parent.parent,    # projeto raiz (fallback)
]

for base in candidatos:
    if (base / "app").exists():
        p = str(base)
        if p not in sys.path:
            sys.path.insert(0, p)
        break