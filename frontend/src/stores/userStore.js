import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('userId') || null)
  const userEmail = ref(localStorage.getItem('userEmail') || null)
  const hasConsent = ref(localStorage.getItem('consent') === 'true')
  const ageVerified = ref(localStorage.getItem('ageVerified') === 'true')
  const user = ref(null)
  const language = ref(localStorage.getItem('language') || 'en')
  const analyticsEnabled = ref(localStorage.getItem('analyticsEnabled') === 'true')
  const pendingDateOfBirth = ref(localStorage.getItem('pendingDateOfBirth') || null)
  const isAuthenticated = ref(!!userId.value)

  const initializeUser = async () => {
    if (userId.value) {
      isAuthenticated.value = true
      try {
        const res = await api.get(`/users/${userId.value}`)
        user.value = res.data
      } catch (err) {
        console.error('Failed to load user:', err)
        logout()
      }
    }
  }

  const registerUser = async ({ email = null, password = null, region = 'EU', dateOfBirth = null } = {}) => {
    try {
      const res = await api.post('/users/register', {
        email,
        password,
        region,
        date_of_birth: dateOfBirth,
        consent_given: true,
        consent_version: '1.0'
      })
      
      userId.value = res.data.id
      user.value = res.data
      hasConsent.value = true
      ageVerified.value = Boolean(dateOfBirth)
      
      localStorage.setItem('userId', userId.value)
      localStorage.setItem('consent', 'true')
      localStorage.setItem('ageVerified', String(Boolean(dateOfBirth)))
      
      return res.data
    } catch (err) {
      console.error('Registration error:', err)
      throw err
    }
  }

  const setConsent = (value) => {
    hasConsent.value = value
    localStorage.setItem('consent', String(value))
  }

  const setAgeVerified = (value) => {
    ageVerified.value = value
    localStorage.setItem('ageVerified', String(value))
  }

  const setLanguage = (lang) => {
    language.value = lang
    localStorage.setItem('language', lang)
  }

  const setAnalyticsEnabled = (value) => {
    analyticsEnabled.value = value
    localStorage.setItem('analyticsEnabled', String(value))
  }

  const setPendingDateOfBirth = (value) => {
    pendingDateOfBirth.value = value
    if (value) {
      localStorage.setItem('pendingDateOfBirth', value)
    } else {
      localStorage.removeItem('pendingDateOfBirth')
    }
  }

  const loginUser = async ({ email, password } = {}) => {
    try {
      const res = await api.post('/users/login', { email, password })
      userId.value = res.data.id
      userEmail.value = res.data.email
      user.value = res.data
      isAuthenticated.value = true
      hasConsent.value = true
      
      localStorage.setItem('userId', userId.value)
      localStorage.setItem('userEmail', userEmail.value || '')
      localStorage.setItem('consent', 'true')
      
      return res.data
    } catch (err) {
      console.error('Login error:', err)
      throw err
    }
  }

  const resetPassword = async ({ email, recoveryCode, newPassword } = {}) => {
    try {
      const res = await api.post('/users/reset-password', {
        email,
        recovery_code: recoveryCode,
        new_password: newPassword
      })
      return res.data
    } catch (err) {
      console.error('Password reset error:', err)
      throw err
    }
  }

  const logout = () => {
    userId.value = null
    userEmail.value = null
    hasConsent.value = false
    ageVerified.value = false
    user.value = null
    analyticsEnabled.value = false
    pendingDateOfBirth.value = null
    isAuthenticated.value = false
    localStorage.removeItem('userId')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('consent')
    localStorage.removeItem('ageVerified')
    localStorage.removeItem('analyticsEnabled')
    localStorage.removeItem('pendingDateOfBirth')
  }

  return {
    userId,
    userEmail,
    isAuthenticated,
    hasConsent,
    ageVerified,
    user,
    language,
    analyticsEnabled,
    pendingDateOfBirth,
    initializeUser,
    registerUser,
    loginUser,
    resetPassword,
    setConsent,
    setAgeVerified,
    setLanguage,
    setAnalyticsEnabled,
    setPendingDateOfBirth,
    logout
  }
})
