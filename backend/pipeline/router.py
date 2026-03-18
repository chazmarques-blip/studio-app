"""Shared router instance for the pipeline package."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/campaigns/pipeline", tags=["pipeline"])
