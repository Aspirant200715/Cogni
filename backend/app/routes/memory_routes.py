# backend/app/routes/memory_routes.py
from fastapi import APIRouter, Query, Body
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from app.services.hindsight_service import hindsight_service
from app.services.memory_analytics_service import memory_analytics_service
from app.services.summary_service import summary_service
from app.engines.reflection_engine import reflection_engine
from app.models.memory_types import APIResponse
from datetime import datetime
from typing import List, Dict, Any
import io

router = APIRouter(prefix="/memory", tags=["memory"])

# Request models
class SummaryRequest(BaseModel):
    conversation: str

class PDFRequest(BaseModel):
    summary_text: str
    topic_name: str = "learning_summary"

@router.get("/recall")
async def recall_memories(
    query: str = Query("*", description="Search query"),
    limit: int = Query(10, description="Max results")
):
    """Memory Inspector: Get memories for transparency"""
    memories = await hindsight_service.recall_all_memories(limit=limit)
    return {
        "status": "success",
        "count": len(memories),
        "memories": memories,
        "demo_mode": True  # Will be false if real API works
    }


@router.get("/timeline")
async def get_memory_timeline(
    user_id: str = Query("anonymous", description="User ID for tracking"),
    limit: int = Query(20, description="Max timeline entries")
):
    """
    🎬 IMPRESSIVE DEMO: Show learning progression timeline with confidence growth.
    
    Returns:
    - Timeline of study sessions with timestamps
    - Confidence scores per topic improving over time
    - Topics studied and recall scores
    - Session-by-session learning growth
    """
    try:
        timeline_payload = await memory_analytics_service.build_timeline(user_id=user_id, limit=limit)
        
        return APIResponse(
            status="success",
            data=timeline_payload,
            demo_mode=False
        )
    except Exception as e:
        print(f"[ERROR] Timeline generation failed: {e}")
        return APIResponse(
            status="error",
            data={
                "message": str(e),
                "timeline": [],
                "topic_confidence_metrics": {}
            }
        )


@router.get("/confidence")
async def get_memory_confidence(
    user_id: str = Query("anonymous", description="User ID for tracking"),
    top_topics: int = Query(5, ge=1, le=12, description="How many top topics to chart"),
    limit: int = Query(120, ge=20, le=400, description="How many memories to analyze"),
):
    """
    Read-only confidence analytics for visualization.
    Additive endpoint; does not modify memory state.
    """
    try:
        payload = await memory_analytics_service.build_confidence_graph(
            user_id=user_id,
            top_topics=top_topics,
            limit=limit,
        )
        return APIResponse(status="success", data=payload, demo_mode=False)
    except Exception as e:
        print(f"[ERROR] Confidence graph generation failed: {e}")
        return APIResponse(
            status="error",
            data={
                "message": str(e),
                "topic_series": [],
                "topic_confidence_metrics": {},
            },
            demo_mode=True,
        )


@router.get("/summary")
async def get_memory_summary(
    user_id: str = Query("anonymous", description="User ID for profile summary"),
    refresh: bool = Query(False, description="Force refresh cached summary"),
):
    """
    Read-only cognitive summary endpoint.
    Uses hindsight-backed analytics + deterministic reflection signals.
    """
    try:
        payload = await memory_analytics_service.build_cognitive_summary(
            user_id=user_id,
            force_refresh=refresh,
        )
        return APIResponse(status="success", data=payload, demo_mode=False)
    except Exception as e:
        print(f"[ERROR] Memory summary generation failed: {e}")
        return APIResponse(
            status="error",
            data={
                "message": str(e),
                "summary": "Unable to generate profile summary at this time.",
                "learning_profile": {},
            },
            demo_mode=True,
        )


@router.get("/what-cogni-knows")
async def get_what_cogni_knows(
    user_id: str = Query("anonymous", description="User ID")
):
    """
    🧠 IMPRESSIVE DEMO: "What Cogni knows about you" - AI-generated insight summary.
    
    Uses Reflect engine to generate an empathetic, personalized summary of:
    - Learning patterns and style
    - Strong and weak topic areas
    - Growth trajectory
    - Recommended focus areas
    - Learning insights
    
    This is the single most impressive visualization for judges - shows the AI
    understands the student as a person, not just processing data.
    """
    try:
        # Get user's learning history
        insights = await hindsight_service.get_user_insights(user_id)
        memories = await hindsight_service.recall_all_memories(limit=30)
        
        if not insights and not memories:
            return APIResponse(
                status="success",
                data={
                    "user_id": user_id,
                    "summary": "No learning history yet. Start studying to build your cognitive profile!",
                    "learning_profile": {}
                },
                demo_mode=True
            )
        
        # Extract learning profile from memories
        topics_studied: Dict[str, Dict[str, Any]] = {}
        learning_patterns = {
            "prefers_step_by_step": 0,
            "prefers_examples": 0,
            "prefers_visual": 0,
            "responds_to_challenges": 0
        }
        
        for memory in memories:
            context = memory.get("context", {}) if isinstance(memory.get("context"), dict) else {}
            topic = context.get("topic") or memory.get("topic") or "general"
            confidence = float(memory.get("confidence", 0.75) or 0.75)
            content = memory.get("content", "").lower()
            
            # Track topics
            if topic not in topics_studied:
                topics_studied[topic] = {
                    "topic": topic,
                    "times_studied": 0,
                    "average_confidence": 0,
                    "recent_confidence": confidence
                }
            
            topics_studied[topic]["times_studied"] += 1
            topics_studied[topic]["recent_confidence"] = confidence
            topics_studied[topic]["average_confidence"] = (
                (topics_studied[topic]["average_confidence"] * (topics_studied[topic]["times_studied"] - 1) +
                 confidence) / topics_studied[topic]["times_studied"]
            )
            
            # Detect learning preferences from content
            if any(p in content for p in ["step", "break down", "step by step", "gradually"]):
                learning_patterns["prefers_step_by_step"] += 1
            if any(p in content for p in ["example", "practical", "demo", "specific case"]):
                learning_patterns["prefers_examples"] += 1
            if any(p in content for p in ["visual", "diagram", "draw", "picture","graph"]):
                learning_patterns["prefers_visual"] += 1
            if any(p in content for p in ["challenge", "hard", "difficult", "edge case"]):
                learning_patterns["responds_to_challenges"] += 1
        
        # Identify strong and weak topics
        strong_topics = sorted(
            [t for t in topics_studied.values() if t["average_confidence"] >= 0.75],
            key=lambda x: x["average_confidence"],
            reverse=True
        )[:5]
        
        weak_topics = sorted(
            [t for t in topics_studied.values() if t["average_confidence"] < 0.75],
            key=lambda x: x["average_confidence"]
        )[:3]
        
        # Determine dominant learning style
        top_pattern = max(learning_patterns, key=learning_patterns.get)
        learning_style_map = {
            "prefers_step_by_step": "Step-by-step methodical learner",
            "prefers_examples": "Example-driven practical learner",
            "prefers_visual": "Visual and diagram-oriented learner",
            "responds_to_challenges": "Challenge-loving ambitious learner"
        }
        learning_style = learning_style_map.get(top_pattern, "Adaptive learner")
        
        # Generate personalized insights using Reflect engine
        reflection_prompt = {
            "topics_studied": len(topics_studied),
            "strong_topics": [t["topic"] for t in strong_topics],
            "weak_topics": [t["topic"] for t in weak_topics],
            "learning_style": learning_style,
            "average_confidence": sum(t["average_confidence"] for t in topics_studied.values()) / len(topics_studied) if topics_studied else 0.5,
            "total_sessions": len(memories)
        }
        
        # Use Reflect to generate empathetic summary (if available)
        ai_summary = ""
        try:
            reflection_analysis = reflection_engine.analyze(
                interaction={
                    "query": f"Summarize learning for {user_id}",
                    "response": "",
                    "engine_used": "memory",
                    "user_id": user_id
                },
                feedback={
                    "understood": True,
                    "confidence": reflection_prompt["average_confidence"],
                    "feedback_text": f"Topics: {', '.join([t['topic'] for t in strong_topics])}. Style: {learning_style}"
                }
            )
            ai_summary = reflection_analysis.get("summary", "") if reflection_analysis else ""
        except Exception as e:
            print(f"[DEBUG] Reflect analysis failed: {e}")
            ai_summary = ""
        
        # Build comprehensive "What Cogni knows about you" summary
        cogni_knows = f"""## **What Cogni Knows About You**

**Learning Profile**: You are a {learning_style.lower()}. Cogni has learned that you respond best to {'step-by-step guidance' if 'Step-by-step' in learning_style else 'real-world examples' if 'Example' in learning_style else 'visual diagrams and illustrations' if 'Visual' in learning_style else 'challenging problems'}.

**Your Strengths**: You've demonstrated strong mastery in {', '.join([t['topic'] for t in strong_topics]) if strong_topics else 'foundational concepts'}. Your average confidence in these areas is {(sum(t['average_confidence'] for t in strong_topics) / len(strong_topics) * 100):.0f}% - keep building on this momentum!

**Growth Opportunity**: Focus on {', '.join([t['topic'] for t in weak_topics]) if weak_topics else 'emerging topics'}. These areas show potential for significant growth.

**Learning Trajectory**: Across {len(memories)} study sessions spanning {len(topics_studied)} topics, you've gathered rich insights about your learning style. Cogni has identified patterns in how you learn best.

**Next Steps**: Based on your strengths and learning style, consider deepening your knowledge in areas adjacent to your strong topics, then tackling the growth opportunities.

{f'**Personal Insight**: {ai_summary}' if ai_summary else ''}"""
        
        return APIResponse(
            status="success",
            data={
                "user_id": user_id,
                "summary": cogni_knows,
                "learning_profile": {
                    "learning_style": learning_style,
                    "strong_topics": [t["topic"] for t in strong_topics],
                    "weak_topics": [t["topic"] for t in weak_topics],
                    "average_confidence": reflection_prompt["average_confidence"],
                    "total_sessions": len(memories),
                    "topics_studied": len(topics_studied),
                    "learning_patterns": [k.replace("prefers_", "").replace("_", " ").title() 
                                         for k, v in learning_patterns.items() if v > 0]
                }
            },
            demo_mode=False
        )
    except Exception as e:
        print(f"[ERROR] What Cogni knows generation failed: {e}")
        import traceback
        traceback.print_exc()
        return APIResponse(
            status="error",
            data={
                "message": str(e),
                "summary": "Unable to generate insights at this time.",
                "learning_profile": {}
            }
        )



@router.post("/summary")
async def generate_conversation_summary(
    request: SummaryRequest
):
    """
    UPGRADE: Generate summary of conversation history.
    
    Handles:
    - Long conversations via chunking
    - Partial summarization per chunk
    - Final summary synthesis
    - Preview extraction for UI
    """
    summary_result = await summary_service.generate_summary(request.conversation)
    
    return {
        "status": "success",
        "data": {
            "preview": summary_result.get("preview", ""),
            "full_summary": summary_result.get("full_summary", ""),
            "demo_mode": summary_result.get("demo_mode", False)
        }
    }


@router.post("/summary/pdf")
async def download_summary_pdf(
    request: PDFRequest
):
    """
    UPGRADE: Download summary as PDF file.
    
    Generates professional PDF report of conversation summary.
    Uses topic name for filename.
    """
    try:
        pdf_bytes = summary_service.generate_pdf(request.summary_text, f"{request.topic_name.replace('_', ' ').title()} - Learning Summary")
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            print("[ERROR] PDF generation returned empty bytes")
            return {
                "status": "error",
                "message": "PDF generation failed - empty output. Try text download instead."
            }
        
        # Return as downloadable PDF
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={request.topic_name}_study_plan.pdf"}
        )
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"PDF generation failed: {str(e)}. Try text download instead."
        }
