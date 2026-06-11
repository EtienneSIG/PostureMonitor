<template>
  <div class="pages">
    <div class="page-header">
      <h2>🎥 Posture Monitor</h2>
      <p>Live posture tracking with real-time alerts and personal calibration</p>
    </div>

    <div class="monitor-container">
      <div class="monitor-main">
        <div class="camera-panel">
          <video
            ref="videoPreview"
            class="camera-preview"
            autoplay
            muted
            playsinline
          ></video>
          <canvas ref="landmarkCanvas" class="landmark-overlay"></canvas>
          <div v-if="!isCameraReady" class="camera-overlay">
            <p v-if="cameraError">⚠️ {{ cameraError }}</p>
            <p v-else>📹 Camera preview will appear here</p>
          </div>
        </div>

        <div class="monitor-status" :class="isConnected ? 'ok' : 'warn'">
          <p v-if="isConnected">🟢 Connected to posture engine</p>
          <p v-else-if="monitoringError">🔴 {{ monitoringError }}</p>
          <p v-else>🟡 Ready to connect</p>
        </div>

        <div v-if="currentMetrics" class="metrics-display">
          <div class="metric" :class="getMetricAlertClass('spine_angle')">
            <span class="metric-label">Spine Angle</span>
            <span class="metric-value">{{ currentMetrics.spine_angle?.toFixed(1) || '—' }}°</span>
          </div>
          <div class="metric" :class="getMetricAlertClass('shoulder_symmetry')">
            <span class="metric-label">Shoulder Symmetry</span>
            <span class="metric-value">{{ currentMetrics.shoulder_symmetry?.toFixed(1) || '—' }}%</span>
          </div>
          <div class="metric" :class="getMetricAlertClass('neck_angle')">
            <span class="metric-label">Neck Angle</span>
            <span class="metric-value">{{ currentMetrics.neck_angle?.toFixed(1) || '—' }}°</span>
          </div>
          <div class="metric" :class="getHeadTiltClass('lr')">
            <span class="metric-label">Head Tilt L/R</span>
            <span class="metric-value">{{ currentMetrics.head_tilt_lr?.toFixed(1) || '—' }}°</span>
            <span class="metric-hint">{{ getHeadTiltDirection('lr') }}</span>
          </div>
          <div class="metric" :class="getHeadTiltClass('fwd')">
            <span class="metric-label">Head Forward</span>
            <span class="metric-value">{{ currentMetrics.head_forward_tilt?.toFixed(1) || '—' }}°</span>
            <span class="metric-hint">{{ getHeadTiltDirection('fwd') }}</span>
          </div>
        </div>

        <div v-if="baseline && calibratedDrift" class="drift-display">
          <p>
            Drift vs baseline:
            spine {{ calibratedDrift.spine_angle?.toFixed(1) ?? '—' }}°, 
            neck {{ calibratedDrift.neck_angle?.toFixed(1) ?? '—' }}°, 
            shoulder {{ calibratedDrift.shoulder_symmetry?.toFixed(1) ?? '—' }}%
          </p>
        </div>

        <div v-if="currentMetrics?.alert" class="alert danger">
          ⚠️ Posture Alert! Please adjust your position.
        </div>

        <div v-if="baseline" class="baseline-note">
          ✅ Personal baseline active. Metrics are adjusted to your morphology.
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
          <h4>Personal Calibration</h4>
          <p class="hint" v-if="!isManualCalibrating">
            Click on your body landmarks to manually adjust your posture points.
          </p>
          <div v-if="!isManualCalibrating" class="button-group">
            <button
              @click="startManualCalibration"
              class="secondary full-width"
              :disabled="!currentMetrics"
            >
              Manual Calibration
            </button>
            <button
              @click="captureBaseline"
              class="secondary full-width"
              :disabled="!currentMetrics"
              style="opacity: 0.6; font-size: 12px;"
            >
              Auto-Calibrate (old)
            </button>
          </div>
          <div v-else class="calibration-panel">
            <div class="calibration-info">
              <p><strong>Click on your {{ calibrationPointName }}</strong></p>
              <p class="calibration-hint">{{ calibrationPointHint }}</p>
              <div class="calibration-progress">
                {{ calibrationPointIndex + 1 }} / {{ calibrationPoints.length }}
              </div>
            </div>
            <div class="button-group">
              <button @click="skipCalibrationPoint" class="ghost full-width">
                Skip
              </button>
              <button @click="cancelManualCalibration" class="danger full-width">
                Cancel
              </button>
            </div>
          </div>
          <button
            v-if="baseline"
            @click="clearBaseline"
            class="ghost full-width"
            style="margin-top: 10px;"
          >
            Reset calibration
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

        <div class="control-section">
          <label class="checkbox">
            <input type="checkbox" v-model="showLandmarks" />
            <span>Show Body Landmarks</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useUserStore } from '../stores/userStore'

const props = defineProps({
  active: { type: Boolean, default: true }
})

const userStore = useUserStore()
const isMonitoring = ref(false)
const isConnected = ref(false)
const currentMetrics = ref(null)
const videoPreview = ref(null)
const landmarkCanvas = ref(null)
const isCameraReady = ref(false)
const cameraError = ref('')
const sensitivity = ref('medium')
const soundEnabled = ref(true)
const visualAlerts = ref(true)
const baseline = ref(null)
const monitoringError = ref('')
const showLandmarks = ref(true)
const isManualCalibrating = ref(false)
const calibrationPointIndex = ref(0)
const manualKeyPoints = ref({})
const currentSessionId = ref(null)
let mediaStream = null
let monitoringTimer = null
const isSendingFrame = ref(false)

const calibrationPoints = [
  { key: 'forehead', hint: 'Center of your forehead, between eyebrows' },
  { key: 'nose', hint: 'Tip of your nose' },
  { key: 'left_eye', hint: 'Left eye center' },
  { key: 'right_eye', hint: 'Right eye center' },
  { key: 'left_ear', hint: 'Left ear lobe' },
  { key: 'right_ear', hint: 'Right ear lobe' },
  { key: 'left_shoulder', hint: 'Top of left shoulder' },
  { key: 'right_shoulder', hint: 'Top of right shoulder' },
  { key: 'left_hip', hint: 'Left hip bone' },
  { key: 'right_hip', hint: 'Right hip bone' }
]

const calibrationPointName = computed(() => {
  if (calibrationPointIndex.value >= calibrationPoints.length) return '?'
  return calibrationPoints[calibrationPointIndex.value].key.replace('_', ' ')
})

const calibrationPointHint = computed(() => {
  if (calibrationPointIndex.value >= calibrationPoints.length) return ''
  return calibrationPoints[calibrationPointIndex.value].hint
})

const baselineStorageKey = computed(() => {
  const userPart = userStore.userId || 'anonymous'
  return `baseline:${userPart}`
})

const calibratedDrift = computed(() => {
  if (!currentMetrics.value) {
    return null
  }

  if (!baseline.value) {
    return null
  }

  const adjustMetric = (metricName) => {
    const currentValue = currentMetrics.value[metricName]
    if (typeof currentValue !== 'number') {
      return null
    }

    const baselineValue = baseline.value[metricName]
    if (typeof baselineValue !== 'number') {
      return currentValue
    }

    return currentValue - baselineValue
  }

  return {
    spine_angle: adjustMetric('spine_angle'),
    neck_angle: adjustMetric('neck_angle'),
    shoulder_symmetry: adjustMetric('shoulder_symmetry')
  }
})

const startCameraPreview = async () => {
  try {
    cameraError.value = ''
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    if (videoPreview.value) {
      videoPreview.value.srcObject = mediaStream
      await videoPreview.value.play()
      isCameraReady.value = true
    }
  } catch (error) {
    console.error('Camera access error:', error)
    cameraError.value = 'Unable to access camera. Check browser permissions.'
    isCameraReady.value = false
  }
}

const stopCameraPreview = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop())
    mediaStream = null
  }

  if (videoPreview.value) {
    videoPreview.value.srcObject = null
  }

  isCameraReady.value = false
  clearLandmarkOverlay()
}

const loadBaseline = () => {
  const raw = localStorage.getItem(baselineStorageKey.value)
  if (!raw) {
    baseline.value = null
    return
  }

  try {
    baseline.value = JSON.parse(raw)
  } catch {
    baseline.value = null
  }
}

const startMonitoring = () => {
  if (!userStore.userId) {
    alert('User not authenticated')
    return
  }

  if (!isCameraReady.value || !videoPreview.value?.srcObject) {
    alert('Camera is not ready. Please allow camera access first.')
    return
  }

  isMonitoring.value = true
  isConnected.value = false
  monitoringError.value = ''

  // Generate a new session id for this monitoring session
  currentSessionId.value = (crypto?.randomUUID && crypto.randomUUID()) ||
    `session-${Date.now()}-${Math.random().toString(36).slice(2)}`

  if (monitoringTimer) {
    clearInterval(monitoringTimer)
    monitoringTimer = null
  }

  runMonitoringTick()
  monitoringTimer = setInterval(runMonitoringTick, 900)
}

const stopMonitoring = () => {
  if (monitoringTimer) {
    clearInterval(monitoringTimer)
    monitoringTimer = null
  }

  isMonitoring.value = false
  isConnected.value = false
  monitoringError.value = ''
  currentSessionId.value = null
}

const runMonitoringTick = async () => {
  if (!isMonitoring.value || isSendingFrame.value) {
    return
  }

  try {
    isSendingFrame.value = true
    const blob = await captureFrameAsBlob()
    if (!blob) {
      return
    }

    const formData = new FormData()
    formData.append('file', blob, 'frame.jpg')

    const sessionParam = currentSessionId.value
      ? `&session_id=${encodeURIComponent(currentSessionId.value)}`
      : ''
    const response = await fetch(
      `/api/posture/analyze?user_id=${encodeURIComponent(userStore.userId)}${sessionParam}`,
      {
        method: 'POST',
        headers: {
          'X-User-Id': userStore.userId
        },
        body: formData
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP_${response.status}`)
    }

    const data = await response.json()
    currentMetrics.value = data
    isConnected.value = true
    monitoringError.value = ''
    drawLandmarkOverlay(data?.key_points || {})

    if (currentMetrics.value.alert && soundEnabled.value) {
      playAlert()
    }
  } catch (error) {
    console.error('Monitoring tick error:', error)
    isConnected.value = false
    if (error?.message?.startsWith('HTTP_')) {
      monitoringError.value = `Backend error (${error.message.replace('HTTP_', '')})`
    } else {
      monitoringError.value = 'Unable to send camera frame'
    }
  } finally {
    isSendingFrame.value = false
  }
}

const captureFrameAsBlob = () => {
  return new Promise((resolve) => {
    const video = videoPreview.value

    if (!video) {
      resolve(null)
      return
    }

    let width = video.videoWidth
    let height = video.videoHeight

    if ((!width || !height) && mediaStream) {
      const track = mediaStream.getVideoTracks()[0]
      const settings = track?.getSettings ? track.getSettings() : null
      width = Number(settings?.width || 0)
      height = Number(settings?.height || 0)
    }

    if (!width || !height) {
      monitoringError.value = 'Camera stream not ready yet'
      resolve(null)
      return
    }

    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')

    if (!ctx) {
      resolve(null)
      return
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.85)
  })
}

const drawLandmarkOverlay = (keyPoints) => {
  const canvas = landmarkCanvas.value
  const video = videoPreview.value
  
  // In manual calibration mode, always show overlay
  const shouldShow = isManualCalibrating.value || (showLandmarks.value && !isManualCalibrating.value)
  if (!canvas || !video || !shouldShow) {
    if (canvas) {
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      }
    }
    return
  }

  const width = video.clientWidth || video.videoWidth
  const height = video.clientHeight || video.videoHeight
  if (!width || !height) {
    return
  }

  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    return
  }

  ctx.clearRect(0, 0, width, height)

  // In manual calibration mode, draw manual points + auto-detected points as reference
  if (isManualCalibrating.value) {
    // Draw auto-detected points as light gray reference
    const autoPoints = Object.entries(keyPoints || {})
    const autoCanvasPoints = {}
    autoPoints.forEach(([name, value]) => {
      if (Array.isArray(value) && value.length >= 2) {
        autoCanvasPoints[name] = {
          x: width - (value[0] * width),
          y: value[1] * height
        }
      }
    })

    // Draw auto-detected points as gray circles (reference only)
    ctx.fillStyle = '#cbd5e1'
    ctx.strokeStyle = '#94a3b8'
    ctx.lineWidth = 1
    ctx.globalAlpha = 0.5
    Object.entries(autoCanvasPoints).forEach(([name, pos]) => {
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
    })
    ctx.globalAlpha = 1.0

    // Draw manual keypoints
    Object.entries(manualKeyPoints.value).forEach(([name, coords]) => {
      if (Array.isArray(coords) && coords.length >= 2) {
        const x = width - (coords[0] * width)
        const y = coords[1] * height

        // Green for completed points
        ctx.fillStyle = '#10b981'
        ctx.strokeStyle = '#0f172a'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.arc(x, y, 6, 0, Math.PI * 2)
        ctx.fill()
        ctx.stroke()

        const label = name.replace('_', ' ')
        ctx.fillStyle = '#0f172a'
        ctx.font = 'bold 11px sans-serif'
        ctx.fillText(label, x + 8, y - 8)
      }
    })

    // Draw instruction for current point to calibrate
    if (calibrationPointIndex.value < calibrationPoints.length) {
      const currentPointKey = calibrationPoints[calibrationPointIndex.value].key
      
      // Draw red circle for next point to click
      if (keyPoints[currentPointKey]) {
        const coords = keyPoints[currentPointKey]
        const x = width - (coords[0] * width)
        const y = coords[1] * height

        ctx.fillStyle = '#ef4444'
        ctx.strokeStyle = '#0f172a'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.arc(x, y, 7, 0, Math.PI * 2)
        ctx.fill()
        ctx.stroke()

        // Draw blinking circle
        ctx.strokeStyle = '#ef4444'
        ctx.lineWidth = 1
        ctx.globalAlpha = 0.6
        ctx.beginPath()
        ctx.arc(x, y, 12, 0, Math.PI * 2)
        ctx.stroke()
        ctx.globalAlpha = 1.0

        const label = currentPointKey.replace('_', ' ')
        ctx.fillStyle = '#ef4444'
        ctx.font = 'bold 11px sans-serif'
        ctx.fillText(label, x + 8, y - 8)
      }
    }

    return
  }

  // Normal mode (not calibrating) - show auto-detected points
  const points = Object.entries(keyPoints || {})
  if (!points.length) {
    return
  }

  // Convert normalized coordinates to canvas coordinates
  const canvasPoints = {}
  points.forEach(([name, value]) => {
    if (Array.isArray(value) && value.length >= 2) {
      canvasPoints[name] = {
        x: width - (value[0] * width),
        y: value[1] * height
      }
    }
  })

  // Draw segments between connected points
  const segments = [
    ['forehead', 'nose'],
    ['nose', 'left_ear'],
    ['nose', 'right_ear'],
    ['left_ear', 'left_shoulder'],
    ['right_ear', 'right_shoulder'],
    ['left_shoulder', 'right_shoulder'],
    ['left_shoulder', 'left_hip'],
    ['right_shoulder', 'right_hip'],
    ['left_hip', 'right_hip']
  ]

  ctx.strokeStyle = '#0f172a'
  ctx.lineWidth = 1.5
  ctx.globalAlpha = 0.6

  segments.forEach(([from, to]) => {
    if (canvasPoints[from] && canvasPoints[to]) {
      ctx.beginPath()
      ctx.moveTo(canvasPoints[from].x, canvasPoints[from].y)
      ctx.lineTo(canvasPoints[to].x, canvasPoints[to].y)
      ctx.stroke()
    }
  })

  ctx.globalAlpha = 1.0

  // Draw points
  ctx.fillStyle = '#22d3ee'
  ctx.strokeStyle = '#0f172a'
  ctx.lineWidth = 2
  ctx.font = '11px sans-serif'

  Object.entries(canvasPoints).forEach(([name, pos]) => {
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()

    const label = name.replace('_', ' ')
    ctx.fillStyle = '#0f172a'
    ctx.fillText(label, pos.x + 7, pos.y - 7)
    ctx.fillStyle = '#22d3ee'
  })
}

const clearLandmarkOverlay = () => {
  const canvas = landmarkCanvas.value
  if (!canvas) {
    return
  }
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    return
  }
  ctx.clearRect(0, 0, canvas.width, canvas.height)
}

const captureBaseline = () => {
  if (!currentMetrics.value) {
    return
  }

  if (
    typeof currentMetrics.value.spine_angle !== 'number' &&
    typeof currentMetrics.value.neck_angle !== 'number' &&
    typeof currentMetrics.value.shoulder_symmetry !== 'number'
  ) {
    alert('No body landmarks detected yet. Stay in frame and try calibration again.')
    return
  }

  baseline.value = {
    spine_angle: currentMetrics.value.spine_angle ?? 0,
    neck_angle: currentMetrics.value.neck_angle ?? 0,
    shoulder_symmetry: currentMetrics.value.shoulder_symmetry ?? 0,
    timestamp: new Date().toISOString()
  }
  localStorage.setItem(baselineStorageKey.value, JSON.stringify(baseline.value))
}

const clearBaseline = () => {
  baseline.value = null
  localStorage.removeItem(baselineStorageKey.value)
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

// Get sensitivity-based threshold for a metric
const getSensitivityThreshold = (metricName) => {
  const thresholds = {
    low: {
      spine_angle: 65,        // Alert below 65° (>25° forward/lateral deviation)
      neck_angle: 40,         // Very tolerant
      shoulder_symmetry: 50,  // Below 50% symmetry is alert
      head_tilt_lr: 25,       // 25° tilt
      head_forward_tilt: 40   // 40° forward
    },
    medium: {
      spine_angle: 75,        // Alert below 75° (>15° deviation, raised cervical load)
      neck_angle: 30,         // Moderate neck angle
      shoulder_symmetry: 70,  // 70% symmetry is good
      head_tilt_lr: 15,       // 15° tilt
      head_forward_tilt: 25   // 25° forward
    },
    high: {
      spine_angle: 82,        // Alert below 82° (>8° deviation, strict upright)
      neck_angle: 20,         // Strict neck alignment
      shoulder_symmetry: 85,  // 85% symmetry required
      head_tilt_lr: 8,        // 8° tilt
      head_forward_tilt: 15   // 15° forward
    }
  }
  return thresholds[sensitivity.value][metricName] || 30
}

const getMetricAlertClass = (metricName) => {
  if (!currentMetrics.value) return ''
  
  const value = currentMetrics.value[metricName]
  if (value === null || value === undefined || typeof value !== 'number') return ''
  
  const threshold = getSensitivityThreshold(metricName)
  
  // Metrics where a higher value is better (alert when below threshold):
  // shoulder_symmetry (% aligned) and spine_angle (CVA: 90° = upright).
  if (metricName === 'shoulder_symmetry' || metricName === 'spine_angle') {
    return value < threshold ? 'alert' : ''
  }
  
  // For the remaining angles: lower absolute deviation is better.
  return Math.abs(value) > threshold ? 'alert' : ''
}

const getHeadTiltClass = (type) => {
  if (!currentMetrics.value) return ''
  
  if (type === 'lr') {
    const tilt = currentMetrics.value.head_tilt_lr
    if (tilt === null || tilt === undefined) return ''
    const threshold = getSensitivityThreshold('head_tilt_lr')
    return Math.abs(tilt) > threshold ? 'alert' : ''
  } else if (type === 'fwd') {
    const tilt = currentMetrics.value.head_forward_tilt
    if (tilt === null || tilt === undefined) return ''
    const threshold = getSensitivityThreshold('head_forward_tilt')
    return tilt > threshold || tilt < -10 ? 'alert' : ''
  }
  return ''
}

const getHeadTiltDirection = (type) => {
  if (!currentMetrics.value) return ''
  
  if (type === 'lr') {
    const tilt = currentMetrics.value.head_tilt_lr
    if (tilt === null || tilt === undefined) return ''
    if (Math.abs(tilt) < 5) return '(level)'
    if (tilt > 0) return '(tilted right)'
    return '(tilted left)'
  } else if (type === 'fwd') {
    const tilt = currentMetrics.value.head_forward_tilt
    if (tilt === null || tilt === undefined) return ''
    if (tilt < 5) return '(upright)'
    if (tilt > 30) return '(too far forward!)'
    return '(forward tilt)'
  }
  return ''
}

const startManualCalibration = () => {
  if (!currentMetrics.value) {
    return
  }
  
  isManualCalibrating.value = true
  calibrationPointIndex.value = 0
  manualKeyPoints.value = {}
  
  // Start monitoring to get continuous frames
  if (!isMonitoring.value) {
    startMonitoring()
  }
  
  // Add click handler and enable pointer events
  const canvas = landmarkCanvas.value
  if (canvas) {
    canvas.classList.add('calibrating')
    canvas.addEventListener('click', handleCalibrationClick, { once: false })
  }
}

const handleCalibrationClick = (event) => {
  const canvas = landmarkCanvas.value
  if (!canvas || calibrationPointIndex.value >= calibrationPoints.length) {
    return
  }
  
  // Stop event propagation
  event.stopPropagation()
  event.preventDefault()
  
  // Get click position relative to canvas element
  const rect = canvas.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const clickY = event.clientY - rect.top
  
  // Use canvas internal dimensions for proper coordinate mapping
  // (canvas.width/height are the drawing surface, not CSS dimensions)
  const canvasWidth = canvas.width || rect.width
  const canvasHeight = canvas.height || rect.height
  
  if (!canvasWidth || !canvasHeight) {
    return
  }
  
  // Convert to normalized coordinates (0-1)
  // Note: camera preview is mirrored (transform: scaleX(-1))
  // So X coordinate needs to be inverted
  const normalizedX = 1.0 - (clickX / rect.width)
  const normalizedY = clickY / rect.height
  
  // Clamp to valid range
  const x = Math.max(0, Math.min(1.0, normalizedX))
  const y = Math.max(0, Math.min(1.0, normalizedY))
  
  console.log(`Click registered: ${calibrationPoints[calibrationPointIndex.value].key} at [${x.toFixed(3)}, ${y.toFixed(3)}]`)
  
  // Store the point
  const pointKey = calibrationPoints[calibrationPointIndex.value].key
  manualKeyPoints.value[pointKey] = [x, y]
  
  // Move to next point
  calibrationPointIndex.value++
  
  // If all points done, save and exit
  if (calibrationPointIndex.value >= calibrationPoints.length) {
    finishManualCalibration()
  }
}

const skipCalibrationPoint = () => {
  calibrationPointIndex.value++
  
  if (calibrationPointIndex.value >= calibrationPoints.length) {
    finishManualCalibration()
  }
}

const finishManualCalibration = () => {
  // Remove click handler and disable calibration mode
  const canvas = landmarkCanvas.value
  if (canvas) {
    canvas.classList.remove('calibrating')
    canvas.removeEventListener('click', handleCalibrationClick)
  }
  
  // Store the manual keypoints
  baseline.value = {
    spine_angle: currentMetrics.value.spine_angle ?? 0,
    neck_angle: currentMetrics.value.neck_angle ?? 0,
    shoulder_symmetry: currentMetrics.value.shoulder_symmetry ?? 0,
    manual_keypoints: manualKeyPoints.value,
    timestamp: new Date().toISOString()
  }
  
  localStorage.setItem(baselineStorageKey.value, JSON.stringify(baseline.value))
  
  isManualCalibrating.value = false
  calibrationPointIndex.value = 0
  manualKeyPoints.value = {}
}

const cancelManualCalibration = () => {
  // Remove click handler and disable calibration mode
  const canvas = landmarkCanvas.value
  if (canvas) {
    canvas.classList.remove('calibrating')
    canvas.removeEventListener('click', handleCalibrationClick)
  }
  
  isManualCalibrating.value = false
  calibrationPointIndex.value = 0
  manualKeyPoints.value = {}
  
  if (isMonitoring.value) {
    stopMonitoring()
  }
}

onMounted(async () => {
  loadBaseline()
  await startCameraPreview()
})

// The parent keeps this page mounted with v-show. When the user navigates away
// while actively monitoring, keep the analysis loop and camera running so the
// session continues in the background. If they are only previewing (not
// monitoring), release the camera to free resources. Re-acquire the preview
// when the tab becomes active again.
watch(() => props.active, async (isActive) => {
  if (isActive) {
    if (!isCameraReady.value) {
      await startCameraPreview()
    }
  } else if (!isMonitoring.value) {
    stopCameraPreview()
  }
})

onUnmounted(() => {
  stopMonitoring()
  stopCameraPreview()
})

// Vite HMR keeps module-level state (monitoringTimer / mediaStream) alive when
// this file is hot-replaced, which leaves a "ghost" analysis loop POSTing
// frames forever. Clean it up when the module is disposed during HMR.
if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    if (monitoringTimer) {
      clearInterval(monitoringTimer)
      monitoringTimer = null
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop())
      mediaStream = null
    }
  })
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

.camera-panel {
  position: relative;
  width: 100%;
  max-width: 860px;
  aspect-ratio: 16 / 9;
  border-radius: 12px;
  overflow: hidden;
  background: #0f172a;
  margin-bottom: 14px;
}

.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.landmark-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.landmark-overlay.calibrating {
  pointer-events: auto;
  cursor: crosshair;
}

.camera-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #e2e8f0;
  font-weight: 600;
  background: rgba(15, 23, 42, 0.5);
  text-align: center;
  padding: 16px;
}

.monitor-status {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  margin-bottom: 20px;
}

.monitor-status.ok {
  background: #c6f6d5;
  color: #22543d;
}

.monitor-status.warn {
  background: #fef3c7;
  color: #92400e;
}

.metrics-display {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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

.metric-hint {
  display: block;
  font-size: 11px;
  color: #718096;
  margin-top: 4px;
}

.metric.alert {
  background: #fef2f2;
  border-left-color: #dc2626;
}

.metric.alert .metric-value {
  color: #dc2626;
}

.baseline-note {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  background: #e6fffa;
  color: #234e52;
  font-size: 13px;
  font-weight: 600;
}

.drift-display {
  margin-bottom: 16px;
  font-size: 13px;
  color: #334155;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 12px;
  width: 100%;
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

.hint {
  font-size: 12px;
  line-height: 1.5;
  color: #4a5568;
  margin-bottom: 10px;
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

.secondary {
  background: #2563eb;
  color: #ffffff;
  border: none;
  margin-bottom: 10px;
}

.secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.calibration-panel {
  background: #fef3c7;
  border: 2px solid #f59e0b;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.calibration-info {
  margin-bottom: 12px;
}

.calibration-info p {
  margin: 0;
  font-size: 13px;
  color: #78350f;
}

.calibration-info p:first-child {
  font-weight: 600;
  margin-bottom: 4px;
}

.calibration-hint {
  font-size: 12px;
  color: #92400e;
  margin: 4px 0 8px 0 !important;
}

.calibration-progress {
  font-size: 11px;
  color: #b45309;
  font-weight: 600;
  margin-top: 6px;
}

.secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost {
  background: #ffffff;
  color: #334155;
  border: 1px solid #cbd5e1;
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
