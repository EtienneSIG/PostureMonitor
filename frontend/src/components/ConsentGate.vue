<template>
  <div class="consent-gate">
    <div class="consent-card card">
      <h2>🔒 Privacy & Consent Required</h2>
      <p class="subtitle">
        {{ selectedLanguage === 'fr'
          ? 'Avant de commencer, nous avons besoin de votre consentement explicite.'
          : 'Before you start, we need your explicit consent.'
        }}
      </p>
      
      <div class="language-selector">
        <label>Language: </label>
        <select v-model="selectedLanguage">
          <option value="en">English</option>
          <option value="fr">Français</option>
        </select>
      </div>

      <div class="policy-section">
        <h3>{{ selectedLanguage === 'fr' ? 'Avis de confidentialité' : 'Privacy Notice' }}</h3>
        <div v-if="isLoading" class="policy-text muted">
          {{ selectedLanguage === 'fr' ? 'Chargement des informations de confidentialité...' : 'Loading privacy information...' }}
        </div>
        <div v-else class="policy-text">
          {{ privacyPolicy }}
        </div>
      </div>

      <div class="consent-section">
        <h3>{{ selectedLanguage === 'fr' ? 'Consentement' : 'Consent' }}</h3>
        <div class="consent-text" v-if="!isLoading">
          {{ consentText }}
        </div>

        <div v-if="loadError" class="alert danger">
          {{ loadError }}
        </div>
        
        <label class="checkbox">
          <input type="checkbox" v-model="userAgreesConsent" />
          <span>{{ selectedLanguage === 'fr' ? 'J\'accepte les conditions' : 'I agree to the terms' }}</span>
        </label>

        <label class="checkbox">
          <input type="checkbox" v-model="userAgreesAnalytics" />
          <span>{{ selectedLanguage === 'fr' ? 'Partager les données d\'amélioration (optionnel)' : 'Share improvement data (optional)' }}</span>
        </label>
      </div>

      <div class="action-buttons">
        <button 
          @click="handleConsent" 
          :disabled="!userAgreesConsent || isLoading"
          class="primary"
        >
          {{ selectedLanguage === 'fr' ? 'Accepter et continuer' : 'Accept and Continue' }}
        </button>
      </div>

      <p class="compliance-note">
        {{ selectedLanguage === 'fr' 
          ? '✓ Conforme RGPD, CCPA/CPRA, BIPA, PIPEDA, COPPA' 
          : '✓ Compliant with GDPR, CCPA/CPRA, BIPA, PIPEDA, COPPA' 
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useUserStore } from '../stores/userStore'

const emit = defineEmits(['consented'])
const userStore = useUserStore()
const selectedLanguage = ref(userStore.language)
const userAgreesConsent = ref(false)
const userAgreesAnalytics = ref(false)
const privacyPolicy = ref('')
const consentText = ref('')
const isLoading = ref(false)
const loadError = ref('')

const loadPolicyTexts = async () => {
  isLoading.value = true
  loadError.value = ''
  
  try {
    const policyRes = await userStore.api.get(`/privacy/policy/${selectedLanguage.value}`)
    privacyPolicy.value = policyRes.data.policy
    
    const consentRes = await userStore.api.get(`/privacy/consent-text/${selectedLanguage.value}`)
    consentText.value = consentRes.data.consent_text
  } catch (err) {
    console.error('Error loading privacy policy:', err)
    loadError.value = selectedLanguage.value === 'fr'
      ? 'Impossible de charger les textes de confidentialité. Réessayez dans quelques secondes.'
      : 'Unable to load privacy texts. Please retry in a few seconds.'
  } finally {
    isLoading.value = false
  }
}

const handleConsent = async () => {
  if (!userAgreesConsent.value) return

  userStore.setLanguage(selectedLanguage.value)
  emit('consented', {
    language: selectedLanguage.value,
    analyticsEnabled: userAgreesAnalytics.value
  })
}

onMounted(async () => {
  await loadPolicyTexts()
})

watch(selectedLanguage, async () => {
  await loadPolicyTexts()
})
</script>

<style scoped>
.consent-gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.consent-card {
  max-width: 600px;
  width: 100%;
  border-radius: 12px;
  max-height: 90vh;
  overflow-y: auto;
}

.subtitle {
  margin: 8px 0 16px 0;
  color: #4a5568;
  font-size: 14px;
}

.language-selector {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.language-selector select {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.policy-section, .consent-section {
  margin-bottom: 20px;
}

.policy-section h3, .consent-section h3 {
  color: #667eea;
  margin-bottom: 12px;
}

.policy-text {
  background: #f7fafc;
  padding: 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
  border-left: 4px solid #667eea;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.policy-text.muted {
  color: #718096;
  font-style: italic;
}

.consent-text {
  background: #f7fafc;
  padding: 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  border-left: 4px solid #667eea;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  cursor: pointer;
  font-size: 14px;
}

.checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin: 20px 0;
}

.action-buttons button {
  flex: 1;
}

.action-buttons button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.compliance-note {
  text-align: center;
  color: #48bb78;
  font-size: 12px;
  font-weight: 600;
  margin-top: 20px;
}
</style>
