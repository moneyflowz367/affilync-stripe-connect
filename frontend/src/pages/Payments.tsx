import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  CreditCard,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
} from 'lucide-react'
import {
  usePayments,
  formatCurrency,
  formatDateTime,
} from '../hooks/useStripeConnectFetch'

interface PaymentsProps {
  accountId: string
}

const statusColors: Record<string, { bg: string; text: string; icon: typeof CheckCircle2 }> = {
  pending: { bg: 'bg-warning/10', text: 'text-warning', icon: Clock },
  synced: { bg: 'bg-accent/10', text: 'text-accent', icon: CheckCircle2 },
  failed: { bg: 'bg-error/10', text: 'text-error', icon: XCircle },
  disputed: { bg: 'bg-error/10', text: 'text-error', icon: AlertTriangle },
}

export default function Payments({ accountId }: PaymentsProps) {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const pageSize = 20

  const { data, isLoading, refetch, isFetching } = usePayments(
    accountId,
    page,
    pageSize,
    statusFilter || undefined
  )

  const filteredPayments = data?.payments.filter((payment) => {
    if (!searchTerm) return true
    return (
      payment.stripe_charge_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payment.tracking_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payment.customer_email?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold">Payments</h1>
          <p className="text-muted mt-1">
            Track and manage affiliate conversions
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="btn-ghost flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="glass-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
            <input
              type="text"
              placeholder="Search by charge ID, tracking code, or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field w-full pl-10"
            />
          </div>

          {/* Status filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="input-field pl-10 pr-8 appearance-none cursor-pointer min-w-[180px]"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="synced">Synced</option>
              <option value="failed">Failed</option>
              <option value="disputed">Disputed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Payments Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card overflow-hidden"
      >
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-pulse">
              <CreditCard className="w-12 h-12 mx-auto text-muted mb-4" />
              <p className="text-muted">Loading payments...</p>
            </div>
          </div>
        ) : filteredPayments && filteredPayments.length > 0 ? (
          <>
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 p-4 border-b border-white/5 text-sm font-medium text-muted">
              <div className="col-span-3">Charge</div>
              <div className="col-span-2">Amount</div>
              <div className="col-span-2">Commission</div>
              <div className="col-span-2">Tracking</div>
              <div className="col-span-2">Status</div>
              <div className="col-span-1">Date</div>
            </div>

            {/* Table Body */}
            <div className="divide-y divide-white/5">
              {filteredPayments.map((payment) => {
                const status = statusColors[payment.commission_status] || statusColors.pending
                const StatusIcon = status.icon

                return (
                  <motion.div
                    key={payment.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="grid grid-cols-12 gap-4 p-4 items-center table-row"
                  >
                    {/* Charge ID */}
                    <div className="col-span-3">
                      <p className="font-mono text-sm truncate">
                        {payment.stripe_charge_id}
                      </p>
                      {payment.customer_email && (
                        <p className="text-xs text-muted truncate">
                          {payment.customer_email}
                        </p>
                      )}
                    </div>

                    {/* Amount */}
                    <div className="col-span-2">
                      <p className="font-semibold">
                        {formatCurrency(payment.amount, payment.currency)}
                      </p>
                      {payment.is_refunded && (
                        <span className="text-xs text-error">Refunded</span>
                      )}
                      {payment.is_disputed && (
                        <span className="text-xs text-error">Disputed</span>
                      )}
                    </div>

                    {/* Commission */}
                    <div className="col-span-2">
                      <p className="text-accent font-semibold">
                        {formatCurrency(payment.commission_amount, payment.currency)}
                      </p>
                    </div>

                    {/* Tracking Code */}
                    <div className="col-span-2">
                      {payment.tracking_code ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-md bg-primary/10 text-primary text-xs font-mono">
                          {payment.tracking_code}
                        </span>
                      ) : (
                        <span className="text-muted text-sm">—</span>
                      )}
                    </div>

                    {/* Status */}
                    <div className="col-span-2">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.bg} ${status.text}`}
                      >
                        <StatusIcon className="w-3.5 h-3.5" />
                        {payment.commission_status}
                      </span>
                    </div>

                    {/* Date */}
                    <div className="col-span-1">
                      <p className="text-sm text-muted">
                        {formatDateTime(payment.created_at).split(',')[0]}
                      </p>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </>
        ) : (
          <div className="p-12 text-center">
            <CreditCard className="w-12 h-12 mx-auto text-muted mb-4" />
            <h3 className="font-display font-semibold text-lg mb-2">No Payments Found</h3>
            <p className="text-muted text-sm">
              {statusFilter
                ? `No payments with status "${statusFilter}"`
                : 'Payments will appear here once you start receiving charges with tracking metadata.'}
            </p>
          </div>
        )}

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-white/5">
            <p className="text-sm text-muted">
              Showing {(page - 1) * pageSize + 1} to{' '}
              {Math.min(page * pageSize, data.total)} of {data.total} payments
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-sm px-4">
                Page {page} of {data.total_pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          {
            label: 'Total Payments',
            value: data?.total || 0,
            color: 'text-primary',
          },
          {
            label: 'With Tracking',
            value: data?.payments.filter((p) => p.tracking_code).length || 0,
            color: 'text-accent',
          },
          {
            label: 'Refunded',
            value: data?.payments.filter((p) => p.is_refunded).length || 0,
            color: 'text-warning',
          },
          {
            label: 'Disputed',
            value: data?.payments.filter((p) => p.is_disputed).length || 0,
            color: 'text-error',
          },
        ].map((stat) => (
          <div key={stat.label} className="glass-card p-4">
            <p className="text-muted text-sm">{stat.label}</p>
            <p className={`font-display text-2xl font-bold ${stat.color}`}>
              {stat.value.toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
