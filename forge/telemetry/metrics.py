from prometheus_client import Counter, Gauge

from forge.experiments.models import ExperimentEvent

events_total = Counter("forge_events_total", "Total events recorded", ["event_type"])
nodes_active = Gauge("forge_nodes_active", "Active nodes across experiments")
experiments_total = Counter("forge_experiments_total", "Experiments created")


class MetricsCollector:
    def record_event(self, event: ExperimentEvent) -> None:
        events_total.labels(event_type=event.event_type).inc()

    def record_experiment_created(self) -> None:
        experiments_total.inc()

    def set_nodes_active(self, count: int) -> None:
        nodes_active.set(count)
