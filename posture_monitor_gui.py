#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Posture Monitor GUI Application

A modern tkinter-based interface for real-time posture monitoring.
Provides easy-to-use controls for all features with a clean, professional interface.

Features:
- Clean, modern GUI with organized panels
- Easy toggle buttons for all features
- Language switching with one click
- Real-time posture status display
- Camera view embedded in the interface
- Professional settings panel

Author: Created with GitHub Copilot
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import mediapipe as mp
import threading
import time
from PIL import Image, ImageTk
import sys
import os
import locale

# Set UTF-8 encoding for the application
if sys.platform.startswith('win'):
    try:
        locale.setlocale(locale.LC_ALL, 'French_France.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        except:
            pass  # Use default locale if French not available

# Import our existing modules
from posture_analyzer import PostureAnalyzer
from posture_visualizer import PostureVisualizer
from posture_translator import PostureTranslator


class PostureMonitorGUI:
    """Modern GUI application for posture monitoring."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Posture Monitor Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Configure font to support French characters
        self.root.option_add('*Font', 'TkDefaultFont')
        
        # Set window icon and properties
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # Initialize components
        self.analyzer = PostureAnalyzer()
        self.visualizer = PostureVisualizer()
        self.translator = PostureTranslator()
        
        # Link translator to visualizer
        self.visualizer.translator = self.translator
        
        # Application state
        self.monitoring_enabled = True
        self.camera_active = False
        self.cap = None
        self.current_frame = None
        self.running = True
        self.last_frame_time = 0  # For frame rate limiting
        
        # Sound alert settings
        self.last_alert_time = 0
        self.alert_cooldown = 5.0  # seconds between sound alerts
        
        # UI state variables
        self.status_visible = tk.BooleanVar(value=True)
        self.measurements_visible = tk.BooleanVar(value=True)
        self.guidelines_visible = tk.BooleanVar(value=True)
        self.controls_visible = tk.BooleanVar(value=True)
        
        # Status variables
        self.current_status = tk.StringVar(value="Initializing...")
        self.current_confidence = tk.StringVar(value="N/A")
        self.current_language = tk.StringVar(value="English")
        self.current_sensitivity = tk.StringVar(value="Medium")
        
        # Create the GUI
        self.create_gui()
        
        # Initialize camera
        self.initialize_camera()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_gui(self):
        """Create the main GUI layout."""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Create panels
        self.create_control_panel(main_frame)
        self.create_camera_panel(main_frame)
        self.create_status_panel(main_frame)
    
    def create_control_panel(self, parent):
        """Create the control panel with buttons and settings."""
        # Control panel frame
        self.control_frame = ttk.LabelFrame(parent, text=self.translator.get_text('controls'), padding="10")
        self.control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        self.control_frame.columnconfigure(0, weight=1)
        
        # Monitoring control
        self.monitor_frame = ttk.LabelFrame(self.control_frame, text=self.translator.get_text('monitoring'), padding="10")
        self.monitor_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.monitor_frame.columnconfigure(0, weight=1)
        
        self.monitor_button = ttk.Button(
            self.monitor_frame, 
            text=self.translator.get_text('monitoring_on'), 
            command=self.toggle_monitoring,
            width=20
        )
        self.monitor_button.grid(row=0, column=0, pady=5)
        
        self.calibrate_button = ttk.Button(
            self.monitor_frame, 
            text=self.translator.get_text('calibrate_posture'), 
            command=self.calibrate_posture,
            width=20
        )
        self.calibrate_button.grid(row=1, column=0, pady=5)
        
        # Language control
        self.lang_frame = ttk.LabelFrame(self.control_frame, text=self.translator.get_text('language'), padding="10")
        self.lang_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.lang_frame.columnconfigure(0, weight=1)
        
        self.language_button = ttk.Button(
            self.lang_frame, 
            text=self.translator.get_text('english'), 
            command=self.toggle_language,
            width=20
        )
        self.language_button.grid(row=0, column=0, pady=5)
        
        # Sensitivity control
        self.sens_frame = ttk.LabelFrame(self.control_frame, text=self.translator.get_text('sensitivity'), padding="10")
        self.sens_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.sens_frame.columnconfigure(0, weight=1)
        
        self.sensitivity_var = tk.StringVar(value="medium")
        self.low_radio = ttk.Radiobutton(self.sens_frame, text=self.translator.get_text('low'), variable=self.sensitivity_var, 
                       value="low", command=self.change_sensitivity)
        self.low_radio.grid(row=0, column=0, sticky=tk.W)
        self.medium_radio = ttk.Radiobutton(self.sens_frame, text=self.translator.get_text('medium'), variable=self.sensitivity_var, 
                       value="medium", command=self.change_sensitivity)
        self.medium_radio.grid(row=1, column=0, sticky=tk.W)
        self.high_radio = ttk.Radiobutton(self.sens_frame, text=self.translator.get_text('high'), variable=self.sensitivity_var, 
                       value="high", command=self.change_sensitivity)
        self.high_radio.grid(row=2, column=0, sticky=tk.W)
        
        # Monitoring Mode control
        self.mode_frame = ttk.LabelFrame(self.control_frame, text=self.translator.get_text('monitoring_mode'), padding="10")
        self.mode_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.mode_frame.columnconfigure(0, weight=1)
        
        self.mode_var = tk.StringVar(value="general")
        self.general_radio = ttk.Radiobutton(
            self.mode_frame, 
            text=self.translator.get_text('general_mode'), 
            variable=self.mode_var,
            value="general", 
            command=self.change_monitoring_mode
        )
        self.general_radio.grid(row=0, column=0, sticky=tk.W)
        
        self.desk_radio = ttk.Radiobutton(
            self.mode_frame, 
            text=self.translator.get_text('desk_work_mode'), 
            variable=self.mode_var,
            value="desk_work", 
            command=self.change_monitoring_mode
        )
        self.desk_radio.grid(row=1, column=0, sticky=tk.W)
        
        # UI Visibility controls
        self.ui_frame = ttk.LabelFrame(self.control_frame, text=self.translator.get_text('interface_elements'), padding="10")
        self.ui_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.ui_frame.columnconfigure(0, weight=1)
        
        self.status_check = ttk.Checkbutton(self.ui_frame, text=self.translator.get_text('show_status_info'), 
                       variable=self.status_visible, command=self.update_ui_visibility)
        self.status_check.grid(row=0, column=0, sticky=tk.W)
        self.measurements_check = ttk.Checkbutton(self.ui_frame, text=self.translator.get_text('show_measurements'), 
                       variable=self.measurements_visible, command=self.update_ui_visibility)
        self.measurements_check.grid(row=1, column=0, sticky=tk.W)
        self.guidelines_check = ttk.Checkbutton(self.ui_frame, text=self.translator.get_text('show_guidelines'), 
                       variable=self.guidelines_visible, command=self.update_ui_visibility)
        self.guidelines_check.grid(row=2, column=0, sticky=tk.W)
        self.controls_check = ttk.Checkbutton(self.ui_frame, text=self.translator.get_text('show_controls_help'), 
                       variable=self.controls_visible, command=self.update_ui_visibility)
        self.controls_check.grid(row=3, column=0, sticky=tk.W)
        
        # Quick actions
        self.action_frame = ttk.LabelFrame(self.control_frame, text=self.translator.get_text('quick_actions'), padding="10")
        self.action_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.action_frame.columnconfigure(0, weight=1)
        
        # Audio alerts control
        self.audio_frame = ttk.LabelFrame(self.control_frame, text=self.translator.get_text('audio_alerts'), padding="10")
        self.audio_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.audio_frame.columnconfigure(0, weight=1)
        
        # Synchronize audio state with analyzer
        self.audio_enabled = self.analyzer.alerter.enabled
        button_text = 'disable_audio_alerts' if self.audio_enabled else 'enable_audio_alerts'
        self.audio_button = ttk.Button(
            self.audio_frame, 
            text=self.translator.get_text(button_text), 
            command=self.toggle_audio_alerts,
            width=20
        )
        self.audio_button.grid(row=0, column=0, pady=2)
        
        self.test_audio_button = ttk.Button(
            self.audio_frame, 
            text=self.translator.get_text('test_audio_alerts'), 
            command=self.test_audio_alerts,
            width=20
        )
        self.test_audio_button.grid(row=1, column=0, pady=2)
        
        self.configure_alerts_button = ttk.Button(
            self.audio_frame, 
            text=self.translator.get_text('configure_alerts'), 
            command=self.configure_alerts,
            width=20
        )
        self.configure_alerts_button.grid(row=2, column=0, pady=2)
        
        self.reset_button = ttk.Button(self.action_frame, text=self.translator.get_text('reset_all_settings'), 
                  command=self.reset_settings, width=20)
        self.reset_button.grid(row=0, column=0, pady=2)
        self.help_button = ttk.Button(self.action_frame, text=self.translator.get_text('show_help'), 
                  command=self.show_help, width=20)
        self.help_button.grid(row=1, column=0, pady=2)
        self.exit_button = ttk.Button(self.action_frame, text=self.translator.get_text('exit_application'), 
                  command=self.on_closing, width=20)
        self.exit_button.grid(row=2, column=0, pady=2)
    
    def create_camera_panel(self, parent):
        """Create the camera display panel."""
        self.camera_frame = ttk.LabelFrame(parent, text=self.translator.get_text('camera_view'), padding="10")
        self.camera_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.camera_frame.columnconfigure(0, weight=1)
        self.camera_frame.rowconfigure(0, weight=1)
        
        # Camera display label
        self.camera_label = ttk.Label(self.camera_frame, text=self.translator.get_text('camera_starting'), background="black", foreground="white")
        self.camera_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        # Camera controls
        self.cam_controls_frame = ttk.Frame(self.camera_frame)
        self.cam_controls_frame.grid(row=1, column=0, pady=(10, 0))
        
        self.camera_button = ttk.Button(self.cam_controls_frame, text=self.translator.get_text('start_camera'), command=self.toggle_camera)
        self.camera_button.grid(row=0, column=0, padx=5)
        
        self.screenshot_button = ttk.Button(self.cam_controls_frame, text=self.translator.get_text('save_screenshot'), command=self.save_screenshot)
        self.screenshot_button.grid(row=0, column=1, padx=5)
    
    def create_status_panel(self, parent):
        """Create the status information panel."""
        self.status_frame = ttk.LabelFrame(parent, text=self.translator.get_text('posture_status'), padding="10")
        self.status_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        self.status_frame.columnconfigure(0, weight=1)
        
        # Current status
        self.current_status_label = ttk.Label(self.status_frame, text=self.translator.get_text('current_status'), font=("Arial", 10, "bold"))
        self.current_status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.status_label = ttk.Label(self.status_frame, textvariable=self.current_status, 
                                     font=("Arial", 12), foreground="green")
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # Confidence
        self.confidence_title_label = ttk.Label(self.status_frame, text=self.translator.get_text('confidence'), font=("Arial", 10, "bold"))
        self.confidence_title_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.confidence_label = ttk.Label(self.status_frame, textvariable=self.current_confidence, 
                                         font=("Arial", 10))
        self.confidence_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        
        # Settings info
        self.settings_frame = ttk.LabelFrame(self.status_frame, text=self.translator.get_text('current_settings'), padding="5")
        self.settings_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.settings_frame.columnconfigure(1, weight=1)
        
        self.language_title_label = ttk.Label(self.settings_frame, text=self.translator.get_text('language') + ":")
        self.language_title_label.grid(row=0, column=0, sticky=tk.W)
        self.language_value_label = ttk.Label(self.settings_frame, textvariable=self.current_language)
        self.language_value_label.grid(row=0, column=1, sticky=tk.W)
        
        self.sensitivity_title_label = ttk.Label(self.settings_frame, text=self.translator.get_text('sensitivity') + ":")
        self.sensitivity_title_label.grid(row=1, column=0, sticky=tk.W)
        self.sensitivity_value_label = ttk.Label(self.settings_frame, textvariable=self.current_sensitivity)
        self.sensitivity_value_label.grid(row=1, column=1, sticky=tk.W)
        
        # Issues display
        self.issues_frame = ttk.LabelFrame(self.status_frame, text=self.translator.get_text('posture_issues'), padding="5")
        self.issues_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.issues_frame.columnconfigure(0, weight=1)
        self.issues_frame.rowconfigure(0, weight=1)
        
        # Scrollable text for issues
        self.issues_text = tk.Text(self.issues_frame, height=8, width=30, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(self.issues_frame, orient=tk.VERTICAL, command=self.issues_text.yview)
        self.issues_text.configure(yscrollcommand=scrollbar.set)
        
        self.issues_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def initialize_camera(self):
        """Initialize the camera in a separate thread with robust backend selection."""
        def init_camera():
            try:
                # Try DirectShow backend first (works better on Windows)
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                
                if not self.cap.isOpened():
                    # Fallback to default backend
                    print("DirectShow failed, trying default backend...")
                    self.cap = cv2.VideoCapture(0)
                
                if self.cap.isOpened():
                    # Configure camera
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Test frame capture to ensure camera actually works
                    ret, test_frame = self.cap.read()
                    if ret and test_frame is not None:
                        print(f"✅ Camera initialized successfully: {test_frame.shape}")
                        self.camera_active = True
                        self.root.after(0, lambda: self.camera_button.configure(text="📷 Stop Camera"))
                        # Start camera update in main thread
                        self.root.after(0, self.start_camera_update)
                    else:
                        print("❌ Camera opened but cannot capture frames")
                        self.cap.release()
                        self.root.after(0, lambda: self.camera_label.configure(text=self.translator.get_text('camera_capture_failed')))
                else:
                    self.root.after(0, lambda: self.camera_label.configure(text=self.translator.get_text('camera_not_available')))
            except Exception as e:
                print(f"Camera initialization error: {e}")
                self.root.after(0, lambda: self.camera_label.configure(text=f"{self.translator.get_text('camera_error')}: {e}"))
        
        threading.Thread(target=init_camera, daemon=True).start()
    
    def start_camera_update(self):
        """Start the camera update loop using Tkinter's after method."""
        print("🎬 Starting camera update loop...")
        self.last_frame_time = time.time()
        self.update_camera_frame()
    
    def update_camera_frame(self):
        """Update a single camera frame - called by Tkinter's after method."""
        if not self.running or not self.camera_active:
            return
        
        try:
            current_time = time.time()
            frame_interval = 1.0 / 15  # 15 FPS
            
            # Limit frame rate
            if current_time - getattr(self, 'last_frame_time', 0) < frame_interval:
                # Schedule next update sooner
                self.root.after(10, self.update_camera_frame)
                return
            
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    # Validate frame
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        # Process frame
                        if self.monitoring_enabled:
                            processed_frame = self.process_frame(frame)
                        else:
                            processed_frame = cv2.flip(frame, 1)
                        
                        # Convert for display
                        try:
                            display_frame = self.prepare_frame_for_display(processed_frame)
                            if display_frame:
                                self.update_camera_display(display_frame)
                        except Exception as e:
                            print(f"Frame preparation error: {e}")
                    else:
                        print(f"Invalid frame shape: {frame.shape}")
                    
                    self.last_frame_time = current_time
                else:
                    print("Camera read failed")
            else:
                print("Camera not available")
        
        except Exception as e:
            print(f"Camera update error: {e}")
        
        # Schedule next update
        if self.running and self.camera_active:
            self.root.after(67, self.update_camera_frame)  # ~15 FPS (1000/15 ≈ 67ms)
    
    def process_frame(self, frame):
        """Process frame for posture analysis."""
        try:
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Analyze posture if monitoring is enabled
            if self.monitoring_enabled:
                analysis = self.analyzer.analyze_posture(frame)
                # Note: Status and message will be generated in update_status_display if needed
            else:
                # Default analysis when monitoring is disabled
                analysis = {
                    'status': 'disabled',
                    'message': self.translator.get_text('monitoring_disabled'),
                    'issues': [],
                    'angles': {},
                    'confidence': 0.0,
                    'key_points': {},
                    'landmarks': None,
                    'good_posture': True
                }
            
            # Update status in GUI (non-blocking)
            self.root.after(0, lambda a=analysis: self.update_status_display(a))
            
            # Add visualizations if enabled
            if (self.status_visible.get() or self.measurements_visible.get() or 
                self.guidelines_visible.get() or self.controls_visible.get()):
                # Update visualizer settings
                self.visualizer.show_status_box = self.status_visible.get()
                self.visualizer.show_measurements_box = self.measurements_visible.get()
                self.visualizer.show_guidelines_box = self.guidelines_visible.get()
                self.visualizer.show_controls_box = self.controls_visible.get()
                
                # Apply visualizations
                frame = self.visualizer.draw_posture_overlay(frame, analysis)
                
                if self.guidelines_visible.get():
                    self.visualizer.draw_posture_guidelines(frame)
                
                if self.controls_visible.get():
                    sensitivity = self.analyzer.get_sensitivity()
                    self.visualizer.draw_controls_help(frame, sensitivity, self.monitoring_enabled, True)
            
            return frame
            
        except Exception as e:
            print(f"Process frame error: {e}")
            return cv2.flip(frame, 1)  # Return basic flipped frame on error
    
    def prepare_frame_for_display(self, frame):
        """Prepare frame for tkinter display with enhanced error handling."""
        try:
            # Safety check for frame validity
            if frame is None or not isinstance(frame, np.ndarray) or len(frame.shape) != 3:
                # Return a black frame if invalid
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, self.translator.get_text('no_video_signal'), (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Ensure frame is the right data type
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            
            # Resize frame to fit display area
            height, width = frame.shape[:2]
            max_width = 600
            max_height = 450
            
            # Calculate scale and new dimensions
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Ensure minimum size
            if new_width < 10 or new_height < 10:
                new_width, new_height = 320, 240
            
            resized_frame = cv2.resize(frame, (new_width, new_height))
            
            # Convert BGR to RGB - ensure proper color conversion
            if len(resized_frame.shape) == 3:
                rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            else:
                # Handle grayscale
                rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_GRAY2RGB)
            
            # Ensure values are in valid range
            rgb_frame = np.clip(rgb_frame, 0, 255).astype(np.uint8)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            return photo
        
        except Exception as e:
            print(f"Frame preparation error: {e}")
            # Return a simple error image
            try:
                error_frame = np.zeros((240, 320, 3), dtype=np.uint8)
                cv2.putText(error_frame, "Video Error", (80, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                pil_error = Image.fromarray(error_frame)
                return ImageTk.PhotoImage(pil_error)
            except:
                return None
    
    def update_camera_display(self, photo):
        """Update the camera display with new frame."""
        try:
            if photo and hasattr(photo, 'width'):
                self.camera_label.configure(image=photo, text="")
                self.camera_label.image = photo  # Keep a reference
            else:
                self.camera_label.configure(text=self.translator.get_text('no_video_signal'), image="")
        except Exception as e:
            print(f"Display update error: {e}")
            self.camera_label.configure(text=f"Display Error: {e}", image="")
    
    def update_status_display(self, analysis):
        """Update the status display panel."""
        if analysis:
            # Generate status and message if not present in analysis
            if 'status' not in analysis or 'message' not in analysis:
                status, status_msg = self._generate_status_from_analysis(analysis)
            else:
                status = analysis.get('status', 'unknown')
                status_msg = analysis.get('message', 'Unknown')
            
            # Map status message to translation key
            status_key = self._map_status_to_key(status_msg)
            translated_status = self.translator.get_text(status_key, status_msg)
            self.current_status.set(translated_status)
            
            # Update status color and handle alerts
            if status == 'excellent':
                self.status_label.configure(foreground="darkgreen")
            elif status == 'good':
                self.status_label.configure(foreground="green")
            elif status == 'fair':
                self.status_label.configure(foreground="orange")
                # Play alert for fair posture using centralized system
                if self.monitoring_enabled:
                    issues = analysis.get('issues', [])
                    self.analyzer.alerter.alert_for_status(status, status_msg, issues)
            elif status == 'poor':
                self.status_label.configure(foreground="red")
                # Play sound alert for poor posture using the centralized alert system
                if self.monitoring_enabled:
                    # Use the analyzer's alert system instead of direct sound
                    issues = analysis.get('issues', [])
                    self.analyzer.alerter.alert_for_status(status, status_msg, issues)
            elif status == 'no_detection':
                self.status_label.configure(foreground="gray")
            elif status == 'disabled':
                self.status_label.configure(foreground="blue")
            else:
                self.status_label.configure(foreground="black")
            
            # Update confidence
            confidence = analysis.get('confidence', 0)
            self.current_confidence.set(f"{confidence:.2f}")
            
            # Update issues
            issues = analysis.get('issues', [])
            self.update_issues_display(issues)
    
    def update_issues_display(self, issues):
        """Update the issues display area."""
        self.issues_text.configure(state=tk.NORMAL)
        self.issues_text.delete(1.0, tk.END)
        
        if issues:
            for i, issue in enumerate(issues):
                # Les issues sont déjà traduites par l'analyzer
                self.issues_text.insert(tk.END, f"• {issue}\n")
        else:
            self.issues_text.insert(tk.END, self.translator.get_text('excellent_posture'))
        
        self.issues_text.configure(state=tk.DISABLED)
    
    def toggle_monitoring(self):
        """Toggle posture monitoring."""
        self.monitoring_enabled = not self.monitoring_enabled
        if self.monitoring_enabled:
            self.monitor_button.configure(text=self.translator.get_text('monitoring_on'))
        else:
            self.monitor_button.configure(text=self.translator.get_text('monitoring_off'))
    
    def toggle_camera(self):
        """Toggle camera on/off."""
        if self.camera_active:
            self.camera_active = False
            self.camera_button.configure(text=self.translator.get_text('start_camera'))
            self.camera_label.configure(image="", text=self.translator.get_text('camera_stopped'))
            if self.cap:
                self.cap.release()
        else:
            self.initialize_camera()
    
    def toggle_language(self):
        """Toggle between English and French."""
        self.translator.toggle_language()
        # Synchronize analyzer translator
        self.analyzer.set_translator_language(self.translator.current_language)
        self.update_ui_texts()
        
        # Update language display
        new_lang = self.translator.get_language_display()
        if new_lang == "EN":
            self.current_language.set("English")
        else:
            self.current_language.set("Français")
    
    def update_ui_texts(self):
        """Update all UI text elements with current language."""
        # Update main frames
        self.control_frame.configure(text=self.translator.get_text('controls'))
        self.monitor_frame.configure(text=self.translator.get_text('monitoring'))
        self.lang_frame.configure(text=self.translator.get_text('language'))
        self.sens_frame.configure(text=self.translator.get_text('sensitivity'))
        self.ui_frame.configure(text=self.translator.get_text('interface_elements'))
        self.action_frame.configure(text=self.translator.get_text('quick_actions'))
        self.camera_frame.configure(text=self.translator.get_text('camera_view'))
        self.status_frame.configure(text=self.translator.get_text('posture_status'))
        
        # Update buttons
        if self.monitoring_enabled:
            self.monitor_button.configure(text=self.translator.get_text('monitoring_on'))
        else:
            self.monitor_button.configure(text=self.translator.get_text('monitoring_off'))
        
        self.calibrate_button.configure(text=self.translator.get_text('calibrate_posture'))
        
        # Update language button
        if self.translator.get_current_language() == 'en':
            self.language_button.configure(text=self.translator.get_text('english'))
        else:
            self.language_button.configure(text=self.translator.get_text('french'))
        
        # Update sensitivity radio buttons
        self.low_radio.configure(text=self.translator.get_text('low'))
        self.medium_radio.configure(text=self.translator.get_text('medium'))
        self.high_radio.configure(text=self.translator.get_text('high'))
        
        # Update checkboxes
        self.status_check.configure(text=self.translator.get_text('show_status_info'))
        self.measurements_check.configure(text=self.translator.get_text('show_measurements'))
        self.guidelines_check.configure(text=self.translator.get_text('show_guidelines'))
        self.controls_check.configure(text=self.translator.get_text('show_controls_help'))
        
        # Update action buttons
        self.reset_button.configure(text=self.translator.get_text('reset_all_settings'))
        self.help_button.configure(text=self.translator.get_text('show_help'))
        self.exit_button.configure(text=self.translator.get_text('exit_application'))
        
        # Update audio alert frame and buttons
        self.audio_frame.configure(text=self.translator.get_text('audio_alerts'))
        if self.audio_enabled:
            self.audio_button.configure(text=self.translator.get_text('disable_audio_alerts'))
        else:
            self.audio_button.configure(text=self.translator.get_text('enable_audio_alerts'))
        self.test_audio_button.configure(text=self.translator.get_text('test_audio_alerts'))
        self.configure_alerts_button.configure(text=self.translator.get_text('configure_alerts'))
        
        # Update camera controls
        if self.camera_active:
            self.camera_button.configure(text=self.translator.get_text('stop_camera'))
        else:
            self.camera_button.configure(text=self.translator.get_text('start_camera'))
        self.screenshot_button.configure(text=self.translator.get_text('save_screenshot'))
        
        # Update status panel labels
        self.current_status_label.configure(text=self.translator.get_text('current_status'))
        self.confidence_title_label.configure(text=self.translator.get_text('confidence'))
        self.settings_frame.configure(text=self.translator.get_text('current_settings'))
        self.language_title_label.configure(text=self.translator.get_text('language') + ":")
        self.sensitivity_title_label.configure(text=self.translator.get_text('sensitivity') + ":")
        self.issues_frame.configure(text=self.translator.get_text('posture_issues'))
    
    def calibrate_posture(self):
        """Calibrate posture thresholds to current position."""
        if self.camera_active and self.cap:
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
                
                # Process frame with MediaPipe to get landmarks
                results = self.analyzer.pose.process(rgb_frame)
                
                if results.pose_landmarks:
                    # Extract key points
                    key_points = self.analyzer.extract_key_landmarks(results.pose_landmarks)
                    
                    if key_points and self.analyzer.calibrate_to_current_posture(key_points):
                        messagebox.showinfo(self.translator.get_text('calibration_title'), 
                            self.translator.get_text('calibration_success'))
                    else:
                        messagebox.showwarning(self.translator.get_text('calibration_title'), 
                            self.translator.get_text('calibration_failed'))
                else:
                    messagebox.showwarning(self.translator.get_text('calibration_title'), 
                        self.translator.get_text('calibration_no_person'))
            else:
                messagebox.showwarning(self.translator.get_text('calibration_title'), 
                    self.translator.get_text('calibration_no_camera'))
        else:
            messagebox.showwarning(self.translator.get_text('calibration_title'), 
                self.translator.get_text('calibration_camera_inactive'))
    
    def change_sensitivity(self):
        """Change sensitivity level."""
        sensitivity = self.sensitivity_var.get()
        self.analyzer.set_sensitivity(sensitivity)
        self.current_sensitivity.set(sensitivity.capitalize())
    
    def change_monitoring_mode(self):
        """Change monitoring mode between general and desk work."""
        mode = self.mode_var.get()
        self.analyzer.set_monitoring_mode(mode)
        print(f"Switched to {mode} mode")  # Debug info
    
    def update_ui_visibility(self):
        """Update UI element visibility."""
        # This will be handled in the process_frame method
        pass
    
    def reset_settings(self):
        """Reset all settings to defaults."""
        self.monitoring_enabled = True
        self.monitor_button.configure(text="🟢 Monitoring ON")
        
        self.sensitivity_var.set("medium")
        self.analyzer.set_sensitivity("medium")
        self.current_sensitivity.set("Medium")
        
        self.mode_var.set("general")
        self.analyzer.set_monitoring_mode("general")
        
        self.status_visible.set(True)
        self.measurements_visible.set(True)
        self.guidelines_visible.set(True)
        self.controls_visible.set(True)
        
        messagebox.showinfo(self.translator.get_text('reset_title'), 
            self.translator.get_text('reset_message'))
    
    def save_screenshot(self):
        """Save a screenshot of the current frame."""
        if self.current_frame is not None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"posture_screenshot_{timestamp}.jpg"
            cv2.imwrite(filename, self.current_frame)
            messagebox.showinfo(self.translator.get_text('screenshot_title'), 
                f"{self.translator.get_text('screenshot_saved')} {filename}")
        else:
            messagebox.showwarning(self.translator.get_text('screenshot_title'), 
                self.translator.get_text('screenshot_no_frame'))
    
    def show_help(self):
        """Show help dialog."""
        help_text = f"""
Posture Monitor Pro - {self.translator.get_text('help_title').split(' - ')[1]}

{self.translator.get_text('monitoring_section')}
{self.translator.get_text('monitoring_help_1')}
{self.translator.get_text('monitoring_help_2')}

{self.translator.get_text('language_section')}
{self.translator.get_text('language_help_1')}
{self.translator.get_text('language_help_2')}

{self.translator.get_text('sensitivity_section')}
{self.translator.get_text('sensitivity_help_1')}
{self.translator.get_text('sensitivity_help_2')}
{self.translator.get_text('sensitivity_help_3')}

{self.translator.get_text('interface_section')}
{self.translator.get_text('interface_help_1')}
{self.translator.get_text('interface_help_2')}
{self.translator.get_text('interface_help_3')}
{self.translator.get_text('interface_help_4')}
{self.translator.get_text('interface_help_5')}

{self.translator.get_text('camera_section')}
{self.translator.get_text('camera_help_1')}
{self.translator.get_text('camera_help_2')}

{self.translator.get_text('tips_section')}
{self.translator.get_text('tips_help_1')}
{self.translator.get_text('tips_help_2')}
{self.translator.get_text('tips_help_3')}
{self.translator.get_text('tips_help_4')}
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title(self.translator.get_text('help_title'))
        help_window.geometry("600x500")
        help_window.resizable(False, False)
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(help_window, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert(1.0, help_text)
        text_widget.configure(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def toggle_audio_alerts(self):
        """Toggle audio alerts on/off."""
        self.audio_enabled = self.analyzer.toggle_audio_alerts()
        
        if self.audio_enabled:
            self.audio_button.configure(text=self.translator.get_text('disable_audio_alerts'))
        else:
            self.audio_button.configure(text=self.translator.get_text('enable_audio_alerts'))
        
        status = "activées" if self.audio_enabled else "désactivées" 
        print(f"Alertes audio {status}")
    
    def test_audio_alerts(self):
        """Test the audio alert system."""
        self.analyzer.test_audio_alerts()
        print("Test des alertes audio - vous devriez entendre un bip simple puis un double bip")
    
    def configure_alerts(self):
        """Open alert configuration window."""
        # Create configuration window
        config_window = tk.Toplevel(self.root)
        config_window.title(self.translator.get_text('alert_configuration'))
        config_window.geometry("400x500")
        config_window.resizable(False, False)
        
        # Make window modal
        config_window.transient(self.root)
        config_window.grab_set()
        
        # Center the window
        config_window.update_idletasks()
        x = (config_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (config_window.winfo_screenheight() // 2) - (500 // 2)
        config_window.geometry(f"+{x}+{y}")
        
        # Get current alert configuration
        current_config = self.analyzer.get_alert_config()
        
        # Create variables for checkboxes
        self.alert_vars = {}
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(config_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=self.translator.get_text('alert_configuration'), 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Checkboxes frame
        checkboxes_frame = ttk.LabelFrame(main_frame, text=self.translator.get_text('individual_alert_settings'), padding="10")
        checkboxes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Define alert types with their display names
        alert_types = [
            ('minor_issues', 'minor_issues'),
            ('multiple_issues', 'multiple_issues'),
            ('head_forward', 'head_forward'),
            ('head_tilt', 'head_tilt'),
            ('shoulders_uneven', 'shoulders_uneven'),
            ('shoulder_general', 'shoulder_general'),
            ('spine_curved', 'spine_curved'),
            ('poor_posture', 'poor_posture'),
            ('neck_forward', 'neck_forward'),
            ('shoulder_tension', 'shoulder_tension'),
            ('head_rotation', 'head_rotation'),
            ('subtle_head_forward', 'subtle_head_forward')
        ]
        
        # Create checkboxes
        for i, (alert_type, translation_key) in enumerate(alert_types):
            var = tk.BooleanVar(value=current_config.get(alert_type, False))
            self.alert_vars[alert_type] = var
            
            checkbox = ttk.Checkbutton(
                checkboxes_frame,
                text=self.translator.get_text(translation_key),
                variable=var
            )
            checkbox.grid(row=i, column=0, sticky=tk.W, pady=2, padx=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Quick action buttons
        quick_frame = ttk.Frame(buttons_frame)
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        enable_all_btn = ttk.Button(
            quick_frame,
            text=self.translator.get_text('enable_all'),
            command=lambda: self._set_all_alerts(True)
        )
        enable_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        disable_all_btn = ttk.Button(
            quick_frame,
            text=self.translator.get_text('disable_all'),
            command=lambda: self._set_all_alerts(False)
        )
        disable_all_btn.pack(side=tk.LEFT)
        
        # Save/Cancel buttons
        action_frame = ttk.Frame(buttons_frame)
        action_frame.pack(fill=tk.X)
        
        save_btn = ttk.Button(
            action_frame,
            text=self.translator.get_text('save_configuration'),
            command=lambda: self._save_alert_config(config_window)
        )
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(
            action_frame,
            text=self.translator.get_text('cancel'),
            command=config_window.destroy
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        # Store reference to window for helper methods
        self.config_window = config_window
    
    def _set_all_alerts(self, enabled):
        """Enable or disable all alert types."""
        for var in self.alert_vars.values():
            var.set(enabled)
    
    def _save_alert_config(self, window):
        """Save alert configuration and close window."""
        # Apply configuration to analyzer
        enabled_count = 0
        for alert_type, var in self.alert_vars.items():
            is_enabled = var.get()
            self.analyzer.set_alert_for_issue(alert_type, is_enabled)
            if is_enabled:
                enabled_count += 1
        
        # Si TOUTES les alertes sont désactivées, désactiver le système global aussi
        if enabled_count == 0:
            print("Toutes les alertes désactivées - désactivation du système global")
            self.analyzer.disable_audio_alerts()
            self.audio_enabled = False
            self.audio_button.configure(text=self.translator.get_text('enable_audio_alerts'))
        else:
            # Si au moins une alerte est activée, s'assurer que le système global est activé
            if not self.analyzer.alerter.enabled:
                print("Certaines alertes activées - réactivation du système global")
                self.analyzer.enable_audio_alerts()
                self.audio_enabled = True
                self.audio_button.configure(text=self.translator.get_text('disable_audio_alerts'))
        
        # Show confirmation with details
        message = f"{self.translator.get_text('config_saved_message')} {enabled_count}/{len(self.alert_vars)} {self.translator.get_text('alerts_enabled')}"
        messagebox.showinfo(self.translator.get_text('configuration'), message)
        
        # Close window
        window.destroy()
    
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
    
    def _generate_status_from_analysis(self, analysis):
        """Generate status and message from analysis results."""
        # Check if pose was detected
        if not analysis.get('key_points') or len(analysis.get('key_points', {})) == 0:
            return 'no_detection', 'No Pose Detected'
        
        # Get confidence and issues
        confidence = analysis.get('confidence', 0.0)
        issues = analysis.get('issues', [])
        good_posture = analysis.get('good_posture', True)
        
        # Determine status based on issues and confidence
        if not self.monitoring_enabled:
            return 'disabled', 'Monitoring Disabled'
        elif confidence < 0.3:
            return 'no_detection', 'No Pose Detected'
        elif len(issues) == 0 and good_posture:
            if confidence > 0.8:
                return 'excellent', 'Excellent Posture'
            else:
                return 'good', 'Good Posture'
        elif len(issues) == 1:
            return 'fair', 'Fair Posture'
        else:  # Multiple issues or bad posture
            return 'poor', 'Poor Posture'
    
    def on_closing(self):
        """Handle application closing."""
        self.running = False
        self.camera_active = False
        
        if self.cap:
            self.cap.release()
        
        # Close MediaPipe pose in analyzer
        if hasattr(self.analyzer, 'pose') and self.analyzer.pose:
            self.analyzer.pose.close()
        
        # Close any OpenCV windows
        cv2.destroyAllWindows()
        
        # Destroy the tkinter window
        self.root.destroy()


def main():
    """Main entry point for GUI application."""
    try:
        root = tk.Tk()
        app = PostureMonitorGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Failed to start GUI application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()