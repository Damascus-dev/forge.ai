import json
import logging
import os
import asyncio
from datetime import datetime
from typing import Optional

from forge.experiments.models import Experiment, ExperimentStatus, Node

logger = logging.getLogger(__name__)


class ExperimentStore:
    def __init__(self, path: Optional[str] = None):
        self._path = path
        self._lock = asyncio.Lock()
        self._data: dict = {"experiments": {}, "nodes": {}}

    async def _load_from_disk(self):
        if not self._path or not os.path.exists(self._path):
            return
        try:
            def _load():
                with open(self._path) as f:
                    return json.load(f)
            raw = await asyncio.to_thread(_load)
            for eid, edata in raw.get("experiments", {}).items():
                edata["created_at"] = datetime.fromisoformat(edata["created_at"])
                edata["status"] = ExperimentStatus(edata["status"])
                self._data["experiments"][eid] = Experiment(**edata)
            self._data["nodes"] = raw.get("nodes", {})
            logger.info("Loaded %d experiments from %s", len(self._data["experiments"]), self._path)
        except Exception as e:
            logger.warning("Failed to load experiment store: %s", e)

    async def _save_to_disk(self):
        if not self._path:
            return
        def _write():
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            with open(self._path, "w") as f:
                json.dump({
                    "experiments": {
                        eid: exp.model_dump(mode="json")
                        for eid, exp in self._data["experiments"].items()
                    },
                    "nodes": self._data["nodes"],
                }, f, indent=2, default=str)
        await asyncio.to_thread(_write)

    async def save_experiment(self, experiment: Experiment) -> Experiment:
        async with self._lock:
            self._data["experiments"][experiment.id] = experiment
            await self._save_to_disk()
            return experiment

    async def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        async with self._lock:
            return self._data["experiments"].get(experiment_id)

    async def list_experiments(self) -> list[Experiment]:
        async with self._lock:
            return list(self._data["experiments"].values())

    async def delete_experiment(self, experiment_id: str) -> bool:
        async with self._lock:
            if experiment_id not in self._data["experiments"]:
                return False
            del self._data["experiments"][experiment_id]
            self._data["nodes"].pop(experiment_id, None)
            await self._save_to_disk()
            return True

    async def save_node(self, experiment_id: str, node: Node) -> Node:
        async with self._lock:
            self._data["nodes"].setdefault(experiment_id, {})[node.id] = node.model_dump(mode="json")
            await self._save_to_disk()
            return node

    async def list_nodes(self, experiment_id: str) -> list[dict]:
        async with self._lock:
            return list(self._data["nodes"].get(experiment_id, {}).values())

    async def clear_nodes(self, experiment_id: str):
        async with self._lock:
            self._data["nodes"].pop(experiment_id, None)
            await self._save_to_disk()

    async def close(self):
        pass
