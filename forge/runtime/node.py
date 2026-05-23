from docker.errors import DockerException, NotFound

from docker import from_env
from docker.types import IPAMConfig, IPAMPool
from forge.configs.settings import settings
from forge.experiments.models import Experiment, Node


class NodeRuntime:
    def __init__(self):
        self.active_containers: dict[str, list[str]] = {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                self._client = from_env()
                self._client.ping()
            except DockerException:
                self._client = None
        return self._client

    def _ensure_network(self):
        client = self._get_client()
        if client is None:
            return
        try:
            client.networks.get(settings.docker_network)
        except NotFound:
            client.networks.create(
                settings.docker_network,
                driver="bridge",
                check_duplicate=True,
            )

    async def launch_nodes(self, experiment: Experiment) -> list[Node]:
        client = self._get_client()
        if client is None:
            return []

        self._ensure_network()

        nodes = []
        container_ids = []

        for i in range(experiment.node_count):
            node_name = f"node-{experiment.id}-{i}"
            container = client.containers.run(
                "alpine:latest",
                command=["sleep", "infinity"],
                name=node_name,
                detach=True,
                network=settings.docker_network,
                remove=True,
            )
            container_ids.append(container.id)
            nodes.append(
                Node(
                    id=f"{experiment.id}-{i}",
                    experiment_id=experiment.id,
                    name=node_name,
                    container_id=container.id,
                    status="running",
                )
            )

        self.active_containers[experiment.id] = container_ids
        return nodes

    async def teardown_nodes(self, experiment_id: str) -> bool:
        client = self._get_client()
        if client is None:
            self.active_containers.pop(experiment_id, [])
            return True

        container_ids = self.active_containers.pop(experiment_id, [])
        for cid in container_ids:
            try:
                container = client.containers.get(cid)
                container.stop(timeout=5)
                container.remove(force=True)
            except DockerException:
                pass
        return True

    async def exec_on_node(self, node_name: str, command: list[str]) -> str:
        client = self._get_client()
        if client is None:
            return "docker not available"

        try:
            container = client.containers.get(node_name)
            exit_code, output = container.exec_run(command)
            return output.decode("utf-8", errors="replace")
        except DockerException as e:
            return f"error: {e}"
