import { ProductContext } from './product-context'
import { useProducts } from '../hooks/useProducts'
import { useSession } from '../hooks/useSession'

export function ProductProvider({ children }) {
  const { sessionId, rotateSession } = useSession()
  const productState = useProducts(sessionId, rotateSession)

  return (
    <ProductContext.Provider value={{ sessionId, rotateSession, ...productState }}>
      {children}
    </ProductContext.Provider>
  )
}
