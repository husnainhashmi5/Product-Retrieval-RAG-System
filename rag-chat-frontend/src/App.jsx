import React, { useEffect, useRef, useState } from 'react'
import { AlertCircle, Bot, ExternalLink, Loader2, Search, Send, Trash2, User } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_TIMEOUT_MS = 30000

const predefinedQuestions = [
  'HMW-20DGS microwave price',
  'Show microwaves under Rs 60,000',
  'HRF-622ICG refrigerator details',
  'Show washing machines in grey',
  'Which one is cheapest?',
]

function formatPrice(price) {
  if (price === null || price === undefined) return 'Price unavailable'
  return `Rs ${Number(price).toLocaleString()}`
}

function filterEntries(filters = {}) {
  return Object.entries(filters).filter(([, value]) => value !== null && value !== undefined && value !== '')
}

async function postJson(path, payload) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS)

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

function ProductCard({ product }) {
  return (
    <article className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-gray-950">{product.name}</h3>
          <div className="mt-2 grid grid-cols-1 gap-1 text-sm text-gray-600 sm:grid-cols-2">
            <span>Model: <strong className="text-gray-800">{product.model || 'Unknown'}</strong></span>
            <span>Brand: <strong className="text-gray-800">{product.brand || 'Unknown'}</strong></span>
            <span>Category: <strong className="text-gray-800">{product.category || 'Unknown'}</strong></span>
            <span>Color: <strong className="text-gray-800">{product.color || product.variation || 'Unknown'}</strong></span>
            <span>Status: <strong className="text-gray-800">{product.status}</strong></span>
            <span>Match: <strong className="text-gray-800">{product.match_type}</strong></span>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-start gap-2 sm:items-end">
          <div className="text-lg font-bold text-gray-950">{formatPrice(product.price)}</div>
          {product.source_url ? (
            <a
              href={product.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-sm font-medium text-blue-700 hover:text-blue-800"
            >
              Source
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          ) : (
            <span className="text-sm text-gray-500">No source link</span>
          )}
        </div>
      </div>
    </article>
  )
}

function AppliedFilters({ filters }) {
  const entries = filterEntries(filters)
  if (!entries.length) return null

  return (
    <div className="mt-3 flex flex-wrap gap-2 border-t border-gray-100 pt-3" aria-label="Applied filters">
      {entries.map(([key, value]) => (
        <span key={key} className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-800">
          {key.replace(/_/g, ' ')}: {String(value)}
        </span>
      ))}
    </div>
  )
}

function BotMessageMeta({ message }) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-3 text-xs text-gray-500">
      <span>{message.timestamp}</span>
      <span className="rounded-full bg-gray-100 px-2 py-1">{message.searchStrategy || 'search'}</span>
      <span className="rounded-full bg-gray-100 px-2 py-1">{message.queryIntent || 'query'}</span>
      {message.usedWebSearch && (
        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-green-700">
          <Search className="h-3 w-3" aria-hidden="true" />
          Web Search
        </span>
      )}
    </div>
  )
}

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState('')
  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}`)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const sendQuery = async (question) => {
    return postJson('/query', {
      question,
      session_id: sessionId,
      max_sources: 10,
    })
  }

  const addUserMessage = (content) => {
    setMessages((previous) => [
      ...previous,
      {
        id: crypto.randomUUID(),
        type: 'user',
        content,
        timestamp: new Date().toLocaleTimeString(),
      },
    ])
  }

  const askQuestion = async (question) => {
    const trimmed = question.trim()
    if (!trimmed || isLoading) return

    setInput('')
    setApiError('')
    addUserMessage(trimmed)
    setIsLoading(true)

    try {
      const result = await sendQuery(trimmed)
      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          type: 'bot',
          content: result.answer,
          timestamp: new Date().toLocaleTimeString(),
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
          id: crypto.randomUUID(),
          type: 'bot',
          content: message,
          timestamp: new Date().toLocaleTimeString(),
          isError: true,
          products: [],
          appliedFilters: {},
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    await askQuestion(input)
  }

  const clearMemory = async () => {
    if (messages.length > 0 && !window.confirm('Clear this chat session?')) return

    setApiError('')
    try {
      await postJson('/clear_memory', { session_id: sessionId })
      setMessages([])
      setSessionId(`session_${Date.now()}`)
    } catch {
      setApiError('Unable to clear this session. Please try again.')
    }
  }

  return (
    <div className="flex h-screen flex-col bg-gray-100">
      <header className="border-b bg-white p-4 shadow-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Bot className="h-8 w-8 text-blue-700" aria-hidden="true" />
            <div>
              <h1 className="text-xl font-bold text-gray-950">Product Retrieval Assistant</h1>
              <p className="text-sm text-gray-500">Session {sessionId.slice(-8)}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={clearMemory}
            className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            aria-label="Clear chat"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            <span>Clear Chat</span>
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto max-w-5xl space-y-4">
          {apiError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              <AlertCircle className="h-4 w-4" aria-hidden="true" />
              {apiError}
            </div>
          )}

          {messages.length === 0 && (
            <section className="py-8 text-center">
              <Bot className="mx-auto mb-4 h-16 w-16 text-gray-300" aria-hidden="true" />
              <h2 className="text-lg font-semibold text-gray-800">Ask about products, prices, colors, and models.</h2>
              <div className="mx-auto mt-6 grid max-w-3xl grid-cols-1 gap-3 md:grid-cols-2">
                {predefinedQuestions.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => askQuestion(question)}
                    disabled={isLoading}
                    className="rounded-lg border border-gray-200 bg-white p-3 text-left text-sm text-gray-700 transition-colors hover:border-blue-300 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </section>
          )}

          {messages.map((message) => (
            <section
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-4xl items-start gap-3 ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                    message.type === 'user'
                      ? 'bg-blue-700 text-white'
                      : message.isError
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {message.type === 'user' ? (
                    <User className="h-4 w-4" aria-hidden="true" />
                  ) : (
                    <Bot className="h-4 w-4" aria-hidden="true" />
                  )}
                </div>

                <div
                  className={`rounded-lg px-4 py-3 ${
                    message.type === 'user'
                      ? 'bg-blue-700 text-white'
                      : message.isError
                        ? 'border border-red-200 bg-red-50 text-red-800'
                        : 'border border-gray-200 bg-white text-gray-800'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>

                  {message.type === 'bot' && !message.isError && (
                    <>
                      {message.products?.length > 0 ? (
                        <div className="mt-4 space-y-3">
                          {message.products.map((product) => (
                            <ProductCard key={product.product_id} product={product} />
                          ))}
                        </div>
                      ) : (
                        <div className="mt-4 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-600">
                          No product records matched the current filters.
                        </div>
                      )}
                      <AppliedFilters filters={message.appliedFilters} />
                      <BotMessageMeta message={message} />
                    </>
                  )}

                  {message.type === 'user' && (
                    <div className="mt-2 text-xs text-blue-100">{message.timestamp}</div>
                  )}
                </div>
              </div>
            </section>
          ))}

          {isLoading && (
            <section className="flex justify-start">
              <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3 text-gray-600">
                <Loader2 className="h-4 w-4 animate-spin text-blue-700" aria-hidden="true" />
                Searching products...
              </div>
            </section>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="border-t bg-white p-4">
        <form className="mx-auto flex max-w-5xl gap-3" onSubmit={handleSubmit}>
          <label htmlFor="product-question" className="sr-only">Product question</label>
          <input
            id="product-question"
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about active products, prices, colors, or exact models..."
            className="min-w-0 flex-1 rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-200"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-5 py-3 font-medium text-white transition-colors hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-5 w-5" aria-hidden="true" />
            )}
            <span>Send</span>
          </button>
        </form>
      </footer>
    </div>
  )
}
