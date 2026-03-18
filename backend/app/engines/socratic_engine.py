
"""
👻 Feature 2: Socratic Ghost
A tutor that remembers every misconception you've ever had.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from app.models.memory_types import Misconception
from typing import Dict, Any, List

class SocraticEngine:
    """
    Socratic Ghost Engine - Persistent dialogue with memory.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
    
    async def ask_socratic_question(self, concept: str, user_belief: str) -> Dict[str, Any]:
        """
        Ask a Socratic question based on past misconceptions.
        """
        # Get past dialogue history
        history = await self.hindsight.recall_socratic_history(concept)
        
        # Generate personalized question
        if history.get("unresolved_count", 0) > 0:
            question = f"You've explored this before. Last time, we discussed: '{history['history'][0].get('context', {}).get('question_asked', 'the basics')}'. Let's go deeper: What happens in the simplest possible case?"
        else:
            question = f"Interesting belief about {concept}. Let's test it: Can you think of a counterexample where '{user_belief}' wouldn't hold true?"
        
        return {
            "feature": "socratic_ghost",
            "concept": concept,
            "user_belief": user_belief,
            "question": question,
            "past_history": history,
            "demo_mode": history.get("demo_mode", True)
        }
    
    async def log_misconception(self, misconception: Misconception) -> Dict[str, Any]:
        """
        Save a misconception to memory.
        """
        content = f"Misconception: {misconception.concept} - '{misconception.incorrect_belief}'"
        
        result = await self.hindsight.retain_misconception(
            content=content,
            context=misconception.model_dump()
        )
        
        return {
            "feature": "misconception_log",
            "status": result.get("status"),
            "misconception": misconception.model_dump(),
            "demo_mode": result.get("demo_mode", True)
        }
    
    async def get_dialogue_history(self, concept: str) -> Dict[str, Any]:
        """
        Get all past dialogues about a concept.
        """
        history = await self.hindsight.recall_socratic_history(concept)
        
        return {
            "feature": "dialogue_history",
            "concept": concept,
            "total_found": history.get("total_found", 0),
            "resolved_count": history.get("resolved_count", 0),
            "unresolved_count": history.get("unresolved_count", 0),
            "history": history.get("history", []),
            "demo_mode": history.get("demo_mode", True)
        }