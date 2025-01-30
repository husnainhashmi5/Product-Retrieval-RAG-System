import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

const queryResponse = {
  answer: 'Here are the matching products.',
  products: [
    {
      product_id: 'product-001',
      name: 'Samsung Galaxy A16',
      brand: 'Samsung',
      model: 'A16',
      price: 48999,
      category: 'phone',
      color: 'Black',
      variation: 'Black',
      status: 'active',
      source_url: 'https://example.com/a16',
      score: 0.92,
      match_type: 'metadata',
    },
  ],
  applied_filters: {
    max_price: 50000,
    brand: 'Samsung',
    category: 'phone',
    color: 'Black',
    status: 'active',
  },
  session_id: 'session-test',
  search_strategy: 'metadata_then_vector',
  query_intent: 'price_filter',
  used_web_search: false,
  latency_ms: 12,
  metadata: { result_count: 1 },
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn((url) => {
      if (String(url).endsWith('/query')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(queryResponse),
        })
      }
      if (String(url).endsWith('/clear_memory')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Memory cleared successfully', session_id: 'session-test' }),
        })
      }
      return Promise.reject(new Error(`Unhandled URL ${url}`))
    }))
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('renders structured product cards and applied filters from the API response', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText(/product question/i), 'Show active Samsung phones under Rs 50,000 in black')
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(await screen.findByText('Samsung Galaxy A16')).toBeTruthy()
    expect(screen.getByText('A16')).toBeTruthy()
    expect(screen.getByText('Rs 48,999')).toBeTruthy()
    expect(screen.getAllByText('phone').length).toBeGreaterThan(0)
    expect(screen.getByText('Black')).toBeTruthy()
    expect(screen.getByRole('link', { name: /source/i })).toBeTruthy()
    expect(screen.getByText('max price: 50000')).toBeTruthy()
    expect(screen.getByText('brand: Samsung')).toBeTruthy()
  })

  it('clears only the current session through the JSON request body', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText(/product question/i), 'Show microwaves')
    await user.click(screen.getByRole('button', { name: /send/i }))
    await screen.findByText('Samsung Galaxy A16')
    await user.click(screen.getByRole('button', { name: /clear chat/i }))

    await waitFor(() => {
      const clearCall = fetch.mock.calls.find(([url]) => String(url).endsWith('/clear_memory'))
      expect(clearCall).toBeTruthy()
      const body = JSON.parse(clearCall[1].body)
      expect(body.session_id).toMatch(/^session_/)
    })
  })
})
