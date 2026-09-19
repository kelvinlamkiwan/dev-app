const API = (import.meta.env.VITE_API_URL) || '/api'

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  get: (path) => fetch(API + path).then(handle),
  post: (path, body) =>
    fetch(API + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(handle),
  put: (path, body) =>
    fetch(API + path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(handle),
  del: (path) => fetch(API + path, { method: 'DELETE' }).then(handle),
  upload: (path, formData) =>
    fetch(API + path, { method: 'POST', body: formData }).then(handle),
}
