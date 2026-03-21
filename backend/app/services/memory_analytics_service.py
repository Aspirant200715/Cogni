from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.engines.reflection_engine import reflection_engine
from app.services.hindsight_service import hindsight_service


class MemoryAnalyticsService:
    """
    Read-only analytics layer over existing memory data.

    Safe guarantees:
    - Does not alter memory ingestion, recall, or scoring pipelines.
    - Uses existing hindsight_service outputs.
    - Exposes deterministic analytics and lightweight caching for summary.
    """

    def __init__(self) -> None:
        self._summary_cache: Dict[str, Dict[str, Any]] = {}

    def _parse_timestamp(self, value: Any) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

        raw = str(value).strip()
        if not raw:
            return datetime.now(timezone.utc)

        cleaned = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(cleaned)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def _merged_context(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        metadata = memory.get("metadata") if isinstance(memory.get("metadata"), dict) else {}
        context = memory.get("context") if isinstance(memory.get("context"), dict) else {}
        merged: Dict[str, Any] = {}
        merged.update(context)
        merged.update(metadata)
        return merged

    def _safe_confidence(self, memory: Dict[str, Any], merged: Dict[str, Any]) -> float:
        for candidate in (
            merged.get("data_confidence"),
            merged.get("confidence"),
            memory.get("confidence"),
        ):
            try:
                if candidate is None:
                    continue
                value = float(candidate)
                return max(0.0, min(1.0, value))
            except Exception:
                continue

        try:
            ratio = merged.get("quiz_score_ratio")
            if ratio is not None:
                value = float(ratio)
                return max(0.0, min(1.0, value))
        except Exception:
            pass

        return 0.65

    def _normalize_topic_label(self, topic: str) -> str:
        cleaned = str(topic or "").strip().lower()
        if not cleaned:
            return "general"

        cleaned = cleaned.replace("_", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"\s+and\s+has\s+encountered\s+confusion.*$", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+has\s+encountered\s+confusion.*$", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s*[:\-]\s*$", "", cleaned).strip()

        if cleaned in {"", "unknown", "none", "null"}:
            return "general"
        return cleaned

    def _extract_topic(self, memory: Dict[str, Any], merged: Dict[str, Any]) -> str:
        content = str(memory.get("content") or memory.get("text") or "")
        topic = str(
            merged.get("topic")
            or merged.get("concept")
            or memory.get("topic")
            or ""
        ).strip().lower()

        if topic and topic not in {"general", "unknown", "none"}:
            return self._normalize_topic_label(topic)

        topic_patterns = [
            r"quiz\s+session\s+on\s+([a-zA-Z0-9_\-\s]{2,60}?)(?:\s+with\s+|\.|,|$)",
            r"on\s+([a-zA-Z0-9_\-\s]{2,60}?)\s+with\s+(?:a\s+)?(?:perfect\s+)?score",
            r"about\s+([a-zA-Z0-9_\-\s]{2,60}?)(?:\.|,|$)",
        ]
        for pattern in topic_patterns:
            match = re.search(pattern, content, flags=re.IGNORECASE)
            if match:
                extracted = match.group(1).strip().lower()
                if extracted and extracted not in {"general", "unknown", "none"}:
                    return self._normalize_topic_label(extracted)

        return "general"

    def _extract_quiz_ratio(self, memory: Dict[str, Any], merged: Dict[str, Any]) -> Optional[float]:
        ratio = merged.get("quiz_score_ratio")
        score = merged.get("quiz_score")
        total = merged.get("quiz_total")
        try:
            if ratio is not None:
                val = float(ratio)
                return max(0.0, min(1.0, val))
            if score is not None and total is not None and float(total) > 0:
                val = float(score) / float(total)
                return max(0.0, min(1.0, val))
        except Exception:
            pass

        content = str(memory.get("content") or memory.get("text") or "")
        score_match = re.search(r"score\s+of\s+(\d+)\s*/\s*(\d+)", content, re.IGNORECASE)
        if not score_match:
            score_match = re.search(r"score\s*:\s*(\d+)\s*/\s*(\d+)", content, re.IGNORECASE)
        if not score_match:
            score_match = re.search(r"score\s+of\s+(\d+)\s+out\s+of\s+(\d+)", content, re.IGNORECASE)
        if not score_match:
            score_match = re.search(r"scor(?:e|ing)\s+(\d+)\s+out\s+of\s+(\d+)", content, re.IGNORECASE)

        if score_match:
            try:
                s_val = float(score_match.group(1))
                t_val = float(score_match.group(2))
                if t_val > 0:
                    val = s_val / t_val
                    return max(0.0, min(1.0, val))
            except Exception:
                return None

        if "perfect score" in content.lower():
            return 1.0

        return None

    def _extract_weak_signals(self, memory: Dict[str, Any], merged: Dict[str, Any]) -> List[str]:
        issues: List[str] = []

        weak_area = str(merged.get("weak_area") or "").strip().lower()
        if weak_area and weak_area not in {"none", "unknown", "general"}:
            issues.append(weak_area)

        mistakes_raw = merged.get("quiz_mistakes")
        if mistakes_raw:
            if isinstance(mistakes_raw, list):
                issues.extend([str(item).strip().lower() for item in mistakes_raw if str(item).strip()])
            elif isinstance(mistakes_raw, str):
                try:
                    parsed = json.loads(mistakes_raw)
                    if isinstance(parsed, list):
                        issues.extend([str(item).strip().lower() for item in parsed if str(item).strip()])
                    elif mistakes_raw.strip():
                        issues.append(mistakes_raw.strip().lower())
                except Exception:
                    if mistakes_raw.strip():
                        issues.append(mistakes_raw.strip().lower())

        content = str(memory.get("content") or memory.get("text") or "")
        weak_match = re.search(r"'([^']{2,120})'\s+as\s+(?:a\s+)?weak\s+area", content, re.IGNORECASE)
        if not weak_match:
            weak_match = re.search(r"mistake\s+related\s+to\s+the\s+'([^']{2,120})'", content, re.IGNORECASE)
        if weak_match:
            issues.append(weak_match.group(1).strip().lower())

        deduped: List[str] = []
        seen = set()
        for issue in issues:
            key = issue.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(issue)
        return deduped

    def _infer_memory_type(self, merged: Dict[str, Any], content: str) -> str:
        memory_type = str(merged.get("type") or "").strip().lower()
        if memory_type:
            return memory_type

        engine_feature = str(merged.get("engine_feature") or "").strip().lower()
        if engine_feature:
            return engine_feature

        content_lower = content.lower()
        if "quiz" in content_lower:
            return "quiz_session"
        if "feedback" in content_lower:
            return "feedback_reflection"
        if "shadow" in content_lower:
            return "shadow"
        if "resonance" in content_lower:
            return "resonance"
        return "study_session"

    def _infer_source(self, merged: Dict[str, Any], memory_type: str) -> str:
        source = str(merged.get("engine_feature") or "").strip().lower()
        if source:
            return source

        if "quiz" in memory_type:
            return "study_routes"
        if "feedback" in memory_type:
            return "feedback_routes"
        if "shadow" in memory_type:
            return "shadow_engine"
        if "resonance" in memory_type:
            return "resonance_engine"
        if "archaeology" in memory_type:
            return "archaeology_engine"
        return "memory"

    async def _get_user_memories(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        memories = await hindsight_service.recall_all_memories(limit=limit, user_id=user_id)
        return [m for m in memories if isinstance(m, dict)]

    async def build_timeline(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        memories = await self._get_user_memories(user_id, max(10, min(250, limit)))

        timeline: List[Dict[str, Any]] = []
        for idx, memory in enumerate(memories):
            merged = self._merged_context(memory)
            content = str(memory.get("content") or memory.get("text") or "")
            timestamp_raw = (
                memory.get("timestamp")
                or memory.get("occurred_end")
                or memory.get("mentioned_at")
            )
            timestamp = self._parse_timestamp(timestamp_raw)

            topic = str(
                merged.get("topic")
                or merged.get("concept")
                or memory.get("topic")
                or "general"
            ).strip().lower() or "general"

            memory_type = self._infer_memory_type(merged, content)
            source = self._infer_source(merged, memory_type)
            confidence = self._safe_confidence(memory, merged)

            timeline.append(
                {
                    "session_id": idx + 1,
                    "timestamp": timestamp.isoformat(),
                    "type": memory_type,
                    "source": source,
                    "topic": topic,
                    "confidence": confidence,
                    "content_preview": content[:140],
                }
            )

        timeline.sort(key=lambda row: row["timestamp"], reverse=True)

        # Backward-compatible topic metrics payload expected by existing UI paths.
        confidence_data = await self.build_confidence_graph(user_id=user_id, top_topics=5, limit=max(60, limit * 2))
        topic_confidence_metrics = confidence_data.get("topic_confidence_metrics", {})

        return {
            "user_id": user_id,
            "timeline": timeline,
            "total_sessions": len(timeline),
            "total_topics": len({str(item.get("topic", "general")) for item in timeline}),
            "topic_confidence_metrics": topic_confidence_metrics,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def build_confidence_graph(self, user_id: str, top_topics: int = 5, limit: int = 120) -> Dict[str, Any]:
        memories = await self._get_user_memories(user_id, max(20, min(400, limit)))

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        topic_quiz_ratios: Dict[str, List[float]] = {}
        topic_weak_signals: Dict[str, int] = {}
        topic_mastery_signal: Dict[str, List[float]] = {}
        seen_memory_points = set()
        seen_quiz_points = set()

        for memory in memories:
            merged = self._merged_context(memory)
            topic = self._extract_topic(memory, merged)

            timestamp_raw = (
                memory.get("timestamp")
                or memory.get("occurred_end")
                or memory.get("mentioned_at")
            )
            timestamp = self._parse_timestamp(timestamp_raw)
            confidence = self._safe_confidence(memory, merged)
            quiz_ratio = self._extract_quiz_ratio(memory, merged)
            weak_signals = self._extract_weak_signals(memory, merged)
            memory_point_key = f"{topic}|{timestamp.isoformat()}"
            if memory_point_key in seen_memory_points:
                continue
            seen_memory_points.add(memory_point_key)

            grouped.setdefault(topic, []).append(
                {
                    "timestamp": timestamp.isoformat(),
                    "confidence": confidence,
                    "sort_key": timestamp,
                }
            )

            topic_mastery_signal.setdefault(topic, []).append(confidence)

            if quiz_ratio is not None:
                quiz_point_key = f"{topic}|{timestamp.isoformat()}|{round(float(quiz_ratio), 3)}"
                if quiz_point_key in seen_quiz_points:
                    continue
                seen_quiz_points.add(quiz_point_key)

                topic_quiz_ratios.setdefault(topic, []).append(quiz_ratio)
                topic_mastery_signal[topic].append(quiz_ratio)
                if quiz_ratio <= 0.67:
                    topic_weak_signals[topic] = topic_weak_signals.get(topic, 0) + 1

            if weak_signals:
                topic_weak_signals[topic] = topic_weak_signals.get(topic, 0) + len(weak_signals)

        ranked_topics = sorted(
            grouped.items(),
            key=lambda item: (len(item[1]), max(point["sort_key"] for point in item[1])),
            reverse=True,
        )

        # If we have specific topics, suppress the generic bucket for clearer student analysis.
        has_specific_topics = any(topic != "general" for topic, _ in ranked_topics)
        if has_specific_topics:
            ranked_topics = [item for item in ranked_topics if item[0] != "general"]

        ranked_topics = ranked_topics[: max(1, top_topics)]

        topic_series: List[Dict[str, Any]] = []
        topic_confidence_metrics: Dict[str, Dict[str, Any]] = {}
        for topic, points in ranked_topics:
            ordered = sorted(points, key=lambda p: p["sort_key"])
            normalized_points = [
                {
                    "session_index": idx + 1,
                    "timestamp": p["timestamp"],
                    "confidence": p["confidence"],
                }
                for idx, p in enumerate(ordered)
            ]

            initial = normalized_points[0]["confidence"]
            current = normalized_points[-1]["confidence"]
            avg = sum(p["confidence"] for p in normalized_points) / len(normalized_points)
            improvement = current - initial
            quiz_values = topic_quiz_ratios.get(topic, [])
            avg_quiz_ratio = (sum(quiz_values) / len(quiz_values)) if quiz_values else None
            mastery_values = topic_mastery_signal.get(topic, [avg])
            mastery_score = sum(mastery_values) / len(mastery_values) if mastery_values else avg
            weak_signal_count = int(topic_weak_signals.get(topic, 0))
            performance_label = (
                "mastering"
                if mastery_score >= 0.78 and weak_signal_count == 0
                else "needs_attention"
                if mastery_score < 0.62 or weak_signal_count >= 2
                else "developing"
            )

            topic_series.append(
                {
                    "topic": topic,
                    "sessions_studied": len(normalized_points),
                    "initial_confidence": round(initial, 3),
                    "current_confidence": round(current, 3),
                    "average_confidence": round(avg, 3),
                    "improvement": round(improvement, 3),
                    "avg_quiz_score_ratio": round(avg_quiz_ratio, 3) if avg_quiz_ratio is not None else None,
                    "mastery_score": round(max(0.0, min(1.0, mastery_score)), 3),
                    "weak_signal_count": weak_signal_count,
                    "performance_label": performance_label,
                    "points": normalized_points,
                }
            )

            topic_confidence_metrics[topic] = {
                "initial_confidence": round(initial, 3),
                "current_confidence": round(current, 3),
                "improvement": round(improvement, 3),
                "average_confidence": round(avg, 3),
                "sessions_studied": len(normalized_points),
                "confidence_trajectory": normalized_points[-5:],
                "avg_quiz_score_ratio": round(avg_quiz_ratio, 3) if avg_quiz_ratio is not None else None,
                "mastery_score": round(max(0.0, min(1.0, mastery_score)), 3),
                "weak_signal_count": weak_signal_count,
                "performance_label": performance_label,
            }

        top_strengths = [
            row.get("topic")
            for row in sorted(topic_series, key=lambda x: float(x.get("mastery_score", 0.0)), reverse=True)
            if float(row.get("mastery_score", 0.0)) >= 0.75
        ][:4]
        top_weaknesses = [
            row.get("topic")
            for row in sorted(
                topic_series,
                key=lambda x: (
                    int(x.get("weak_signal_count", 0)),
                    -float(x.get("mastery_score", 0.0)),
                ),
                reverse=True,
            )
            if int(row.get("weak_signal_count", 0)) > 0 or float(row.get("mastery_score", 1.0)) < 0.65
        ][:4]

        all_quiz_values: List[float] = []
        for vals in topic_quiz_ratios.values():
            all_quiz_values.extend(vals)

        performance_overview = {
            "topics_tracked": len(topic_series),
            "strength_topics": top_strengths,
            "focus_topics": top_weaknesses,
            "avg_quiz_score_ratio": round(sum(all_quiz_values) / len(all_quiz_values), 3) if all_quiz_values else None,
            "total_quiz_attempts": len(all_quiz_values),
        }

        return {
            "user_id": user_id,
            "topic_series": topic_series,
            "topic_confidence_metrics": topic_confidence_metrics,
            "performance_overview": performance_overview,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def build_cognitive_summary(self, user_id: str, force_refresh: bool = False, limit: int = 120) -> Dict[str, Any]:
        memories = await self._get_user_memories(user_id, max(30, min(400, limit)))
        confidence_data = await self.build_confidence_graph(user_id=user_id, top_topics=6, limit=limit)
        topic_series = confidence_data.get("topic_series", []) if isinstance(confidence_data, dict) else []

        latest_timestamp = ""
        if memories:
            latest_timestamp = max(
                str(
                    memory.get("timestamp")
                    or memory.get("occurred_end")
                    or memory.get("mentioned_at")
                    or ""
                )
                for memory in memories
            )

        cache_signature = f"{len(memories)}|{latest_timestamp}"
        cache_entry = self._summary_cache.get(user_id)
        if (
            not force_refresh
            and cache_entry
            and cache_entry.get("signature") == cache_signature
            and isinstance(cache_entry.get("payload"), dict)
        ):
            cached_payload = dict(cache_entry["payload"])
            cached_payload["cache"] = {
                "hit": True,
                "signature": cache_signature,
                "generated_at": cache_entry.get("generated_at"),
            }
            return cached_payload

        strengths = [
            str(item.get("topic"))
            for item in sorted(topic_series, key=lambda x: float(x.get("mastery_score", x.get("current_confidence", 0.0))), reverse=True)
            if float(item.get("mastery_score", item.get("current_confidence", 0.0))) >= 0.75
        ][:4]
        weaknesses = [
            str(item.get("topic"))
            for item in sorted(
                topic_series,
                key=lambda x: (
                    int(x.get("weak_signal_count", 0)),
                    -float(x.get("mastery_score", x.get("current_confidence", 1.0))),
                ),
                reverse=True,
            )
            if int(item.get("weak_signal_count", 0)) > 0 or float(item.get("mastery_score", item.get("current_confidence", 1.0))) < 0.6
        ][:4]
        interests = [str(item.get("topic")) for item in topic_series[:4]]

        patterns: List[str] = []
        if topic_series:
            improving_topics = [
                str(item.get("topic"))
                for item in topic_series
                if float(item.get("improvement", 0.0)) > 0.05
            ]
            if improving_topics:
                patterns.append(
                    f"Confidence is increasing in: {', '.join(improving_topics[:3])}."
                )

            repeated_focus = [
                str(item.get("topic"))
                for item in topic_series
                if int(item.get("sessions_studied", 0)) >= 3
            ]
            if repeated_focus:
                patterns.append(
                    f"You revisit these topics consistently: {', '.join(repeated_focus[:3])}."
                )

            high_quiz_topics = [
                str(item.get("topic"))
                for item in topic_series
                if isinstance(item.get("avg_quiz_score_ratio"), (int, float)) and float(item.get("avg_quiz_score_ratio")) >= 0.8
            ]
            if high_quiz_topics:
                patterns.append(
                    f"Quiz performance is strongest in: {', '.join(high_quiz_topics[:3])}."
                )

        insights = await hindsight_service.get_user_insights(user_id)
        if insights:
            patterns.append(f"Cogni has stored {len(insights)} structured insight signals for your learning behavior.")

        average_confidence = (
            sum(float(item.get("average_confidence", 0.0)) for item in topic_series) / len(topic_series)
            if topic_series
            else 0.0
        )

        reflect_signals = reflection_engine.analyze(
            interaction={
                "query": f"Summarize learning profile for {user_id}",
                "response": "",
                "engine_used": "memory_analytics",
                "user_id": user_id,
            },
            feedback={
                "understood": True,
                "confidence": max(0.0, min(1.0, average_confidence)),
                "feedback_text": f"Strengths: {', '.join(strengths) if strengths else 'none'}. Weaknesses: {', '.join(weaknesses) if weaknesses else 'none'}.",
            },
        )

        summary_lines = ["What Cogni Knows About You"]
        summary_lines.append(
            f"- Sessions analyzed: {len(memories)}"
        )
        summary_lines.append(
            f"- Topics tracked: {len(topic_series)}"
        )
        summary_lines.append(
            f"- Strengths: {', '.join(strengths) if strengths else 'still emerging'}"
        )
        summary_lines.append(
            f"- Growth areas: {', '.join(weaknesses) if weaknesses else 'no major weak trend detected'}"
        )
        summary_lines.append(
            f"- Interests: {', '.join(interests) if interests else 'insufficient data yet'}"
        )
        if patterns:
            summary_lines.append(f"- Patterns: {' '.join(patterns[:3])}")

        total_quiz_attempts = sum(
            1
            for item in topic_series
            if isinstance(item.get("avg_quiz_score_ratio"), (int, float))
        )
        if total_quiz_attempts > 0:
            quiz_mean = sum(
                float(item.get("avg_quiz_score_ratio", 0.0))
                for item in topic_series
                if isinstance(item.get("avg_quiz_score_ratio"), (int, float))
            ) / max(1, total_quiz_attempts)
            summary_lines.append(
                f"- Student performance snapshot: average quiz score trend is {round(quiz_mean * 100)}% across tracked topics."
            )

        payload: Dict[str, Any] = {
            "user_id": user_id,
            "summary": "\n".join(summary_lines),
            "learning_profile": {
                "strengths": strengths,
                "weaknesses": weaknesses,
                "interests": interests,
                "patterns": patterns[:5],
                "average_confidence": round(average_confidence, 3),
                "total_sessions": len(memories),
                "topics_studied": len(topic_series),
            },
            "reflect_signals": reflect_signals,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        self._summary_cache[user_id] = {
            "signature": cache_signature,
            "generated_at": payload["generated_at"],
            "payload": payload,
        }

        payload["cache"] = {
            "hit": False,
            "signature": cache_signature,
            "generated_at": payload["generated_at"],
        }
        return payload


memory_analytics_service = MemoryAnalyticsService()
