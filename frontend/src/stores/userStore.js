import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('userId') || null)
  const hasConsent = ref(localStorage.getItem('consent') === 'true')
  const ageVerified = ref(localStorage.getItem('ageVerified') === 'true')
  const user = ref(null)
  const language = ref(localStorage.getItem('language') || 'en')

  const api = axios.create({
    baseURL: '/api',
    headers: {
      'Content-Type': 'application/json'
    }
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

  const registerUser = async (email, region = 'EU') => {
    try {
      const res = await api.post('/users/register', {
        email,
        region,
        consent_given: true,
        consent_version: '1.0'
      })
      
      userId.value = res.data.id
      user.value = res.data
      
      localStorage.setItem('userId', userId.value)
      localStorage.setItem('consent', 'true')
      
      return res.data
    } catch (err) {
      console.error('Registration error:', err)
      throw err
    }
  }

  const setConsent = (value) => {
    hasConsent.value = value
    localStorage.setItem('consent', value)
  }

  const setAgeVerified = (value) => {
    ageVerified.value = value
    localStorage.setItem('ageVerified', value)
  }

  const setLanguage = (lang) => {
    language.value = lang
    localStorage.setItem('language', lang)
  }

  const logout = () => {
    userId.value = null
    hasConsent.value = false
    ageVerified.value = false
    user.value = null
    localStorage.removeItem('userId')
    localStorage.removeItem('consent')
    localStorage.removeItem('ageVerified')
  }

  return {
    userId,
    hasConsent,
    ageVerified,
    user,
    language,
    api,
    initializeUser,
    registerUser,
    setConsent,
    setAgeVerified,
    setLanguage,
    logout
  }
})
