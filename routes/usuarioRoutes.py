from fastapi import FastAPI, HTTPException
from curso import Usuario, listar_usuarios, buscar_usuario_por_id, criar_usuario, atualizar_usuario, deletar_usuario

app = FastAPI()

@app.get("/usuario")
def get_usuarios():
    return listar_usuarios()

@app.get("/usuario/{usuario_id}")
def get_usuario(usuario_id: int):
    usuario = buscar_usuario_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

@app.post("/usuario")
def post_usuario(usuario: Usuario):
    usuario_id = criar_usuario(usuario.id, usuario.nome, usuario.email, usuario.senha, usuario.criado_em, usuario.atualizado_em)
    return {"id": usuario_id}

@app.put("/usuario/{usuario_id}")
def put_usuario(usuario_id: int, usuario: Usuario):
    atualizar_usuario(usuario_id, usuario.nome, usuario.email, usuario.senha, usuario.atualizado_em)
    return {"status": "atualizado"}

@app.delete("/usuario/{usuario_id}")
def delete_usuario(usuario_id: int):
    deletar_usuario(usuario_id)
    return {"status": "deletado"}
