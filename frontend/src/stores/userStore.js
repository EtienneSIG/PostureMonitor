import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('userId') || null)
  const hasConsent = ref(localStorage.getItem('consent') === 'true')
  const ageVerified = ref(localStorage.getItem('ageVerified') === 'true')
  const user = ref(null)
  const language = ref(localStorage.getItem('language') || 'en')
  const analyticsEnabled = ref(localStorage.getItem('analyticsEnabled') === 'true')
  const pendingDateOfBirth = ref(localStorage.getItem('pendingDateOfBirth') || null)

  const api = axios.create({
    baseURL: '/api',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  api.interceptors.request.use((config) => {
    if (userId.value) {
      config.headers['X-User-Id'] = userId.value
    }
    return config
  })

  const initializeUser = async () => {
    if (userId.value) {
      try {
        const res = await api.get(`/users/${userId.value}`)
        user.value = res.data
      } catch (err) {
        console.error('Failed to load user:', err)
        logout()
      }
    }
  }

  const registerUser = async ({ email = null, region = 'EU', dateOfBirth = null } = {}) => {
    try {
      const res = await api.post('/users/register', {
        email,
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

  const logout = () => {
    userId.value = null
    hasConsent.value = false
    ageVerified.value = false
    user.value = null
    analyticsEnabled.value = false
    pendingDateOfBirth.value = null
    localStorage.removeItem('userId')
    localStorage.removeItem('consent')
    localStorage.removeItem('ageVerified')
    localStorage.removeItem('analyticsEnabled')
    localStorage.removeItem('pendingDateOfBirth')
  }

  return {
    userId,
    hasConsent,
    ageVerified,
    user,
    language,
    analyticsEnabled,
    pendingDateOfBirth,
    api,
    initializeUser,
    registerUser,
    setConsent,
    setAgeVerified,
    setLanguage,
    setAnalyticsEnabled,
    setPendingDateOfBirth,
    logout
  }
})
