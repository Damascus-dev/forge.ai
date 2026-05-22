class AgentTools:
    @staticmethod
    async def exec_command(node: str, command: str) -> dict:
        return {"node": node, "command": command, "output": f"output of '{command}' on {node}"}

    @staticmethod
    async def read_file(path: str) -> dict:
        return {"path": path, "content": f"contents of {path}"}

    @staticmethod
    async def restart_service(node: str, service: str) -> dict:
        return {"node": node, "service": service, "status": "restarted"}
