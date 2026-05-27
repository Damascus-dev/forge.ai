import logging

from fastapi import Header, HTTPException, WebSocket, status

from forge.configs.settings import settings

logger = logging.getLogger(__name__)


def verify_api_key(x_api_key: str = Header("")) -> None:
    if not settings.auth_enabled:
        return
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if x_api_key != settings.effective_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


async def verify_ws_api_key(websocket: WebSocket) -> bool:
    if not settings.auth_enabled:
        return True
    api_key = websocket.query_params.get("api_key", "")
    if not api_key:
        await websocket.close(code=4001, reason="Missing api_key query parameter")
        return False
    if api_key != settings.effective_api_key:
        await websocket.close(code=4003, reason="Invalid API key")
        return False
    return True
