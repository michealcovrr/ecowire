from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import skills, matching, financial

app = FastAPI(
    title="EcoNet ML Service",
    description="AI/ML endpoints — called only by the main backend, never directly by clients",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Module 4 — Work Profile & Skill System
app.include_router(skills.router, prefix="/ml")

# Module 7 — Job Parsing & Matching
app.include_router(matching.router, prefix="/ml")

# Modules 11 & 12 — Financial Tracking & Identity
app.include_router(financial.router, prefix="/ml")

# Routers added as modules are built:
# app.include_router(assistant.router, prefix="/ml")  # Module 14


@app.get("/health")
async def health():
    return {"success": True, "data": {"status": "ok", "service": "econet-ml"}, "error": None}
