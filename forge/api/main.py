from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from forge.api.routes import events, experiments, nodes, replay
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


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}
