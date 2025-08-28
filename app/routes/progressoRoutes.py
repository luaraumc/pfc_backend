from fastapi import APIRouter

loginRouter = APIRouter(prefix="/progresso", tags=["progresso"])


@loginRouter.get("/")
async def progresso():
    # obter o progresso de cada carreira do usuário (habilidades que possui e habilidades faltantes)
    # somente usuarios autenticados, com token de acesso, terão acesso a essa funcionalidade
    return {"message": "Progresso"}
    # funcionalidade para exibir o progresso em porcentagem para cada carreira



@loginRouter.put("/")
async def atualizar_habilidades():
    # atualizar o progresso do usuário (habilidades que adquiriu recentemente)
    return {"message": "Habilidades Atualizadas"}

@loginRouter.post("/")
async def adicionar_habilidades():
    # adicionar habilidades do usuário (habilidades que adquiriu recentemente)
    return {"message": "Habilidades Adicionadas"}

@loginRouter.delete("/")
async def deletar_habilidades():
    # deletar habilidades do usuário (habilidades que não possui mais)
    return {"message": "Habilidades Deletadas"}
