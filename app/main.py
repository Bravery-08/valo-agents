import logging
from typing import Dict

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.schemas.valo import HealthResponse, MapsResponse, AgentsResponse
from app.services.valo_service import ValoService


configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

service = ValoService()


@app.get("/healthz", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/maps", response_model=MapsResponse)
def get_maps() -> MapsResponse:
    try:
        maps = service.get_map_pool()
        return MapsResponse(maps=maps)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).exception("Failed to fetch map pool: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to fetch map pool") from exc


@app.get("/agents/{map_name}", response_model=AgentsResponse)
def get_agents(map_name: str = Path(..., min_length=2, max_length=50)) -> AgentsResponse:
    try:
        data: Dict[int | str, str | float] = service.get_agents_for_map(map_name)
        # Normalize shape for response_model
        map_value = str(data.get("Map", map_name))
        agents_only = {str(k): v for k, v in data.items() if isinstance(k, int)}
        return AgentsResponse(map=map_value, agents=agents_only)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).exception("Failed to fetch agents for map %s: %s", map_name, exc)
        raise HTTPException(status_code=502, detail="Failed to fetch agents") from exc
