
"""
🔗 Feature 4: Cognitive Resonance Detection
Find hidden connections between seemingly unrelated topics.
"""
from app.services.hindsight_service import HindsightService, hindsight_service
from typing import Dict, Any, List

class ResonanceEngine:
    """
    Resonance Detection Engine - Graph-based conceptual connections.
    """
    
    def __init__(self, hindsight: HindsightService = hindsight_service):
        self.hindsight = hindsight
    
    async def find_connections(self, topic: str) -> Dict[str, Any]:
        """
        Find hidden connections between topics.
        """
        
        connections = self._get_demo_connections(topic)
        
        return {
            "feature": "resonance_detection",
            "topic": topic,
            "hidden_connections": connections,
            "insight": f"You might find {topic} easier if you revisit {connections[0]['topic']} first." if connections else None,
            "demo_mode": True
        }
    
    def _get_demo_connections(self, topic: str) -> List[Dict[str, Any]]:
        """
        Generate realistic demo connections based on topic.
        """
        connection_map = {
            "recursion": [
                {"topic": "mathematical_induction", "strength": 0.87, "reason": "Both use base case + inductive step"},
                {"topic": "stack_data_structure", "strength": 0.82, "reason": "Call stack mirrors LIFO structure"},
                {"topic": "tree_traversal", "strength": 0.79, "reason": "Recursive tree walks use same pattern"}
            ],
            "dynamic_programming": [
                {"topic": "recursion", "strength": 0.91, "reason": "DP is optimized recursion with memoization"},
                {"topic": "optimization", "strength": 0.75, "reason": "Both minimize redundant computation"},
                {"topic": "graph_algorithms", "strength": 0.68, "reason": "Shortest path uses DP principles"}
            ],
            "binary_trees": [
                {"topic": "recursion", "strength": 0.88, "reason": "Tree operations naturally recursive"},
                {"topic": "divide_and_conquer", "strength": 0.72, "reason": "Both split problems into subproblems"},
                {"topic": "binary_search", "strength": 0.69, "reason": "Similar halving strategy"}
            ]
        }
        
        
        default = [
            {"topic": "foundational_concepts", "strength": 0.65, "reason": "Review basics first"},
            {"topic": "related_algorithms", "strength": 0.60, "reason": "Similar problem patterns"}
        ]
        
        return connection_map.get(topic.lower(), default)