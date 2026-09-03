"""FastAPI application entry point for PlacementOps."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    project_root = Path(__file__).resolve().parents[2]
    for env_filename in [".env", ".env.local", ".env.example"]:
        env_file = project_root / env_filename
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from placementops.api.routes import router

app = FastAPI(
    title="PlacementOps API",
    description="Constraint-aware placement scheduling and real-time replanning platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https://placement-ops-final(?:-[a-z0-9-]+)?-yashsharma23csds-2811s-projects\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok"}