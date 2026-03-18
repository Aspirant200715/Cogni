# backend/app/routes/socratic_routes.py
from fastapi import APIRouter, HTTPException
from app.engines.socratic_engine import SocraticEngine
from app.models.memory_types import Misconception, APIResponse

router = APIRouter(prefix="/socratic", tags=["socratic"])

@router.post("/ask", response_model=APIResponse)
async def ask_question(concept: str, user_belief: str):
    """Ask a Socratic question based on past misconceptions"""
    try:
        engine = SocraticEngine()
        result = await engine.ask_socratic_question(concept, user_belief)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log", response_model=APIResponse)
async def log_misconception(misconception: Misconception):
    """Save a misconception to memory"""
    try:
        engine = SocraticEngine()
        result = await engine.log_misconception(misconception)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=APIResponse)
async def get_history(concept: str):
    """Get dialogue history for a concept"""
    try:
        engine = SocraticEngine()
        result = await engine.get_dialogue_history(concept)
        return APIResponse(
            status="success",
            data=result,
            demo_mode=result.get("demo_mode", True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))