from fastapi import APIRouter, UploadFile, File, Form
from app.controllers.device_controller import DeviceController
from app.schemas.device import ConfirmRequest
from app.controllers.device_controller import DeviceController
from app.schemas.device import SpecsRequest
from app.controllers.device_controller import DeviceController
from app.schemas.device import SaveRequest
from app.controllers.device_controller import DeviceController
from app.schemas.device import IdeasRequest
from app.controllers.device_controller import DeviceController
from app.schemas.device import CompatibilityRequest, GeneratePWARequest
from app.schemas.device import NextStepRequest, SubmitStepRequest
from app.schemas.device import RunProjectRequest



router = APIRouter(prefix="/api")


@router.post("/detect-device")
async def detect_device(
    file: UploadFile = File(...),
    brand: str = Form(None),
    model: str = Form(None),
    condition: str = Form(None),
    additionalInfo: str = Form(None),
):
    image = await file.read()

    return await DeviceController.detect_device(
        image,
        brand,
        model,
        condition,
        additionalInfo
    )
@router.post("/confirm-device")
def confirm_device(req: ConfirmRequest):
    return DeviceController.confirm_device(
        device_id=req.device_id,
        brand=req.brand,
        model=req.model
    )
from app.schemas.device import SpecsRequest
from app.controllers.device_controller import DeviceController


@router.post("/device-specs")
def device_specs(req: SpecsRequest):
    return DeviceController.device_specs(
        device_id=req.device_id,
        device_name=req.device_name
    )
@router.post("/save-device")
def save_device(req: SaveRequest):
    return DeviceController.save_device(
        device_id=req.device_id,
        components=req.components,
        capabilities=req.capabilities
    )
@router.post("/generate-ideas")
def generate_ideas(req: IdeasRequest):
    return DeviceController.generate_ideas(req.device_id)


@router.post("/check-pwa-compatibility")
def check_pwa_compatibility(payload: CompatibilityRequest):
    return DeviceController.check_pwa_compatibility(
        device_id=payload.device_id,
        software_capabilities=payload.software_capabilities
    )


@router.post("/generate-pwa")
def generate_pwa(payload: GeneratePWARequest):
    return DeviceController.generate_pwa(
        device_id=payload.device_id
    )





@router.post("/run-project")
def run_project(req: RunProjectRequest):
    return DeviceController.run_project(
        device_id=req.device_id,
        device_name=req.device_name,
        title=req.title,
        difficulty=req.difficulty,
        steps=req.steps
    )

@router.post("/next-step")
def next_step(req: NextStepRequest):
    return DeviceController.next_step(req.project_id)

@router.post("/submit-step")
def submit_step(req: SubmitStepRequest):
    return DeviceController.submit_step(
        project_id=req.project_id,
        action=req.action,
        issue_detail=req.issue_detail
    )