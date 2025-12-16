"""
Latency Metrics Model
=====================

MongoDB model for storing and retrieving connection latency metrics.
Used for contextualizing engagement analysis during live Zoom sessions.

The latency metrics help avoid misclassifying students with poor network
conditions as disengaged, improving fairness and reliability of analytics.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

# Import database connection
from src.database.connection import get_database


class LatencyMetric(BaseModel):
    """Individual latency measurement"""
    rtt_ms: float = Field(..., description="Round-trip time in milliseconds")
    jitter_ms: float = Field(default=0, description="Jitter in milliseconds")
    packet_loss_percent: float = Field(default=0, description="Estimated packet loss")
    quality: str = Field(default="good", description="Connection quality assessment")
    timestamp: datetime = Field(default_factory=datetime.now)


class StudentLatencyProfile(BaseModel):
    """Aggregated latency profile for a student in a session"""
    session_id: str
    student_id: str
    student_name: Optional[str] = None
    
    # Aggregated metrics
    avg_rtt_ms: float = 0
    min_rtt_ms: float = 0
    max_rtt_ms: float = 0
    avg_jitter_ms: float = 0
    
    # Quality assessment
    overall_quality: str = "good"  # excellent, good, fair, poor, critical
    stability_score: float = 100  # 0-100
    
    # Engagement adjustment factor (1.0 = no adjustment, <1.0 = reduce engagement penalty)
    engagement_adjustment_factor: float = 1.0
    
    # Historical data
    samples_count: int = 0
    recent_samples: List[LatencyMetric] = []
    
    # Timestamps
    first_measured: Optional[datetime] = None
    last_measured: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LatencyMetricsModel:
    """MongoDB operations for latency metrics"""
    
    COLLECTION_NAME = "latency_metrics"
    
    @classmethod
    async def get_collection(cls):
        """Get the MongoDB collection"""
        db = await get_database()
        return db[cls.COLLECTION_NAME]
    
    @classmethod
    async def save_metric(
        cls,
        session_id: str,
        student_id: str,
        rtt_ms: float,
        jitter_ms: float = 0,
        packet_loss_percent: float = 0,
        student_name: Optional[str] = None
    ) -> Dict:
        """
        Save a new latency metric and update the student's profile.
        
        Returns the updated profile with engagement adjustment factor.
        """
        collection = await cls.get_collection()
        now = datetime.now()
        
        # Create the metric
        metric = LatencyMetric(
            rtt_ms=rtt_ms,
            jitter_ms=jitter_ms,
            packet_loss_percent=packet_loss_percent,
            quality=cls._assess_quality(rtt_ms, jitter_ms),
            timestamp=now
        )
        
        # Find existing profile
        profile = await collection.find_one({
            "session_id": session_id,
            "student_id": student_id
        })
        
        if profile:
            # Update existing profile
            recent_samples = profile.get("recent_samples", [])
            recent_samples.append(metric.model_dump())
            
            # Keep only last 50 samples
            if len(recent_samples) > 50:
                recent_samples = recent_samples[-50:]
            
            # Recalculate aggregates
            rtt_values = [s["rtt_ms"] for s in recent_samples]
            jitter_values = [s["jitter_ms"] for s in recent_samples]
            
            avg_rtt = sum(rtt_values) / len(rtt_values)
            avg_jitter = sum(jitter_values) / len(jitter_values) if jitter_values else 0
            
            # Calculate engagement adjustment factor
            adjustment_factor = cls._calculate_adjustment_factor(avg_rtt, avg_jitter)
            
            # Calculate stability score
            stability_score = cls._calculate_stability_score(rtt_values, jitter_values)
            
            await collection.update_one(
                {"_id": profile["_id"]},
                {
                    "$set": {
                        "avg_rtt_ms": round(avg_rtt, 2),
                        "min_rtt_ms": round(min(rtt_values), 2),
                        "max_rtt_ms": round(max(rtt_values), 2),
                        "avg_jitter_ms": round(avg_jitter, 2),
                        "overall_quality": cls._assess_quality(avg_rtt, avg_jitter),
                        "stability_score": round(stability_score, 2),
                        "engagement_adjustment_factor": round(adjustment_factor, 3),
                        "samples_count": len(recent_samples),
                        "recent_samples": recent_samples,
                        "last_measured": now,
                        "updated_at": now
                    }
                }
            )
        else:
            # Create new profile
            adjustment_factor = cls._calculate_adjustment_factor(rtt_ms, jitter_ms)
            stability_score = cls._calculate_stability_score([rtt_ms], [jitter_ms])
            
            new_profile = StudentLatencyProfile(
                session_id=session_id,
                student_id=student_id,
                student_name=student_name,
                avg_rtt_ms=round(rtt_ms, 2),
                min_rtt_ms=round(rtt_ms, 2),
                max_rtt_ms=round(rtt_ms, 2),
                avg_jitter_ms=round(jitter_ms, 2),
                overall_quality=cls._assess_quality(rtt_ms, jitter_ms),
                stability_score=round(stability_score, 2),
                engagement_adjustment_factor=round(adjustment_factor, 3),
                samples_count=1,
                recent_samples=[metric],
                first_measured=now,
                last_measured=now
            )
            
            await collection.insert_one(new_profile.model_dump())
        
        # Return updated profile
        return await cls.get_profile(session_id, student_id)
    
    @classmethod
    async def get_profile(cls, session_id: str, student_id: str) -> Optional[Dict]:
        """Get a student's latency profile for a session"""
        collection = await cls.get_collection()
        profile = await collection.find_one({
            "session_id": session_id,
            "student_id": student_id
        })
        
        if profile:
            profile["_id"] = str(profile["_id"])
        
        return profile
    
    @classmethod
    async def get_engagement_adjustment(cls, session_id: str, student_id: str) -> float:
        """
        Get the engagement adjustment factor for a student.
        
        Returns a value between 0 and 1:
        - 1.0: No adjustment needed (good connection)
        - <1.0: Reduce engagement penalty (poor connection)
        - 0.5: Maximum adjustment (critical connection)
        
        This factor should be applied when calculating engagement scores
        to avoid penalizing students with connectivity issues.
        """
        profile = await cls.get_profile(session_id, student_id)
        
        if not profile:
            return 1.0  # No data, assume good connection
        
        return profile.get("engagement_adjustment_factor", 1.0)
    
    @classmethod
    async def get_session_summary(cls, session_id: str) -> Dict:
        """Get latency summary for all students in a session"""
        collection = await cls.get_collection()
        
        cursor = collection.find({"session_id": session_id})
        profiles = await cursor.to_list(length=None)
        
        if not profiles:
            return {
                "session_id": session_id,
                "total_students": 0,
                "quality_distribution": {},
                "students_needing_attention": [],
                "average_rtt_ms": 0,
                "average_stability_score": 100
            }
        
        quality_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "critical": 0}
        students_needing_attention = []
        
        for profile in profiles:
            quality = profile.get("overall_quality", "good")
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
            if quality in ["poor", "critical"]:
                students_needing_attention.append({
                    "student_id": profile["student_id"],
                    "student_name": profile.get("student_name"),
                    "quality": quality,
                    "avg_rtt_ms": profile.get("avg_rtt_ms", 0),
                    "adjustment_factor": profile.get("engagement_adjustment_factor", 1.0)
                })
        
        avg_rtt = sum(p.get("avg_rtt_ms", 0) for p in profiles) / len(profiles)
        avg_stability = sum(p.get("stability_score", 100) for p in profiles) / len(profiles)
        
        return {
            "session_id": session_id,
            "total_students": len(profiles),
            "quality_distribution": quality_counts,
            "students_needing_attention": students_needing_attention,
            "average_rtt_ms": round(avg_rtt, 2),
            "average_stability_score": round(avg_stability, 2)
        }
    
    @classmethod
    async def clear_session_data(cls, session_id: str) -> int:
        """Clear all latency data for a session"""
        collection = await cls.get_collection()
        result = await collection.delete_many({"session_id": session_id})
        return result.deleted_count
    
    @classmethod
    def _assess_quality(cls, rtt_ms: float, jitter_ms: float = 0) -> str:
        """Assess connection quality based on RTT and jitter"""
        # RTT thresholds
        if rtt_ms < 50:
            rtt_quality = "excellent"
        elif rtt_ms < 100:
            rtt_quality = "good"
        elif rtt_ms < 200:
            rtt_quality = "fair"
        elif rtt_ms < 500:
            rtt_quality = "poor"
        else:
            rtt_quality = "critical"
        
        # Jitter thresholds
        if jitter_ms < 10:
            jitter_quality = "excellent"
        elif jitter_ms < 30:
            jitter_quality = "good"
        elif jitter_ms < 50:
            jitter_quality = "fair"
        elif jitter_ms < 100:
            jitter_quality = "poor"
        else:
            jitter_quality = "critical"
        
        # Return the worse of the two
        quality_order = ["excellent", "good", "fair", "poor", "critical"]
        return quality_order[max(quality_order.index(rtt_quality), quality_order.index(jitter_quality))]
    
    @classmethod
    def _calculate_adjustment_factor(cls, avg_rtt: float, avg_jitter: float) -> float:
        """
        Calculate the engagement adjustment factor.
        
        Poor connections should not be penalized in engagement analysis.
        This factor reduces the impact of engagement penalties for students
        with connectivity issues.
        """
        quality = cls._assess_quality(avg_rtt, avg_jitter)
        
        # Adjustment factors based on connection quality
        adjustment_map = {
            "excellent": 1.0,    # No adjustment
            "good": 1.0,         # No adjustment
            "fair": 0.85,        # 15% reduction in penalty
            "poor": 0.7,         # 30% reduction in penalty
            "critical": 0.5      # 50% reduction in penalty
        }
        
        return adjustment_map.get(quality, 1.0)
    
    @classmethod
    def _calculate_stability_score(cls, rtt_values: List[float], jitter_values: List[float]) -> float:
        """Calculate connection stability score (0-100)"""
        if not rtt_values:
            return 100
        
        avg_rtt = sum(rtt_values) / len(rtt_values)
        avg_jitter = sum(jitter_values) / len(jitter_values) if jitter_values else 0
        
        # RTT score (higher RTT = lower score)
        rtt_score = max(0, 100 - (avg_rtt / 5))
        
        # Jitter score (higher jitter = lower score)
        jitter_score = max(0, 100 - (avg_jitter * 2))
        
        # Variability score (high variance in RTT = unstable)
        if len(rtt_values) > 1:
            variance = sum((x - avg_rtt) ** 2 for x in rtt_values) / len(rtt_values)
            std_dev = variance ** 0.5
            variability_score = max(0, 100 - (std_dev / 2))
        else:
            variability_score = 100
        
        # Weighted combination
        return (rtt_score * 0.4 + jitter_score * 0.3 + variability_score * 0.3)

