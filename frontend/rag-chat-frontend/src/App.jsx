import { useEffect, useRef, useState } from 'react'
import { AlertCircle, Bot, Loader2, Search, Send, Trash2, User } from 'lucide-react'
import ProductResults from './components/ProductResults/ProductResults'
import { ProductProvider } from './context/ProductContext'
import { useProductContext } from './context/useProductContext'

const predefinedQuestions = [
  'HMW-20DGS microwave price',
  'Show microwaves under Rs 60,000',
  'HRF-622ICG refrigerator details',
  'Show washing machines in grey',
  'Which one is cheapest?',
]

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

function ChatInterface() {
  const [input, setInput] = useState('')
  const { sessionId, messages, isLoading, apiError, askQuestion, clearRemoteSession } = useProductContext()
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handleAskQuestion = async (question) => {
    setInput('')
    await askQuestion(question)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    await handleAskQuestion(input)
  }

  const clearMemory = async () => {
    if (messages.length > 0 && !window.confirm('Clear this chat session?')) return
    await clearRemoteSession()
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
                    onClick={() => handleAskQuestion(question)}
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
            <div key={message.id} className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.type === 'bot' && (
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700">
                  <Bot className="h-5 w-5" aria-hidden="true" />
                </div>
              )}

              <div className={`max-w-3xl rounded-lg p-4 shadow-sm ${message.type === 'user' ? 'bg-blue-700 text-white' : message.isError ? 'border border-red-200 bg-red-50 text-red-900' : 'bg-white text-gray-800'}`}>
                <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                {message.type === 'bot' && (
                  <>
                    <ProductResults products={message.products} appliedFilters={message.appliedFilters} />
                    <BotMessageMeta message={message} />
                  </>
                )}
                {message.type === 'user' && (
                  <div className="mt-2 text-right text-xs text-blue-100">{message.timestamp}</div>
                )}
              </div>

              {message.type === 'user' && (
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-900 text-white">
                  <User className="h-5 w-5" aria-hidden="true" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700">
                <Bot className="h-5 w-5" aria-hidden="true" />
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-white p-4 text-sm text-gray-600 shadow-sm">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Searching product catalog...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="border-t bg-white p-4">
        <form onSubmit={handleSubmit} className="mx-auto flex max-w-5xl gap-3">
          <label htmlFor="product-query" className="sr-only">Product question</label>
          <input
            id="product-query"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about a product, price, category, color, or model..."
            disabled={isLoading}
            className="min-w-0 flex-1 rounded-lg border border-gray-300 px-4 py-3 text-sm text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
            <span>Send</span>
          </button>
        </form>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <ProductProvider>
      <ChatInterface />
    </ProductProvider>
  )
}
