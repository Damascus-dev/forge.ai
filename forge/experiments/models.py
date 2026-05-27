from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class NodeType(str, Enum):
    compute = "compute"
    agent = "agent"
    monitor = "monitor"
    gateway = "gateway"


class ExperimentStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class EventSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    name: str
    description: str = ""
    status: ExperimentStatus = ExperimentStatus.pending
    node_count: int = 2
    created_at: datetime = Field(default_factory=_now)
    config: dict = {}
    tags: list[str] = []


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    tags: Optional[list[str]] = None


class Node(BaseModel):
    id: str
    experiment_id: str
    name: str
    node_type: NodeType = NodeType.compute
    container_id: Optional[str] = None
    status: str = "created"
    created_at: datetime = Field(default_factory=_now)
    tags: list[str] = []


class ExperimentEvent(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    experiment_id: str
    timestamp: datetime = Field(default_factory=_now)
    event_type: str
    source: str
    data: dict = {}
    severity: EventSeverity = EventSeverity.info
    metadata: dict = {}
    tags: list[str] = []


class FaultConfig(BaseModel):
    experiment_id: str
    target_node: str
    fault_type: str  # latency, packet_loss, crash, disconnect
    params: dict = {}
    severity: EventSeverity = EventSeverity.warning


class AgentConfig(BaseModel):
    model: str = "ollama/qwen2.5:0.5b"
    system_prompt: str = ""
    task_description: str = ""


class AgentLog(BaseModel):
    experiment_id: str
    agent_id: str
    step: int
    observation: dict = {}
    decision: str = ""
    action: str = ""
    result: dict = {}
    timestamp: datetime = Field(default_factory=_now)


class ExportFormat(str, Enum):
    json = "json"
    csv = "csv"
    markdown = "markdown"


class HealthComponent(BaseModel):
    name: str
    status: str
    details: Optional[dict] = None


class HealthCheck(BaseModel):
    status: str
    version: str
    components: list[HealthComponent]
