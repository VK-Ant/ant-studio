"""
Ant Studio — Main Application
Build. Run. Trust.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.api.websocket import ws_router
from backend.nodes.register import register_all_nodes
from backend.config import settings

logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("antstudio")

app = FastAPI(
    title="Ant Studio",
    description="Build. Run. Trust. — Local-first visual AI pipeline builder.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    count = register_all_nodes()
    logger.info(f"Ant Studio v0.1.0 ready — {count} nodes registered")

app.include_router(router, prefix="/api")
app.include_router(ws_router)
