import cv2
import numpy as np
import pygame
import time
from typing import Tuple, Optional
from posture_translator import PostureTranslator


class PostureVisualizer:
    """
    Handles visual alerts and overlay rendering for posture monitoring.
    """
    
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        
        # Initialize translator
        self.translator = PostureTranslator()
        
        # Character mapping for OpenCV display (no UTF-8 support)
        self.char_mapping = {
            # Lowercase accented characters
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a', 'æ': 'ae',
            'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
            'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o', 'œ': 'oe',
            'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n', 'ÿ': 'y',
            # Uppercase accented characters
            'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A', 'Æ': 'AE',
            'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
            'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
            'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O', 'Œ': 'OE',
            'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C', 'Ñ': 'N', 'Ÿ': 'Y',
            # Additional symbols
            ''': "'", ''': "'", '"': '"', '"': '"', '…': '...',
            '–': '-', '—': '-', '«': '"', '»': '"'
        }
        
        # Initialize pygame for sound alerts (optional)
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False
        
        # Alert states
        self.alert_start_time = None
        self.alert_duration = 3.0  # seconds
        self.blink_interval = 0.5  # seconds
        
        # Individual box visibility states
        self.show_status_box = True
        self.show_measurements_box = True  
        self.show_guidelines_box = True
        self.show_controls_box = True
        
        # Mouse interaction
        self.mouse_callback_set = False
        self.close_button_areas = {}  # Store clickable areas for close buttons
        
        # Colors (BGR format for OpenCV)
        self.colors = {
            'good': (0, 255, 0),      # Green
            'fair': (0, 255, 255),    # Yellow
            'poor': (0, 0, 255),      # Red
            'background_good': (0, 50, 0),    # Dark green
            'background_fair': (0, 50, 50),   # Dark yellow
            'background_poor': (0, 0, 50),    # Dark red
            'text': (255, 255, 255),   # White
            'landmark': (255, 0, 255), # Magenta
            'close_button': (0, 0, 255),      # Red for close button
            'close_button_hover': (0, 0, 150) # Darker red for hover
        }
    
    def _map_status_to_key(self, status_msg):
        """Map status message to translation key."""
        status_mapping = {
            'Excellent Posture': 'excellent_posture',
            'Good Posture': 'good_posture', 
            'Fair Posture': 'fair_posture',
            'Poor Posture': 'poor_posture',
            'No Pose Detected': 'no_detection',
            'Unknown Status': 'unknown',
            'Monitoring Disabled': 'disabled'
        }
        return status_mapping.get(status_msg, 'unknown')
    
    def _map_sensitivity_to_key(self, sensitivity):
        """Map sensitivity level to translation key."""
        sensitivity_mapping = {
            'very_low': 'low_sensitivity',  # Map very_low to low for display
            'low': 'low_sensitivity',
            'medium': 'medium_sensitivity',
            'high': 'high_sensitivity'
        }
        return sensitivity_mapping.get(sensitivity, 'medium_sensitivity')
    
    def _add_status_to_analysis(self, analysis):
        """Add status to analysis if missing using same logic as GUI."""
        # Check if pose was detected
        if not analysis.get('key_points') or len(analysis.get('key_points', {})) == 0:
            analysis['status'] = 'no_detection'
            analysis['message'] = 'No Pose Detected'
            return analysis
        
        # Get confidence and issues
        confidence = analysis.get('confidence', 0.0)
        issues = analysis.get('issues', [])
        good_posture = analysis.get('good_posture', True)
        
        # Determine status based on issues and confidence
        if confidence < 0.3:
            analysis['status'] = 'no_detection'
            analysis['message'] = 'No Pose Detected'
        elif len(issues) == 0 and good_posture:
            if confidence > 0.8:
                analysis['status'] = 'excellent'
                analysis['message'] = 'Excellent Posture'
            else:
                analysis['status'] = 'good'
                analysis['message'] = 'Good Posture'
        elif len(issues) == 1:
            analysis['status'] = 'fair'
            analysis['message'] = 'Fair Posture'
        else:  # Multiple issues or bad posture
            analysis['status'] = 'poor'
            analysis['message'] = 'Poor Posture'
        
        return analysis
    
    def _convert_text_for_opencv(self, text: str) -> str:
        """Convert French characters to ASCII for OpenCV display."""
        for french_char, ascii_char in self.char_mapping.items():
            text = text.replace(french_char, ascii_char)
        return text
    
    def _put_text_utf8(self, image, text, position, font, font_scale, color, thickness=1):
        """Wrapper for cv2.putText that handles UTF-8 characters."""
        converted_text = self._convert_text_for_opencv(text)
        cv2.putText(image, converted_text, position, font, font_scale, color, thickness)
    
    def draw_pose_landmarks(self, image: np.ndarray, key_points: dict) -> np.ndarray:
        """Draw pose landmarks on the image."""
        if not key_points:
            return image
        
        # Convert normalized coordinates to pixel coordinates
        h, w = image.shape[:2]
        
        # Draw key points with different colors for different body parts
        point_colors = {
            'nose': (0, 255, 255),      # Yellow for nose
            'left_ear': (255, 0, 255),  # Magenta for ears
            'right_ear': (255, 0, 255), # Magenta for ears
            'left_shoulder': (0, 255, 0),   # Green for shoulders
            'right_shoulder': (0, 255, 0),  # Green for shoulders
            'left_elbow': (255, 255, 0),    # Cyan for elbows
            'right_elbow': (255, 255, 0),   # Cyan for elbows
            'left_wrist': (255, 0, 0),      # Blue for wrists
            'right_wrist': (255, 0, 0),     # Blue for wrists
            'left_hip': (128, 255, 128),    # Light green for hips
            'right_hip': (128, 255, 128),   # Light green for hips
        }
        
        for name, (x, y) in key_points.items():
            pixel_x, pixel_y = int(x * w), int(y * h)
            color = point_colors.get(name, self.colors['landmark'])
            # Draw larger circles for better visibility
            cv2.circle(image, (pixel_x, pixel_y), 8, color, -1)
            cv2.circle(image, (pixel_x, pixel_y), 10, (255, 255, 255), 2)  # White border
            
            # Label the point with better visibility
            self._put_text_utf8(image, name.replace('_', ' '), 
                       (pixel_x + 15, pixel_y - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, 
                       (0, 0, 0), 2)  # Black outline
            self._put_text_utf8(image, name.replace('_', ' '), 
                       (pixel_x + 15, pixel_y - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, 
                       (255, 255, 255), 1)  # White text
        
        # Draw connections with thicker lines
        connections = [
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            ('nose', 'left_shoulder'),
            ('nose', 'right_shoulder'),
            # Add ear connections if ears are detected
            ('left_ear', 'nose'),
            ('right_ear', 'nose'),
            ('left_ear', 'left_shoulder'),
            ('right_ear', 'right_shoulder')
        ]
        
        for point1, point2 in connections:
            if point1 in key_points and point2 in key_points:
                x1, y1 = key_points[point1]
                x2, y2 = key_points[point2]
                pt1 = (int(x1 * w), int(y1 * h))
                pt2 = (int(x2 * w), int(y2 * h))
                # Use different colors for different connection types
                if 'ear' in point1 or 'ear' in point2:
                    line_color = (255, 0, 255)  # Magenta for ear connections
                elif point1 == 'nose' or point2 == 'nose':
                    line_color = (0, 255, 255)  # Yellow for nose triangle
                else:
                    line_color = self.colors['landmark']  # Default color
                cv2.line(image, pt1, pt2, line_color, 3)
        
        return image
    
    def set_mouse_callback(self, window_name: str):
        """Set up mouse callback for close button clicks."""
        if not self.mouse_callback_set:
            cv2.setMouseCallback(window_name, self._mouse_callback)
            self.mouse_callback_set = True
    
    def _mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks for close buttons."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if click is on any close button
            for box_name, (bx, by, bw, bh) in self.close_button_areas.items():
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    # Close the corresponding box
                    if box_name == 'status':
                        self.show_status_box = False
                    elif box_name == 'measurements':
                        self.show_measurements_box = False
                    elif box_name == 'guidelines':
                        self.show_guidelines_box = False
                    elif box_name == 'controls':
                        self.show_controls_box = False
                    print(f"Closed {box_name} box")
                    break
    
    def _draw_close_button(self, image: np.ndarray, x: int, y: int, scale_factor: float, box_name: str) -> Tuple[int, int, int, int]:
        """Draw a close button (X) and store its clickable area."""
        button_size = int(16 * scale_factor)
        button_x = x - button_size - int(5 * scale_factor)
        button_y = y - int(5 * scale_factor)
        
        # Draw close button background
        cv2.rectangle(image, (button_x, button_y), 
                     (button_x + button_size, button_y + button_size), 
                     self.colors['close_button'], -1)
        
        # Draw X symbol
        cv2.line(image, (button_x + 3, button_y + 3), 
                (button_x + button_size - 3, button_y + button_size - 3), 
                self.colors['text'], 2)
        cv2.line(image, (button_x + button_size - 3, button_y + 3), 
                (button_x + 3, button_y + button_size - 3), 
                self.colors['text'], 2)
        
        # Store clickable area
        self.close_button_areas[box_name] = (button_x, button_y, button_size, button_size)
        
        return button_x, button_y, button_size, button_size
    
    def draw_posture_overlay(self, image: np.ndarray, analysis: dict) -> np.ndarray:
        """Draw posture status overlay on the image."""
        # Ensure status and message exist in analysis
        if 'status' not in analysis or 'message' not in analysis:
            analysis = self._add_status_to_analysis(analysis)
        
        if analysis['status'] == 'no_detection':
            return self._draw_no_detection_overlay(image)
        
        # Draw pose landmarks first (if available)
        if 'key_points' in analysis and analysis['key_points']:
            image = self.draw_pose_landmarks(image, analysis['key_points'])
        
        # Get colors based on posture status
        status_color = self.colors.get(analysis['status'], self.colors['text'])
        bg_color = self.colors.get(f"background_{analysis['status']}", (0, 0, 0))
        
        # Draw semi-transparent overlay for alerts
        if analysis['status'] in ['fair', 'poor']:
            overlay = image.copy()
            cv2.rectangle(overlay, (0, 0), (image.shape[1], image.shape[0]), bg_color, -1)
            
            # Add blinking effect for poor posture
            if analysis['status'] == 'poor':
                current_time = time.time()
                if self.alert_start_time is None:
                    self.alert_start_time = current_time
                
                # Blink effect
                elapsed = current_time - self.alert_start_time
                blink_cycle = elapsed % (self.blink_interval * 2)
                if blink_cycle < self.blink_interval:
                    alpha = 0.3
                else:
                    alpha = 0.1
            else:
                alpha = 0.15
            
            image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
        else:
            self.alert_start_time = None
        
        # Always draw status text (basic posture info)
        self._draw_status_text(image, analysis, status_color)
        
        return image
    
    def _draw_no_detection_overlay(self, image: np.ndarray) -> np.ndarray:
        """Draw overlay when no pose is detected."""
        # Message suppressed - no overlay when no pose detected
        return image
    
    def _draw_status_text(self, image: np.ndarray, analysis: dict, color: Tuple[int, int, int]):
        """Draw posture status text with enhanced accuracy information."""
        if not self.show_status_box:
            return
            
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Calculate responsive sizing based on image dimensions
        height, width = image.shape[:2]
        scale_factor = min(width / 640, height / 480)  # Base scale on 640x480
        
        # Adjust box size and positioning
        box_width = int(400 * scale_factor)
        box_height = int(180 * scale_factor)
        margin = int(5 * scale_factor)
        
        # Draw close button for status box
        self._draw_close_button(image, box_width + margin, margin + int(10 * scale_factor), scale_factor, 'status')
        
        # Draw semi-transparent background for better readability
        cv2.rectangle(image, (margin, margin), (box_width, box_height), (0, 0, 0), -1)
        cv2.rectangle(image, (margin, margin), (box_width, box_height), (50, 50, 50), 2)
        
        # Responsive font scaling
        main_font_scale = 0.9 * scale_factor
        sub_font_scale = 0.5 * scale_factor
        detail_font_scale = 0.35 * scale_factor
        
        text_margin = int(15 * scale_factor)
        line_spacing = int(25 * scale_factor)
        
        # Main status message - larger and more prominent - translate it
        status_msg = analysis['message']
        status_key = self._map_status_to_key(status_msg)
        translated_message = self.translator.get_text(status_key, status_msg)
        self._put_text_utf8(image, translated_message, (text_margin, text_margin + int(20 * scale_factor)), 
                   font, main_font_scale, color, 2)
        
        y_offset = text_margin + int(45 * scale_factor)
        
        # Show confidence and consistency if available (only if showing measurements)
        if hasattr(self, 'show_measurements') and getattr(self, 'show_measurements', True):
            if 'confidence' in analysis and analysis['confidence'] > 0:
                confidence_text = f"{self.translator.get_text('confidence')} {analysis['confidence']:.2f}"
                self._put_text_utf8(image, confidence_text, (text_margin, y_offset), 
                           font, sub_font_scale, self.colors['text'], 1)
            
            if 'frame_consistency' in analysis:
                consistency_text = f"{self.translator.get_text('consistency')} {analysis['frame_consistency']:.2f}"
                self._put_text_utf8(image, consistency_text, (text_margin + int(180 * scale_factor), y_offset), 
                           font, sub_font_scale, self.colors['text'], 1)
            
            y_offset += int(25 * scale_factor)
        
        # List issues with severity indicators
        for i, issue in enumerate(analysis['issues']):
            # Add severity indicator based on issue type
            severity = "●" if "poor" in issue.lower() or "multiple" in issue.lower() else "○"
            # Les issues sont déjà traduites par l'analyzer
            issue_text = f"{severity} {issue}"
            self._put_text_utf8(image, issue_text, (text_margin, y_offset + i * int(20 * scale_factor)), 
                       font, sub_font_scale, color, 1)
        
        # Show angle measurements if available and enabled
        if (self.show_measurements_box and hasattr(self, 'show_measurements') and 
            getattr(self, 'show_measurements', True) and 'angles' in analysis and analysis['angles']):
            
            angle_y = y_offset + len(analysis['issues']) * int(20 * scale_factor) + int(15 * scale_factor)
            
            # Draw close button for measurements
            self._draw_close_button(image, text_margin + int(250 * scale_factor), angle_y - int(5 * scale_factor), scale_factor, 'measurements')
            
            self._put_text_utf8(image, self.translator.get_text('measurements'), (text_margin, angle_y), 
                       font, sub_font_scale, self.colors['text'], 1)
            
            angle_info = []
            angles = analysis['angles']
            
            if 'head_forward_angle' in angles:
                angle_info.append(f"{self.translator.get_text('head_angle')} {angles['head_forward_angle']:.1f}°")
            if 'spine_angle' in angles:
                angle_info.append(f"{self.translator.get_text('spine_angle')} {angles['spine_angle']:.1f}°")
            if 'shoulder_roll_angle' in angles:
                angle_info.append(f"{self.translator.get_text('shoulder_roll')} {angles['shoulder_roll_angle']:.1f}°")
            
            for i, info in enumerate(angle_info[:3]):  # Show max 3 measurements
                self._put_text_utf8(image, info, (text_margin, angle_y + int(18 * scale_factor) + i * int(15 * scale_factor)), 
                           font, detail_font_scale, self.colors['text'], 1)
    
    def draw_posture_guidelines(self, image: np.ndarray):
        """Draw enhanced posture guidelines on the image."""
        if not self.show_guidelines_box:
            return
            
        guidelines = [
            self.translator.get_text('posture_guidelines'),
            self.translator.get_text('head_above_shoulders'),
            self.translator.get_text('ears_aligned'), 
            self.translator.get_text('shoulders_level'),
            self.translator.get_text('straight_spine'),
            self.translator.get_text('avoid_forward_head'),
            self.translator.get_text('stay_centered')
        ]
        
        # Calculate responsive sizing
        height, width = image.shape[:2]
        scale_factor = min(width / 640, height / 480)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4 * scale_factor
        
        # Position at bottom left with responsive sizing
        x_start = int(15 * scale_factor)
        box_width = int(350 * scale_factor)
        box_height = len(guidelines) * int(16 * scale_factor) + int(30 * scale_factor)
        y_start = height - box_height - int(10 * scale_factor)
        
        # Draw close button for guidelines box
        self._draw_close_button(image, box_width, y_start - int(5 * scale_factor), scale_factor, 'guidelines')
        
        # Draw background for better readability
        cv2.rectangle(image, (int(10 * scale_factor), y_start - int(15 * scale_factor)), 
                     (box_width, height - int(10 * scale_factor)), (0, 0, 0), -1)
        cv2.rectangle(image, (int(10 * scale_factor), y_start - int(15 * scale_factor)), 
                     (box_width, height - int(10 * scale_factor)), (50, 50, 50), 1)
        
        for i, guideline in enumerate(guidelines):
            y_pos = y_start + i * int(16 * scale_factor)
            color = self.colors['good'] if i == 0 else self.colors['text']
            weight = 2 if i == 0 else 1
            self._put_text_utf8(image, guideline, (x_start, y_pos), 
                       font, font_scale, color, weight)
    
    def draw_controls_help(self, image: np.ndarray, sensitivity: str, monitoring_enabled: bool, show_info_panels: bool = True):
        """Draw control instructions on the image."""
        if not show_info_panels or not self.show_controls_box:
            return  # Don't draw if info panels are hidden or controls box is closed
            
        # Translate sensitivity
        sensitivity_key = self._map_sensitivity_to_key(sensitivity)
        translated_sensitivity = self.translator.get_text(sensitivity_key)
        monitoring_text = self.translator.get_text('monitoring_on') if monitoring_enabled else self.translator.get_text('monitoring_off')
        
        controls = [
            self.translator.get_text('balanced_accuracy'),
            f"{self.translator.get_text('space_toggle')}: {monitoring_text}",
            f"{self.translator.get_text('s_sensitivity')}: {translated_sensitivity.upper()}",
            f"{self.translator.get_text('c_calibrate')} | {self.translator.get_text('i_info_panels')}",
            f"{self.translator.get_text('m_measurements')} | {self.translator.get_text('g_guidelines')}",
            f"{self.translator.get_text('h_controls_help')} | {self.translator.get_text('l_language')}",
            f"{self.translator.get_text('esc_exit')} | {self.translator.get_text('click_x_close')}"
        ]
        
        # Calculate responsive sizing
        height, width = image.shape[:2]
        scale_factor = min(width / 640, height / 480)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4 * scale_factor
        
        # Position at bottom right with responsive sizing
        box_width = int(320 * scale_factor)
        box_height = len(controls) * int(18 * scale_factor) + int(20 * scale_factor)
        x_start = width - box_width - int(10 * scale_factor)
        y_start = height - box_height - int(10 * scale_factor)
        
        # Draw background
        cv2.rectangle(image, (x_start - int(10 * scale_factor), y_start - int(10 * scale_factor)), 
                     (width - int(5 * scale_factor), height - int(5 * scale_factor)), 
                     (0, 0, 0), -1)
        
        # Draw close button for controls box
        self._draw_close_button(image, width - int(5 * scale_factor), y_start - int(5 * scale_factor), scale_factor, 'controls')
        
        for i, control in enumerate(controls):
            y_pos = y_start + i * int(18 * scale_factor)
            if i == 0:  # Balanced mode indicator
                color = self.colors['fair']  # Yellow to indicate balanced
                weight = 2
            elif 'ON' in control:
                color = self.colors['good']
                weight = 1
            else:
                color = self.colors['text']
                weight = 1
            self._put_text_utf8(image, control, (x_start, y_pos), 
                       font, font_scale, color, weight)
    
    def play_alert_sound(self):
        """Play alert sound (if sound is enabled)."""
        if not self.sound_enabled:
            return
        
        try:
            # Generate a simple beep sound
            duration = 200  # milliseconds
            sample_rate = 22050
            t = np.linspace(0, duration / 1000, int(sample_rate * duration / 1000))
            frequency = 800  # Hz
            wave = np.sin(frequency * 2 * np.pi * t) * 0.3
            
            # Convert to 16-bit integers and ensure C-contiguous
            wave = (wave * 32767).astype(np.int16)
            wave = np.ascontiguousarray(wave)
            
            # Create stereo sound
            stereo_wave = np.array([wave, wave]).T
            stereo_wave = np.ascontiguousarray(stereo_wave)
            
            # Play sound
            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.play()
        except Exception as e:
            print(f"Could not play sound: {e}")
            self.sound_enabled = False