import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from forge.api.auth import verify_api_key
from forge.api.ratelimit import RateLimitMiddleware
from forge.api.routes import agents, events, experiments, nodes, replay, semantic, ws
from forge.configs.settings import settings
from forge.db.postgres import PostgresDB
from forge.experiments.models import HealthCheck, HealthComponent
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.insights import InsightsGenerator
from forge.semantic.processor import SemanticProcessor
from forge.semantic.scheduler import SemanticScheduler
from forge.semantic.summary import SummaryGenerator

logger = logging.getLogger(__name__)

_semantic_scheduler: SemanticScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _semantic_scheduler

    if not settings.api_key:
        logger.warning("SECURITY: No FORGE_API_KEY configured. Set one in .env for production.")
    if settings.debug:
        logger.warning("SECURITY: Running in DEBUG mode. CORS allows all origins and auth is disabled.")
    if not settings.database_url:
        logger.warning("DATA: No database_url configured. Semantic logging (pgvector) will be unavailable.")

    if hasattr(settings, 'database_url') and settings.database_url:
        try:
            _db = PostgresDB(settings.database_url)
            _engine = EmbeddingEngine()
            ollama_ok = await _engine.health_check()
            if ollama_ok:
                logger.info("Ollama embedding service: connected")
            else:
                logger.info("Ollama embedding service: unavailable — using bag-of-words fallback")
            _processor = SemanticProcessor(_engine, _db)
            _summary_gen = SummaryGenerator(_db, _engine)
            _insights_gen = InsightsGenerator(_db, _engine)
            semantic.init_semantic(_db, _processor, _summary_gen, _insights_gen)
            if ollama_ok:
                _semantic_scheduler = SemanticScheduler(_db, _engine)
                _semantic_scheduler.start()
        except Exception as e:
            logger.warning("Semantic logging initialization failed: %s", e, exc_info=True)
    yield
    if _semantic_scheduler:
        _semantic_scheduler.stop()


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Forge AI — Distributed system experimentation platform for chaos engineering, AI agent orchestration, and experiment observability.",
    lifespan=lifespan,
    docs_url="/docs",
    contact={
        "name": "Forge AI",
        "url": "https://github.com/anomalyco/opencode",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["nodes"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(replay.router, prefix="/api/v1/replay", tags=["replay"])
app.include_router(agents.router, prefix="/api/v1/experiments", tags=["agents"])
app.include_router(semantic.router, tags=["semantic"])
app.include_router(ws.router)


_ollama_available: bool = False


@app.get(
    "/health",
    response_model=HealthCheck,
    summary="Health check",
    description="Returns the health status of all system components.",
)
async def health():
    global _ollama_available
    components = [
        HealthComponent(name="api", status="healthy", details={"version": settings.version}),
    ]
    if hasattr(settings, 'database_url') and settings.database_url:
        components.append(HealthComponent(name="semantic_processor", status="healthy"))
    else:
        components.append(HealthComponent(name="semantic_processor", status="disabled"))

    import forge.api.routes.semantic as semantic_routes
    if semantic_routes._processor:
        engine = getattr(semantic_routes._processor, 'embeddings', None)
        if isinstance(engine, EmbeddingEngine):
            _ollama_available = engine.available
            status = "healthy" if engine.available else "degraded" if engine.using_fallback else "disabled"
            details = {"model": engine.model}
            if engine.using_fallback:
                details["fallback"] = "bag-of-words"
            components.append(HealthComponent(
                name="ollama",
                status=status,
                details=details,
            ))
    else:
        components.append(HealthComponent(name="ollama", status="disabled"))

    overall = "healthy" if all(c.status == "healthy" or c.status == "disabled" for c in components) else "degraded"
    return HealthCheck(status=overall, version=settings.version, components=components)


@app.get("/metrics")
async def metrics(_=Depends(verify_api_key)):
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
