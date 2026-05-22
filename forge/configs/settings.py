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

    docker_network: str = "forge_net"
    data_dir: str = "storage"

    model_config = {"env_prefix": "FORGE_", "env_file": ".env"}


settings = Settings()
