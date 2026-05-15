from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import auth, wallet, webhooks, intent, profile, jobs, finance, chat, workers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="EcoNet API",
    description="Community-anchored financial ecosystem — GTCO HabariPay Squad Hackathon 3.0",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Module 1 — Authentication"])
app.include_router(wallet.router, prefix="/wallet", tags=["Module 2 — Wallet"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Squad Webhooks"])
app.include_router(intent.router, prefix="/intent", tags=["Module 3 — Intent Routing"])
app.include_router(profile.router, prefix="/profile", tags=["Module 4 — Work Profile"])
app.include_router(jobs.router, prefix="/jobs", tags=["Module 7 — Job Posting & Matching"])
app.include_router(workers.router, prefix="/workers", tags=["Module 5 — Voice to Search"])
app.include_router(finance.router, prefix="/finance", tags=["Modules 11-13 — Finance"])
app.include_router(chat.router, prefix="/chat", tags=["Module 8+9 — Chat & Escrow"])


@app.get("/health", tags=["Health"])
async def health():
    return {"success": True, "data": {"status": "ok", "service": "econet-backend"}, "error": None}
