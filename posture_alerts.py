import pygame
import time
import threading
import json
import os

class PostureAlerter:
    def __init__(self):
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False
        self.alerts_enabled = True
        self.last_alert_time = 0
        self.alert_cooldown = 5.0
    
    def can_alert(self):
        if not self.alerts_enabled:
            return False
        current_time = time.time()
        return current_time - self.last_alert_time >= self.alert_cooldown
    
    def play_beep(self, frequency=800, duration=0.2):
        if self.sound_enabled and self.can_alert():
            self.last_alert_time = time.time()
    
    def play_double_beep(self):
        if self.sound_enabled and self.can_alert():
            def play():
                self.play_beep()
                time.sleep(0.1)
                self.play_beep()
            threading.Thread(target=play, daemon=True).start()
    
    def trigger_alert(self, analysis):
        if not self.can_alert():
            return
        try:
            status = analysis.get('status', 'unknown')
            issues = analysis.get('issues', [])
            if status == 'poor' or len(issues) > 1:
                print("🔊 Double beep: Multiple posture problems detected!")
                self.play_double_beep()
            elif status in ['fair', 'warning'] or len(issues) == 1:
                issue_type = issues[0] if issues else 'posture issue'
                print(f"🔊 Beep: {issue_type} detected!")
                self.play_beep()
        except:
            pass
    
    def set_enabled(self, enabled):
        self.alerts_enabled = enabled
    
    @property
    def enabled(self):
        """Propriété pour la compatibilité avec l'interface GUI."""
        return self.alerts_enabled
    
    @enabled.setter
    def enabled(self, value):
        """Setter pour la propriété enabled."""
        self.alerts_enabled = value
    
    def set_alert_for_issue(self, issue_type, enabled):
        """Activer/désactiver l'alerte pour un type de problème spécifique."""
        # Pour l'instant, on gère globalement
        pass
    
    def get_alert_config(self):
        """Obtenir la configuration actuelle des alertes."""
        return {
            'enabled': self.alerts_enabled,
            'sound_enabled': self.sound_enabled,
            'cooldown': self.alert_cooldown
        }
    
    def is_alert_enabled_for_issue(self, issue_type):
        """Vérifier si l'alerte est activée pour un type de problème."""
        return self.alerts_enabled
    
    def test_alerts(self):
        """Tester le système d'alertes."""
        if self.sound_enabled:
            print("🔊 Test des alertes sonores")
            self.play_beep()
    
    def play_alert(self, issue_type):
        """Play alert for specific issue type"""
        if not self.can_alert():
            return
        try:
            print(f"🚨 Alert: {issue_type} detected!")
            self.play_beep()
        except:
            pass
    
    def alert_for_status(self, status, status_msg, issues):
        """Trigger alerts based on status and issues"""
        if not self.can_alert():
            return
        try:
            if status == 'poor' or len(issues) > 1:
                print(f"🚨 Multiple issues: {status_msg}")
                self.play_double_beep()
            elif status in ['fair', 'warning'] or len(issues) == 1:
                issue_type = issues[0] if issues else 'posture issue'
                print(f"⚠️ Warning: {issue_type}")
                self.play_beep()
        except:
            pass
    
    def cleanup(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except:
            pass
