from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from forge.api.routes import agents, events, experiments, nodes, replay, semantic
from forge.configs.settings import settings
from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.processor import SemanticProcessor
from forge.semantic.summary import SummaryGenerator

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize semantic logging if database URL is configured
if hasattr(settings, 'database_url') and settings.database_url:
    try:
        _db = PostgresDB(settings.database_url)
        _engine = EmbeddingEngine()
        _processor = SemanticProcessor(_engine, _db)
        _summary_gen = SummaryGenerator(_db, _engine)
        semantic.init_semantic(_db, _processor, _summary_gen)
    except Exception:
        # If database initialization fails, semantic endpoints will return 503
        pass

app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["nodes"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(replay.router, prefix="/api/v1/replay", tags=["replay"])
app.include_router(agents.router, prefix="/api/v1/experiments", tags=["agents"])
app.include_router(semantic.router, tags=["semantic"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
