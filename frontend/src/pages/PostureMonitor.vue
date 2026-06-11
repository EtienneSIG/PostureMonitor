<template>
  <div class="pages">
    <div class="page-header">
      <h2>🎥 Posture Monitor</h2>
      <p>Live posture tracking with real-time alerts</p>
    </div>

    <div class="monitor-container">
      <div class="monitor-main">
        <div v-if="!isConnected" class="monitor-placeholder">
          <p>📹 Camera will display here</p>
          <button @click="startMonitoring" class="primary">Start Monitoring</button>
        </div>

        <div v-else class="monitor-status">
          <p>🟢 Connected</p>
        </div>

        <div v-if="currentMetrics" class="metrics-display">
          <div class="metric">
            <span class="metric-label">Spine Angle</span>
            <span class="metric-value">{{ currentMetrics.spine_angle?.toFixed(1) || '—' }}°</span>
          </div>
          <div class="metric">
            <span class="metric-label">Shoulder Symmetry</span>
            <span class="metric-value">{{ currentMetrics.shoulder_symmetry?.toFixed(1) || '—' }}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">Neck Angle</span>
            <span class="metric-value">{{ currentMetrics.neck_angle?.toFixed(1) || '—' }}°</span>
          </div>
        </div>

        <div v-if="currentMetrics?.alert" class="alert danger">
          ⚠️ Posture Alert! Please adjust your position.
        </div>
      </div>

      <div class="monitor-controls card">
        <h3>Controls</h3>

        <div class="control-section">
          <h4>Monitoring Status</h4>
          <button 
            v-if="!isMonitoring" 
            @click="startMonitoring"
            class="primary full-width"
          >
            Start
          </button>
          <button 
            v-else 
            @click="stopMonitoring"
            class="danger full-width"
          >
            Stop
          </button>
        </div>

        <div class="control-section">
          <h4>Sensitivity</h4>
          <div class="radio-group">
            <label class="radio">
              <input type="radio" v-model="sensitivity" value="low" />
              <span>Low</span>
            </label>
            <label class="radio">
              <input type="radio" v-model="sensitivity" value="medium" />
              <span>Medium</span>
            </label>
            <label class="radio">
              <input type="radio" v-model="sensitivity" value="high" />
              <span>High</span>
            </label>
          </div>
        </div>

        <div class="control-section">
          <label class="checkbox">
            <input type="checkbox" v-model="soundEnabled" />
            <span>Sound Alerts</span>
          </label>
        </div>

        <div class="control-section">
          <label class="checkbox">
            <input type="checkbox" v-model="visualAlerts" />
            <span>Visual Alerts</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const isMonitoring = ref(false)
const isConnected = ref(false)
const currentMetrics = ref(null)
const sensitivity = ref('medium')
const soundEnabled = ref(true)
const visualAlerts = ref(true)
let ws = null

const startMonitoring = () => {
  if (!userStore.userId) {
    alert('User not authenticated')
    return
  }

  isMonitoring.value = true
  
  // WebSocket connection
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//127.0.0.1:8000/ws/posture/${userStore.userId}`)

  ws.onopen = () => {
    isConnected.value = true
  }

  ws.onmessage = (event) => {
    currentMetrics.value = JSON.parse(event.data)
    
    if (currentMetrics.value.alert && soundEnabled.value) {
      playAlert()
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    isConnected.value = false
  }

  ws.onclose = () => {
    isConnected.value = false
    isMonitoring.value = false
  }
}

const stopMonitoring = () => {
  if (ws) {
    ws.close()
  }
  isMonitoring.value = false
  isConnected.value = false
}

const playAlert = () => {
  // Simple beep (in production, use proper audio file)
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  const oscillator = audioContext.createOscillator()
  const gainNode = audioContext.createGain()

  oscillator.connect(gainNode)
  gainNode.connect(audioContext.destination)

  oscillator.frequency.value = 800
  oscillator.type = 'sine'

  gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)

  oscillator.start(audioContext.currentTime)
  oscillator.stop(audioContext.currentTime + 0.5)
}
</script>

<style scoped>
.page-header {
  margin-bottom: 30px;
}

.monitor-container {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
}

.monitor-main {
  background: white;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  padding: 20px;
  aspect-ratio: 16 / 9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.monitor-placeholder {
  text-align: center;
  color: #a0aec0;
}

.monitor-placeholder p {
  margin-bottom: 20px;
  font-size: 18px;
}

.monitor-status {
  padding: 8px 16px;
  background: #c6f6d5;
  border-radius: 6px;
  color: #22543d;
  font-weight: 600;
  margin-bottom: 20px;
}

.metrics-display {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  width: 100%;
  margin-bottom: 20px;
}

.metric {
  background: #f7fafc;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  border-left: 3px solid #667eea;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #718096;
  margin-bottom: 4px;
}

.metric-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #667eea;
}

.monitor-controls h3 {
  margin-bottom: 20px;
}

.control-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.control-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.control-section h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #2d3748;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.radio input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.full-width {
  width: 100%;
}

@media (max-width: 1024px) {
  .monitor-container {
    grid-template-columns: 1fr;
  }

  .monitor-controls {
    max-width: none;
  }
}
</style>
