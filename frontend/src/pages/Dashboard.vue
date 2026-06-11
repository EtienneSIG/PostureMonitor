<template>
  <div class="pages">
    <div class="page-header">
      <h2>📊 Dashboard</h2>
      <p>Real-time posture metrics and history</p>
    </div>

    <div v-if="loading" class="alert info">
      Loading data...
    </div>

    <div v-else class="dashboard-grid">
      <!-- Stats Cards -->
      <div class="stat-card">
        <h3>Sessions</h3>
        <p class="big-number">{{ stats.totalSessions }}</p>
        <p class="stat-label">This week</p>
      </div>

      <div class="stat-card">
        <h3>Alerts</h3>
        <p class="big-number" :style="{ color: stats.alertCount > 5 ? '#f56565' : '#48bb78' }">
          {{ stats.alertCount }}
        </p>
        <p class="stat-label">Total alerts</p>
      </div>

      <div class="stat-card">
        <h3>Avg Spine Angle</h3>
        <p class="big-number">{{ stats.avgSpineAngle.toFixed(1) }}°</p>
        <p class="stat-label">Target: 85-95°</p>
      </div>

      <div class="stat-card">
        <h3>Best Posture</h3>
        <p class="big-number">{{ stats.bestPosture }}%</p>
        <p class="stat-label">Session score</p>
      </div>
    </div>

    <!-- Recent Data -->
    <div class="card" style="margin-top: 20px;">
      <h3>Recent Posture Data</h3>
      
      <div v-if="recentData.length === 0" class="alert info">
        No posture data yet. Start monitoring to collect data.
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Spine Angle</th>
            <th>Shoulder Symmetry</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="data in recentData" :key="data.id">
            <td>{{ formatTime(data.timestamp) }}</td>
            <td>{{ data.spine_angle ? data.spine_angle.toFixed(1) : '—' }}°</td>
            <td>{{ data.shoulder_symmetry ? data.shoulder_symmetry.toFixed(1) : '—' }}%</td>
            <td>
              <span v-if="data.alert_triggered" class="badge danger">Alert</span>
              <span v-else class="badge success">Good</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
const loading = ref(true)
const recentData = ref([])
const stats = ref({
  totalSessions: 0,
  alertCount: 0,
  avgSpineAngle: 0,
  bestPosture: 0
})

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const loadHistory = async () => {
  try {
    const res = await userStore.api.get(`/posture/history?limit=20`)
    recentData.value = res.data
    
    // Calculate stats
    if (recentData.value.length > 0) {
      stats.value.alertCount = recentData.value.filter(d => d.alert_triggered).length
      stats.value.avgSpineAngle = recentData.value.reduce((sum, d) => sum + (d.spine_angle || 0), 0) / recentData.value.length
      stats.value.bestPosture = Math.max(...recentData.value.map(d => d.shoulder_symmetry || 0))
      stats.value.totalSessions = 1 // Simplified
    }
  } catch (err) {
    console.error('Error loading history:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.page-header {
  margin-bottom: 30px;
}

.page-header h2 {
  font-size: 28px;
  margin-bottom: 8px;
}

.page-header p {
  color: #718096;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.stat-card h3 {
  color: #718096;
  font-size: 14px;
  text-transform: uppercase;
  margin: 0 0 10px 0;
}

.big-number {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
  margin: 10px 0;
}

.stat-label {
  font-size: 12px;
  color: #a0aec0;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #f7fafc;
}

.data-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #4a5568;
  border-bottom: 2px solid #e2e8f0;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.data-table tr:hover {
  background: #f7fafc;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.badge.success {
  background: #c6f6d5;
  color: #22543d;
}

.badge.danger {
  background: #fed7d7;
  color: #742a2a;
}
</style>
