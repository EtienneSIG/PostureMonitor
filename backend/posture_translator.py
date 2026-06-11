#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation system for the Posture Monitor application.
Supports English and French languages.
"""

class PostureTranslator:
    """Handles language translation for the posture monitoring application."""
    
    def __init__(self, language='en'):
        self.current_language = language
        
        # Translation dictionaries
        self.translations = {
            'en': {
                # Status messages
                'excellent_posture': 'Excellent Posture',
                'good_posture': 'Good Posture',
                'fair_posture': 'Fair Posture',
                'poor_posture': 'Poor Posture',
                'no_detection': 'No Pose Detected',
                'unknown': 'Unknown Status',
                'disabled': 'Monitoring Disabled',
                'monitoring_on': 'ON',
                'monitoring_off': 'OFF',
                'balanced_accuracy': 'Balanced Accuracy Mode',
                
                # Instructions and guidelines
                'position_yourself': 'Position yourself in the camera view',
                'posture_guidelines': 'Enhanced Posture Guidelines:',
                'head_above_shoulders': '• Head directly above shoulders',
                'ears_aligned': '• Ears aligned with shoulders',
                'shoulders_level': '• Keep shoulders level & relaxed',
                'straight_spine': '• Maintain straight, vertical spine',
                'avoid_forward_head': '• Avoid forward head position',
                'stay_centered': '• Keep body centered & balanced',
                
                # Controls help
                'controls': 'Controls:',
                'space_toggle': 'Space: Toggle monitoring',
                'c_calibrate': 'C: Calibrate posture',
                's_sensitivity': 'S: Change sensitivity',
                'i_info_panels': 'I: Toggle info panels',
                'm_measurements': 'M: Toggle measurements',
                'g_guidelines': 'G: Toggle guidelines',
                'h_controls_help': 'H: Toggle controls help',
                'l_language': 'L: Toggle language',
                'esc_exit': 'ESC: Exit',
                'click_x_close': 'Click X to close boxes',
                
                # Measurements
                'measurements': 'Measurements:',
                'confidence': 'Confidence:',
                'consistency': 'Consistency:',
                'head_angle': 'Head angle:',
                'spine_angle': 'Spine angle:',
                'shoulder_roll': 'Shoulder roll:',
                
                # Issues
                'head_forward': 'Forward head posture',
                'shoulders_uneven': 'Uneven shoulders',
                'spine_curved': 'Curved spine',
                'poor_overall_posture': 'Poor overall posture',
                'multiple_issues': 'Multiple posture issues detected',
                'leaning_detected': 'Body leaning detected',
                'head_tilt': 'Head tilt detected',
                
                # Posture issues messages
                'subtle_head_forward_detected': 'Subtle head forward detected - small correction needed',
                'combined_posture_issue': 'Combined posture issue: Forward head and elevated shoulders',
                'shoulder_tension_detected': 'Shoulder tension detected - one shoulder higher than the other',
                'shoulders_too_elevated_detailed': 'Shoulders too elevated - actively lower shoulders, drop arms',
                'shoulder_imbalance_adjust': 'Shoulder imbalance - adjust shoulder position',
                'significant_forward_head': 'Significant forward head posture - pull chin back, align ears over shoulders',
                'forward_head_posture': 'Forward head posture - pull chin back, straighten neck',
                'desk_shoulder_head_combo': 'Desk posture: Shoulder tension combined with forward head - adjust posture completely',
                'desk_uneven_tension': 'Desk posture: Uneven shoulder tension - adjust seating position',
                'desk_shoulders_elevated': 'Desk posture: Shoulders elevated - relax and drop shoulders',
                'desk_shoulder_imbalance': 'Desk posture: Shoulder imbalance - check monitor position',
                'head_tilted_left': 'Head tilted left - straighten head position',
                'head_tilted_right': 'Head tilted right - straighten head position',
                'arms_too_close': 'Arms too close to body - adjust desk/chair height',
                
                # Sensitivity levels
                'low_sensitivity': 'Low',
                'medium_sensitivity': 'Medium',
                'high_sensitivity': 'High',
                
                # UI elements
                'close': '×',
                'language_code': 'EN',
                
                # GUI Labels and Buttons
                'language_button': 'Language',
                'sensitivity_button': 'Sensitivity',
                'guidelines_button': 'Guidelines',
                'calibration_button': 'Calibrate',
                'controls_button': 'Controls',
                'measurements_button': 'Measurements',
                'status_panel': 'Status',
                'title': 'Posture Monitor',
                
                # Calibration
                'calibration_complete': 'Calibration complete!',
                'calibration_in_progress': 'Calibrating... Please maintain good posture',
                
                # Thresholds and adjustments
                'threshold_adjusted': 'Threshold adjusted for better comfort',
                'sensitivity_changed': 'Sensitivity level changed',
                
                # System messages  
                'monitoring_disabled': 'Monitoring disabled',
                'no_video_signal': 'No video signal',
                'camera_not_available': 'Camera not available',
                'camera_error': 'Camera error',
                'camera_capture_failed': 'Camera opened but cannot capture frames'
            },
            
            'fr': {
                # Status messages
                'excellent_posture': 'Excellente Posture',
                'good_posture': 'Bonne Posture',
                'fair_posture': 'Posture Acceptable',
                'poor_posture': 'Mauvaise Posture',
                'no_detection': 'Aucune Pose Détectée',
                'unknown': 'Statut Inconnu',
                'disabled': 'Surveillance Désactivée',
                'monitoring_on': 'ACTIVÉ',
                'monitoring_off': 'DÉSACTIVÉ',
                'balanced_accuracy': 'Mode Précision Équilibrée',
                
                # Instructions and guidelines
                'position_yourself': 'Positionnez-vous dans le champ de la caméra',
                'posture_guidelines': 'Conseils de Posture Améliorés:',
                'head_above_shoulders': '• Tête directement au-dessus des épaules',
                'ears_aligned': '• Oreilles alignées avec les épaules',
                'shoulders_level': '• Garder les épaules nivelées et détendues',
                'straight_spine': '• Maintenir une colonne vertébrale droite',
                'avoid_forward_head': '• Éviter la position tête en avant',
                'stay_centered': '• Garder le corps centré et équilibré',
                
                # Controls help
                'controls': 'Contrôles:',
                'space_toggle': 'Espace: Activer/Désactiver surveillance',
                'c_calibrate': 'C: Calibrer la posture',
                's_sensitivity': 'S: Changer la sensibilité',
                'i_info_panels': 'I: Activer/Désactiver panneaux info',
                'm_measurements': 'M: Activer/Désactiver mesures',
                'g_guidelines': 'G: Activer/Désactiver conseils',
                'h_controls_help': 'H: Activer/Désactiver aide contrôles',
                'l_language': 'L: Changer de langue',
                'esc_exit': 'ESC: Quitter',
                'click_x_close': 'Cliquez X pour fermer les boîtes',
                
                # Measurements
                'measurements': 'Mesures:',
                'confidence': 'Confiance:',
                'consistency': 'Consistance:',
                'head_angle': 'Angle de tête:',
                'spine_angle': 'Angle de colonne:',
                'shoulder_roll': 'Roulement d\'épaules:',
                
                # Issues
                'head_forward': 'Posture tête en avant',
                'shoulders_uneven': 'Épaules inégales',
                'spine_curved': 'Colonne courbée',
                'poor_overall_posture': 'Mauvaise posture générale',
                'multiple_issues': 'Multiples problèmes de posture détectés',
                'leaning_detected': 'Inclinaison du corps détectée',
                'head_tilt': 'Inclinaison de tête détectée',
                
                # Posture issues messages
                'subtle_head_forward_detected': 'Légère tête en avant détectée - petite correction nécessaire',
                'combined_posture_issue': 'Problème de posture combiné: Tête en avant et épaules élevées',
                'shoulder_tension_detected': 'Tension d\'épaule détectée - une épaule plus haute que l\'autre',
                'shoulders_too_elevated_detailed': 'Épaules trop élevées - baissez activement les épaules, détendez les bras',
                'shoulder_imbalance_adjust': 'Déséquilibre des épaules - ajustez la position des épaules',
                'significant_forward_head': 'Posture de tête significativement en avant - tirez le menton vers l\'arrière, alignez les oreilles sur les épaules',
                'forward_head_posture': 'Posture tête en avant - tirez le menton vers l\'arrière, redressez le cou',
                'desk_shoulder_head_combo': 'Posture bureau: Tension d\'épaule combinée avec tête en avant - ajustez complètement la posture',
                'desk_uneven_tension': 'Posture bureau: Tension inégale des épaules - ajustez la position assise',
                'desk_shoulders_elevated': 'Posture bureau: Épaules élevées - détendez et baissez les épaules',
                'desk_shoulder_imbalance': 'Posture bureau: Déséquilibre des épaules - vérifiez la position de l\'écran',
                'head_tilted_left': 'Tête inclinée à gauche - redressez la position de la tête',
                'head_tilted_right': 'Tête inclinée à droite - redressez la position de la tête',
                'arms_too_close': 'Bras trop près du corps - ajustez la hauteur du bureau/chaise',
                
                # Sensitivity levels
                'low_sensitivity': 'Faible',
                'medium_sensitivity': 'Moyenne',
                'high_sensitivity': 'Élevée',
                
                # UI elements
                'close': '×',
                'language_code': 'FR',
                
                # GUI Labels and Buttons
                'language_button': 'Langue',
                'sensitivity_button': 'Sensibilité',
                'guidelines_button': 'Conseils',
                'calibration_button': 'Calibrer',
                'controls_button': 'Contrôles',
                'measurements_button': 'Mesures',
                'status_panel': 'Statut',
                'title': 'Moniteur de Posture',
                
                # Calibration
                'calibration_complete': 'Calibration terminée!',
                'calibration_in_progress': 'Calibration en cours... Veuillez maintenir une bonne posture',
                
                # Thresholds and adjustments
                'threshold_adjusted': 'Seuil ajusté pour plus de confort',
                'sensitivity_changed': 'Niveau de sensibilité modifié',
                
                # System messages  
                'monitoring_disabled': 'Surveillance désactivée',
                'no_video_signal': 'Aucun signal vidéo',
                'camera_not_available': 'Caméra non disponible',
                'camera_error': 'Erreur de caméra',
                'camera_capture_failed': 'Caméra ouverte mais impossible de capturer des images'
            }
        }
    
    def get_text(self, key, default=None):
        """Get translated text for the given key in the current language."""
        try:
            if self.current_language in self.translations:
                if key in self.translations[self.current_language]:
                    return self.translations[self.current_language][key]
            
            # Fallback to English if current language doesn't have the key
            if 'en' in self.translations and key in self.translations['en']:
                return self.translations['en'][key]
            
            # Return default or key if no translation found
            return default if default is not None else key
        except Exception as e:
            print(f"Translation error for key '{key}': {e}")
            return default if default is not None else key
    
    def set_language(self, language):
        """Set the current language."""
        if language in self.translations:
            self.current_language = language
            return True
        return False
    
    def get_current_language(self):
        """Get the current language code."""
        return self.current_language
    
    def get_language_display(self):
        """Get language display code (EN/FR)."""
        return self.get_text('language_code')
    
    def get_available_languages(self):
        """Get list of available language codes."""
        return list(self.translations.keys())
    
    def toggle_language(self):
        """Toggle between available languages."""
        languages = self.get_available_languages()
        current_index = languages.index(self.current_language)
        next_index = (current_index + 1) % len(languages)
        self.current_language = languages[next_index]
        return self.current_language