<template>
  <div class="age-gate">
    <div class="age-card card">
      <h2>👤 {{ t.title }}</h2>
      <p>{{ t.subtitle }}</p>
      <p class="compliance-pill">{{ t.rule }}</p>
      
      <div class="form-group">
        <label for="dob">{{ t.label }}</label>
        <input 
          id="dob"
          type="date" 
          v-model="dateOfBirth"
          :max="maxDate"
        />
      </div>

      <div v-if="ageError" class="alert danger">
        {{ ageError }}
      </div>

      <button 
        @click="verifyAge"
        :disabled="!dateOfBirth"
        class="primary full-width"
      >
        {{ t.cta }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/userStore'

const emit = defineEmits(['verified'])
const userStore = useUserStore()
const dateOfBirth = ref('')
const ageError = ref('')

const t = computed(() => {
  const fr = userStore.language === 'fr'
  return {
    title: fr ? 'Vérification d\'âge (COPPA)' : 'Age Verification (COPPA)',
    subtitle: fr
      ? 'Pour protéger la confidentialité des mineurs, nous devons vérifier votre âge.'
      : 'To protect children\'s privacy, we need to verify your age.',
    rule: fr ? 'Règle: âge minimum 13 ans' : 'Rule: minimum age is 13',
    label: fr ? 'Date de naissance:' : 'Date of Birth:',
    cta: fr ? 'Vérifier mon âge' : 'Verify Age',
    missingDob: fr ? 'Veuillez sélectionner votre date de naissance' : 'Please select your date of birth',
    underAge: fr ? 'Vous devez avoir au moins 13 ans pour utiliser ce service' : 'You must be at least 13 years old to use this service'
  }
})

const maxDate = computed(() => {
  const today = new Date()
  today.setFullYear(today.getFullYear() - 13)
  return today.toISOString().split('T')[0]
})

const verifyAge = () => {
  if (!dateOfBirth.value) {
    ageError.value = t.value.missingDob
    return
  }

  const birth = new Date(dateOfBirth.value)
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const month = today.getMonth() - birth.getMonth()
  
  if (month < 0 || (month === 0 && today.getDate() < birth.getDate())) {
    age--
  }

  if (age >= 13) {
    ageError.value = ''
    emit('verified', { dateOfBirth: dateOfBirth.value })
  } else {
    ageError.value = t.value.underAge
  }
}
</script>

<style scoped>
.age-gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.age-card {
  max-width: 400px;
  width: 100%;
}

.age-card p {
  margin-bottom: 20px;
  color: #4a5568;
}

.compliance-pill {
  display: inline-block;
  background: #edf2ff;
  color: #4338ca;
  border: 1px solid #c7d2fe;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  margin: 0 0 16px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2d3748;
}

.form-group input {
  width: 100%;
}

.full-width {
  width: 100%;
}
</style>
