from forge.experiments.models import ExperimentEvent


class MetricsCollector:
    def __init__(self):
        self.event_count = 0

    def record_event(self, event: ExperimentEvent):
        self.event_count += 1
