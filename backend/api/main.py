"""
Midnight Core — FastAPI Entry Point
Takeoff LLC
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
import secrets, os

app = FastAPI(title="Midnight Core", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    password = os.getenv("TOOL_PASSWORD", "midnight2025")
    correct = secrets.compare_digest(credentials.password.encode(), password.encode())
    if not correct:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Basic"})
    return credentials.username

from backend.api.routes     import router as pipeline_router
from backend.api.dashboard  import router as dashboard_router
from backend.api.smart_scan import router as smart_scan_router

app.include_router(pipeline_router,   dependencies=[Depends(verify_password)])
app.include_router(dashboard_router,  dependencies=[Depends(verify_password)])
app.include_router(smart_scan_router, dependencies=[Depends(verify_password)])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "midnight-core"}

@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")