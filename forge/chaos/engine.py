from forge.experiments.models import FaultConfig


class ChaosEngine:
    async def inject_fault(self, config: FaultConfig) -> dict:
        print(f"[chaos] injecting {config.fault_type} on {config.target_node}: {config.params}")
        return {
            "status": "injected",
            "fault_type": config.fault_type,
            "target": config.target_node,
        }

    async def inject_latency(self, node_name: str, delay_ms: int = 100, jitter_ms: int = 10):
        print(f"[chaos] latency +{delay_ms}ms (±{jitter_ms}ms) → {node_name}")

    async def inject_packet_loss(self, node_name: str, loss_pct: float = 5.0):
        print(f"[chaos] packet loss {loss_pct}% → {node_name}")

    async def kill_node(self, node_name: str):
        print(f"[chaos] killing node {node_name}")
