"""FastAPI application entry point for PlacementOps."""

from __future__ import annotations

from fastapi import FastAPI

from placementops.api.routes import router

app = FastAPI(
    title="PlacementOps API",
    description="Constraint-aware placement scheduling and real-time replanning platform.",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok"}
