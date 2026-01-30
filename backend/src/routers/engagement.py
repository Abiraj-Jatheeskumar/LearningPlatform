"""
Engagement Prediction and Adaptive Scheduling API
Endpoints for ML-based student engagement classification
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from ..middleware.auth import get_current_user, require_instructor
from ..services.engagement_predictor import get_engagement_predictor
from ..services.adaptive_scheduler import get_adaptive_scheduler

router = APIRouter(prefix="/api/engagement", tags=["engagement"])


class PredictionRequest(BaseModel):
    """Request for engagement prediction"""
    is_correct: bool
    response_time_sec: float = Field(..., gt=0, le=300)
    rtt_ms: float = Field(..., ge=0, le=1000)
    question_difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    expected_time_sec: float = Field(default=30.0, gt=0, le=300)
    network_quality: str = Field(default="Good", pattern="^(Poor|Good|Fair|Excellent)$")


class PredictionResponse(BaseModel):
    """Response with engagement prediction"""
    engagement_level: str
    confidence: float
    probabilities: Dict[str, float]


class StudentEngagementStats(BaseModel):
    """Student engagement statistics"""
    student_id: str
    engagement_level: str
    questions_sent: int
    questions_answered: int
    accuracy: float
    last_rtt: float
    engagement_history: List[str]


@router.post("/predict", response_model=PredictionResponse)
async def predict_engagement(
    request: PredictionRequest,
    user: dict = Depends(get_current_user)
):
    """
    Predict student engagement level using ML model
    
    - **Active**: Highly engaged, needs fewer questions
    - **Moderate**: Moderately engaged, regular frequency
    - **Passive**: Low engagement, needs more frequent questions
    """
    try:
        predictor = get_engagement_predictor()
        
        if not predictor.model_loaded:
            raise HTTPException(
                status_code=503,
                detail="Engagement model not loaded. Please add model file to ml_models directory."
            )
        
        engagement_level, confidence, probabilities = predictor.predict_from_system_data(
            is_correct=request.is_correct,
            response_time=request.response_time_sec,
            rtt_ms=request.rtt_ms,
            question_difficulty=request.question_difficulty,
            expected_time=request.expected_time_sec,
            network_quality=request.network_quality
        )
        
        return PredictionResponse(
            engagement_level=engagement_level,
            confidence=confidence,
            probabilities=probabilities
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/model-info")
async def get_model_info(user: dict = Depends(get_current_user)):
    """Get information about the engagement prediction model"""
    predictor = get_engagement_predictor()
    
    if not predictor.model_loaded:
        return {
            "model_loaded": False,
            "message": "Model not loaded. Please add engagement_xgb_hybrid_clean.joblib to ml_models directory."
        }
    
    return {
        "model_loaded": True,
        "model_type": "XGBoost Classifier",
        "accuracy": "99.77%",
        "classes": ["Active", "Moderate", "Passive"],
        "features_count": len(predictor.feature_columns) if predictor.feature_columns else 0,
        "strategy": {
            "Passive": "Receives MORE questions with SHORTER intervals (2-5 min)",
            "Moderate": "Receives MEDIUM frequency questions (5-8 min)",
            "Active": "Receives FEWER questions with LONGER intervals (10-15 min)"
        }
    }


@router.post("/session/{session_id}/start-adaptive")
async def start_adaptive_questioning(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """
    Start adaptive questioning for a session
    Questions will be automatically sent based on engagement levels
    """
    scheduler = get_adaptive_scheduler()
    scheduler.start_session(session_id)
    
    return {
        "success": True,
        "message": "Adaptive questioning started",
        "session_id": session_id
    }


@router.post("/session/{session_id}/stop-adaptive")
async def stop_adaptive_questioning(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """Stop adaptive questioning for a session"""
    scheduler = get_adaptive_scheduler()
    overview = scheduler.get_session_overview(session_id)
    scheduler.stop_session(session_id)
    
    return {
        "success": True,
        "message": "Adaptive questioning stopped",
        "session_id": session_id,
        "final_stats": overview
    }


@router.post("/session/{session_id}/student/{student_id}/add")
async def add_student_to_adaptive(
    session_id: str,
    student_id: str,
    initial_engagement: str = "Moderate",
    user: dict = Depends(get_current_user)
):
    """
    Add student to adaptive questioning schedule
    They will start receiving questions based on their engagement level
    """
    if initial_engagement not in ["Active", "Moderate", "Passive"]:
        raise HTTPException(status_code=400, detail="Invalid engagement level")
    
    scheduler = get_adaptive_scheduler()
    scheduler.add_student(session_id, student_id, initial_engagement)
    
    return {
        "success": True,
        "message": "Student added to adaptive scheduling",
        "student_id": student_id,
        "initial_engagement": initial_engagement
    }


@router.get("/session/{session_id}/overview")
async def get_session_engagement_overview(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """
    Get real-time overview of student engagement levels in a session
    Shows distribution of Active/Moderate/Passive students
    """
    scheduler = get_adaptive_scheduler()
    overview = scheduler.get_session_overview(session_id)
    
    if overview is None:
        raise HTTPException(status_code=404, detail="Session not found or adaptive scheduling not started")
    
    return overview


@router.get("/student/{student_id}/stats")
async def get_student_engagement_stats(
    student_id: str,
    user: dict = Depends(get_current_user)
):
    """Get current engagement statistics for a student"""
    scheduler = get_adaptive_scheduler()
    stats = scheduler.get_student_stats(student_id)
    
    if stats is None:
        raise HTTPException(status_code=404, detail="Student not found in adaptive scheduling")
    
    return stats


@router.get("/session/{session_id}/ready-students")
async def get_students_ready_for_question(
    session_id: str,
    user: dict = Depends(require_instructor)
):
    """
    Get list of students who should receive a question now
    Based on their individual schedules and engagement levels
    """
    scheduler = get_adaptive_scheduler()
    ready_students = scheduler.get_students_ready_for_question(session_id)
    
    return {
        "session_id": session_id,
        "ready_count": len(ready_students),
        "students": ready_students
    }
