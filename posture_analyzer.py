import cv2
import mediapipe as mp
import numpy as np
import math
import time
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Tuple, Optional
from posture_alerts import PostureAlerter
from posture_translator import PostureTranslator


POSE_TASK_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/1/pose_landmarker_full.task"
)
POSE_TASK_MODEL_PATH = (
    Path(__file__).resolve().parent / ".cache" / "models" / "pose_landmarker_full.task"
)


class _LandmarkListAdapter:
    def __init__(self, landmarks):
        self.landmark = landmarks


class _PoseResultAdapter:
    def __init__(self, landmarks):
        self.pose_landmarks = _LandmarkListAdapter(landmarks) if landmarks else None


class PostureAnalyzer:
    """
    Analyzes posture using MediaPipe pose detection.
    
    Focuses on key postural indicators:
    - Head forward posture
    - Shoulder slouching
    - Spine alignment
    """
    
    def __init__(self):
        self._pose_backend = None
        self._last_video_timestamp_ms = 0
        self.mp_pose = None
        self.mp_drawing = None
        self.pose = self._create_pose_backend()
        
        # Translation system
        self.translator = PostureTranslator()
        
        # Calibration values (will be set when user calibrates)
        self.good_posture_angles = {
            'head_shoulder_angle': None,
            'shoulder_hip_angle': None,
            'ear_shoulder_alignment': None
        }
        
        # Posture monitoring modes
        self.monitoring_modes = {
            'general': {
                'enabled': True,
                'focus_areas': ['head', 'shoulders', 'neck_angle']
            },
            'desk_work': {
                'enabled': True,
                'focus_areas': ['head', 'shoulders', 'neck_angle', 'arm_position']
            }
        }
        self.current_mode = 'general'
        
        # Sensitivity thresholds - Adjusted for less frequent "minor" detections
        self.sensitivity_levels = {
            'very_low': {'angle_threshold': 25, 'alignment_threshold': 0.20, 'shoulder_threshold': 0.08, 'head_sensitivity': 0.12, 'shoulder_elevation_threshold': 0.25},
            'low': {'angle_threshold': 22, 'alignment_threshold': 0.18, 'shoulder_threshold': 0.07, 'head_sensitivity': 0.10, 'shoulder_elevation_threshold': 0.22},
            'medium': {'angle_threshold': 18, 'alignment_threshold': 0.15, 'shoulder_threshold': 0.06, 'head_sensitivity': 0.08, 'shoulder_elevation_threshold': 0.18},
            'high': {'angle_threshold': 14, 'alignment_threshold': 0.12, 'shoulder_threshold': 0.05, 'head_sensitivity': 0.06, 'shoulder_elevation_threshold': 0.15}
        }
        self.current_sensitivity = 'low'  # Changé de 'medium' à 'low' pour réduire les détections
        
        # Mode-specific thresholds for desk work - Adjusted to be more tolerant
        self.desk_work_thresholds = {
            'very_low': {
                'neck_forward_threshold': 0.15,  # Much more tolerant
                'shoulder_tension_threshold': 0.10,
                'head_tilt_threshold': 0.06,  # More tolerant
                'arm_angle_threshold': 35,
                'shoulder_elevation_threshold': 0.25  # Very tolerant
            },
            'low': {
                'neck_forward_threshold': 0.12,  # More tolerant than before
                'shoulder_tension_threshold': 0.08,
                'head_tilt_threshold': 0.04,  # More tolerant
                'arm_angle_threshold': 30,
                'shoulder_elevation_threshold': 0.22  # More tolerant
            },
            'medium': {
                'neck_forward_threshold': 0.10,  # Same as old 'low'
                'shoulder_tension_threshold': 0.06,
                'head_tilt_threshold': 0.03,
                'arm_angle_threshold': 25,
                'shoulder_elevation_threshold': 0.18
            },
            'high': {
                'neck_forward_threshold': 0.08,  # Same as old 'medium'
                'shoulder_tension_threshold': 0.05,
                'head_tilt_threshold': 0.025,
                'arm_angle_threshold': 20,
                'shoulder_elevation_threshold': 0.15
            }
        }
        
        # Enhanced detection parameters - Much more forgiving alerting
        self.consecutive_bad_frames = 0
        self.frames_needed_for_alert = 18  # Need more consecutive bad frames (was 12)
        self.posture_history = []
        self.history_length = 20  # Longer history for much smoother detection (was 15)
        
        # Audio alerts system
        self.alerter = PostureAlerter()

    def _create_pose_backend(self):
        if hasattr(mp, 'solutions'):
            self._pose_backend = 'solutions'
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            return self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                enable_segmentation=False,
                smooth_segmentation=True,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )

        self._pose_backend = 'tasks'
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.core.base_options import BaseOptions
        from mediapipe.tasks.python.vision import pose_landmarker

        model_path = self._ensure_pose_task_model()
        self.mp_pose = SimpleNamespace(
            POSE_CONNECTIONS=pose_landmarker.PoseLandmarksConnections.POSE_LANDMARKS
        )
        self.mp_drawing = None

        options = pose_landmarker.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        return pose_landmarker.PoseLandmarker.create_from_options(options)

    def _ensure_pose_task_model(self) -> Path:
        if POSE_TASK_MODEL_PATH.exists():
            return POSE_TASK_MODEL_PATH

        POSE_TASK_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(POSE_TASK_MODEL_URL, POSE_TASK_MODEL_PATH)
        return POSE_TASK_MODEL_PATH

    def _next_video_timestamp_ms(self) -> int:
        current_ms = int(time.monotonic() * 1000)
        self._last_video_timestamp_ms = max(self._last_video_timestamp_ms + 1, current_ms)
        return self._last_video_timestamp_ms

    def _process_pose(self, rgb_frame: np.ndarray):
        if self._pose_backend == 'solutions':
            return self.pose.process(rgb_frame)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb_frame)
        )
        result = self.pose.detect_for_video(mp_image, self._next_video_timestamp_ms())
        landmarks = result.pose_landmarks[0] if result.pose_landmarks else None
        return _PoseResultAdapter(landmarks)
    
    def set_translator_language(self, language: str):
        """Synchronize translator language with main interface."""
        self.translator.current_language = language
    
    def calculate_angle(self, point1: Tuple[float, float], 
                       point2: Tuple[float, float], 
                       point3: Tuple[float, float]) -> float:
        """Calculate angle between three points."""
        # Convert to numpy arrays
        a = np.array(point1)
        b = np.array(point2)
        c = np.array(point3)
        
        # Calculate vectors
        ba = a - b
        bc = c - b
        
        # Calculate angle
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        # Handle numerical errors
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        
        return np.degrees(angle)
    
    def calculate_distance(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def extract_key_landmarks(self, landmarks) -> Optional[dict]:
        """Extract relevant landmarks for posture analysis."""
        if not landmarks:
            return None
        
        # Key landmark indices for posture analysis
        landmark_indices = {
            'nose': 0,
            'left_ear': 7,
            'right_ear': 8,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16,
            'left_hip': 23,
            'right_hip': 24
        }
        
        key_points = {}
        for name, idx in landmark_indices.items():
            if idx < len(landmarks.landmark):
                landmark = landmarks.landmark[idx]
                # More lenient visibility threshold for better landmark detection
                visibility_threshold = 0.3 if name in ['left_ear', 'right_ear'] else 0.5
                if landmark.visibility > visibility_threshold:
                    key_points[name] = (landmark.x, landmark.y)
        
        # For desk work mode, we're more lenient about missing hips
        if self.current_mode == 'desk_work':
            required_points = 3  # More flexible for seated position
        else:
            required_points = 4  # Standard requirement
        
        return key_points if len(key_points) >= required_points else None

    def get_key_points(self, landmarks) -> Dict[str, Tuple[float, float]]:
        """Extract key body points from landmarks."""
        if not landmarks:
            return {}
        
        key_points = {}
        landmark_indices = {
            'nose': 0,
            'left_eye': 2, 'right_eye': 5,
            'left_ear': 7, 'right_ear': 8,
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_elbow': 13, 'right_elbow': 14,
            'left_wrist': 15, 'right_wrist': 16,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28
        }
        
        # Extract coordinates for each landmark
        for name, idx in landmark_indices.items():
            if idx < len(landmarks.landmark):
                landmark = landmarks.landmark[idx]
                # Only include landmarks with good visibility
                if landmark.visibility > 0.5:
                    key_points[name] = (landmark.x, landmark.y)
        
        return key_points
    
    def analyze_posture(self, frame: np.ndarray) -> Dict:
        """
        Main posture analysis function.
        Returns dictionary with analysis results.
        """
        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = self._process_pose(rgb_frame)
        
        analysis_result = {
            'landmarks': results.pose_landmarks,
            'issues': [],
            'angles': {},
            'confidence': 0.0,
            'key_points': {},
            'good_posture': True
        }
        
        if not results.pose_landmarks:
            return analysis_result
        
        # Get key body points
        key_points = self.get_key_points(results.pose_landmarks)
        analysis_result['key_points'] = key_points
        
        if len(key_points) < 4:  # Need at least basic points
            return analysis_result
        
        # Analyze based on current mode
        if self.current_mode == 'desk_work':
            analysis_result = self._analyze_desk_work_posture(key_points, analysis_result)
        else:
            analysis_result = self._analyze_general_posture(key_points, analysis_result)
        
        # Overall assessment
        analysis_result['good_posture'] = len(analysis_result['issues']) == 0
        
        # Add to history and check for alerts
        self._update_posture_history(analysis_result)
        
        return analysis_result
    
    def _analyze_general_posture(self, key_points: Dict, analysis_result: Dict) -> Dict:
        """Analyze general posture indicators."""
        issues = analysis_result['issues']
        angles = analysis_result['angles']
        confidence_scores = []
        
        # Use current sensitivity settings
        current_thresholds = self.sensitivity_levels[self.current_sensitivity]
        
        # 1. Head forward posture - Increased sensitivity
        neck_forward_detected = False
        if all(k in key_points for k in ['nose', 'left_ear', 'right_ear']):
            # Calculate average ear position
            avg_ear_x = (key_points['left_ear'][0] + key_points['right_ear'][0]) / 2
            nose_x = key_points['nose'][0]
            
            # Head forward detection - more sensitive
            head_forward_distance = nose_x - avg_ear_x
            angles['head_forward'] = head_forward_distance
            
            if head_forward_distance > current_thresholds['head_sensitivity']:
                neck_forward_detected = True
                issues.append(self.translator.get_text('subtle_head_forward_detected'))
                confidence_scores.append(0.8)
        
        # 2. Shoulder alignment - Enhanced sensitivity
        if 'left_shoulder' in key_points and 'right_shoulder' in key_points:
            left_y = key_points['left_shoulder'][1]
            right_y = key_points['right_shoulder'][1]
            shoulder_diff = abs(left_y - right_y)
            angles['shoulder_alignment'] = shoulder_diff
            
            if shoulder_diff > current_thresholds['shoulder_threshold']:
                if left_y < right_y:
                    issues.append(self.translator.get_text('left_shoulder_high'))
                else:
                    issues.append(self.translator.get_text('right_shoulder_high'))
                confidence_scores.append(0.7)
            
            # Check if shoulders are too high (tension)
            if 'nose' in key_points:
                avg_shoulder_y = (key_points['left_shoulder'][1] + key_points['right_shoulder'][1]) / 2
                nose_shoulder_diff = key_points['nose'][1] - avg_shoulder_y
                angles['shoulder_elevation'] = nose_shoulder_diff
                
                # AMÉLIORATION : Détection plus précise des épaules élevées
                # Vérifier plusieurs indicateurs pour éviter les faux positifs dus aux problèmes de cou
                shoulder_elevation_threshold = self.sensitivity_levels[self.current_sensitivity]['shoulder_elevation_threshold']
                
                # Vérification 1: Distance nez-épaules (critère principal)
                nose_too_close_to_shoulders = nose_shoulder_diff < shoulder_elevation_threshold
                
                # Vérification 2: Épaules par rapport aux hanches (pour détecter vraie élévation)
                shoulder_hip_ratio = None
                if 'left_hip' in key_points and 'right_hip' in key_points:
                    avg_hip_y = (key_points['left_hip'][1] + key_points['right_hip'][1]) / 2
                    shoulder_hip_diff = avg_hip_y - avg_shoulder_y  # Distance épaules-hanches
                    shoulder_hip_ratio = shoulder_hip_diff
                    # Ratio normal épaules-hanches devrait être > 0.25 (épaules bien au-dessus des hanches)
                    shoulders_truly_elevated = shoulder_hip_diff < 0.22  # Épaules trop proches des hanches
                
                # Vérification 3: Asymétrie des épaules (tension unilatérale)
                shoulder_asymmetry = abs(key_points['left_shoulder'][1] - key_points['right_shoulder'][1])
                significant_asymmetry = shoulder_asymmetry > 0.03
                
                # LOGIQUE AMÉLIORÉE : Détecter seulement les vrais problèmes d'épaules
                if nose_too_close_to_shoulders:
                    # Si problème de cou détecté, être plus strict pour les épaules
                    if neck_forward_detected:
                        # Cou en avant détecté = proximité nez-épaules probablement due au cou
                        # Alerter seulement si indicateurs forts d'élévation des épaules
                        if shoulder_hip_ratio is not None and shoulders_truly_elevated and significant_asymmetry:
                            issues.append(self.translator.get_text('combined_posture_issue'))
                            confidence_scores.append(0.8)
                    else:
                        # Pas de problème de cou = analyse normale des épaules
                        if shoulder_hip_ratio is not None and shoulders_truly_elevated:
                            # Vraie élévation des épaules détectée
                            if significant_asymmetry:
                                issues.append(self.translator.get_text('shoulder_tension_detected'))
                            else:
                                issues.append(self.translator.get_text('shoulders_too_elevated_detailed'))
                            confidence_scores.append(0.7)
                        elif significant_asymmetry:
                            # Asymétrie sans élévation générale = problème spécifique
                            issues.append(self.translator.get_text('shoulder_imbalance_adjust'))
                            confidence_scores.append(0.6)
        
        # Calculate overall confidence
        if confidence_scores:
            analysis_result['confidence'] = sum(confidence_scores) / len(confidence_scores)
        
        return analysis_result
    
    def _analyze_desk_work_posture(self, key_points: Dict, analysis_result: Dict) -> Dict:
        """Analyze posture specifically for desk work."""
        issues = analysis_result['issues']
        angles = analysis_result['angles']
        confidence_scores = []
        
        # Use desk work specific thresholds
        thresholds = self.desk_work_thresholds[self.current_sensitivity]
        
        # 1. Forward head posture (more common during computer work) - PRIORITÉ ÉLEVÉE
        neck_forward_detected = False
        if all(k in key_points for k in ['nose', 'left_ear', 'right_ear']):
            avg_ear_x = (key_points['left_ear'][0] + key_points['right_ear'][0]) / 2
            nose_x = key_points['nose'][0]
            head_forward_distance = nose_x - avg_ear_x
            angles['head_forward'] = head_forward_distance
            
            if head_forward_distance > thresholds['neck_forward_threshold']:
                # Détection spécifique pour le cou
                neck_forward_detected = True
                if head_forward_distance > thresholds['neck_forward_threshold'] * 1.5:
                    issues.append(self.translator.get_text('significant_forward_head'))
                else:
                    issues.append(self.translator.get_text('forward_head_posture'))
                confidence_scores.append(0.9)
        
        # 2. Shoulder tension (common during typing)
        if 'left_shoulder' in key_points and 'right_shoulder' in key_points:
            left_y = key_points['left_shoulder'][1]
            right_y = key_points['right_shoulder'][1]
            shoulder_diff = abs(left_y - right_y)
            angles['shoulder_alignment'] = shoulder_diff
            
            if shoulder_diff > thresholds['shoulder_tension_threshold']:
                if left_y < right_y:
                    issues.append(self.translator.get_text('left_shoulder_high'))
                else:
                    issues.append(self.translator.get_text('right_shoulder_high'))
                confidence_scores.append(0.7)
            
            # AMÉLIORATION : Détection plus précise des épaules élevées en mode desk_work
            if 'nose' in key_points:
                avg_shoulder_y = (key_points['left_shoulder'][1] + key_points['right_shoulder'][1]) / 2
                nose_shoulder_diff = key_points['nose'][1] - avg_shoulder_y
                angles['shoulder_elevation'] = nose_shoulder_diff
                
                # Seuil pour élévation des épaules
                shoulder_elevation_threshold = thresholds['shoulder_elevation_threshold']
                nose_too_close = nose_shoulder_diff < shoulder_elevation_threshold
                
                # Vérifications supplémentaires pour plus de précision
                shoulder_hip_ratio = None
                if 'left_hip' in key_points and 'right_hip' in key_points:
                    avg_hip_y = (key_points['left_hip'][1] + key_points['right_hip'][1]) / 2
                    shoulder_hip_diff = avg_hip_y - avg_shoulder_y
                    shoulder_hip_ratio = shoulder_hip_diff
                    shoulders_truly_elevated = shoulder_hip_diff < 0.20  # Plus strict en mode desk
                
                # Asymétrie des épaules
                shoulder_asymmetry = abs(key_points['left_shoulder'][1] - key_points['right_shoulder'][1])
                significant_asymmetry = shoulder_asymmetry > 0.025  # Plus sensible en mode desk
                
                # Logique de détection améliorée pour desk_work
                if nose_too_close:
                    # Si on a déjà détecté un problème de cou, éviter les faux positifs d'épaules
                    if neck_forward_detected:
                        # Problème de cou détecté = la proximité nez-épaules est probablement due au cou
                        # On ne déclenche les alertes épaules que si on a de vrais indicateurs d'élévation
                        if shoulder_hip_ratio is not None and shoulders_truly_elevated and significant_asymmetry:
                            issues.append(self.translator.get_text('desk_shoulder_head_combo'))
                            confidence_scores.append(0.8)
                    else:
                        # Pas de problème de cou = on peut analyser les épaules normalement
                        if shoulder_hip_ratio is not None and shoulders_truly_elevated:
                            if significant_asymmetry:
                                issues.append(self.translator.get_text('desk_uneven_tension'))
                            else:
                                issues.append(self.translator.get_text('desk_shoulders_elevated'))
                            confidence_scores.append(0.7)
                        elif significant_asymmetry:
                            issues.append(self.translator.get_text('desk_shoulder_imbalance'))
                            confidence_scores.append(0.6)
        
        # 3. Head tilt (looking down at screen) - More sensitive detection
        if 'left_ear' in key_points and 'right_ear' in key_points:
            ear_height_diff = abs(key_points['left_ear'][1] - key_points['right_ear'][1])
            angles['head_tilt'] = ear_height_diff
            
            if ear_height_diff > thresholds['head_tilt_threshold']:
                left_ear_y = key_points['left_ear'][1]
                right_ear_y = key_points['right_ear'][1]
                if left_ear_y < right_ear_y:
                    issues.append(self.translator.get_text('head_tilted_left'))
                else:
                    issues.append(self.translator.get_text('head_tilted_right'))
                confidence_scores.append(0.6)
        
        # 4. Arm positioning (relevant for desk work)
        if all(k in key_points for k in ['left_shoulder', 'left_elbow', 'left_wrist']):
            arm_angle = self.calculate_angle(
                key_points['left_shoulder'],
                key_points['left_elbow'],
                key_points['left_wrist']
            )
            angles['left_arm_angle'] = arm_angle
            
            # Check if arm angle is too acute (hunched typing)
            if arm_angle < thresholds['arm_angle_threshold']:
                issues.append(self.translator.get_text('arms_too_close'))
                confidence_scores.append(0.5)
        
        # Calculate overall confidence
        if confidence_scores:
            analysis_result['confidence'] = sum(confidence_scores) / len(confidence_scores)
        
        return analysis_result
    
    def _update_posture_history(self, analysis_result: Dict):
        """Update posture history and trigger alerts if needed."""
        # Add current result to history
        self.posture_history.append(analysis_result['good_posture'])
        
        # Maintain history length
        if len(self.posture_history) > self.history_length:
            self.posture_history.pop(0)
        
        # Check for consistent bad posture
        if not analysis_result['good_posture']:
            self.consecutive_bad_frames += 1
        else:
            self.consecutive_bad_frames = 0
        
        # Trigger alerts if needed
        if (self.consecutive_bad_frames >= self.frames_needed_for_alert and 
            len(analysis_result['issues']) > 0):
            
            # Use the first issue as the primary alert
            primary_issue = analysis_result['issues'][0]
            self.alerter.play_alert(primary_issue)
            
            # Reset counter to avoid spam
            self.consecutive_bad_frames = 0
    
    def set_sensitivity(self, level: str):
        """Set sensitivity level for posture detection."""
        if level in self.sensitivity_levels:
            self.current_sensitivity = level
            print(f"Sensitivity set to: {level}")
    
    def get_sensitivity(self) -> str:
        """Get current sensitivity level."""
        return self.current_sensitivity
    
    def set_monitoring_mode(self, mode: str):
        """Set monitoring mode (general or desk_work)."""
        if mode in self.monitoring_modes:
            self.current_mode = mode
            print(f"Monitoring mode set to: {mode}")
    
    def get_status(self) -> Dict:
        """Get current analyzer status."""
        return {
            'sensitivity': self.current_sensitivity,
            'mode': self.current_mode,
            'consecutive_bad_frames': self.consecutive_bad_frames,
            'history_length': len(self.posture_history),
            'alert_config': self.alerter.get_alert_config()
        }
    
    def calibrate_good_posture(self, frame: np.ndarray):
        """Calibrate what constitutes good posture for this user."""
        analysis = self.analyze_posture(frame)
        
        if analysis['landmarks'] and len(analysis['key_points']) >= 4:
            # Store current angles as good posture reference
            self.good_posture_angles.update(analysis['angles'])
            print("Good posture calibrated successfully!")
            return True
        else:
            print("Could not detect enough landmarks for calibration")
            return False
    
    def get_angle_from_vertical(self, point1: Tuple[float, float], 
                               point2: Tuple[float, float]) -> float:
        """Calculate angle from vertical line."""
        x1, y1 = point1
        x2, y2 = point2
        
        # Calculate angle from vertical (positive y-axis pointing down)
        dx = x2 - x1
        dy = y2 - y1
        
        if dy == 0:  # Horizontal line
            return 90.0
        else:
            return abs(math.degrees(math.atan2(dx, dy)))
    
    def calibrate_to_current_posture(self, key_points: dict):
        """Calibrate thresholds based on current posture for personalized detection."""
        if not key_points or len(key_points) < 4:
            return False
            
        # Calculate current posture parameters
        current_params = {}
        
        # Head-shoulder alignment
        if all(k in key_points for k in ['nose', 'left_shoulder', 'right_shoulder']):
            avg_shoulder_x = (key_points['left_shoulder'][0] + key_points['right_shoulder'][0]) / 2
            current_params['neck_forward'] = abs(key_points['nose'][0] - avg_shoulder_x)
        
        # Shoulder level
        if 'left_shoulder' in key_points and 'right_shoulder' in key_points:
            current_params['shoulder_diff'] = abs(key_points['left_shoulder'][1] - key_points['right_shoulder'][1])
        
        # Adjust thresholds to be more lenient based on current posture
        base_multiplier = 1.5  # 50% more tolerant than current posture
        
        if 'neck_forward' in current_params:
            # Adjust general thresholds
            for level in self.sensitivity_levels:
                self.sensitivity_levels[level]['alignment_threshold'] = max(
                    self.sensitivity_levels[level]['alignment_threshold'],
                    current_params['neck_forward'] * base_multiplier
                )
        
        if 'shoulder_diff' in current_params:
            for level in self.sensitivity_levels:
                self.sensitivity_levels[level]['shoulder_threshold'] = max(
                    self.sensitivity_levels[level]['shoulder_threshold'],
                    current_params['shoulder_diff'] * base_multiplier
                )
        
        print(f"Calibration completed! Thresholds adjusted to current posture.")
        print(f"Neck forward tolerance: {current_params.get('neck_forward', 0):.3f}")
        print(f"Shoulder difference tolerance: {current_params.get('shoulder_diff', 0):.3f}")
        
        return True
    
    def toggle_audio_alerts(self):
        """Toggle audio alerts on/off."""
        return self.alerter.toggle_alerts()
    
    def enable_audio_alerts(self):
        """Enable audio alerts."""
        self.alerter.enable_alerts()
    
    def disable_audio_alerts(self):
        """Disable audio alerts."""
        self.alerter.disable_alerts()
    
    def test_audio_alerts(self):
        """Test the audio alert system."""
        self.alerter.test_alerts()
    
    def set_alert_for_issue(self, issue_type, enabled):
        """Enable or disable alert for specific issue type."""
        self.alerter.set_alert_for_issue(issue_type, enabled)
    
    def get_alert_config(self):
        """Get current alert configuration."""
        return self.alerter.get_alert_config()
    
    def is_alert_enabled_for_issue(self, issue_type):
        """Check if alert is enabled for specific issue type."""
        return self.alerter.is_alert_enabled_for_issue(issue_type)

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self.pose, 'close'):
            self.pose.close()


# Example usage and testing
if __name__ == "__main__":
    analyzer = PostureAnalyzer()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze posture
            result = analyzer.analyze_posture(frame)
            
            # Draw landmarks if detected
            if result['landmarks'] and analyzer.mp_drawing:
                analyzer.mp_drawing.draw_landmarks(
                    frame, result['landmarks'], analyzer.mp_pose.POSE_CONNECTIONS)
            
            # Display issues
            y_offset = 30
            for issue in result['issues']:
                cv2.putText(frame, issue, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                y_offset += 25
            
            # Show frame
            cv2.imshow('Posture Monitor', frame)
            
            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        analyzer.cleanup()