# backend/app/engines/contagion_engine.py
"""
🌐 Feature 5: Metacognitive Contagion
Learn from anonymized patterns of similar thinkers.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from typing import Dict, Any, List

class ContagionEngine:
    """
    Metacognitive Contagion Engine - Collective intelligence from peer patterns.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
    
    async def get_community_insights(self, error_pattern: str) -> Dict[str, Any]:
        """
        Get insights from anonymized peer data.
        """
        insights = await self.hindsight.recall_global_contagion(error_pattern)
        
        return {
            "feature": "metacognitive_contagion",
            "error_pattern": error_pattern,
            "community_size": insights.get("community_size", 47),
            "top_strategy": insights.get("top_strategy", "visual_analogy"),
            "success_rate": insights.get("success_rate", 0.82),
            "privacy_note": insights.get("privacy_note", "Aggregated from anonymized peer data"),
            "additional_strategies": self._get_demo_strategies(error_pattern),
            "demo_mode": insights.get("demo_mode", True)
        }
    
    def _get_demo_strategies(self, error_pattern: str) -> List[Dict[str, Any]]:
        """
        Generate realistic demo strategies based on error pattern.
        """
        strategy_map = {
            "base_case_missing": [
                {"strategy": "Write base case first before recursive logic", "success_rate": 0.89},
                {"strategy": "Test with smallest input (n=0 or n=1)", "success_rate": 0.85},
                {"strategy": "Draw the recursion tree visually", "success_rate": 0.82}
            ],
            "stack_overflow": [
                {"strategy": "Check termination condition is reachable", "success_rate": 0.87},
                {"strategy": "Add debug prints to track call depth", "success_rate": 0.79},
                {"strategy": "Convert to iterative approach temporarily", "success_rate": 0.74}
            ],
            "off_by_one": [
                {"strategy": "Write loop boundaries on paper first", "success_rate": 0.88},
                {"strategy": "Test edge cases (empty, single element)", "success_rate": 0.84},
                {"strategy": "Use <= instead of < (or vice versa)", "success_rate": 0.76}
            ]
        }
        
        default = [
            {"strategy": "Break problem into smaller steps", "success_rate": 0.75},
            {"strategy": "Explain problem out loud", "success_rate": 0.71},
            {"strategy": "Draw diagrams/visualizations", "success_rate": 0.68}
        ]
        
        return strategy_map.get(error_pattern.lower(), default)