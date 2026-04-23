import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import tokens, filters, ws
from app.config import settings

logging.basicConfig(level=settings.log_level)

app = FastAPI(title="mem-coin API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tokens.router)
app.include_router(filters.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
