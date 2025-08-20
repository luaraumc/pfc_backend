from fastapi import APIRouter

authRouter = APIRouter(prefix="/auth", tags=["auth"])

@authRouter.post("/login")
def login():
    return {"message": "Login"}

@authRouter.post("/register")
def register():
    return {"message": "Register"}
