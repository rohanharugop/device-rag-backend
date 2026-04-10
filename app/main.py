# from dotenv import load_dotenv
# load_dotenv()   # ✅ LOAD FIRST (TOP OF FILE)

# from fastapi import FastAPI
# from app.api.routes.device import router as device_router

# app = FastAPI()

# app.include_router(device_router)





from fastapi import FastAPI
from app.controllers.device_controller import DeviceController

app = FastAPI()