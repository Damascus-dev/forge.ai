
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "forge"
    version: str = "0.1.0"
    debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    redis_url: str = "redis://localhost:6379/0"
    redis_event_stream: str = "forge:events"

    sqlite_path: str = "data/forge.db"
    database_url: str = "postgresql+asyncpg://forge:forge_password@localhost:5432/forge"

    docker_network: str = "forge_net"
    data_dir: str = "storage"

    api_key: str = ""
    allowed_origins: str = ""

    model_config = {"env_prefix": "FORGE_", "env_file": ".env"}

    @property
    def effective_api_key(self) -> str:
        return self.api_key or "dev-key-change-me"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",")]
        if self.debug:
            return ["*"]
        return ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]

    @property
    def auth_enabled(self) -> bool:
        return bool(self.api_key) and not self.debug


settings = Settings()
