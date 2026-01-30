"""
Student Engagement Prediction Service
Uses XGBoost model to classify students as Active/Moderate/Passive
Based on quiz performance and network quality metrics
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path

class EngagementPredictor:
    """
    Predicts student engagement level using trained XGBoost model
    
    Model Accuracy: 99.77%
    Classes: Active, Moderate, Passive
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize and load the engagement prediction model"""
        self.model = None
        self.preprocessor = None
        self.feature_columns = None
        self.reverse_mapping = None
        self.model_loaded = False
        
        # Default model path
        if model_path is None:
            base_dir = Path(__file__).parent.parent
            model_path = base_dir / "ml_models" / "engagement_xgb_hybrid_clean.joblib"
        
        self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """Load the pre-trained model bundle"""
        try:
            if not os.path.exists(model_path):
                print(f"⚠️  Model file not found: {model_path}")
                print("   Engagement prediction will be disabled until model is added")
                return False
            
            bundle = joblib.load(model_path)
            self.model = bundle['model']
            self.preprocessor = bundle['preprocessor']
            self.feature_columns = bundle['feature_columns']
            self.reverse_mapping = bundle['reverse_mapping']
            self.model_loaded = True
            
            print(f"✅ Engagement model loaded successfully")
            print(f"   Features: {len(self.feature_columns)}")
            print(f"   Classes: {list(self.reverse_mapping.values())}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading engagement model: {e}")
            self.model_loaded = False
            return False
    
    def extract_features_from_system_data(
        self,
        is_correct: bool,
        response_time: float,
        rtt_ms: float,
        question_difficulty: str,
        expected_time: float = 30.0,
        network_quality_raw: str = "Good"
    ) -> Dict:
        """
        Extract 13 features required by the model from system data
        
        Args:
            is_correct: Whether answer was correct (bool)
            response_time: Time taken to answer in seconds (float)
            rtt_ms: Network round-trip time in milliseconds (float)
            question_difficulty: "easy", "medium", or "hard" (str)
            expected_time: Expected time to answer (default 30 sec)
            network_quality_raw: Network quality from monitoring ("Good", "Fair", "Poor")
        
        Returns:
            Dictionary with all 13 features in correct format
        """
        
        # 1. Is Correct (0 or 1)
        is_correct_int = 1 if is_correct else 0
        
        # 2. Response Time (sec)
        response_time_sec = float(response_time)
        
        # 3-5. Network metrics (RTT, Jitter, Stability)
        # RTT: Use actual value
        rtt = float(rtt_ms) if rtt_ms > 0 else 100.0
        
        # Jitter: Estimate based on RTT (in real system, track variance)
        # For now, use 10-15% of RTT as jitter estimate
        jitter = rtt * 0.12  # 12% of RTT as jitter
        
        # Stability: Infer from RTT (lower RTT = higher stability)
        if rtt < 100:
            stability = 98.0  # Excellent
        elif rtt < 200:
            stability = 95.0  # Good
        elif rtt < 400:
            stability = 85.0  # Fair
        else:
            stability = 70.0  # Poor
        
        # 6-8. Speed indicators
        is_fast = 1 if response_time < expected_time * 0.8 else 0
        correct_and_fast = 1 if (is_correct and is_fast) else 0
        is_very_fast = 1 if response_time < expected_time * 0.5 else 0
        
        # 9-10. Network quality flags
        network_quality = network_quality_raw
        if network_quality not in ["Poor", "Good", "Excellent"]:
            # Map "Fair" to "Good"
            network_quality = "Good" if network_quality == "Fair" else "Excellent"
        
        poor_network = 1 if network_quality == "Poor" else 0
        excellent_network = 1 if network_quality == "Excellent" else 0
        
        # 11. Speed Ratio
        speed_ratio = expected_time / response_time if response_time > 0 else 1.0
        speed_ratio = min(speed_ratio, 10.0)  # Cap at 10
        
        # 12. Difficulty Score (convert difficulty string to 0-1 score)
        difficulty_map = {
            "easy": 1.0,      # Easy = high score
            "medium": 0.5,    # Medium = mid score
            "hard": 0.0       # Hard = low score
        }
        difficulty_score = difficulty_map.get(question_difficulty.lower(), 0.5)
        
        # Return features in the EXACT order model expects
        features = {
            'Is Correct': is_correct_int,
            'Response Time (sec)': response_time_sec,
            'RTT (ms)': rtt,
            'Jitter (ms)': jitter,
            'Stability (%)': stability,
            'is_fast': is_fast,
            'correct_and_fast': correct_and_fast,
            'is_very_fast': is_very_fast,
            'poor_network': poor_network,
            'excellent_network': excellent_network,
            'Speed_Ratio': speed_ratio,
            'Difficulty_Score': difficulty_score,
            'Network Quality': network_quality
        }
        
        return features
    
    def predict(self, features: Dict) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict engagement level from features
        
        Args:
            features: Dictionary with 13 required features
        
        Returns:
            Tuple of (engagement_level, confidence, probabilities)
            - engagement_level: "Active", "Moderate", or "Passive"
            - confidence: Highest probability (0-1)
            - probabilities: Dict with all class probabilities
        """
        
        if not self.model_loaded:
            # Fallback if model not loaded
            return "Moderate", 0.5, {"Active": 0.33, "Moderate": 0.34, "Passive": 0.33}
        
        try:
            # Convert to DataFrame with exact feature names
            df = pd.DataFrame([features])
            
            # Ensure correct column order
            df = df[self.feature_columns]
            
            # Transform using preprocessor (automatic scaling + encoding)
            X_transformed = self.preprocessor.transform(df)
            
            # Predict
            prediction = self.model.predict(X_transformed)[0]
            probabilities = self.model.predict_proba(X_transformed)[0]
            
            # Map to label
            engagement_label = self.reverse_mapping[prediction]
            
            # Get confidence
            confidence = float(max(probabilities))
            
            # Build probability dictionary
            prob_dict = {
                self.reverse_mapping[i]: float(probabilities[i]) 
                for i in range(len(probabilities))
            }
            
            return engagement_label, confidence, prob_dict
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return "Moderate", 0.5, {"Active": 0.33, "Moderate": 0.34, "Passive": 0.33}
    
    def predict_from_system_data(
        self,
        is_correct: bool,
        response_time: float,
        rtt_ms: float,
        question_difficulty: str,
        expected_time: float = 30.0,
        network_quality: str = "Good"
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Convenience method: Extract features and predict in one call
        
        Args:
            Same as extract_features_from_system_data()
        
        Returns:
            Tuple of (engagement_level, confidence, probabilities)
        """
        features = self.extract_features_from_system_data(
            is_correct=is_correct,
            response_time=response_time,
            rtt_ms=rtt_ms,
            question_difficulty=question_difficulty,
            expected_time=expected_time,
            network_quality_raw=network_quality
        )
        
        return self.predict(features)


# Global instance
_engagement_predictor = None

def get_engagement_predictor() -> EngagementPredictor:
    """Get or create global engagement predictor instance"""
    global _engagement_predictor
    if _engagement_predictor is None:
        _engagement_predictor = EngagementPredictor()
    return _engagement_predictor
