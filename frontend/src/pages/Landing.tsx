import { motion } from 'framer-motion'
import {
  Zap,
  ArrowRight,
  Shield,
  BarChart3,
  CreditCard,
  Users,
  CheckCircle2,
} from 'lucide-react'

const features = [
  {
    icon: CreditCard,
    title: 'Automatic Tracking',
    description: 'Every payment is automatically tracked and attributed to affiliates via metadata.',
  },
  {
    icon: BarChart3,
    title: 'Real-time Analytics',
    description: 'Monitor revenue, commissions, and affiliate performance in real-time.',
  },
  {
    icon: Users,
    title: 'Affiliate Attribution',
    description: 'Seamlessly attribute conversions to affiliates using tracking codes.',
  },
  {
    icon: Shield,
    title: 'Secure & Reliable',
    description: 'Enterprise-grade security with encrypted tokens and webhook verification.',
  },
]

const steps = [
  'Connect your Stripe account',
  'Configure commission rates',
  'Add tracking metadata to charges',
  'Watch conversions roll in',
]

export default function Landing() {
  const handleConnect = () => {
    window.location.href = '/oauth/connect'
  }

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-[120px]" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display font-bold text-lg">Affilync</h1>
              <p className="text-xs text-muted">Stripe Connect</p>
            </div>
          </div>
          <button onClick={handleConnect} className="btn-primary flex items-center gap-2">
            Connect Stripe
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Hero section */}
      <section className="relative z-10 py-24">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm mb-8">
              <Zap className="w-4 h-4" />
              Powered by Affilync
            </span>
            <h1 className="font-display text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Track Affiliate
              <br />
              <span className="gradient-text">Conversions</span> from
              <br />
              Stripe Payments
            </h1>
            <p className="text-xl text-muted max-w-2xl mx-auto mb-10">
              Connect your Stripe account and automatically track affiliate conversions,
              calculate commissions, and sync data to the Affilync platform.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={handleConnect}
                className="btn-accent flex items-center gap-2 text-lg px-8 py-4"
              >
                Connect with Stripe
                <ArrowRight className="w-5 h-5" />
              </button>
              <a
                href="https://affilync.com"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-ghost"
              >
                Learn about Affilync
              </a>
            </div>
          </motion.div>

          {/* Stats preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-20 glass-card p-8 max-w-4xl mx-auto"
          >
            <div className="grid grid-cols-3 gap-8">
              {[
                { label: 'Revenue Tracked', value: '$2.4M+', color: 'text-accent' },
                { label: 'Commissions Paid', value: '$240K+', color: 'text-primary' },
                { label: 'Active Merchants', value: '1,200+', color: 'text-warning' },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <p className={`font-display text-4xl font-bold ${stat.color}`}>{stat.value}</p>
                  <p className="text-muted mt-2">{stat.label}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 py-24 bg-surface/50">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="font-display text-4xl font-bold mb-4">
              Everything You Need
            </h2>
            <p className="text-muted text-lg max-w-2xl mx-auto">
              Powerful features to track, manage, and optimize your affiliate conversions.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="glass-card p-6 hover:border-primary/30 transition-colors group"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-display font-semibold text-lg mb-2">{feature.title}</h3>
                <p className="text-muted text-sm">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="relative z-10 py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="font-display text-4xl font-bold mb-6">
                Get Started in
                <br />
                <span className="gradient-text">4 Simple Steps</span>
              </h2>
              <p className="text-muted text-lg mb-8">
                Connect your Stripe account and start tracking affiliate conversions
                in under 5 minutes.
              </p>
              <div className="space-y-4">
                {steps.map((step, index) => (
                  <motion.div
                    key={step}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="flex items-center gap-4"
                  >
                    <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
                      <CheckCircle2 className="w-5 h-5 text-accent" />
                    </div>
                    <p className="text-lg">{step}</p>
                  </motion.div>
                ))}
              </div>
              <button
                onClick={handleConnect}
                className="btn-primary mt-8 flex items-center gap-2"
              >
                Start Now
                <ArrowRight className="w-4 h-4" />
              </button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="relative"
            >
              <div className="glass-card p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-3 h-3 rounded-full bg-error" />
                  <div className="w-3 h-3 rounded-full bg-warning" />
                  <div className="w-3 h-3 rounded-full bg-accent" />
                </div>
                <pre className="font-mono text-sm text-muted overflow-x-auto">
                  <code>{`// Add tracking code to charge metadata
const charge = await stripe.charges.create({
  amount: 2000,
  currency: 'usd',
  source: 'tok_visa',
  metadata: {
    tracking_code: 'AFF_12345',
    affiliate_id: 'aff_abc123'
  }
});

// Affilync automatically tracks:
// ✓ Charge amount
// ✓ Commission calculation
// ✓ Affiliate attribution
// ✓ Real-time sync`}</code>
                </pre>
              </div>
              {/* Decorative glow */}
              <div className="absolute -inset-4 bg-gradient-to-r from-primary/20 to-accent/20 rounded-3xl blur-xl -z-10" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-24">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="glass-card p-12 relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/5" />
            <div className="relative z-10">
              <h2 className="font-display text-4xl font-bold mb-4">
                Ready to Track Conversions?
              </h2>
              <p className="text-muted text-lg mb-8">
                Connect your Stripe account and start tracking affiliate revenue today.
              </p>
              <button
                onClick={handleConnect}
                className="btn-accent text-lg px-10 py-4 flex items-center gap-2 mx-auto"
              >
                Connect with Stripe
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-8">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-2 text-muted">
            <Zap className="w-4 h-4" />
            <span className="text-sm">Powered by Affilync</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted">
            <a href="https://affilync.com/privacy" className="hover:text-white transition-colors">
              Privacy
            </a>
            <a href="https://affilync.com/terms" className="hover:text-white transition-colors">
              Terms
            </a>
            <a href="https://affilync.com/support" className="hover:text-white transition-colors">
              Support
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
