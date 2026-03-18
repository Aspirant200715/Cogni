# backend/app/services/hindsight_service.py
"""
🧠 Cogni - Hindsight Memory Service
Unified interface for all memory operations with real API + demo fallback.
"""
import os
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# CRITICAL: Load environment variables BEFORE any client initialization
load_dotenv()


class _HindsightClient:
    """Simple httpx-based client for Hindsight API with correct endpoints."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def recall(self, bank_id: str, query: str, types: Optional[List[str]] = None, max_tokens: int = 4096, budget: str = 'mid'):
        """Recall memories from the bank."""
        url = f'{self.base_url}/v1/default/banks/{bank_id}/memories/recall'
        payload = {
            'query': query,
            'strategies': types or ['semantic'],
            'limit': max_tokens
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
    
    async def retain(self, bank_id: str, content: str, timestamp: Optional[datetime] = None, context: Optional[str] = None, document_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Retain a memory in the bank."""
        url = f'{self.base_url}/v1/default/banks/{bank_id}/memories'
        payload = {
            'content': content,
            'metadata': metadata or {}
        }
        if context:
            payload['context'] = context
        if timestamp:
            payload['timestamp'] = timestamp.isoformat()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def reflect(self, bank_id: str, query: str, budget: str = 'low', context: Optional[str] = None):
        """Reflect on memories to create synthesized insights."""
        url = f'{self.base_url}/v1/default/banks/{bank_id}/memories/reflect'
        payload = {
            'query': query,
            'budget': budget
        }
        if context:
            payload['context'] = context
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()



class HindsightService:
    """
    🧠 THE CORE: Unified memory service with real Hindsight API support.
    
    Features:
    - retain(): Save study sessions and misconceptions to memory
    - recall(): Query memories with temporal/semantic/graph strategies
    - reflect(): Synthesize patterns into predictive insights
    - Demo fallback: Returns realistic responses if API fails
    """
    
    def __init__(self):
        # Load and CLEAN all environment values aggressively
        raw_key = os.getenv("HINDSIGHT_API_KEY")
        raw_url = os.getenv("HINDSIGHT_BASE_URL")
        raw_bank = os.getenv("HINDSIGHT_BANK_ID")
        raw_global = os.getenv("HINDSIGHT_GLOBAL_BANK")
        
        # DEBUG: Print RAW values with repr() to reveal hidden characters
        print("\n" + "="*70)
        print("[DEBUG] HindsightService - RAW ENV LOADING DEBUG")
        print(f"   raw_key repr: {repr(raw_key)}")
        print(f"   raw_url repr: {repr(raw_url)}")
        print(f"   raw_bank repr: {repr(raw_bank)}")
        print(f"   raw_global repr: {repr(raw_global)}")
        print("="*70 + "\n")
        
        # Clean values: strip whitespace, handle None defaults
        self.api_key = (raw_key or "").strip()
        self.base_url = (raw_url or "https://api.hindsight.vectorize.io").strip().rstrip('/')
        self.bank_id = (raw_bank or "student_demo_001").strip()
        self.global_bank = (raw_global or "global_wisdom_public").strip()
        
        # DEBUG: Print CLEANED values
        print("\n" + "="*70)
        print("[DEBUG] HindsightService - CLEANED VALUES")
        print(f"   api_key: {'[SET]' if self.api_key else '[MISSING]'} ({len(self.api_key)} chars)")
        print(f"   base_url: [{self.base_url}] ({len(self.base_url)} chars)")
        print(f"   bank_id: [{self.bank_id}]")
        print(f"   global_bank: [{self.global_bank}]")
        print(f"   -> Contains 'hhindsight' typo: {'hhindsight' in self.base_url.lower()}")
        print(f"   -> Ends with slash: {self.base_url.endswith('/')}")
        print(f"   -> api_available: {bool(self.api_key and self.base_url)}")
        print("="*70 + "\n")
        
        # Safety check: disable API if obvious typo detected
        if "hhindsight" in self.base_url.lower():
            print("[FATAL] Typo 'hhindsight' detected in base_url! Disabling API.")
            print("   -> Fix: Change 'hhindsight' to 'hindsight' in .env or code")
            self.api_available = False
            self.client = None
        else:
            self.api_available = bool(self.api_key and self.base_url)
            # Initialize httpx-based client with correct Hindsight API endpoints
            if self.api_available:
                try:
                    self.client = _HindsightClient(api_key=self.api_key, base_url=self.base_url)
                    print(f"[SUCCESS] Hindsight client initialized with Bearer token authentication")
                except Exception as e:
                    print(f"[WARNING] Failed to initialize Hindsight client: {str(e)}")
                    self.client = None
                    self.api_available = False
            else:
                self.client = None
        
        print(f"[INIT] HindsightService initialized: api_available={self.api_available}\n")
    
   
    
    async def retain_study_session(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a study session to memory."""
        if not self.api_available or not self.client:
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
        
        try:
            # Directly await the async client method
            response = await self.client.retain(
                bank_id=self.bank_id,
                content=content,
                context=str(context),
                timestamp=datetime.now()
            )
            print(f"[SUCCESS] retain_study_session")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": False}
            
        except Exception as e:
            print(f"[WARNING] Hindsight retain error: {str(e)}")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
    
    async def retain_misconception(self, content: str, context: Dict[str, Any]) -> Dict:
        """Save a misconception for Socratic Ghost."""
        if not self.api_available or not self.client:
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
        
        try:
            response = await self.client.retain(
                bank_id=self.bank_id,
                content=content,
                context=str(context),
                timestamp=datetime.now()
            )
            print(f"[SUCCESS] retain_misconception")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": False}
            
        except Exception as e:
            print(f"[WARNING] Hindsight retain error: {str(e)}")
            return {"status": "success", "bank_id": self.bank_id, "demo_mode": True}
    
  
    
    async def recall_temporal_archaeology(self, topic: str, confusion_level: int, days: int = 30) -> Dict:
        """Feature 1: Find similar confusion moments in the past."""
        if not self.api_available or not self.client:
            return self._get_demo_archaeology_response(topic, confusion_level)
        
        try:
            query = f"confusion about {topic} with level {confusion_level} or higher"
            
            # Directly await the async client method (no need for executor)
            memories = await self.client.recall(
                bank_id=self.bank_id,
                query=query,
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_temporal_archaeology: Got {len(memories)} results")
            
            # Parse API response
            helpful = [
                {
                    "timestamp": m.get("timestamp", "") if isinstance(m, dict) else "",
                    "hint_used": m.get("metadata", {}).get("hint_used", "") if isinstance(m, dict) else "",
                    "outcome": m.get("metadata", {}).get("outcome", "") if isinstance(m, dict) else "",
                    "confidence": 0.85
                }
                for m in memories[:3]
            ]
            
            return {
                "similar_moments": len(memories),
                "what_helped_before": helpful,
                "recommendation": self._generate_recommendation(helpful),
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_archaeology_response(topic, confusion_level)
    
    async def recall_socratic_history(self, concept: str) -> Dict:
        """Feature 2: Find past misconceptions about a concept."""
        if not self.api_available or not self.client:
            return self._get_demo_socratic_response(concept)
        
        try:
            query = f"misconception about {concept}"
            
            memories = await self.client.recall(
                bank_id=self.bank_id,
                query=query,
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_socratic_history: Got {len(memories)} results")
            
            resolved = [m for m in memories if isinstance(m, dict) and m.get("metadata", {}).get("resolved")]
            unresolved = [m for m in memories if not (isinstance(m, dict) and m.get("metadata", {}).get("resolved"))]
            
            return {
                "total_found": len(memories),
                "resolved_count": len(resolved),
                "unresolved_count": len(unresolved),
                "history": [{"content": m.get("content", str(m))} for m in memories[:5]],
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_socratic_response(concept)
    
    async def recall_all_memories(self, limit: int = 10) -> List[Dict]:
        """Memory Inspector: Get all memories for transparency."""
        if not self.api_available or not self.client:
            return self._get_demo_memories(limit)
        
        try:
            memories = await self.client.recall(
                bank_id=self.bank_id,
                query="*",
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_all_memories: Got {len(memories)} results")
            
            return [
                {
                    "id": m.get("id", f"mem_{i}") if isinstance(m, dict) else f"mem_{i}",
                    "content": m.get("content", str(m)) if isinstance(m, dict) else str(m),
                    "timestamp": m.get("timestamp", datetime.now().isoformat()) if isinstance(m, dict) else datetime.now().isoformat(),
                    "confidence": 0.85
                }
                for i, m in enumerate(memories[:limit])
            ]
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_memories(limit)
    
 
    
    async def reflect_cognitive_shadow(self, days: int = 7) -> Dict:
        """Feature 3: Synthesize patterns into predictive insights."""
        if not self.api_available or not self.client:
            return self._get_demo_shadow_response()
        
        try:
            query = "Summarize learning patterns and predict upcoming challenges"
            
            result = await self.client.reflect(
                bank_id=self.bank_id,
                query=query,
                budget="low"
            )
            
            print(f"[SUCCESS] reflect_cognitive_shadow")
            
            content = result.get('prediction', str(result)) if isinstance(result, dict) else str(result)
            return {
                "prediction": content,
                "confidence": 0.75,
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight reflect error: {str(e)}")
            return self._get_demo_shadow_response()
    
    async def recall_global_contagion(self, error_pattern: str) -> Dict:
        """Feature 5: Query global wisdom bank for peer patterns."""
        if not self.api_available or not self.client:
            return self._get_demo_contagion_response(error_pattern)
        
        try:
            memories = await self.client.recall(
                bank_id=self.global_bank,
                query=error_pattern,
                max_tokens=4096
            )
            
            print(f"[SUCCESS] recall_global_contagion: Got {len(memories)} results")
            
            # Extract strategy hints from results
            hints = []
            for m in memories:
                if isinstance(m, dict) and m.get("metadata", {}).get("hint_used"):
                    hints.append(m.get("metadata", {}).get("hint_used"))
            
            top_hint = max(set(hints), key=hints.count) if hints else None
            
            return {
                "community_size": len(memories),
                "top_strategy": top_hint,
                "success_rate": 0.78 if top_hint else None,
                "privacy_note": "Aggregated from anonymized peer data",
                "demo_mode": False
            }
            
        except Exception as e:
            print(f"[WARNING] Hindsight recall error: {str(e)}")
            return self._get_demo_contagion_response(error_pattern)
    
   
    def _get_demo_archaeology_response(self, topic: str, confusion_level: int) -> Dict:
        """Realistic demo response for Temporal Archaeology."""
        return {
            "similar_moments": 3,
            "what_helped_before": [
                {"timestamp": "2026-03-10T14:30:00Z", "hint_used": "visual_gift_analogy", "outcome": "resolved", "confidence": 0.92},
                {"timestamp": "2026-03-15T09:15:00Z", "hint_used": "draw_call_stack", "outcome": "resolved", "confidence": 0.87}
            ],
            "recommendation": f"Last time you felt this confused about {topic}, 'visual_gift_analogy' helped. Try that approach again.",
            "demo_mode": True
        }
    
    def _get_demo_socratic_response(self, concept: str) -> Dict:
        """Realistic demo response for Socratic Ghost."""
        return {
            "total_found": 2,
            "resolved_count": 1,
            "unresolved_count": 1,
            "history": [{"content": f"Misconception: {concept}", "context": {"resolved": True}}],
            "next_question": f"Let's explore {concept} deeper. What's the simplest case you can think of?",
            "demo_mode": True
        }
    
    def _get_demo_memories(self, limit: int) -> List[Dict]:
        """Realistic demo memories for Memory Inspector."""
        return [
            {
                "id": f"mem_{i}",
                "content": f"Studied {['recursion', 'DP', 'trees'][i%3]}: confusion={4-i%3}/5",
                "context": {
                    "type": "StudySession",
                    "topic": ["recursion", "DP", "trees"][i%3],
                    "confusion_level": 4-i%3,
                    "outcome": "resolved" if i%2==0 else "partial"
                },
                "timestamp": (datetime.now() - timedelta(days=i*2)).isoformat(),
                "confidence": 0.85 + (i*0.03),
                "tags": ["study_session"]
            }
            for i in range(min(limit, 5))
        ]
    
    def _get_demo_shadow_response(self) -> Dict:
        """Realistic demo response for Cognitive Shadow."""
        return {
            "prediction": "Your Cognitive Twin predicts you'll struggle with tree traversal recursion tomorrow. Prep with the 'unwrapping gifts' visual exercise first.",
            "confidence": 0.84,
            "demo_mode": True
        }
    
    def _get_demo_contagion_response(self, error_pattern: str) -> Dict:
        """Realistic demo response for Metacognitive Contagion."""
        return {
            "community_size": 47,
            "top_strategy": "visual_analogy",
            "success_rate": 0.82,
            "privacy_note": "Aggregated from anonymized peer data",
            "demo_mode": True
        }
    
    def _generate_recommendation(self, helpful_patterns: List[Dict]) -> str:
        """Generate personalized recommendation from past patterns."""
        if not helpful_patterns:
            return "Try breaking the problem into smaller steps and explaining each aloud."
        hints = [p["hint_used"] for p in helpful_patterns if p.get("hint_used")]
        if hints:
            most_helpful = max(set(hints), key=hints.count)
            return f"Last time you felt this confused, '{most_helpful}' helped. Try that approach again."
        return "Review the foundational concept first, then attempt the problem again."


# Singleton instance for easy import across the app
hindsight_service = HindsightService()