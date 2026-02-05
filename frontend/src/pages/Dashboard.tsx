import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CreditCard,
  Users,
  Activity,
  ArrowUpRight,
  CheckCircle2,
  AlertCircle,
  Clock,
} from 'lucide-react'
import {
  useAccount,
  useAnalytics,
  useRevenueByDay,
  useTopAffiliates,
  formatCurrency,
  formatPercentage,
} from '../hooks/useStripeConnectFetch'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface DashboardProps {
  accountId: string
}

export default function Dashboard({ accountId }: DashboardProps) {
  const { data: account, isLoading: accountLoading } = useAccount(accountId)
  const { data: analytics, isLoading: analyticsLoading } = useAnalytics(accountId, 30)
  const { data: revenueData } = useRevenueByDay(accountId, 30)
  const { data: topAffiliates } = useTopAffiliates(accountId, 5, 30)

  const isLoading = accountLoading || analyticsLoading

  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Loading skeleton */}
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-card p-6 animate-pulse">
            <div className="h-6 bg-white/10 rounded w-1/4 mb-4" />
            <div className="h-12 bg-white/10 rounded w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  const stats = [
    {
      label: 'Total Revenue',
      value: formatCurrency(analytics?.total_revenue || 0),
      change: analytics?.revenue_change || 0,
      icon: DollarSign,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
    },
    {
      label: 'Commission Earned',
      value: formatCurrency(analytics?.total_commission || 0),
      change: analytics?.commission_change || 0,
      icon: TrendingUp,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      label: 'Payments',
      value: analytics?.payment_count?.toLocaleString() || '0',
      change: analytics?.payment_change || 0,
      icon: CreditCard,
      color: 'text-warning',
      bgColor: 'bg-warning/10',
    },
    {
      label: 'Avg Order Value',
      value: formatCurrency(analytics?.average_order_value || 0),
      change: 0,
      icon: Activity,
      color: 'text-purple-400',
      bgColor: 'bg-purple-400/10',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold">Dashboard</h1>
          <p className="text-muted mt-1">
            Welcome back, {account?.business_name || 'Merchant'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {account?.charges_enabled ? (
            <span className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 text-accent text-sm">
              <CheckCircle2 className="w-4 h-4" />
              Active
            </span>
          ) : (
            <span className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-warning/10 text-warning text-sm">
              <AlertCircle className="w-4 h-4" />
              Setup Required
            </span>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="stat-card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-10 h-10 rounded-xl ${stat.bgColor} flex items-center justify-center`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              {stat.change !== 0 && (
                <span
                  className={`flex items-center gap-1 text-sm ${
                    stat.change > 0 ? 'text-accent' : 'text-error'
                  }`}
                >
                  {stat.change > 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                  {formatPercentage(stat.change)}
                </span>
              )}
            </div>
            <p className="text-muted text-sm">{stat.label}</p>
            <p className={`font-display text-2xl font-bold mt-1 ${stat.color}`}>
              {stat.value}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2 glass-card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-display font-semibold text-lg">Revenue Overview</h3>
            <span className="text-sm text-muted">Last 30 days</span>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueData || []}>
                <defs>
                  <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0066e6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0066e6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="commissionGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date"
                  stroke="rgba(255,255,255,0.3)"
                  fontSize={12}
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                />
                <YAxis
                  stroke="rgba(255,255,255,0.3)"
                  fontSize={12}
                  tickFormatter={(value) => `$${(value / 100).toFixed(0)}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                  }}
                  formatter={(value: number) => [formatCurrency(value), '']}
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#0066e6"
                  strokeWidth={2}
                  fill="url(#revenueGradient)"
                  name="Revenue"
                />
                <Area
                  type="monotone"
                  dataKey="commission"
                  stroke="#00ff88"
                  strokeWidth={2}
                  fill="url(#commissionGradient)"
                  name="Commission"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Top Affiliates */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-display font-semibold text-lg">Top Affiliates</h3>
            <Users className="w-5 h-5 text-muted" />
          </div>
          <div className="space-y-4">
            {topAffiliates && topAffiliates.length > 0 ? (
              topAffiliates.map((affiliate, index) => (
                <div key={affiliate.affiliate_id} className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold text-primary">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {affiliate.affiliate_id.slice(0, 8)}...
                    </p>
                    <p className="text-xs text-muted">
                      {affiliate.payments} payments
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-accent">
                      {formatCurrency(affiliate.revenue)}
                    </p>
                    <p className="text-xs text-muted">
                      {formatCurrency(affiliate.commission)} earned
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted">
                <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No affiliate data yet</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions & Status */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass-card p-6"
        >
          <h3 className="font-display font-semibold text-lg mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-4">
            <a
              href="/payments"
              className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <CreditCard className="w-5 h-5 text-primary" />
                <span className="text-sm font-medium">View Payments</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-muted group-hover:text-white transition-colors" />
            </a>
            <a
              href="/analytics"
              className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-accent" />
                <span className="text-sm font-medium">Analytics</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-muted group-hover:text-white transition-colors" />
            </a>
            <a
              href="/settings"
              className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-warning" />
                <span className="text-sm font-medium">Settings</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-muted group-hover:text-white transition-colors" />
            </a>
            <a
              href="https://dashboard.stripe.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <DollarSign className="w-5 h-5 text-purple-400" />
                <span className="text-sm font-medium">Stripe Dashboard</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-muted group-hover:text-white transition-colors" />
            </a>
          </div>
        </motion.div>

        {/* Account Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="glass-card p-6"
        >
          <h3 className="font-display font-semibold text-lg mb-4">Account Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
              <div className="flex items-center gap-3">
                <CheckCircle2 className={`w-5 h-5 ${account?.charges_enabled ? 'text-accent' : 'text-muted'}`} />
                <span className="text-sm">Charges Enabled</span>
              </div>
              <span className={`text-sm ${account?.charges_enabled ? 'text-accent' : 'text-muted'}`}>
                {account?.charges_enabled ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
              <div className="flex items-center gap-3">
                <CheckCircle2 className={`w-5 h-5 ${account?.payouts_enabled ? 'text-accent' : 'text-muted'}`} />
                <span className="text-sm">Payouts Enabled</span>
              </div>
              <span className={`text-sm ${account?.payouts_enabled ? 'text-accent' : 'text-muted'}`}>
                {account?.payouts_enabled ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
              <div className="flex items-center gap-3">
                <Activity className={`w-5 h-5 ${account?.tracking_enabled ? 'text-accent' : 'text-muted'}`} />
                <span className="text-sm">Conversion Tracking</span>
              </div>
              <span className={`text-sm ${account?.tracking_enabled ? 'text-accent' : 'text-muted'}`}>
                {account?.tracking_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-primary" />
                <span className="text-sm">Commission Rate</span>
              </div>
              <span className="text-sm text-primary font-semibold">
                {((account?.commission_rate || 0) * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
