import { useCallback, useState } from 'react'
import { postJson } from '../lib/api'

function createMessageId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  return `message_${Date.now()}_${Math.random().toString(16).slice(2)}`
}

function timestamp() {
  return new Date().toLocaleTimeString()
}

export function useProducts(sessionId, rotateSession) {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  const askQuestion = useCallback(async (question) => {
    const trimmed = question.trim()
    if (!trimmed || isLoading) return

    setApiError('')
    setMessages((previous) => [
      ...previous,
      {
        id: createMessageId(),
        type: 'user',
        content: trimmed,
        timestamp: timestamp(),
      },
    ])
    setIsLoading(true)

    try {
      const result = await postJson('/query', {
        question: trimmed,
        session_id: sessionId,
        max_sources: 10,
      })

      setMessages((previous) => [
        ...previous,
        {
          id: createMessageId(),
          type: 'bot',
          content: result.answer,
          timestamp: timestamp(),
          products: result.products || [],
          appliedFilters: result.applied_filters || {},
          searchStrategy: result.search_strategy,
          queryIntent: result.query_intent,
          usedWebSearch: result.used_web_search,
        },
      ])
    } catch (error) {
      const message = error.name === 'AbortError'
        ? 'The request timed out. Please try again.'
        : 'Sorry, I encountered an API error while processing your request.'

      setApiError(message)
      setMessages((previous) => [
        ...previous,
        {
          id: createMessageId(),
          type: 'bot',
          content: message,
          timestamp: timestamp(),
          isError: true,
          products: [],
          appliedFilters: {},
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, sessionId])

  const clearRemoteSession = useCallback(async () => {
    setApiError('')

    try {
      await postJson('/clear_memory', { session_id: sessionId })
      setMessages([])
      rotateSession()
    } catch {
      setApiError('Unable to clear this session. Please try again.')
    }
  }, [rotateSession, sessionId])

  const resetMessages = useCallback(() => {
    setMessages([])
    setApiError('')
  }, [])

  return {
    messages,
    isLoading,
    apiError,
    askQuestion,
    clearRemoteSession,
    resetMessages,
  }
}
