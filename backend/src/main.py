"""
Developer Academy — FastAPI Backend Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.api import progress, templates, auth, courses, quiz, exercise, dashboard, certificates, github, forum, hackathons, jobs, arbitrum, leaderboard, payment, jobs_aggregated, cron
from src.services.ai_mentor import router as mentor_router
from src.services.db import connect_to_mongo, close_mongo_connection
from src.services.job_scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print(f"🚀  Developer Academy API starting — env={settings.app_env}")
    await connect_to_mongo()
    start_scheduler()
    yield
    stop_scheduler()
    await close_mongo_connection()
    print("🛑  Developer Academy API shutting down")


app = FastAPI(
    title="Developer Academy API",
    version="0.1.0",
    description="Modular backend for the Developer Academy — AI Mentor, Progress Tracking, Code Templates.",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["http://192.168.1.102:5173", "https://mor-finance-developer-academy.onrender.com"],
    allow_origin_regex=r"http://(localhost|192\.168\.\d+\.\d+|127\.0\.0\.1):\d+|https://.*\.onrender\.com|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth V1"])
app.include_router(auth.router, prefix="/v1/auth", tags=["Auth V1 Root"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(exercise.router, prefix="/api/exercise", tags=["Exercise"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(certificates.router, prefix="/api/certificates", tags=["Certificates"])
app.include_router(github.router, prefix="/api/github", tags=["Github"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(mentor_router, prefix="/api/mentor", tags=["AI Mentor"])
app.include_router(forum.router, prefix="/api/forum", tags=["Forum"])
app.include_router(hackathons.router, prefix="/api/hackathons", tags=["Hackathons"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs & Careers"])
app.include_router(jobs_aggregated.router, prefix="/api/jobs-aggregated", tags=["Jobs & Careers (aggregated, alternate)"])
app.include_router(cron.router, prefix="/api/cron/aggregate", tags=["Jobs & Careers (aggregated, alternate)"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["Leaderboard"])
app.include_router(payment.router, prefix="/api/payment-callback", tags=["Payment Callback (sandbox)"])
app.include_router(arbitrum.router, prefix="/api", tags=["Arbitrum Analytics & Cohorts"])
app.include_router(arbitrum.router, tags=["Arbitrum Analytics & Cohorts Root"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
