from typing import Dict, List, Union
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Service health status")


class MapsResponse(BaseModel):
    maps: List[str]


class AgentsResponse(BaseModel):
    map: str
    agents: Dict[str, Union[str, float]]