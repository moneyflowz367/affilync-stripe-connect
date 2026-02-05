# Affilync Stripe Connect Integration

Track affiliate conversions from Stripe payments and sync them to the Affilync platform.

## Overview

This integration allows SaaS businesses and merchants using Stripe to:
- Connect their Stripe accounts via OAuth
- Automatically track charges and attribute them to affiliates
- Calculate and track affiliate commissions
- Sync conversion data to the Affilync platform
- View real-time analytics and performance metrics

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Stripe Connect                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Frontend   │  │   Backend    │  │    Webhooks      │   │
│  │   (React)    │──│  (FastAPI)   │──│  (Stripe Events) │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│         │                 │                   │              │
│         └─────────────────┼───────────────────┘              │
│                           │                                  │
│                    ┌──────▼──────┐                           │
│                    │  PostgreSQL │                           │
│                    │  (Neon DB)  │                           │
│                    └─────────────┘                           │
│                           │                                  │
│                    ┌──────▼──────┐                           │
│                    │  Affilync   │                           │
│                    │    API      │                           │
│                    └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Conversion Tracking
- Automatic charge tracking via Stripe webhooks
- Metadata-based affiliate attribution
- Support for one-time charges and subscriptions
- Refund and dispute handling
- Commission calculation and tracking

### Dashboard
- Real-time revenue and commission metrics
- Daily/weekly/monthly analytics
- Top affiliate leaderboard
- Payment history with filtering
- Webhook event logs

### Configuration
- Customizable commission rates
- Webhook notifications to external systems
- Enable/disable tracking
- Secure token storage

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (Neon)
- **ORM:** SQLAlchemy (async)
- **Authentication:** JWT
- **Payments:** Stripe API

### Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** Tailwind CSS
- **Components:** Radix UI
- **Charts:** Recharts
- **Animations:** Framer Motion
- **Data Fetching:** TanStack Query

## Project Structure

```
affilync-stripe-connect/
├── backend/
│   ├── app/
│   │   ├── config.py           # Settings and environment
│   │   ├── database.py         # Database connection
│   │   ├── main.py             # FastAPI app entry
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── account.py      # StripeConnectedAccount
│   │   │   ├── payment.py      # TrackedPayment
│   │   │   └── webhook_log.py  # StripeWebhookLog
│   │   ├── routes/             # API endpoints
│   │   │   ├── api.py          # Dashboard API
│   │   │   ├── oauth.py        # Stripe OAuth flow
│   │   │   └── webhooks.py     # Webhook handlers
│   │   ├── services/           # Business logic
│   │   │   ├── account_service.py
│   │   │   ├── commission_service.py
│   │   │   └── stripe_client.py
│   │   ├── middleware/         # Rate limiting, etc.
│   │   └── utils/              # Encryption utilities
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── hooks/              # Data fetching hooks
│   │   │   └── useStripeConnectFetch.ts
│   │   ├── components/         # Shared components
│   │   │   └── Layout.tsx
│   │   └── pages/              # Page components
│   │       ├── Landing.tsx
│   │       ├── Dashboard.tsx
│   │       ├── Payments.tsx
│   │       ├── Analytics.tsx
│   │       └── Settings.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── render.yaml                  # Render deployment config
└── README.md
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database (Neon recommended)
- Stripe account with Connect enabled

### Stripe Configuration

1. Enable Stripe Connect in your Stripe Dashboard
2. Create a Connect application and get your Client ID
3. Configure OAuth redirect URLs:
   - Development: `http://localhost:8000/oauth/callback`
   - Production: `https://connect.affilync.com/oauth/callback`
4. Set up webhooks:
   - Endpoint URL: `https://connect.affilync.com/webhooks/stripe`
   - Events to listen for:
     - `charge.succeeded`
     - `charge.refunded`
     - `charge.dispute.created`
     - `invoice.paid`
     - `invoice.payment_failed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `account.application.deauthorized`
     - `account.updated`

### Environment Variables

```bash
# Backend
ENVIRONMENT=development
DATABASE_URL=postgresql://user:pass@host/db
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CLIENT_ID=ca_...
ENCRYPTION_KEY=<auto-generated>
JWT_SECRET_KEY=<auto-generated>
AFFILYNC_API_KEY=<your-affilync-api-key>
AFFILYNC_API_URL=https://api.affilync.com
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
```

### Running Locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## How Tracking Works

### Attribution via Metadata

When creating a charge or payment intent, include tracking metadata:

```javascript
// Stripe.js / Server-side
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000,
  currency: 'usd',
  metadata: {
    tracking_code: 'AFF_12345',      // Required for attribution
    affiliate_id: 'aff_abc123',       // Optional: direct affiliate ID
    campaign_id: 'camp_xyz789',       // Optional: campaign reference
  }
});
```

### Webhook Processing Flow

1. Stripe sends `charge.succeeded` webhook
2. Backend verifies webhook signature
3. System checks for tracking metadata
4. Commission is calculated based on configured rate
5. Payment is logged and synced to Affilync API

### Commission Calculation

```
Commission = Net Amount × Commission Rate

Where:
- Net Amount = Charge Amount - Stripe Fees
- Commission Rate = Configured percentage (default 10%)
```

## API Endpoints

### OAuth
- `GET /oauth/connect` - Start OAuth flow
- `GET /oauth/callback` - OAuth callback handler
- `GET /oauth/deauthorize` - Disconnect account

### Dashboard API
- `GET /api/account/{id}` - Get account details
- `PATCH /api/account/{id}/settings` - Update settings
- `GET /api/account/{id}/payments` - List payments
- `GET /api/account/{id}/analytics` - Get analytics
- `GET /api/account/{id}/analytics/revenue` - Revenue by day
- `GET /api/account/{id}/analytics/top-affiliates` - Top performers
- `GET /api/account/{id}/webhooks` - Webhook logs

### Webhooks
- `POST /webhooks/stripe` - Stripe webhook endpoint

## Database Schema

### stripe_connected_accounts
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| stripe_account_id | String | Stripe account ID (acct_xxx) |
| brand_id | UUID | Affilync brand ID |
| business_name | String | Business display name |
| email | String | Account email |
| charges_enabled | Boolean | Can accept charges |
| payouts_enabled | Boolean | Can receive payouts |
| tracking_enabled | Boolean | Conversion tracking active |
| commission_rate | Float | Default commission rate |
| access_token_encrypted | String | Encrypted OAuth token |

### stripe_tracked_payments
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| account_id | UUID | FK to connected account |
| stripe_charge_id | String | Stripe charge ID |
| amount | Integer | Amount in cents |
| commission_amount | Integer | Calculated commission |
| tracking_code | String | Attribution code |
| affiliate_id | UUID | Attributed affiliate |
| commission_status | String | pending/synced/failed |

### stripe_webhook_logs
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| stripe_event_id | String | Stripe event ID |
| event_type | String | Event type |
| payload | JSONB | Full event payload |
| status | String | processed/failed |

## Deployment

### Render.com

The `render.yaml` file configures automatic deployment:

```bash
# Deploy to Render
git push origin main  # Auto-deploys on push
```

### Manual Deployment

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
# Serve the dist/ folder
```

## Security

- All tokens encrypted with Fernet (AES-128)
- Webhook signatures verified using Stripe SDK
- JWT authentication for dashboard access
- Rate limiting on all endpoints
- CORS configured for frontend origin only

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: [docs.affilync.com](https://docs.affilync.com)
- Support: support@affilync.com
- Issues: GitHub Issues
