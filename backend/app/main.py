from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.api.routes import router
from app.rag import vectorstore


@asynccontextmanager
async def lifespan(app: FastAPI):
    vectorstore.seed_knowledge_base_if_empty()
    yield


app = FastAPI(title="RFP Analysis & Response Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
