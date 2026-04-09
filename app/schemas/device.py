from pydantic import BaseModel


class DetectResponse(BaseModel):
    device_id: str
    brand: str
    model: str
    confidence: float


class ConfirmRequest(BaseModel):
    device_id: str
    brand: str
    model: str


class ConfirmResponse(BaseModel):
    device_id: str
    device_name: str


from pydantic import BaseModel
from typing import List


class SpecsRequest(BaseModel):
    device_id: str
    device_name: str


class SpecsResponse(BaseModel):
    device_id: str
    components: List[str]
    capabilities: List[str]
    sources: List[str]

from typing import List


class SaveRequest(BaseModel):
    device_id: str
    components: List[str]
    capabilities: List[str]

class IdeasRequest(BaseModel):
    device_id: str  