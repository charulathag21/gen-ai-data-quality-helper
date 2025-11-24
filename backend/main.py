from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from src.routers.data_router import router as data_router
from src.routers.quality_router import router as quality_router
from src.routers.auth_router import router as auth_router

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://gen-ai-data-quality-helper.netlify.app",
    "https://charulathag21-gen-ai-data-quality-helper.hf.space",
]

app = FastAPI(title="Gen-AI Data Quality Helper")

@app.get("/")
def health_check():
    return {"FastAPI": "working"}

# AUTH ROUTES
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# DATA ROUTES
app.include_router(data_router, prefix="/data", tags=["data"])

# QUALITY ROUTES
app.include_router(quality_router, prefix="/quality", tags=["quality"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
