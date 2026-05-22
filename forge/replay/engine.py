
from forge.experiments.models import Experiment, ExperimentEvent


class ReplayEngine:
    async def replay(self, experiment: Experiment, events: list[ExperimentEvent]) -> dict:
        print(f"[replay] replaying experiment {experiment.id}: {len(events)} events")
        timeline = [
            {
                "timestamp": e.timestamp.isoformat(),
                "type": e.event_type,
                "source": e.source,
                "data": e.data,
            }
            for e in events
        ]
        return {
            "experiment_id": experiment.id,
            "name": experiment.name,
            "event_count": len(events),
            "timeline": timeline,
        }

    async def replay_at_speed(self, events: list[ExperimentEvent], speed: float = 1.0):
        print(f"[replay] replaying {len(events)} events at {speed}x speed")
