import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Settings as SettingsIcon,
  Shield,
  Bell,
  Key,
  Webhook,
  ExternalLink,
  Copy,
  Check,
  AlertTriangle,
  Trash2,
} from 'lucide-react'
import {
  useAccount,
  useStripeInfo,
  useUpdateSettings,
  useDisconnectAccount,
} from '../hooks/useStripeConnectFetch'

interface SettingsProps {
  accountId: string
  onDisconnect: () => void
}

export default function Settings({ accountId, onDisconnect }: SettingsProps) {
  const { data: account, isLoading } = useAccount(accountId)
  const { data: stripeInfo } = useStripeInfo(accountId)
  const updateSettings = useUpdateSettings(accountId)
  const disconnectAccount = useDisconnectAccount(accountId)

  const [trackingEnabled, setTrackingEnabled] = useState(account?.tracking_enabled ?? true)
  const [commissionRate, setCommissionRate] = useState(
    ((account?.commission_rate || 0.1) * 100).toString()
  )
  const [webhookUrl, setWebhookUrl] = useState('')
  const [copied, setCopied] = useState(false)
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false)

  const handleSave = async () => {
    await updateSettings.mutateAsync({
      tracking_enabled: trackingEnabled,
      commission_rate: parseFloat(commissionRate) / 100,
      webhook_url: webhookUrl || undefined,
    })
  }

  const handleCopyAccountId = () => {
    navigator.clipboard.writeText(account?.stripe_account_id || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDisconnect = async () => {
    await disconnectAccount.mutateAsync()
    onDisconnect()
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-card p-6 animate-pulse">
            <div className="h-6 bg-white/10 rounded w-1/4 mb-4" />
            <div className="h-12 bg-white/10 rounded w-full" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold">Settings</h1>
        <p className="text-muted mt-1">
          Configure your Stripe Connect integration
        </p>
      </div>

      {/* Account Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Key className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-display font-semibold text-lg">Account Information</h2>
            <p className="text-muted text-sm">Your connected Stripe account details</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
            <div>
              <p className="text-sm text-muted">Stripe Account ID</p>
              <p className="font-mono">{account?.stripe_account_id}</p>
            </div>
            <button
              onClick={handleCopyAccountId}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              {copied ? (
                <Check className="w-5 h-5 text-accent" />
              ) : (
                <Copy className="w-5 h-5 text-muted" />
              )}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-sm text-muted">Business Name</p>
              <p className="font-medium">
                {account?.business_name || stripeInfo?.business_name || 'Not set'}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-sm text-muted">Email</p>
              <p className="font-medium">
                {account?.email || stripeInfo?.email || 'Not set'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-sm text-muted">Country</p>
              <p className="font-medium">{stripeInfo?.country || '—'}</p>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-sm text-muted">Default Currency</p>
              <p className="font-medium uppercase">{stripeInfo?.default_currency || '—'}</p>
            </div>
          </div>

          <a
            href="https://dashboard.stripe.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-primary hover:text-primary-400 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Open Stripe Dashboard
          </a>
        </div>
      </motion.div>

      {/* Tracking Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h2 className="font-display font-semibold text-lg">Tracking Settings</h2>
            <p className="text-muted text-sm">Configure conversion tracking behavior</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Tracking toggle */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
            <div>
              <p className="font-medium">Enable Conversion Tracking</p>
              <p className="text-sm text-muted">
                Track charges and attribute them to affiliates
              </p>
            </div>
            <button
              onClick={() => setTrackingEnabled(!trackingEnabled)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                trackingEnabled ? 'bg-accent' : 'bg-white/20'
              }`}
            >
              <span
                className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  trackingEnabled ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Commission rate */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Commission Rate (%)</label>
            <div className="flex items-center gap-4">
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={commissionRate}
                onChange={(e) => setCommissionRate(e.target.value)}
                className="input-field w-32"
              />
              <input
                type="range"
                min="0"
                max="50"
                step="0.5"
                value={commissionRate}
                onChange={(e) => setCommissionRate(e.target.value)}
                className="flex-1 h-2 bg-white/10 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:rounded-full"
              />
            </div>
            <p className="text-sm text-muted">
              Affiliates will earn {commissionRate}% of each tracked payment
            </p>
          </div>
        </div>
      </motion.div>

      {/* Webhook Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-warning/10 flex items-center justify-center">
            <Webhook className="w-5 h-5 text-warning" />
          </div>
          <div>
            <h2 className="font-display font-semibold text-lg">Webhook Notifications</h2>
            <p className="text-muted text-sm">Receive real-time updates for events</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Webhook URL (optional)</label>
            <input
              type="url"
              placeholder="https://your-server.com/webhook"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="input-field w-full"
            />
            <p className="text-sm text-muted mt-2">
              We'll send POST requests to this URL when conversions are tracked
            </p>
          </div>

          <div className="p-4 rounded-xl bg-primary/5 border border-primary/20">
            <div className="flex items-start gap-3">
              <Bell className="w-5 h-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium text-primary">Events we send</p>
                <ul className="text-sm text-muted mt-2 space-y-1">
                  <li>• charge.tracked - New conversion tracked</li>
                  <li>• charge.refunded - Commission adjusted for refund</li>
                  <li>• charge.disputed - Payment disputed</li>
                  <li>• sync.completed - Data synced to Affilync</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Save Button */}
      <div className="flex justify-end gap-4">
        <button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          className="btn-primary"
        >
          {updateSettings.isPending ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Danger Zone */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-6 border-error/20"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-error/10 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-error" />
          </div>
          <div>
            <h2 className="font-display font-semibold text-lg text-error">Danger Zone</h2>
            <p className="text-muted text-sm">Irreversible actions</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-error/5 border border-error/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Disconnect Stripe Account</p>
              <p className="text-sm text-muted">
                This will stop all tracking and remove your connection
              </p>
            </div>
            {showDisconnectConfirm ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowDisconnectConfirm(false)}
                  className="btn-ghost text-sm py-2"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDisconnect}
                  disabled={disconnectAccount.isPending}
                  className="bg-error hover:bg-error/80 text-white font-semibold px-4 py-2 rounded-xl transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  {disconnectAccount.isPending ? 'Disconnecting...' : 'Confirm'}
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowDisconnectConfirm(true)}
                className="border border-error/30 text-error hover:bg-error/10 font-semibold px-4 py-2 rounded-xl transition-colors"
              >
                Disconnect
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
