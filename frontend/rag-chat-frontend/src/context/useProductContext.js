import { useContext } from 'react'
import { ProductContext } from './product-context'

export function useProductContext() {
  const context = useContext(ProductContext)

  if (!context) {
    throw new Error('useProductContext must be used within ProductProvider')
  }

  return context
}
