from forge.experiments.models import FaultConfig
from forge.runtime.node import NodeRuntime


class ChaosEngine:
    def __init__(self, node_runtime: NodeRuntime | None = None):
        self._node_runtime = node_runtime

    async def inject_fault(self, config: FaultConfig) -> dict:
        target = config.target_node
        params = config.params

        if config.fault_type == "latency":
            delay = params.get("delay_ms", 100)
            jitter = params.get("jitter_ms", 10)
            return await self.inject_latency(target, delay, jitter)

        if config.fault_type == "packet_loss":
            loss = params.get("loss_pct", 5.0)
            return await self.inject_packet_loss(target, loss)

        if config.fault_type == "crash":
            return await self.kill_node(target)

        if config.fault_type == "disconnect":
            return await self.disconnect_node(target)

        if config.fault_type == "clear":
            return await self.clear_faults(target)

        return {"status": "unknown", "fault_type": config.fault_type, "target": target}

    async def _exec(self, node_name: str, command: list[str]) -> str:
        if self._node_runtime is None:
            return "node runtime not available"
        return await self._node_runtime.exec_on_node(node_name, command)

    async def _ensure_tc(self, node_name: str) -> str:
        cmd = "command -v tc >/dev/null 2>&1 || apk add iproute2 >/dev/null 2>&1"
        return await self._exec(node_name, ["sh", "-c", f"{cmd}; tc --version 2>&1"])

    async def inject_latency(
        self, node_name: str, delay_ms: int = 100, jitter_ms: int = 10
    ) -> dict:
        await self._ensure_tc(node_name)
        result = await self._exec(
            node_name,
            [
                "sh",
                "-c",
                f"tc qdisc add dev eth0 root netem delay {delay_ms}ms {jitter_ms}ms 2>/dev/null "
                f"|| tc qdisc replace dev eth0 root netem delay {delay_ms}ms {jitter_ms}ms",
            ],
        )
        return {
            "status": "injected",
            "fault_type": "latency",
            "target": node_name,
            "delay_ms": delay_ms,
            "jitter_ms": jitter_ms,
            "output": result.strip(),
        }

    async def inject_packet_loss(self, node_name: str, loss_pct: float = 5.0) -> dict:
        await self._ensure_tc(node_name)
        result = await self._exec(
            node_name,
            [
                "sh",
                "-c",
                f"tc qdisc add dev eth0 root netem loss {loss_pct}% 2>/dev/null "
                f"|| tc qdisc replace dev eth0 root netem loss {loss_pct}%",
            ],
        )
        return {
            "status": "injected",
            "fault_type": "packet_loss",
            "target": node_name,
            "loss_pct": loss_pct,
            "output": result.strip(),
        }

    async def kill_node(self, node_name: str) -> dict:
        if self._node_runtime is None:
            return {"status": "error", "message": "node runtime not available"}
        result = await self._node_runtime.exec_on_node(node_name, ["sh", "-c", "kill 1"])
        return {
            "status": "injected",
            "fault_type": "crash",
            "target": node_name,
            "output": result.strip(),
        }

    async def disconnect_node(self, node_name: str) -> dict:
        await self._ensure_tc(node_name)
        result = await self._exec(
            node_name,
            [
                "sh",
                "-c",
                "tc qdisc add dev eth0 root netem loss 100% 2>/dev/null "
                "|| tc qdisc replace dev eth0 root netem loss 100%",
            ],
        )
        return {
            "status": "injected",
            "fault_type": "disconnect",
            "target": node_name,
            "output": result.strip(),
        }

    async def clear_faults(self, node_name: str) -> dict:
        await self._ensure_tc(node_name)
        result = await self._exec(
            node_name,
            ["sh", "-c", "tc qdisc del dev eth0 root 2>/dev/null; echo 'cleared'"],
        )
        return {
            "status": "cleared",
            "target": node_name,
            "output": result.strip(),
        }
