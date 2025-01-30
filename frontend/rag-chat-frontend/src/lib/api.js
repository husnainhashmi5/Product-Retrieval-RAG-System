export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
export const API_TIMEOUT_MS = 30000

export async function postJson(path, payload, { timeoutMs = API_TIMEOUT_MS } = {}) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `Request failed with ${response.status}`)
    }

    return response.json()
  } finally {
    window.clearTimeout(timeout)
  }
}
