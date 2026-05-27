import json
import logging
from datetime import datetime

import redis.asyncio as redis

from forge.configs.settings import settings
from forge.experiments.models import ExperimentEvent

logger = logging.getLogger(__name__)


def _stream_key(experiment_id: str) -> str:
    return f"{settings.redis_event_stream}:{experiment_id}"


def _event_to_dict(event: ExperimentEvent) -> dict:
    return {
        "id": event.id,
        "experiment_id": event.experiment_id,
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "source": event.source,
        "data": json.dumps(event.data),
    }


def _dict_to_event(d: dict) -> ExperimentEvent:
    return ExperimentEvent(
        id=d.get("id", ""),
        experiment_id=d.get("experiment_id", ""),
        timestamp=datetime.fromisoformat(d["timestamp"]),
        event_type=d["event_type"],
        source=d["source"],
        data=json.loads(d.get("data", "{}")),
    )


class EventStore:
    async def append_event(self, experiment_id: str, event: ExperimentEvent) -> None:
        raise NotImplementedError

    async def get_events(
        self, experiment_id: str, limit: int = 100
    ) -> list[ExperimentEvent]:
        raise NotImplementedError

    async def get_timeline(
        self, experiment_id: str, limit: int = 100
    ) -> list[ExperimentEvent]:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class InMemoryEventStore(EventStore):
    def __init__(self):
        self.events: dict[str, list[ExperimentEvent]] = {}

    async def append_event(self, experiment_id: str, event: ExperimentEvent) -> None:
        self.events.setdefault(experiment_id, []).append(event)

    async def get_events(
        self, experiment_id: str, limit: int = 100
    ) -> list[ExperimentEvent]:
        return (self.events.get(experiment_id, []))[-limit:]

    async def get_timeline(
        self, experiment_id: str, limit: int = 100
    ) -> list[ExperimentEvent]:
        return (self.events.get(experiment_id, []))[-limit:]


class RedisEventStore(EventStore):
    def __init__(self, redis_url: str | None = None):
        self._redis: redis.Redis | None = None
        self._redis_url = redis_url or settings.redis_url

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                self._redis_url, decode_responses=True, socket_connect_timeout=2
            )
            await self._redis.ping()  # type: ignore[misc]
        return self._redis

    async def append_event(self, experiment_id: str, event: ExperimentEvent) -> None:
        r = await self._get_redis()
        await r.xadd(_stream_key(experiment_id), _event_to_dict(event))

    async def get_events(
        self, experiment_id: str, limit: int = 100
    ) -> list[ExperimentEvent]:
        r = await self._get_redis()
        raw = await r.xrevrange(_stream_key(experiment_id), "+", "-", count=limit)
        events = [_dict_to_event(d) for _, d in reversed(raw)]
        return events

    async def get_timeline(
        self, experiment_id: str, limit: int = 100
    ) -> list[ExperimentEvent]:
        return await self.get_events(experiment_id, limit)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None


async def create_event_store(force_in_memory: bool = False) -> EventStore:
    if force_in_memory:
        logger.info("Event store: using InMemoryEventStore (explicit)")
        return InMemoryEventStore()
    try:
        store = RedisEventStore()
        await store._get_redis()
        logger.info("Event store: connected to Redis")
        return store
    except Exception:
        logger.warning("EVENT STORE: Redis unavailable — falling back to InMemoryEventStore. ALL events lost on restart!")
        return InMemoryEventStore()
