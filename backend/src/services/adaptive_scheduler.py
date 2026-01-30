"""
Adaptive Question Scheduler
Automatically sends questions to students based on their engagement level
- Passive students: Get MORE questions with SHORTER intervals (unpredictable)
- Moderate students: Get MEDIUM frequency questions
- Active students: Get FEWER questions with LONGER intervals
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..services.engagement_predictor import get_engagement_predictor
from ..models.question import Question

class AdaptiveQuestionScheduler:
    """
    Manages adaptive questioning based on student engagement levels
    Keeps students engaged by varying question frequency
    """
    
    # Question interval ranges (in seconds)
    INTERVALS = {
        "Passive": (120, 300),     # 2-5 minutes - RAPID questions
        "Moderate": (300, 480),    # 5-8 minutes - MEDIUM frequency
        "Active": (600, 900)       # 10-15 minutes - FEWER questions
    }
    
    # Expected question counts per 60-minute session
    EXPECTED_COUNTS = {
        "Passive": 15-20,   # ~12-20 questions
        "Moderate": 8-12,    # ~8-12 questions
        "Active": 4-6        # ~4-6 questions
    }
    
    def __init__(self):
        """Initialize scheduler"""
        self.active_sessions: Dict[str, Dict] = {}  # session_id -> session_data
        self.student_schedules: Dict[str, Dict] = {}  # student_id -> schedule_data
        self.engagement_predictor = get_engagement_predictor()
        self.running = False
    
    def start_session(self, session_id: str):
        """Start adaptive questioning for a session"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "start_time": datetime.utcnow(),
                "students": {},
                "questions_sent": 0
            }
            print(f"🎯 Adaptive scheduler started for session: {session_id}")
    
    def stop_session(self, session_id: str):
        """Stop adaptive questioning for a session"""
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            duration = (datetime.utcnow() - session_data["start_time"]).total_seconds() / 60
            print(f"🛑 Adaptive scheduler stopped for session: {session_id}")
            print(f"   Duration: {duration:.1f} minutes")
            print(f"   Questions sent: {session_data['questions_sent']}")
            
            # Remove students associated with this session
            students_to_remove = []
            for student_id, schedule in self.student_schedules.items():
                if schedule.get("session_id") == session_id:
                    students_to_remove.append(student_id)
            
            for student_id in students_to_remove:
                del self.student_schedules[student_id]
            
            del self.active_sessions[session_id]
    
    def add_student(
        self,
        session_id: str,
        student_id: str,
        initial_engagement: str = "Moderate"
    ):
        """Add student to adaptive scheduling"""
        if session_id not in self.active_sessions:
            self.start_session(session_id)
        
        # Initialize student schedule
        interval_min, interval_max = self.INTERVALS[initial_engagement]
        next_question_delay = random.randint(interval_min, interval_max)
        
        self.student_schedules[student_id] = {
            "session_id": session_id,
            "engagement_level": initial_engagement,
            "next_question_time": datetime.utcnow() + timedelta(seconds=next_question_delay),
            "questions_sent": 0,
            "questions_answered": 0,
            "questions_correct": 0,
            "last_rtt": 100.0,
            "last_network_quality": "Good",
            "engagement_history": [initial_engagement]
        }
        
        # Track in session
        self.active_sessions[session_id]["students"][student_id] = initial_engagement
        
        print(f"👤 Student {student_id} added to session {session_id}")
        print(f"   Initial engagement: {initial_engagement}")
        print(f"   Next question in: {next_question_delay} seconds")
    
    def remove_student(self, student_id: str):
        """Remove student from adaptive scheduling"""
        if student_id in self.student_schedules:
            schedule = self.student_schedules[student_id]
            session_id = schedule["session_id"]
            
            # Remove from session tracking
            if session_id in self.active_sessions:
                if student_id in self.active_sessions[session_id]["students"]:
                    del self.active_sessions[session_id]["students"][student_id]
            
            del self.student_schedules[student_id]
            print(f"👤 Student {student_id} removed from adaptive scheduling")
    
    def update_student_engagement(
        self,
        student_id: str,
        is_correct: bool,
        response_time: float,
        rtt_ms: float,
        question_difficulty: str
    ):
        """
        Update student engagement level based on their latest answer
        Reclassify using ML model and adjust question frequency
        """
        if student_id not in self.student_schedules:
            return
        
        schedule = self.student_schedules[student_id]
        
        # Update statistics
        schedule["questions_answered"] += 1
        if is_correct:
            schedule["questions_correct"] += 1
        schedule["last_rtt"] = rtt_ms
        
        # Predict new engagement level
        engagement_level, confidence, probabilities = self.engagement_predictor.predict_from_system_data(
            is_correct=is_correct,
            response_time=response_time,
            rtt_ms=rtt_ms,
            question_difficulty=question_difficulty,
            network_quality=schedule.get("last_network_quality", "Good")
        )
        
        old_engagement = schedule["engagement_level"]
        schedule["engagement_level"] = engagement_level
        schedule["engagement_history"].append(engagement_level)
        
        # Update session tracking
        session_id = schedule["session_id"]
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["students"][student_id] = engagement_level
        
        # Adjust next question timing based on new engagement level
        interval_min, interval_max = self.INTERVALS[engagement_level]
        next_question_delay = random.randint(interval_min, interval_max)
        schedule["next_question_time"] = datetime.utcnow() + timedelta(seconds=next_question_delay)
        
        if old_engagement != engagement_level:
            print(f"📊 Student {student_id} engagement changed: {old_engagement} → {engagement_level}")
            print(f"   Confidence: {confidence:.2%}")
            print(f"   Next question in: {next_question_delay} seconds")
    
    def update_student_network(self, student_id: str, rtt_ms: float, quality: str):
        """Update student network metrics"""
        if student_id in self.student_schedules:
            self.student_schedules[student_id]["last_rtt"] = rtt_ms
            self.student_schedules[student_id]["last_network_quality"] = quality
    
    def get_students_ready_for_question(self, session_id: str) -> List[Dict]:
        """
        Get list of students who should receive a question now
        Returns list of student data dictionaries
        """
        if session_id not in self.active_sessions:
            return []
        
        now = datetime.utcnow()
        ready_students = []
        
        for student_id, schedule in self.student_schedules.items():
            if schedule["session_id"] == session_id:
                if now >= schedule["next_question_time"]:
                    ready_students.append({
                        "student_id": student_id,
                        "engagement_level": schedule["engagement_level"],
                        "questions_sent": schedule["questions_sent"]
                    })
        
        return ready_students
    
    def mark_question_sent(self, student_id: str):
        """Mark that a question was sent to student"""
        if student_id in self.student_schedules:
            schedule = self.student_schedules[student_id]
            schedule["questions_sent"] += 1
            
            # Schedule next question
            engagement_level = schedule["engagement_level"]
            interval_min, interval_max = self.INTERVALS[engagement_level]
            next_question_delay = random.randint(interval_min, interval_max)
            schedule["next_question_time"] = datetime.utcnow() + timedelta(seconds=next_question_delay)
            
            # Update session count
            session_id = schedule["session_id"]
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["questions_sent"] += 1
    
    def get_student_stats(self, student_id: str) -> Optional[Dict]:
        """Get current statistics for a student"""
        if student_id not in self.student_schedules:
            return None
        
        schedule = self.student_schedules[student_id]
        accuracy = 0.0
        if schedule["questions_answered"] > 0:
            accuracy = schedule["questions_correct"] / schedule["questions_answered"]
        
        return {
            "engagement_level": schedule["engagement_level"],
            "questions_sent": schedule["questions_sent"],
            "questions_answered": schedule["questions_answered"],
            "accuracy": accuracy,
            "last_rtt": schedule["last_rtt"],
            "engagement_history": schedule["engagement_history"]
        }
    
    def get_session_overview(self, session_id: str) -> Optional[Dict]:
        """Get overview of all students in a session"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        student_count = {
            "Active": 0,
            "Moderate": 0,
            "Passive": 0
        }
        
        for engagement in session["students"].values():
            student_count[engagement] += 1
        
        duration = (datetime.utcnow() - session["start_time"]).total_seconds() / 60
        
        return {
            "session_id": session_id,
            "duration_minutes": round(duration, 1),
            "total_students": len(session["students"]),
            "active_count": student_count["Active"],
            "moderate_count": student_count["Moderate"],
            "passive_count": student_count["Passive"],
            "total_questions_sent": session["questions_sent"]
        }


# Global scheduler instance
_scheduler = None

def get_adaptive_scheduler() -> AdaptiveQuestionScheduler:
    """Get or create global adaptive scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AdaptiveQuestionScheduler()
    return _scheduler
