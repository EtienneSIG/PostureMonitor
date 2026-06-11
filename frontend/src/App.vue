<template>
  <div class="app">
    <!-- Auth Gate (local login/register) - must be first -->
    <AuthGate v-if="!userStore.isAuthenticated" @authenticated="handleAuthenticated" />
    
    <!-- Consent Gate (must be before AgeGate) -->
    <ConsentGate v-else-if="!userStore.hasConsent" @consented="handleConsent" />
    
    <!-- Age Gate (COPPA - NA-04) -->
    <AgeGate v-else-if="!userStore.ageVerified" @verified="handleAgeVerified" />
    
    <!-- Main App -->
    <div v-else class="app-container">
      <header class="app-header">
        <div class="container">
          <h1>🧍 Posture Monitor Pro</h1>
          <nav class="nav">
            <button 
              @click="currentPage = 'dashboard'" 
              :class="{ active: currentPage === 'dashboard' }"
              class="nav-btn"
            >
              Dashboard
            </button>
            <button 
              @click="currentPage = 'monitor'" 
              :class="{ active: currentPage === 'monitor' }"
              class="nav-btn"
            >
              Monitor
            </button>
            <button 
              @click="currentPage = 'privacy'" 
              :class="{ active: currentPage === 'privacy' }"
              class="nav-btn"
            >
              Privacy & Data
            </button>
            <button 
              @click="handleLogout"
              class="nav-btn logout"
            >
              Logout
            </button>
          </nav>
        </div>
      </header>

      <main class="app-main">
        <div class="container">
          <Dashboard v-show="currentPage === 'dashboard'" :active="currentPage === 'dashboard'" />
          <PostureMonitor v-show="currentPage === 'monitor'" :active="currentPage === 'monitor'" />
          <PrivacyCenter v-show="currentPage === 'privacy'" />
        </div>
      </main>

      <footer class="app-footer">
        <p>&copy; 2026 Posture Monitor Pro. All data is processed locally. User: {{ userStore.userEmail || 'Guest' }}</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from './stores/userStore'
import AuthGate from './components/AuthGate.vue'
import ConsentGate from './components/ConsentGate.vue'
import AgeGate from './components/AgeGate.vue'
import Dashboard from './pages/Dashboard.vue'
import PostureMonitor from './pages/PostureMonitor.vue'
import PrivacyCenter from './pages/PrivacyCenter.vue'

const userStore = useUserStore()
const currentPage = ref('dashboard')

const handleAuthenticated = ({ email }) => {
  // User is now authenticated and has given consent
  userStore.setConsent(true)
  userStore.setLanguage(userStore.language)
}

const handleConsent = ({ language, analyticsEnabled }) => {
  userStore.setConsent(true)
  userStore.setLanguage(language)
  userStore.setAnalyticsEnabled(analyticsEnabled)
}

const handleAgeVerified = async ({ dateOfBirth }) => {
  // Update user with age verification
  userStore.setAgeVerified(true)
  userStore.setPendingDateOfBirth(null)
}

const handleLogout = () => {
  userStore.logout()
  currentPage.value = 'dashboard'
}

onMounted(() => {
  userStore.initializeUser()
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: white;
}

.app-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 20px 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header h1 {
  margin: 0;
  font-size: 28px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav {
  display: flex;
  gap: 10px;
}

.nav-btn {
  padding: 10px 16px;
  background: white;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  color: #4a5568;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background: #f7fafc;
  border-color: #667eea;
}

.nav-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.nav-btn.logout {
  background: #fed7d7;
  color: #742a2a;
}

.nav-btn.logout:hover {
  background: #fc8181;
}

.app-main {
  flex: 1;
  padding: 40px 0;
  background: #f7fafc;
}

.app-footer {
  background: #1a202c;
  color: white;
  text-align: center;
  padding: 20px;
  margin-top: auto;
}

@media (max-width: 768px) {
  .app-header .container {
    flex-direction: column;
    gap: 20px;
  }

  .nav {
    flex-wrap: wrap;
  }

  .nav-btn {
    padding: 8px 12px;
    font-size: 14px;
  }
}
</style>
