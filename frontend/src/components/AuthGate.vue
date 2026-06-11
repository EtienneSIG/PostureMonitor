<template>
  <div class="auth-gate">
    <div class="auth-card card">
      <!-- RECOVERY CODE DISPLAY (after register / reset) -->
      <div v-if="recoveryCode" class="tab-content">
        <h2>🔑 {{ t.recoveryTitle }}</h2>
        <p class="recovery-intro">{{ t.recoveryIntro }}</p>
        <div class="recovery-code">{{ recoveryCode }}</div>
        <div class="alert warning">{{ t.recoveryWarning }}</div>
        <label class="checkbox-row">
          <input type="checkbox" v-model="recoverySaved" />
          <span>{{ t.recoverySavedLabel }}</span>
        </label>
        <button
          @click="confirmRecoverySaved"
          :disabled="!recoverySaved"
          class="primary full-width"
        >
          {{ t.continueBtn }}
        </button>
      </div>

      <template v-else>
        <h2>👤 {{ headerTitle }}</h2>

        <div class="tabs" v-if="activeTab !== 'forgot'">
          <button
            @click="activeTab = 'login'"
            :class="{ active: activeTab === 'login' }"
            class="tab-btn"
          >
            {{ t.login }}
          </button>
          <button
            @click="activeTab = 'register'"
            :class="{ active: activeTab === 'register' }"
            class="tab-btn"
          >
            {{ t.register }}
          </button>
        </div>

        <!-- LOGIN TAB -->
        <div v-if="activeTab === 'login'" class="tab-content">
          <div class="form-group">
            <label for="login-email">{{ t.email }}</label>
            <input
              id="login-email"
              v-model="loginForm.email"
              type="email"
              placeholder="user@example.com"
              @keyup.enter="handleLogin"
            />
          </div>

          <div class="form-group">
            <label for="login-password">{{ t.password }}</label>
            <input
              id="login-password"
              v-model="loginForm.password"
              type="password"
              placeholder="••••••••"
              @keyup.enter="handleLogin"
            />
          </div>

          <div v-if="loginError" class="alert danger">
            {{ loginError }}
          </div>

          <button
            @click="handleLogin"
            :disabled="!loginForm.email || !loginForm.password || isLoading"
            class="primary full-width"
          >
            {{ isLoading ? t.loading : t.loginBtn }}
          </button>

          <button type="button" class="link-btn" @click="goToForgot">
            {{ t.forgotLink }}
          </button>
        </div>

        <!-- REGISTER TAB -->
        <div v-if="activeTab === 'register'" class="tab-content">
          <div class="form-group">
            <label for="register-email">{{ t.email }}</label>
            <input
              id="register-email"
              v-model="registerForm.email"
              type="email"
              placeholder="user@example.com"
            />
          </div>

          <div class="form-group">
            <label for="register-password">{{ t.password }}</label>
            <input
              id="register-password"
              v-model="registerForm.password"
              type="password"
              placeholder="Min 8 chars"
            />
          </div>

          <div class="form-group">
            <label for="register-confirm">{{ t.confirmPassword }}</label>
            <input
              id="register-confirm"
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="Confirm password"
            />
          </div>

          <div v-if="registerError" class="alert danger">
            {{ registerError }}
          </div>

          <button
            @click="handleRegister"
            :disabled="!registerForm.email || !registerForm.password || !registerForm.confirmPassword || isLoading"
            class="primary full-width"
          >
            {{ isLoading ? t.loading : t.registerBtn }}
          </button>
        </div>

        <!-- FORGOT PASSWORD TAB -->
        <div v-if="activeTab === 'forgot'" class="tab-content">
          <p class="recovery-intro">{{ t.forgotIntro }}</p>

          <div class="form-group">
            <label for="forgot-email">{{ t.email }}</label>
            <input
              id="forgot-email"
              v-model="forgotForm.email"
              type="email"
              placeholder="user@example.com"
            />
          </div>

          <div class="form-group">
            <label for="forgot-code">{{ t.recoveryCodeLabel }}</label>
            <input
              id="forgot-code"
              v-model="forgotForm.recoveryCode"
              type="text"
              placeholder="XXXX-XXXX-XXXX-XXXX"
            />
          </div>

          <div class="form-group">
            <label for="forgot-password">{{ t.newPassword }}</label>
            <input
              id="forgot-password"
              v-model="forgotForm.newPassword"
              type="password"
              placeholder="Min 8 chars"
            />
          </div>

          <div class="form-group">
            <label for="forgot-confirm">{{ t.confirmPassword }}</label>
            <input
              id="forgot-confirm"
              v-model="forgotForm.confirmPassword"
              type="password"
              placeholder="Confirm password"
            />
          </div>

          <div v-if="forgotError" class="alert danger">
            {{ forgotError }}
          </div>

          <button
            @click="handleReset"
            :disabled="!forgotForm.email || !forgotForm.recoveryCode || !forgotForm.newPassword || !forgotForm.confirmPassword || isLoading"
            class="primary full-width"
          >
            {{ isLoading ? t.loading : t.resetBtn }}
          </button>

          <button type="button" class="link-btn" @click="activeTab = 'login'">
            {{ t.backToLogin }}
          </button>
        </div>

        <p class="compliance-note">
          {{ t.local }}
        </p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/userStore'

const emit = defineEmits(['authenticated'])
const userStore = useUserStore()

const activeTab = ref('login')
const isLoading = ref(false)
const loginError = ref('')
const registerError = ref('')
const forgotError = ref('')

// Recovery code shown once after register/reset; user must confirm they saved it.
const recoveryCode = ref('')
const recoverySaved = ref(false)
const pendingAuthEmail = ref('')
const pendingAuthPassword = ref('')

const loginForm = ref({
  email: '',
  password: ''
})

const registerForm = ref({
  email: '',
  password: '',
  confirmPassword: ''
})

const forgotForm = ref({
  email: '',
  recoveryCode: '',
  newPassword: '',
  confirmPassword: ''
})

const t = computed(() => {
  const fr = userStore.language === 'fr'
  return {
    loginTitle: fr ? 'Connexion' : 'Login',
    registerTitle: fr ? 'Créer un compte' : 'Create Account',
    forgotTitle: fr ? 'Réinitialiser le mot de passe' : 'Reset Password',
    login: fr ? 'Connexion' : 'Login',
    register: fr ? 'Inscription' : 'Register',
    email: fr ? 'Email:' : 'Email:',
    password: fr ? 'Mot de passe:' : 'Password:',
    newPassword: fr ? 'Nouveau mot de passe:' : 'New password:',
    confirmPassword: fr ? 'Confirmer le mot de passe:' : 'Confirm password:',
    recoveryCodeLabel: fr ? 'Code de récupération:' : 'Recovery code:',
    loginBtn: fr ? 'Se connecter' : 'Sign In',
    registerBtn: fr ? 'Créer un compte' : 'Create Account',
    resetBtn: fr ? 'Réinitialiser' : 'Reset Password',
    continueBtn: fr ? 'Continuer' : 'Continue',
    backToLogin: fr ? '← Retour à la connexion' : '← Back to login',
    forgotLink: fr ? 'Mot de passe oublié ?' : 'Forgot password?',
    loading: fr ? 'Chargement...' : 'Loading...',
    local: fr
      ? '✓ Authentification locale - données stockées sur votre appareil'
      : '✓ Local authentication - data stored on your device',
    loginFailed: fr ? 'Email ou mot de passe incorrect' : 'Invalid email or password',
    emailRequired: fr ? 'Email requis' : 'Email required',
    passwordRequired: fr ? 'Mot de passe requis' : 'Password required',
    passwordTooShort: fr ? 'Le mot de passe doit contenir au moins 8 caractères' : 'Password must be at least 8 characters',
    passwordMismatch: fr ? 'Les mots de passe ne correspondent pas' : 'Passwords do not match',
    emailInvalid: fr ? 'Email invalide' : 'Invalid email',
    emailTaken: fr ? 'Email déjà enregistré' : 'Email already registered',
    registrationFailed: fr ? 'Erreur lors de l\'inscription' : 'Registration failed',
    loginSuccessful: fr ? 'Connexion réussie' : 'Login successful',
    // Forgot password
    forgotIntro: fr
      ? 'Entrez votre email et le code de récupération fourni lors de votre inscription pour définir un nouveau mot de passe.'
      : 'Enter your email and the recovery code you received at registration to set a new password.',
    resetFailed: fr ? 'Email ou code de récupération invalide' : 'Invalid email or recovery code',
    // Recovery code display
    recoveryTitle: fr ? 'Votre code de récupération' : 'Your Recovery Code',
    recoveryIntro: fr
      ? 'Conservez ce code en lieu sûr. C\'est le SEUL moyen de réinitialiser votre mot de passe (aucun email n\'est envoyé).'
      : 'Save this code somewhere safe. It is the ONLY way to reset your password (no email is sent).',
    recoveryWarning: fr
      ? '⚠️ Ce code ne sera plus affiché. Sans lui, un mot de passe oublié est irrécupérable.'
      : '⚠️ This code will not be shown again. Without it, a forgotten password cannot be recovered.',
    recoverySavedLabel: fr ? 'J\'ai enregistré mon code de récupération' : 'I have saved my recovery code'
  }
})

const headerTitle = computed(() => {
  if (activeTab.value === 'register') return t.value.registerTitle
  if (activeTab.value === 'forgot') return t.value.forgotTitle
  return t.value.loginTitle
})

const goToForgot = () => {
  forgotError.value = ''
  forgotForm.value.email = loginForm.value.email
  activeTab.value = 'forgot'
}

const confirmRecoverySaved = async () => {
  // Authenticate only after the user confirms they saved the recovery code,
  // so the recovery display isn't unmounted prematurely by isAuthenticated flipping.
  isLoading.value = true
  try {
    await userStore.loginUser({
      email: pendingAuthEmail.value,
      password: pendingAuthPassword.value
    })
    recoveryCode.value = ''
    recoverySaved.value = false
    pendingAuthPassword.value = ''
    emit('authenticated', { email: pendingAuthEmail.value })
  } catch (err) {
    console.error('Post-recovery login error:', err)
  } finally {
    isLoading.value = false
  }
}

const handleLogin = async () => {
  if (!loginForm.value.email || !loginForm.value.password) {
    loginError.value = t.value.passwordRequired
    return
  }

  isLoading.value = true
  loginError.value = ''

  try {
    await userStore.loginUser({
      email: loginForm.value.email,
      password: loginForm.value.password
    })
    emit('authenticated', { email: loginForm.value.email })
  } catch (err) {
    console.error('Login error:', err)
    if (err.response?.status === 401) {
      loginError.value = t.value.loginFailed
    } else {
      loginError.value = err.response?.data?.detail || t.value.loginFailed
    }
  } finally {
    isLoading.value = false
  }
}

const handleRegister = async () => {
  if (!registerForm.value.email || !registerForm.value.password || !registerForm.value.confirmPassword) {
    registerError.value = t.value.passwordRequired
    return
  }

  if (registerForm.value.password.length < 8) {
    registerError.value = t.value.passwordTooShort
    return
  }

  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    registerError.value = t.value.passwordMismatch
    return
  }

  isLoading.value = true
  registerError.value = ''

  try {
    // Register + consent in one call (returns a one-time recovery code)
    const created = await userStore.registerUser({
      email: registerForm.value.email,
      password: registerForm.value.password,
      consent_given: true
    })

    // Keep credentials so we can authenticate after the user saves the recovery code.
    pendingAuthEmail.value = registerForm.value.email
    pendingAuthPassword.value = registerForm.value.password
    if (created?.recovery_code) {
      // Show the recovery code first; login happens in confirmRecoverySaved().
      recoveryCode.value = created.recovery_code
    } else {
      await userStore.loginUser({
        email: registerForm.value.email,
        password: registerForm.value.password
      })
      emit('authenticated', { email: registerForm.value.email })
    }
  } catch (err) {
    console.error('Registration error:', err)
    if (err.response?.status === 409) {
      registerError.value = t.value.emailTaken
    } else if (err.response?.status === 400) {
      registerError.value = err.response?.data?.detail || t.value.registrationFailed
    } else {
      registerError.value = t.value.registrationFailed
    }
  } finally {
    isLoading.value = false
  }
}

const handleReset = async () => {
  if (!forgotForm.value.email || !forgotForm.value.recoveryCode || !forgotForm.value.newPassword || !forgotForm.value.confirmPassword) {
    forgotError.value = t.value.passwordRequired
    return
  }

  if (forgotForm.value.newPassword.length < 8) {
    forgotError.value = t.value.passwordTooShort
    return
  }

  if (forgotForm.value.newPassword !== forgotForm.value.confirmPassword) {
    forgotError.value = t.value.passwordMismatch
    return
  }

  isLoading.value = true
  forgotError.value = ''

  try {
    const result = await userStore.resetPassword({
      email: forgotForm.value.email,
      recoveryCode: forgotForm.value.recoveryCode,
      newPassword: forgotForm.value.newPassword
    })

    // Keep credentials so we can authenticate after the user saves the new recovery code.
    pendingAuthEmail.value = forgotForm.value.email
    pendingAuthPassword.value = forgotForm.value.newPassword
    forgotForm.value = { email: '', recoveryCode: '', newPassword: '', confirmPassword: '' }
    if (result?.recovery_code) {
      // Show the rotated recovery code first; login happens in confirmRecoverySaved().
      recoveryCode.value = result.recovery_code
    } else {
      await userStore.loginUser({
        email: pendingAuthEmail.value,
        password: pendingAuthPassword.value
      })
      emit('authenticated', { email: pendingAuthEmail.value })
    }
  } catch (err) {
    console.error('Reset error:', err)
    if (err.response?.status === 401) {
      forgotError.value = t.value.resetFailed
    } else {
      forgotError.value = err.response?.data?.detail || t.value.resetFailed
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-card {
  max-width: 400px;
  width: 100%;
}

.tabs {
  display: flex;
  gap: 0;
  margin: 0 0 24px 0;
  border-bottom: 2px solid #e2e8f0;
}

.tab-btn {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  color: #718096;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  margin-bottom: -2px;
}

.tab-btn.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.tab-btn:hover:not(.active) {
  color: #4a5568;
}

.tab-content {
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2d3748;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input::placeholder {
  color: #cbd5e0;
}

.full-width {
  width: 100%;
}

.compliance-note {
  font-size: 12px;
  color: #718096;
  margin-top: 20px;
  text-align: center;
}

.alert {
  margin: 12px 0;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}

.alert.danger {
  background: #fed7d7;
  color: #742a2a;
  border: 1px solid #fc8181;
}

.alert.warning {
  background: #fefcbf;
  color: #744210;
  border: 1px solid #f6e05e;
}

.link-btn {
  display: block;
  width: 100%;
  margin-top: 14px;
  padding: 6px;
  background: transparent;
  border: none;
  color: #667eea;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
}

.link-btn:hover {
  text-decoration: underline;
}

.recovery-intro {
  font-size: 14px;
  color: #4a5568;
  margin: 8px 0 16px 0;
}

.recovery-code {
  font-family: 'Courier New', monospace;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
  text-align: center;
  color: #2d3748;
  background: #edf2f7;
  border: 2px dashed #667eea;
  border-radius: 8px;
  padding: 16px;
  margin: 12px 0;
  word-break: break-all;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 0;
  font-size: 14px;
  color: #2d3748;
  cursor: pointer;
}

.checkbox-row input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}
</style>
