const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface BackendUser {
  id: number
  name: string
  phone_number: string
}

export interface BackendSession {
  id: string
  description: string | null
  owner_id: number
  status: "active" | "closed"
}

export interface BackendInvoice {
  id: number
  description: string | null
  total: number
  pending_amount: number
  payer_id: number
  session_id: string
}

export interface BackendItem {
  id: number
  invoice_id: number
  debtor_id: number | null
  unit_price: number
  paid_amount: number
  tip: number
  total: number
  is_paid: boolean
  payment_id: number | null
  description: string | null
  debtor?: BackendUser
}

export interface SessionData {
  sessionId: string
  tituloCompra: string
  fecha: string
  montoTotal: number
  saldoFaltante: number
}

export interface Participante {
  id: string
  nombre: string
  montoReembolsadoEnEstaCompra: number
  estadoPago: "pagado" | "pendiente" | "atrasado"
}

/**
 * Fetch a session by ID
 */
export async function getSession(sessionId: string): Promise<BackendSession> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch session: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Fetch invoices for a session
 */
export async function getInvoicesBySession(sessionId: string): Promise<BackendInvoice[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/invoices/session/${sessionId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch invoices: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Fetch items for an invoice
 */
export async function getItemsByInvoice(invoiceId: number): Promise<BackendItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/items/invoice/${invoiceId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch items: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Fetch a user by ID
 */
export async function getUser(userId: number): Promise<BackendUser> {
  const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch user: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Transform backend data to frontend format
 */
export function transformSessionData(
  session: BackendSession,
  invoices: BackendInvoice[],
  itemsByInvoice: Record<number, BackendItem[]>
): { sessionData: SessionData; participants: Participante[] } {
  // Calculate total amount from all invoices
  const montoTotal = invoices.reduce((sum, invoice) => sum + Number(invoice.total), 0)

  // Calculate pending amount (saldo faltante) from all invoices
  const saldoFaltante = invoices.reduce((sum, invoice) => sum + Number(invoice.pending_amount), 0)

  // Get current date formatted
  const fecha = new Date().toLocaleDateString("es-CL", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })

  const sessionData: SessionData = {
    sessionId: session.id,
    tituloCompra: session.description || "Sesión sin descripción",
    fecha,
    montoTotal,
    saldoFaltante,
  }

  // Collect all unique users from items
  const userItemsMap = new Map<number, BackendItem[]>()

  // Group items by debtor
  invoices.forEach((invoice) => {
    const items = itemsByInvoice[invoice.id] || []
    items.forEach((item) => {
      if (item.debtor_id) {
        if (!userItemsMap.has(item.debtor_id)) {
          userItemsMap.set(item.debtor_id, [])
        }
        userItemsMap.get(item.debtor_id)!.push(item)
      }
    })
  })

  // Transform to participants
  const participants: Participante[] = Array.from(userItemsMap.entries()).map(([userId, items]) => {
    // Only sum items that are paid
    const montoReembolsado = items
      .reduce((sum, item) => sum + Number(item.total), 0)
    const allPaid = items.every((item) => item.is_paid)
    const somePaid = items.some((item) => item.is_paid)

    // Determine payment status
    let estadoPago: "pagado" | "pendiente" | "atrasado"
    if (allPaid) {
      estadoPago = "pagado"
    } else if (somePaid) {
      estadoPago = "pendiente"
    } else {
      estadoPago = "pendiente"
    }

    // Get user name from first item's debtor if available
    const userName = items[0]?.debtor?.name || `Usuario ${userId}`

    return {
      id: userId.toString(),
      nombre: userName,
      montoReembolsadoEnEstaCompra: montoReembolsado,
      estadoPago,
    }
  })

  return { sessionData, participants }
}

/**
 * Fetch complete session data with all related information
 */
export async function getSessionData(sessionId: string): Promise<{
  sessionData: SessionData
  participants: Participante[]
}> {
  // Fetch session
  const session = await getSession(sessionId)

  // Fetch invoices for the session
  const invoices = await getInvoicesBySession(sessionId)

  // Fetch items for each invoice
  const itemsPromises = invoices.map((invoice) => getItemsByInvoice(invoice.id))
  const itemsArrays = await Promise.all(itemsPromises)

  // Create a map of invoice_id -> items
  const itemsByInvoice: Record<number, BackendItem[]> = {}
  invoices.forEach((invoice, index) => {
    itemsByInvoice[invoice.id] = itemsArrays[index]
  })

  // Fetch user details for items that don't have debtor info loaded
  const userIds = new Set<number>()
  itemsArrays.flat().forEach((item) => {
    if (item.debtor_id && !item.debtor) {
      userIds.add(item.debtor_id)
    }
  })

  // Fetch missing user details if needed
  if (userIds.size > 0) {
    const userPromises = Array.from(userIds).map((userId) => getUser(userId))
    const users = await Promise.all(userPromises)
    const userMap = new Map(users.map((user) => [user.id, user]))

    // Attach user details to items
    itemsArrays.forEach((items) => {
      items.forEach((item) => {
        if (item.debtor_id && !item.debtor) {
          item.debtor = userMap.get(item.debtor_id)
        }
      })
    })
  }

  return transformSessionData(session, invoices, itemsByInvoice)
}

