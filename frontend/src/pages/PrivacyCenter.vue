<template>
  <div class="pages">
    <div class="page-header">
      <h2>🔐 Privacy & Data Management</h2>
      <p>Manage your personal data and privacy preferences</p>
    </div>

    <div class="privacy-grid">
      <!-- Consent Management -->
      <div class="card">
        <h3>✓ Consent Management</h3>
        <p>You have provided explicit consent to use Posture Monitor Pro.</p>
        <p class="consent-date">Consented on: {{ userStore.user?.consent_given_at }}</p>
        
        <button @click="withdrawConsent" class="danger">
          Withdraw Consent
        </button>
      </div>

      <!-- Data Export (GDPR Article 20, CCPA) -->
      <div class="card">
        <h3>📥 Export Your Data</h3>
        <p>Download all your personal data in machine-readable format.</p>
        <p class="right-info">Right to Portability (GDPR, CCPA)</p>
        
        <button @click="exportData" :disabled="exporting" class="primary">
          {{ exporting ? 'Exporting...' : 'Export Data' }}
        </button>
      </div>

      <!-- Data Deletion (GDPR Article 17, CCPA) -->
      <div class="card danger-card">
        <h3>🗑️ Delete All Data</h3>
        <p>Permanently delete all your personal data from our servers.</p>
        <p class="right-info">Right to Erasure (GDPR, CCPA)</p>
        
        <button @click="openDeleteConfirm" class="danger">
          Request Deletion
        </button>
      </div>

      <!-- Data Subject Access Request -->
      <div class="card">
        <h3>📋 DSAR Request</h3>
        <p>Request a comprehensive data access report.</p>
        <p class="right-info">Data Subject Access Request (GDPR)</p>
        
        <select v-model="dsarType" class="full-width">
          <option value="access">Access My Data</option>
          <option value="export">Export Data</option>
          <option value="delete">Request Deletion</option>
        </select>
        
        <button @click="submitDSAR" :disabled="submittingDSAR" class="primary" style="margin-top: 10px;">
          {{ submittingDSAR ? 'Submitting...' : 'Submit Request' }}
        </button>
      </div>
    </div>

    <!-- Deletion Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="closeDeleteConfirm">
      <div class="modal-content card" @click.stop>
        <h3>⚠️ Confirm Permanent Deletion</h3>
        <p>This action will permanently delete:</p>
        <ul>
          <li>All your posture data</li>
          <li>Your profile and settings</li>
          <li>Session history</li>
        </ul>
        <p>This cannot be undone. Audit logs will be retained for legal compliance.</p>
        
        <div class="modal-actions">
          <button @click="closeDeleteConfirm" class="secondary">Cancel</button>
          <button @click="confirmDelete" :disabled="deleting" class="danger">
            {{ deleting ? 'Deleting...' : 'Yes, Delete Everything' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Success Alert -->
    <div v-if="successMessage" class="alert success" style="position: fixed; bottom: 20px; right: 20px; max-width: 400px;">
      {{ successMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/userStore'
import api from '../api/client'

const userStore = useUserStore()
const exporting = ref(false)
const deleting = ref(false)
const submittingDSAR = ref(false)
const showDeleteConfirm = ref(false)
const dsarType = ref('access')
const successMessage = ref('')

const exportData = async () => {
  exporting.value = true
  try {
    const res = await api.get('/dsar/export', {
      responseType: 'blob'
    })
    
    // Create download link
    const url = window.URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = 'posture_monitor_export.json'
    link.click()
    
    successMessage.value = 'Data exported successfully!'
    setTimeout(() => { successMessage.value = '' }, 3000)
  } catch (err) {
    alert('Error exporting data: ' + err.message)
  } finally {
    exporting.value = false
  }
}

const openDeleteConfirm = () => {
  showDeleteConfirm.value = true
}

const closeDeleteConfirm = () => {
  showDeleteConfirm.value = false
}

const confirmDelete = async () => {
  deleting.value = true
  try {
    await api.delete(`/users/${userStore.userId}/data`)
    successMessage.value = 'Your data has been deleted. Logging out...'
    setTimeout(() => {
      userStore.logout()
    }, 2000)
  } catch (err) {
    alert('Error deleting data: ' + err.message)
  } finally {
    deleting.value = false
    showDeleteConfirm.value = false
  }
}

const submitDSAR = async () => {
  submittingDSAR.value = true
  try {
    const res = await api.post('/dsar/request', {
      request_type: dsarType.value
    })
    
    successMessage.value = `DSAR request submitted! Reference: ${res.data.id}`
    setTimeout(() => { successMessage.value = '' }, 5000)
  } catch (err) {
    alert('Error submitting DSAR: ' + err.message)
  } finally {
    submittingDSAR.value = false
  }
}

const withdrawConsent = async () => {
  if (!confirm('Withdraw consent? You will not be able to use the app.')) {
    return
  }
  
  try {
    await api.put(`/users/${userStore.userId}/consent`, {
      consent_given: false
    })
    
    successMessage.value = 'Consent withdrawn. Logging out...'
    setTimeout(() => {
      userStore.logout()
    }, 2000)
  } catch (err) {
    alert('Error: ' + err.message)
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 30px;
}

.privacy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
}

.card p {
  color: #718096;
  margin-bottom: 10px;
  font-size: 14px;
}

.consent-date {
  font-size: 12px;
  color: #a0aec0;
  font-weight: 600;
}

.right-info {
  font-size: 12px;
  color: #667eea;
  font-weight: 600;
  margin-bottom: 15px;
}

.danger-card {
  border-left: 4px solid #f56565;
}

.full-width {
  width: 100%;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

button {
  width: 100%;
  margin-top: 15px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  max-width: 400px;
  width: 90%;
  background: white;
}

.modal-content h3 {
  margin-bottom: 15px;
}

.modal-content ul {
  margin-left: 20px;
  margin-bottom: 15px;
  color: #718096;
}

.modal-content ul li {
  margin-bottom: 8px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.modal-actions button {
  flex: 1;
  margin-top: 0;
}
</style>
