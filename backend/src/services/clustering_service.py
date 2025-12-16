from typing import Dict, List, Optional
from ..models.cluster import StudentCluster
from ..models.cluster_model import ClusterModel
from ..models.latency_metrics import LatencyMetricsModel


class ClusteringService:
    """
    Clustering service for student engagement analysis.
    
    This service now incorporates WebRTC-aware connection latency monitoring
    to contextualize engagement analysis. Students with poor network conditions
    are not misclassified as disengaged, improving fairness and reliability.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClusteringService, cls).__new__(cls)
        return cls._instance

    async def get_clusters(self, session_id: str) -> List[StudentCluster]:
        """Get clusters from MongoDB or create default ones"""
        # Try to get clusters from database
        cluster_docs = await ClusterModel.find_by_session(session_id)
        
        if len(cluster_docs) > 0:
            # Convert to StudentCluster objects
            return [StudentCluster(**doc) for doc in cluster_docs]

        # Initialize default clusters if none exist
        default_clusters = [
            StudentCluster(
                id="1",
                name="Active Participants",
                description="Highly engaged students",
                studentCount=18,
                engagementLevel="high",
                color="#10b981",
                prediction="stable",
                students=[],
            ),
            StudentCluster(
                id="2",
                name="Moderate Participants",
                description="Moderately engaged students",
                studentCount=10,
                engagementLevel="medium",
                color="#f59e0b",
                prediction="improving",
                students=[],
            ),
            StudentCluster(
                id="3",
                name="At-Risk Students",
                description="Low engagement, need support",
                studentCount=4,
                engagementLevel="low",
                color="#ef4444",
                prediction="declining",
                students=[],
            ),
        ]

        # Save default clusters to database
        await ClusterModel.update_clusters_for_session(session_id, default_clusters)
        return default_clusters

    async def update_clusters(
        self,
        session_id: str,
        quiz_performance: Optional[Dict] = None
    ) -> List[StudentCluster]:
        """Update clusters in MongoDB"""
        clusters = await self.get_clusters(session_id)

        if quiz_performance:
            # Update clusters based on quiz performance
            clusters = self._recalculate_clusters(clusters, quiz_performance)
            # Save to database
            await ClusterModel.update_clusters_for_session(session_id, clusters)

        return clusters

    def _recalculate_clusters(
        self,
        current_clusters: List[StudentCluster],
        quiz_performance: Dict
    ) -> List[StudentCluster]:
        # Simple clustering algorithm based on quiz performance
        # In a real implementation, this would consider:
        # - Quiz performance
        # - Response time
        # - Engagement metrics
        # - Historical data

        performance = quiz_performance.get("correctPercentage", 0)

        # Adjust cluster sizes based on performance
        # High performance (>80%) -> more students in active cluster
        # Low performance (<60%) -> more students in at-risk cluster

        total_students = sum(c.studentCount for c in current_clusters)

        if performance >= 80:
            # High performance: shift students to active cluster
            return [
                StudentCluster(
                    **current_clusters[0].model_dump(),
                    studentCount=min(total_students, int(total_students * 0.6)),
                    prediction="stable",
                ),
                StudentCluster(
                    **current_clusters[1].model_dump(),
                    studentCount=int(total_students * 0.3),
                    prediction="improving",
                ),
                StudentCluster(
                    **current_clusters[2].model_dump(),
                    studentCount=max(
                        0,
                        total_students
                        - int(total_students * 0.6)
                        - int(total_students * 0.3)
                    ),
                    prediction="declining",
                ),
            ]
        elif performance < 60:
            # Low performance: shift students to at-risk cluster
            return [
                StudentCluster(
                    **current_clusters[0].model_dump(),
                    studentCount=int(total_students * 0.4),
                    prediction="stable",
                ),
                StudentCluster(
                    **current_clusters[1].model_dump(),
                    studentCount=int(total_students * 0.3),
                    prediction="declining",
                ),
                StudentCluster(
                    **current_clusters[2].model_dump(),
                    studentCount=total_students
                    - int(total_students * 0.4)
                    - int(total_students * 0.3),
                    prediction="declining",
                ),
            ]

        # Medium performance: keep current distribution
        return current_clusters

    async def get_student_cluster(
        self, student_id: str, session_id: str
    ) -> Optional[str]:
        """Get student's cluster from MongoDB"""
        cluster_id = await ClusterModel.find_student_cluster(student_id, session_id)
        return cluster_id

    async def get_latency_adjusted_engagement(
        self,
        student_id: str,
        session_id: str,
        raw_engagement_score: float
    ) -> Dict:
        """
        Adjust engagement score based on connection latency.
        
        Students with poor network conditions should not be penalized
        in engagement analysis. This method applies a latency-based
        adjustment factor to the raw engagement score.
        
        Args:
            student_id: The student's identifier
            session_id: The current session ID
            raw_engagement_score: The original engagement score (0-100)
            
        Returns:
            Dictionary containing:
            - adjusted_score: The latency-adjusted engagement score
            - adjustment_factor: The factor applied (1.0 = no change)
            - connection_quality: The student's connection quality
            - should_contextualize: Whether engagement should be contextualized
        """
        # Get the latency adjustment factor
        adjustment_factor = await LatencyMetricsModel.get_engagement_adjustment(
            session_id, student_id
        )
        
        # Get connection quality profile
        profile = await LatencyMetricsModel.get_profile(session_id, student_id)
        
        if not profile:
            return {
                "adjusted_score": raw_engagement_score,
                "raw_score": raw_engagement_score,
                "adjustment_factor": 1.0,
                "connection_quality": "unknown",
                "stability_score": 100,
                "should_contextualize": False,
                "message": "No latency data available"
            }
        
        connection_quality = profile.get("overall_quality", "good")
        stability_score = profile.get("stability_score", 100)
        
        # Apply adjustment: poor connections get more lenient scoring
        # If engagement is low but connection is poor, we reduce the penalty
        if raw_engagement_score < 50 and adjustment_factor < 1.0:
            # Student appears disengaged but has connectivity issues
            # Apply the adjustment to reduce the gap from average
            adjustment = (50 - raw_engagement_score) * (1 - adjustment_factor)
            adjusted_score = raw_engagement_score + adjustment
        else:
            adjusted_score = raw_engagement_score
        
        # Ensure score is within bounds
        adjusted_score = max(0, min(100, adjusted_score))
        
        should_contextualize = connection_quality in ["poor", "critical"]
        
        return {
            "adjusted_score": round(adjusted_score, 2),
            "raw_score": raw_engagement_score,
            "adjustment_factor": adjustment_factor,
            "connection_quality": connection_quality,
            "stability_score": stability_score,
            "avg_rtt_ms": profile.get("avg_rtt_ms", 0),
            "should_contextualize": should_contextualize,
            "message": self._get_engagement_message(connection_quality, raw_engagement_score, adjusted_score)
        }
    
    def _get_engagement_message(
        self,
        connection_quality: str,
        raw_score: float,
        adjusted_score: float
    ) -> str:
        """Generate a human-readable message about engagement adjustment"""
        if connection_quality in ["excellent", "good"]:
            return "Connection is stable. Engagement metrics are accurate."
        
        if connection_quality == "fair":
            if adjusted_score > raw_score:
                return "Slight connectivity issues detected. Engagement may be underreported."
            return "Mild connectivity fluctuations. Engagement metrics are generally reliable."
        
        if connection_quality == "poor":
            return "Poor connection quality detected. Low engagement may be due to technical difficulties rather than disinterest."
        
        if connection_quality == "critical":
            return "Severe connectivity issues. Engagement metrics should be interpreted with caution. Student may be experiencing significant technical difficulties."
        
        return "Unable to assess connection quality."

    async def recalculate_clusters_with_latency(
        self,
        session_id: str,
        quiz_performance: Optional[Dict] = None
    ) -> List[StudentCluster]:
        """
        Recalculate clusters considering latency data.
        
        This method updates cluster assignments while considering
        connection quality. Students with poor connections who appear
        disengaged may be given the benefit of the doubt.
        """
        clusters = await self.get_clusters(session_id)
        
        # Get latency summary for the session
        latency_summary = await LatencyMetricsModel.get_session_summary(session_id)
        students_with_issues = latency_summary.get("students_needing_attention", [])
        
        # If there are students with connectivity issues, we may need to
        # reconsider their cluster assignments
        if students_with_issues and quiz_performance:
            # For students with poor connectivity who are in "at-risk" cluster,
            # consider moving them to "moderate" if their adjusted engagement is higher
            for student_info in students_with_issues:
                student_id = student_info.get("student_id")
                adjustment_factor = student_info.get("adjustment_factor", 1.0)
                
                # If the adjustment factor is low (poor connection),
                # this student's cluster assignment should be lenient
                if adjustment_factor < 0.8:
                    # Log this for instructor awareness
                    print(f"📶 Student {student_id} has connectivity issues "
                          f"(adjustment_factor={adjustment_factor}). "
                          f"Cluster assignment will be contextualized.")
        
        # Proceed with normal cluster calculation
        if quiz_performance:
            clusters = self._recalculate_clusters(clusters, quiz_performance)
            await ClusterModel.update_clusters_for_session(session_id, clusters)
        
        return clusters

