<template>
  <div class="age-gate">
    <div class="age-card card">
      <h2>👤 Age Verification (COPPA)</h2>
      <p>To protect children's privacy, we need to verify your age.</p>
      
      <div class="form-group">
        <label for="dob">Date of Birth:</label>
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
        Verify Age
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['verified'])
const dateOfBirth = ref('')
const ageError = ref('')

const maxDate = computed(() => {
  const today = new Date()
  today.setFullYear(today.getFullYear() - 13)
  return today.toISOString().split('T')[0]
})

const verifyAge = () => {
  if (!dateOfBirth.value) {
    ageError.value = 'Please select your date of birth'
    return
  }

  const birth = new Date(dateOfBirth.value)
  const today = new Date()
  const age = today.getFullYear() - birth.getFullYear()
  const month = today.getMonth() - birth.getMonth()
  
  if (month < 0 || (month === 0 && today.getDate() < birth.getDate())) {
    age--
  }

  if (age >= 13) {
    ageError.value = ''
    emit('verified')
  } else {
    ageError.value = 'You must be at least 13 years old to use this service'
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
