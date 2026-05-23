from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from forge.api.routes import agents, events, experiments, nodes, replay
from forge.configs.settings import settings

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

app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["nodes"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(replay.router, prefix="/api/v1/replay", tags=["replay"])
app.include_router(agents.router, prefix="/api/v1/experiments", tags=["agents"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
