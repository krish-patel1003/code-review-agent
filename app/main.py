from fastapi import FastAPI
from app.api.endpoints import router
from app.db.database import init_db

app = FastAPI(title="Code Review Agent", version="1.0.0")

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Code Review Agent"}

# Initialize database
@app.on_event("startup")
async def startup_event():
    await init_db()