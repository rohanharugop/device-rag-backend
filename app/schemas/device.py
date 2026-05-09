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


class CompatibilityRequest(BaseModel):
    device_id: str
    software_capabilities: List[str]


class GeneratePWARequest(BaseModel):
    device_id: str

class RunProjectRequest(BaseModel):
    device_id: str
    device_name: str
    title: str
    difficulty: str
    steps: dict  # {"1": "step one", "2": "step two", ...}

class NextStepRequest(BaseModel):
    project_id: str

class SubmitStepRequest(BaseModel):
    project_id: str
    action: str          # "done" or "issue"
    issue_detail: str | None = None