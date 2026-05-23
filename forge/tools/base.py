from forge.runtime.node import NodeRuntime


class AgentTools:
    def __init__(self, node_runtime: NodeRuntime | None = None):
        self._node_runtime = node_runtime

    async def exec_command(self, node: str, command: str) -> dict:
        if self._node_runtime is None:
            return {"node": node, "command": command, "error": "node runtime not available"}
        output = await self._node_runtime.exec_on_node(node, ["sh", "-c", command])
        return {"node": node, "command": command, "output": output}

    async def read_file(self, path: str) -> dict:
        return {"path": path, "content": f"contents of {path}"}

    async def restart_service(self, node: str, service: str) -> dict:
        if self._node_runtime is None:
            return {"node": node, "service": service, "error": "node runtime not available"}
        cmd = (
            f"rc-service {service} restart 2>/dev/null "
            f"|| service {service} restart 2>/dev/null "
            f"|| echo 'no service manager'"
        )
        output = await self._node_runtime.exec_on_node(node, ["sh", "-c", cmd])
        return {"node": node, "service": service, "output": output.strip()}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "exec_command",
                    "description": "Run a shell command on a node",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "node": {"type": "string", "description": "Node name"},
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute",
                            },
                        },
                        "required": ["node", "command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "restart_service",
                    "description": "Restart a service on a node",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "node": {"type": "string", "description": "Node name"},
                            "service": {"type": "string", "description": "Service name"},
                        },
                        "required": ["node", "service"],
                    },
                },
            },
        ]
