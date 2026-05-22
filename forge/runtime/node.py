
from forge.experiments.models import Experiment


class NodeRuntime:
    def __init__(self):
        self.active_containers: dict[str, list[str]] = {}

    async def launch_nodes(self, experiment: Experiment):
        node_names = [f"node-{experiment.id}-{i}" for i in range(experiment.node_count)]
        self.active_containers[experiment.id] = node_names
        for name in node_names:
            print(f"[runtime] launching {name}")

    async def teardown_nodes(self, experiment_id: str):
        nodes = self.active_containers.pop(experiment_id, [])
        for name in nodes:
            print(f"[runtime] tearing down {name}")
        return True

    async def exec_on_node(self, node_name: str, command: list[str]) -> str:
        print(f"[runtime] exec on {node_name}: {' '.join(command)}")
        return f"executed on {node_name}"
