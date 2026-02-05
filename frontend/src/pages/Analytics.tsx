import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  ArrowUpRight,
  Calendar,
} from 'lucide-react'
import {
  useAnalytics,
  useRevenueByDay,
  useTopAffiliates,
  formatCurrency,
  formatPercentage,
} from '../hooks/useStripeConnectFetch'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface AnalyticsProps {
  accountId: string
}

export default function Analytics({ accountId }: AnalyticsProps) {
  const [timeRange, setTimeRange] = useState(30)
  const { data: analytics, isLoading: analyticsLoading } = useAnalytics(accountId, timeRange)
  const { data: revenueData, isLoading: revenueLoading } = useRevenueByDay(accountId, timeRange)
  const { data: topAffiliates, isLoading: affiliatesLoading } = useTopAffiliates(accountId, 10, timeRange)

  const isLoading = analyticsLoading || revenueLoading || affiliatesLoading

  const timeRanges = [
    { label: '7 days', value: 7 },
    { label: '30 days', value: 30 },
    { label: '90 days', value: 90 },
    { label: '1 year', value: 365 },
  ]

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-card p-6 animate-pulse">
            <div className="h-6 bg-white/10 rounded w-1/4 mb-4" />
            <div className="h-48 bg-white/10 rounded" />
          </div>
        ))}
      </div>
    )
  }

  const metrics = [
    {
      label: 'Total Revenue',
      value: formatCurrency(analytics?.total_revenue || 0),
      change: analytics?.revenue_change || 0,
      icon: DollarSign,
      color: 'from-primary to-primary/50',
    },
    {
      label: 'Total Commission',
      value: formatCurrency(analytics?.total_commission || 0),
      change: analytics?.commission_change || 0,
      icon: TrendingUp,
      color: 'from-accent to-accent/50',
    },
    {
      label: 'Avg Order Value',
      value: formatCurrency(analytics?.average_order_value || 0),
      change: 0,
      icon: BarChart3,
      color: 'from-warning to-warning/50',
    },
    {
      label: 'Refund Rate',
      value: `${((analytics?.refund_rate || 0) * 100).toFixed(1)}%`,
      change: 0,
      icon: ArrowUpRight,
      color: 'from-purple-500 to-purple-500/50',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold">Analytics</h1>
          <p className="text-muted mt-1">
            Performance insights and trends
          </p>
        </div>
        <div className="flex items-center gap-2 bg-surface rounded-xl p-1">
          {timeRanges.map((range) => (
            <button
              key={range.value}
              onClick={() => setTimeRange(range.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                timeRange === range.value
                  ? 'bg-primary text-white'
                  : 'text-muted hover:text-white'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card p-6 relative overflow-hidden"
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${metric.color} opacity-5`} />
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <metric.icon className="w-5 h-5 text-muted" />
                {metric.change !== 0 && (
                  <span
                    className={`flex items-center gap-1 text-sm ${
                      metric.change > 0 ? 'text-accent' : 'text-error'
                    }`}
                  >
                    {metric.change > 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    {formatPercentage(metric.change)}
                  </span>
                )}
              </div>
              <p className="text-muted text-sm mb-1">{metric.label}</p>
              <p className="font-display text-2xl font-bold">{metric.value}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Revenue Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-card p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="font-display font-semibold text-lg">Revenue & Commission</h3>
            <p className="text-muted text-sm">Daily breakdown over selected period</p>
          </div>
          <Calendar className="w-5 h-5 text-muted" />
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={revenueData || []}>
              <defs>
                <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0066e6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#0066e6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="commissionGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff88" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="date"
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })
                }
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
                formatter={(value: number, name: string) => [
                  formatCurrency(value),
                  name === 'revenue' ? 'Revenue' : 'Commission',
                ]}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                formatter={(value) => (
                  <span className="text-muted text-sm capitalize">{value}</span>
                )}
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#0066e6"
                strokeWidth={2}
                fill="url(#revenueGradient)"
              />
              <Area
                type="monotone"
                dataKey="commission"
                stroke="#00ff88"
                strokeWidth={2}
                fill="url(#commissionGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Bottom Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Payments by Day */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-display font-semibold text-lg">Payment Volume</h3>
              <p className="text-muted text-sm">Number of payments per day</p>
            </div>
            <BarChart3 className="w-5 h-5 text-muted" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenueData || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date"
                  stroke="rgba(255,255,255,0.3)"
                  fontSize={12}
                  tickFormatter={(value) =>
                    new Date(value).toLocaleDateString('en-US', { day: 'numeric' })
                  }
                />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    padding: '12px',
                  }}
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                />
                <Bar dataKey="payments" fill="#0066e6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Top Affiliates */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass-card p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-display font-semibold text-lg">Top Affiliates</h3>
              <p className="text-muted text-sm">By revenue generated</p>
            </div>
            <Users className="w-5 h-5 text-muted" />
          </div>
          <div className="space-y-4">
            {topAffiliates && topAffiliates.length > 0 ? (
              topAffiliates.slice(0, 5).map((affiliate, index) => {
                const maxRevenue = topAffiliates[0]?.revenue || 1
                const percentage = (affiliate.revenue / maxRevenue) * 100

                return (
                  <div key={affiliate.affiliate_id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-xs font-semibold text-primary">
                          {index + 1}
                        </div>
                        <span className="text-sm font-medium font-mono">
                          {affiliate.affiliate_id.slice(0, 12)}...
                        </span>
                      </div>
                      <span className="text-sm text-accent font-semibold">
                        {formatCurrency(affiliate.revenue)}
                      </span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 1, delay: index * 0.1 }}
                        className="h-full bg-gradient-to-r from-primary to-accent rounded-full"
                      />
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="text-center py-8 text-muted">
                <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No affiliate data yet</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Commission Trend */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="glass-card p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="font-display font-semibold text-lg">Commission Trend</h3>
            <p className="text-muted text-sm">Commission earned over time</p>
          </div>
          <TrendingUp className="w-5 h-5 text-accent" />
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={revenueData || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="date"
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })
                }
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
                formatter={(value: number) => [formatCurrency(value), 'Commission']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Line
                type="monotone"
                dataKey="commission"
                stroke="#00ff88"
                strokeWidth={3}
                dot={false}
                activeDot={{ r: 6, fill: '#00ff88' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </div>
  )
}
