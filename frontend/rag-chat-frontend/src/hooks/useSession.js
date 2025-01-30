import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'product_rag_session_id'

function createSessionId() {
  const randomPart = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(16).slice(2, 10)

  return `session_${Date.now()}_${randomPart}`
}

export function useSession() {
  const [sessionId, setSessionId] = useState(() => {
    const storedSession = window.sessionStorage.getItem(STORAGE_KEY)
    return storedSession || createSessionId()
  })

  useEffect(() => {
    window.sessionStorage.setItem(STORAGE_KEY, sessionId)
  }, [sessionId])

  const rotateSession = useCallback(() => {
    setSessionId(createSessionId())
  }, [])

  return { sessionId, rotateSession }
}
