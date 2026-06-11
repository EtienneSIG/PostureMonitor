import axios from 'axios'

// Shared axios client for the whole app.
//
// NOTE: This lives outside the Pinia store on purpose. A setup-store treats any
// returned function as an "action" and wraps it, which strips the methods
// (.get/.post/...) off an axios instance. Importing the client directly keeps
// those methods intact.
const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Attach the current user id (read from localStorage so this stays independent
// of the store lifecycle).
api.interceptors.request.use((config) => {
  const userId = localStorage.getItem('userId')
  if (userId) {
    config.headers['X-User-Id'] = userId
  }
  return config
})

export default api
