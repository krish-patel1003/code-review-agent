from fastapi import FastAPI
from app.api.endpoints import router
from app.db.database import init_db

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Code Review Agent"}

# Initialize database
@app.on_event("startup")
def startup_event():
    init_db()