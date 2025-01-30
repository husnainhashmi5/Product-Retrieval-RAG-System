import { useMemo, useState } from 'react'
import { ExternalLink, Grid2X2, List, SlidersHorizontal } from 'lucide-react'

function formatPrice(price) {
  if (price === null || price === undefined || price === '') return 'Price unavailable'
  return `Rs ${Number(price).toLocaleString()}`
}

function filterEntries(filters = {}) {
  return Object.entries(filters).filter(([, value]) => value !== null && value !== undefined && value !== '')
}

function uniqueValues(products, key) {
  return [...new Set(products.map((product) => product[key]).filter(Boolean))].sort()
}

function ProductCard({ product, viewMode }) {
  return (
    <article className={`rounded-lg border border-gray-200 bg-gray-50 p-4 ${viewMode === 'list' ? 'sm:flex sm:items-start sm:justify-between sm:gap-4' : ''}`}>
      <div className="min-w-0">
        <h3 className="text-base font-semibold text-gray-950">{product.name}</h3>
        <div className="mt-3 grid grid-cols-1 gap-2 text-sm text-gray-600 sm:grid-cols-2">
          <span>Model: <strong className="text-gray-800">{product.model || 'Unknown'}</strong></span>
          <span>Brand: <strong className="text-gray-800">{product.brand || 'Unknown'}</strong></span>
          <span>Category: <strong className="text-gray-800">{product.category || 'Unknown'}</strong></span>
          <span>Color: <strong className="text-gray-800">{product.color || product.variation || 'Unknown'}</strong></span>
          <span>Status: <strong className="text-gray-800">{product.status || 'Unknown'}</strong></span>
          <span>Match: <strong className="text-gray-800">{product.match_type || 'retrieval'}</strong></span>
        </div>
      </div>

      <div className="mt-4 flex shrink-0 flex-col items-start gap-2 sm:mt-0 sm:items-end">
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

export default function ProductResults({ products = [], appliedFilters = {} }) {
  const [viewMode, setViewMode] = useState('grid')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  const categories = useMemo(() => uniqueValues(products, 'category'), [products])
  const statuses = useMemo(() => uniqueValues(products, 'status'), [products])

  const visibleProducts = useMemo(() => products.filter((product) => {
    const categoryMatches = categoryFilter === 'all' || product.category === categoryFilter
    const statusMatches = statusFilter === 'all' || product.status === statusFilter
    return categoryMatches && statusMatches
  }), [categoryFilter, products, statusFilter])

  if (!products.length) return null

  return (
    <section className="mt-4 rounded-lg border border-gray-100 bg-white p-4" aria-label="Product results">
      <div className="flex flex-col gap-3 border-b border-gray-100 pb-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Structured Results</h2>
          <p className="mt-1 text-sm text-gray-600">{visibleProducts.length} of {products.length} products shown</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-gray-400" aria-hidden="true" />
          <label className="text-xs font-medium text-gray-600">
            <span className="sr-only">Filter products by category</span>
            <select
              value={categoryFilter}
              onChange={(event) => setCategoryFilter(event.target.value)}
              className="rounded-md border border-gray-200 bg-white px-2 py-1.5 text-sm text-gray-800"
              aria-label="Filter products by category"
            >
              <option value="all">All categories</option>
              {categories.map((category) => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </label>

          <label className="text-xs font-medium text-gray-600">
            <span className="sr-only">Filter products by status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="rounded-md border border-gray-200 bg-white px-2 py-1.5 text-sm text-gray-800"
              aria-label="Filter products by status"
            >
              <option value="all">All statuses</option>
              {statuses.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </label>

          <div className="inline-flex overflow-hidden rounded-md border border-gray-200" aria-label="Result view mode">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-2 ${viewMode === 'grid' ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:bg-gray-50'}`}
              aria-label="Grid view"
            >
              <Grid2X2 className="h-4 w-4" aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`border-l border-gray-200 p-2 ${viewMode === 'list' ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:bg-gray-50'}`}
              aria-label="List view"
            >
              <List className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      <AppliedFilters filters={appliedFilters} />

      <div className={`mt-4 grid gap-3 ${viewMode === 'grid' ? 'md:grid-cols-2' : 'grid-cols-1'}`}>
        {visibleProducts.map((product) => (
          <ProductCard
            key={product.product_id || product.model || product.name}
            product={product}
            viewMode={viewMode}
          />
        ))}
      </div>
    </section>
  )
}
