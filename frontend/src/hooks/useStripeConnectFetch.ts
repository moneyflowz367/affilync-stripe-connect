import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

const API_BASE = '/api'

interface FetchOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
}

async function fetchAPI<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

// Types
export interface Account {
  id: string
  stripe_account_id: string
  brand_id: string | null
  business_name: string | null
  email: string | null
  charges_enabled: boolean
  payouts_enabled: boolean
  tracking_enabled: boolean
  commission_rate: number
  total_revenue: number
  total_commission: number
  payment_count: number
  created_at: string
}

export interface Payment {
  id: string
  stripe_charge_id: string
  stripe_payment_intent_id: string | null
  amount: number
  currency: string
  net_amount: number | null
  commission_amount: number
  commission_status: string
  tracking_code: string | null
  affiliate_id: string | null
  customer_email: string | null
  is_subscription: boolean
  is_refunded: boolean
  is_disputed: boolean
  created_at: string
}

export interface AnalyticsOverview {
  total_revenue: number
  total_commission: number
  payment_count: number
  average_order_value: number
  conversion_rate: number
  refund_rate: number
  revenue_change: number
  commission_change: number
  payment_change: number
}

export interface RevenueByDay {
  date: string
  revenue: number
  commission: number
  payments: number
}

export interface TopAffiliate {
  affiliate_id: string
  revenue: number
  commission: number
  payments: number
}

export interface WebhookLog {
  id: string
  stripe_event_id: string
  event_type: string
  status: string
  processing_time_ms: number | null
  created_at: string
}

export interface PaginatedPayments {
  payments: Payment[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PaginatedWebhooks {
  logs: WebhookLog[]
  total: number
  page: number
  page_size: number
}

// Hooks
export function useAccount(accountId: string | null) {
  return useQuery({
    queryKey: ['account', accountId],
    queryFn: () => fetchAPI<Account>(`/account/${accountId}`),
    enabled: !!accountId,
  })
}

export function useAccountByStripeId(stripeAccountId: string | null) {
  return useQuery({
    queryKey: ['account', 'stripe', stripeAccountId],
    queryFn: () => fetchAPI<Account>(`/account/stripe/${stripeAccountId}`),
    enabled: !!stripeAccountId,
  })
}

export function usePayments(
  accountId: string | null,
  page: number = 1,
  pageSize: number = 20,
  statusFilter?: string
) {
  return useQuery({
    queryKey: ['payments', accountId, page, pageSize, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      if (statusFilter) params.set('status_filter', statusFilter)
      return fetchAPI<PaginatedPayments>(`/account/${accountId}/payments?${params}`)
    },
    enabled: !!accountId,
  })
}

export function useAnalytics(accountId: string | null, days: number = 30) {
  return useQuery({
    queryKey: ['analytics', accountId, days],
    queryFn: () => fetchAPI<AnalyticsOverview>(`/account/${accountId}/analytics?days=${days}`),
    enabled: !!accountId,
  })
}

export function useRevenueByDay(accountId: string | null, days: number = 30) {
  return useQuery({
    queryKey: ['revenue-by-day', accountId, days],
    queryFn: () => fetchAPI<RevenueByDay[]>(`/account/${accountId}/analytics/revenue?days=${days}`),
    enabled: !!accountId,
  })
}

export function useTopAffiliates(accountId: string | null, limit: number = 10, days: number = 30) {
  return useQuery({
    queryKey: ['top-affiliates', accountId, limit, days],
    queryFn: () =>
      fetchAPI<TopAffiliate[]>(
        `/account/${accountId}/analytics/top-affiliates?limit=${limit}&days=${days}`
      ),
    enabled: !!accountId,
  })
}

export function useWebhookLogs(
  accountId: string | null,
  page: number = 1,
  pageSize: number = 20,
  eventType?: string
) {
  return useQuery({
    queryKey: ['webhook-logs', accountId, page, pageSize, eventType],
    queryFn: () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      if (eventType) params.set('event_type', eventType)
      return fetchAPI<PaginatedWebhooks>(`/account/${accountId}/webhooks?${params}`)
    },
    enabled: !!accountId,
  })
}

export function useStripeInfo(accountId: string | null) {
  return useQuery({
    queryKey: ['stripe-info', accountId],
    queryFn: () => fetchAPI<Record<string, unknown>>(`/account/${accountId}/stripe-info`),
    enabled: !!accountId,
  })
}

// Mutations
export function useUpdateSettings(accountId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (settings: {
      tracking_enabled?: boolean
      commission_rate?: number
      webhook_url?: string
    }) => fetchAPI(`/account/${accountId}/settings`, { method: 'PATCH', body: settings }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account', accountId] })
    },
  })
}

export function useDisconnectAccount(accountId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => fetchAPI(`/account/${accountId}/disconnect`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account'] })
    },
  })
}

// Helper to format currency
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 2,
  }).format(amount / 100) // Stripe amounts are in cents
}

// Helper to format percentage
export function formatPercentage(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}

// Helper to format date
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
