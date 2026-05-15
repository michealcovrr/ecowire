# CLAUDE.md — Project Context for Claude Code

Read this file completely before writing any code. This is the full context for the project.

---

## WHAT WE ARE BUILDING

**Product name:** TBD (working name: EcoNet)

**One-line description:**
A community-anchored financial ecosystem that takes informal economic life — cash movement, local hiring, community trust, small business activity — and turns it into a structured, financially usable identity. Built for the Squad Hackathon 3.0, Challenge 02: "Intelligent Economic System."

**Core insight:**
Informal economies already work. People already trust each other, exchange cash, and hire through word of mouth. This system does not replace that behaviour — it plugs into it, records it, and makes it legible to formal financial systems without forcing users to change how they live.

**Hackathon:** GTCO HabariPay "Take on Squad" Hackathon 3.0
**Theme:** Smart Systems: The Intelligent Economy
**Judging weights:** Squad API Integration 25% · Technical Architecture 20% · Problem Understanding 20% · Economic Viability 20% · Presentation 15% · Impact Bonus 10%

---

## TEAM

- **Mike** — ML Engineer (Python, FastAPI, ML models, AI integrations)
- **Researcher** — Content, pitch, testing
- **Frontend Dev** — Next.js, Tailwind, UI screens
- **Backend Dev** — Node.js or FastAPI, PostgreSQL, Squad API integration

---

## TECH STACK

**Frontend:**
- Next.js 14 (App Router)
- Tailwind CSS + shadcn/ui
- Deployed on Vercel
- PWA-enabled (mobile-first)
- Socket.io client for real-time chat

**Backend:**
- Node.js with Express OR Python FastAPI (confirm with backend dev)
- PostgreSQL (hosted on Supabase or Railway)
- Redis for queues and caching
- Socket.io server for real-time chat
- Deployed on Railway or Render

**ML Service:**
- Python FastAPI (separate service from main backend)
- spaCy + transformer models for NLP
- OpenAI Whisper for voice transcription
- GPT-4o or Claude API for assistant + agreement extraction + dispute analysis
- ElevenLabs or Google TTS for voice responses
- Deployed separately on Railway

**External APIs:**
- **Squad** (squadco.com) — all financial infrastructure
  - Sandbox base URL: `https://sandbox-api-d.squadco.com`
  - Docs: `https://docs.squadco.com`
- **Dojah** (dojah.io) — KYC: BVN/NIN validation, liveness
  - Sandbox available at `https://api-docs.dojah.io`
- **Mono** (mono.co) — alternative KYC if needed
- **Termii or Africa's Talking** — OTP SMS delivery
- **Cloudinary** — media storage (profile videos/images)
- **OpenAI** — Whisper (transcription) + GPT-4o (assistant/extraction)

---

## ARCHITECTURE OVERVIEW

```
[User/Agent] → [Next.js Frontend]
                      ↓
              [Main Backend API]
              /        |        \
    [Squad APIs]  [PostgreSQL]  [ML Service]
                      |
              [Dojah/Mono KYC]
```

The ML service is a **separate FastAPI app** that the main backend calls. It never talks to Squad directly. Squad integration lives exclusively in the main backend.

---

## THE 15 MODULES

### MODULE 1: ENTRY & AUTHENTICATION
**Purpose:** Sign up, KYC, wallet creation.

**KYC Tiers (CBN-compliant):**
- Tier 1: Phone + OTP + BVN OR NIN → wallet active, ₦50k/day limit
- Tier 2: BVN + one government ID → escrow and hiring unlocked
- Tier 3: Liveness check → loans and insurance unlocked

**Key flows:**
- Phone → OTP (via Termii/Africa's Talking)
- BVN or NIN → validated via Dojah API
- On success: generate unique User ID (format: `ECO-XXXX-XXXX`)
- Call Squad `POST /virtual-account` to create wallet
- Generate QR code from User ID
- Agent-assisted version: agent logs in to separate portal, onboards user on their behalf

**Database tables:** `users`, `kyc_records`, `squad_accounts`

---

### MODULE 2: WALLET & MONEY MOVEMENT
**Purpose:** Send, receive, cash-in, cash-out.

**Squad APIs used:**
- `POST /payout/transfer` — send money
- `POST /payout/account/lookup` — verify recipient before transfer
- `GET /virtual-account/customer/transactions/{id}` — transaction history
- Webhook `charge_successful` — confirms inbound payments

**Key flows:**
- Send: validate recipient ID → Squad transfer → log transaction
- Receive: display QR + User ID
- Cash-in: agent logs → backend credits Squad wallet
- Cash-out: user requests → agent confirms → wallet debited

**Database tables:** `transactions`

---

### MODULE 3: INTENT & VERIFICATION ROUTING
**Purpose:** Route user to correct features. Upgrade KYC only when needed.

**Intent question flow (one at a time):**
1. What are you here to do? → Work / Hire / Business / Financial / Just send money
2. Do you make money from any activity? → Yes / No
3. If yes, what kind? → Trade / Service / Transport / Other
4. Do you want to hire? → Yes / No
5. Do you need financial support? → Yes / No

**Routing output:** sets `active_role` field (not permanent)
**ML role:** parses voice/free-text answers into structured intent

**Database tables:** `user_intents`

---

### MODULE 4: WORK PROFILE & SKILL SYSTEM
**Purpose:** Workers describe skills in own words. No CVs. No formal qualifications.

**Key flows:**
- Voice or text skill description → transcribe (Whisper) → extract skill tags (ML)
- Optional proof media upload → stored on Cloudinary → ML analyses content
- Profile dashboard shows: skills, job history, recommendations, proof media

**ML calls:**
- `POST /ml/transcribe` — audio → text
- `POST /ml/extract-skills` — text → skill tags array
- `POST /ml/analyse-media` — image/video → human present? activity matches?

**Database tables:** `work_profiles`, `skill_tags`, `proof_media`

---

### MODULE 5: COMMUNITY CIRCLES
**Purpose:** Group users into geographic + social local networks.

**Key flows:**
- On registration: snap user location to LGA cluster
- Optional: import contacts → check which are on platform → build overlap connections
- Display: nearby users (within 5km radius), friends-of-friends

**Database tables:** `community_groups`, `community_memberships`, `user_connections`

---

### MODULE 6: RECOMMENDATION GRAPH
**Purpose:** Social proof. NOT ratings. NOT reviews. Interactive trust through real connections.

**Key flows:**
- After job completion: prompt "Do you recommend this worker?" → short text/voice
- Recommendation stored → link created in social graph
- Display: 1st/2nd/3rd degree (computed at query time from graph traversal, NOT stored)
- "Ask about this worker" → opens direct chat with the recommender

**Important:** Degree is NEVER stored. It is computed at query time based on the viewer's position in the graph.

**Database tables:** `recommendations`, `social_graph`

---

### MODULE 7: JOB POSTING & MATCHING
**Purpose:** Employers post in plain language. System matches workers by skill + location + community + trust.

**Matching factors:**
1. Skill tag overlap (Jaccard similarity)
2. Geographic proximity (haversine distance)
3. Same community circle (+20 points)
4. Recommendation degree (1st=+30, 2nd=+15, 3rd=+5)
5. Job completion rate (positive weight)
6. Dispute rate (negative weight)

**ML calls:**
- `POST /ml/parse-job` — job description → required skill tags
- `POST /ml/match-workers` — returns ranked worker list with explanations

**Database tables:** `jobs`, `job_applications`

---

### MODULE 8: JOB CHAT & AGREEMENT SYSTEM
**Purpose:** All negotiation happens inside structured chat. Chat = official agreement record.

**Key flows:**
- Employer selects worker → chat channel created
- Real-time messaging via Socket.io
- "Confirm Agreement" button → ML extracts price, scope, timeline from chat history
- Both parties confirm → job state = `agreement_locked`
- Chat is immutable after lock

**ML calls:**
- `POST /ml/extract-agreement` — chat history → structured JSON {price, scope, timeline}

**Database tables:** `job_chats`, `chat_messages`, `job_agreements`

---

### MODULE 9: ESCROW & PAYMENT RELEASE
**Purpose:** Payment secured before work begins. Released after completion.

**Squad APIs used:**
- `POST /virtual-account/create-dynamic-virtual-account` — job-specific escrow account
- Webhook `charge_successful` → job status = `funded`
- `POST /payout/transfer` — release to worker
- `POST /payout/account/lookup` — verify worker account before release
- `POST /payout/requery` — check payout status
- HMAC-SHA512 signature verification on ALL webhooks (use `x-squad-encrypted-body` header)

**Key flows:**
- Agreement locked → employer prompted to fund escrow DVA
- Worker sees "Job Funded" → starts work
- Worker marks complete → employer has 48h to confirm or dispute
- If confirmed → Transfer API releases funds
- If no response in 48h → auto-release (cron job)
- If dispute → funds frozen → Module 10 triggered

**Database tables:** `escrow_records`

---

### MODULE 10: DISPUTE RESOLUTION
**Purpose:** Fair resolution using recorded evidence.

**Key flows:**
- Either party opens dispute → escrow frozen immediately
- 48h window for both parties to add evidence
- ML analyses: chat history + agreement + behavioral histories → resolution recommendation
- Clear-cut cases → automated resolution
- Complex cases → flagged for human review

**ML calls:**
- `POST /ml/analyse-dispute` — returns {summary, recommendation, confidence, reasons}

**Database tables:** `disputes`, `dispute_evidence`

---

### MODULE 11: FINANCIAL TRACKING
**Purpose:** Record income, expenses, and informal debts in plain language.

**Key flows:**
- Voice or text input: "I sold 10 bags of rice for ₦45,000"
- ML extracts: type=income, amount=45000, category=trade, item=rice
- All Squad transactions auto-imported and tagged
- Debt tracker: log informal IOUs, send reminders if debtor is on platform

**ML calls:**
- `POST /ml/categorise-entry` — raw text → structured financial log entry

**Database tables:** `financial_logs`, `debt_records`

---

### MODULE 12: BEHAVIORAL FINANCIAL IDENTITY
**Purpose:** All activity builds a financial identity. Gradual unlock of financial products.

**Score components:**
- Transaction volume and consistency
- Job completion rate
- Dispute rate (negative)
- Repayment behaviour
- Community trust signals (recommendation count)
- Platform engagement consistency
- Financial log regularity

**Score display:** NOT shown as a number to user. Shown as a progress bar toward next product unlock.

**Product unlock thresholds:**
- Micro-savings: 30 days consistent activity
- Micro-insurance: 3+ months, no major disputes
- Micro-loan: 6+ months, consistent income, Tier 2 KYC
- Working capital: business verified, Tier 3 KYC, proven revenue

**ML calls:**
- `POST /ml/financial-score` — returns {composite_score, eligible_products, improvement_suggestions}

**Database tables:** `financial_identities`

---

### MODULE 13: LOANS, SAVINGS & INSURANCE
**Purpose:** The financial products the identity system unlocks.

**Key flows:**
- Loan: user reaches threshold → sees max eligible amount → applies → Squad Transfer API disburses → auto-repayment from escrow releases
- Savings: set daily/weekly amount → Squad savings virtual account → auto-debit on schedule
- Insurance: micro-insurance products displayed when eligible → premium auto-debited
- BVN guidance: step-by-step content flow for users without BVN (no API — pure content)

**Database tables:** `loans`, `savings_plans`, `insurance_policies`

---

### MODULE 14: AI ASSISTANT & LEARNING LAYER
**Purpose:** Embedded intelligence guiding every user at every step.

**Capabilities:**
- Answers questions about any platform feature
- Guides users step by step through any flow
- Reads all screen content aloud (for low-literacy users)
- Accepts voice input in English, Pidgin, Yoruba, Igbo, Hausa
- Responds in the same language the user used
- Executes voice navigation commands: "show my balance", "help me post a job"

**Daily learning prompts:**
- Looks at user's last 24h of activity
- Generates ONE contextual tip tied to what they actually did
- NOT generic financial education

**ML calls:**
- `POST /ml/assistant` — text in, text out (LLM backbone)
- `POST /ml/assistant/voice` — audio in, audio out
- `GET /ml/learning-prompt/{user_id}` — generates daily contextual tip

**Database tables:** `ai_interactions`, `learning_prompts`

---

### MODULE 15: AGENT PORTAL
**Purpose:** Physical access point for users who can't use smartphones.

**Key flows:**
- Agent logs into separate portal (elevated permissions)
- Onboards users by entering their phone + BVN/NIN
- Facilitates cash-in and cash-out
- Earns commission on every transaction (stored and withdrawable)
- Can post jobs and confirm completions on behalf of non-smartphone users

**Database tables:** `agents`, `agent_transactions`

---

## COMPLETE DATABASE SCHEMA

```sql
-- USERS & AUTH
CREATE TABLE users (
  user_id VARCHAR(20) PRIMARY KEY, -- format: ECO-XXXX-XXXX
  phone_number VARCHAR(15) UNIQUE NOT NULL,
  full_name VARCHAR(100),
  kyc_type VARCHAR(10), -- 'BVN' or 'NIN'
  kyc_value VARCHAR(50), -- encrypted
  kyc_tier INTEGER DEFAULT 1, -- 1, 2, or 3
  kyc_status VARCHAR(20) DEFAULT 'tier_1',
  active_role VARCHAR(20), -- worker, employer, business, financial, basic
  onboarding_channel VARCHAR(10) DEFAULT 'self', -- self or agent
  agent_id VARCHAR(20), -- if agent-onboarded
  location_lat DECIMAL(10, 8),
  location_lng DECIMAL(11, 8),
  location_lga VARCHAR(100),
  preferred_language VARCHAR(20) DEFAULT 'english',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kyc_records (
  kyc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  kyc_type VARCHAR(10),
  kyc_value_encrypted TEXT,
  dojah_reference VARCHAR(100),
  verified BOOLEAN DEFAULT FALSE,
  tier INTEGER,
  verified_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE squad_accounts (
  account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  squad_virtual_account_id VARCHAR(100),
  squad_account_number VARCHAR(20),
  squad_bank_name VARCHAR(100),
  squad_customer_identifier VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

-- TRANSACTIONS
CREATE TABLE transactions (
  transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_user_id VARCHAR(20) REFERENCES users(user_id),
  receiver_user_id VARCHAR(20) REFERENCES users(user_id),
  amount BIGINT NOT NULL, -- in kobo
  type VARCHAR(20), -- send, receive, cash_in, cash_out, escrow, release, loan, repayment
  channel VARCHAR(10) DEFAULT 'self', -- self or agent
  squad_reference VARCHAR(100),
  status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed
  tagged_as VARCHAR(20), -- personal, business, job_payment
  job_id UUID,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- USER INTENT
CREATE TABLE user_intents (
  intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  intent_response JSONB, -- full answers JSON
  active_role VARCHAR(20),
  kyc_tier_required INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- WORK PROFILES
CREATE TABLE work_profiles (
  profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  skill_description_raw TEXT,
  skill_tags TEXT[], -- AI extracted
  profile_visibility_score DECIMAL(5,2) DEFAULT 0,
  job_completion_count INTEGER DEFAULT 0,
  dispute_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE proof_media (
  media_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  media_url TEXT,
  media_type VARCHAR(10), -- image or video
  human_present BOOLEAN,
  detected_activity_tags TEXT[],
  confidence_score DECIMAL(5,2),
  uploaded_at TIMESTAMP DEFAULT NOW()
);

-- COMMUNITY
CREATE TABLE community_groups (
  group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_name VARCHAR(100),
  lga VARCHAR(100),
  geo_lat DECIMAL(10, 8),
  geo_lng DECIMAL(11, 8),
  radius_km INTEGER DEFAULT 5,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE community_memberships (
  membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  group_id UUID REFERENCES community_groups(group_id),
  joined_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_connections (
  connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_a_id VARCHAR(20) REFERENCES users(user_id),
  user_b_id VARCHAR(20) REFERENCES users(user_id),
  connection_type VARCHAR(30), -- contact, recommendation, job_history
  created_at TIMESTAMP DEFAULT NOW()
);

-- RECOMMENDATIONS
CREATE TABLE recommendations (
  recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recommender_user_id VARCHAR(20) REFERENCES users(user_id),
  worker_user_id VARCHAR(20) REFERENCES users(user_id),
  recommendation_text TEXT,
  job_id UUID,
  created_at TIMESTAMP DEFAULT NOW()
);

-- JOBS
CREATE TABLE jobs (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  employer_user_id VARCHAR(20) REFERENCES users(user_id),
  worker_user_id VARCHAR(20), -- set after match accepted
  job_description_raw TEXT,
  job_tags TEXT[], -- AI extracted
  location_lat DECIMAL(10, 8),
  location_lng DECIMAL(11, 8),
  location_address TEXT,
  budget BIGINT, -- in kobo
  status VARCHAR(20) DEFAULT 'open',
  -- open, matched, agreement_locked, funded, active, completed, disputed, cancelled
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE job_applications (
  application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(job_id),
  worker_user_id VARCHAR(20) REFERENCES users(user_id),
  status VARCHAR(20) DEFAULT 'applied', -- applied, shortlisted, accepted, rejected
  applied_at TIMESTAMP DEFAULT NOW()
);

-- CHAT
CREATE TABLE job_chats (
  chat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(job_id),
  employer_user_id VARCHAR(20) REFERENCES users(user_id),
  worker_user_id VARCHAR(20) REFERENCES users(user_id),
  chat_type VARCHAR(20) DEFAULT 'job_chat', -- job_chat or verification_request
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_messages (
  message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id UUID REFERENCES job_chats(chat_id),
  sender_user_id VARCHAR(20) REFERENCES users(user_id),
  message_type VARCHAR(10), -- text, voice, image, file, system
  content TEXT, -- text content or media URL
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE job_agreements (
  agreement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(job_id),
  agreed_price BIGINT, -- in kobo
  job_scope_summary TEXT,
  timeline TEXT,
  conditions TEXT,
  confirmed_by_employer BOOLEAN DEFAULT FALSE,
  confirmed_by_worker BOOLEAN DEFAULT FALSE,
  locked_at TIMESTAMP
);

-- ESCROW
CREATE TABLE escrow_records (
  escrow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(job_id),
  squad_dva_account_number VARCHAR(20),
  squad_dva_reference VARCHAR(100),
  amount BIGINT, -- in kobo
  status VARCHAR(20) DEFAULT 'pending',
  -- pending, funded, released, frozen, refunded
  funded_at TIMESTAMP,
  released_at TIMESTAMP,
  auto_release_at TIMESTAMP, -- funded_at + 48h
  created_at TIMESTAMP DEFAULT NOW()
);

-- DISPUTES
CREATE TABLE disputes (
  dispute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(job_id),
  escrow_id UUID REFERENCES escrow_records(escrow_id),
  opened_by_user_id VARCHAR(20) REFERENCES users(user_id),
  reason_text TEXT,
  ai_summary TEXT,
  ai_recommendation VARCHAR(20), -- worker_wins, employer_wins, escalate
  ai_confidence DECIMAL(5,2),
  status VARCHAR(20) DEFAULT 'open', -- open, under_review, resolved
  resolution VARCHAR(20), -- worker_wins, employer_wins, split, escalated
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE dispute_evidence (
  evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dispute_id UUID REFERENCES disputes(dispute_id),
  submitted_by_user_id VARCHAR(20) REFERENCES users(user_id),
  content_type VARCHAR(10), -- text, image, video
  content TEXT,
  submitted_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL TRACKING
CREATE TABLE financial_logs (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  entry_type VARCHAR(20), -- income, expense, debt_owed, debt_owing
  amount BIGINT, -- in kobo
  category VARCHAR(50),
  description_raw TEXT,
  ai_extracted_tags JSONB,
  source VARCHAR(20) DEFAULT 'manual', -- manual or squad_auto
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE debt_records (
  debt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  creditor_user_id VARCHAR(20) REFERENCES users(user_id),
  debtor_name VARCHAR(100),
  debtor_user_id VARCHAR(20), -- null if not on platform
  amount BIGINT, -- in kobo
  reason TEXT,
  status VARCHAR(20) DEFAULT 'outstanding', -- outstanding, settled
  created_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL IDENTITY
CREATE TABLE financial_identities (
  identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  transaction_score DECIMAL(5,2) DEFAULT 0,
  job_completion_score DECIMAL(5,2) DEFAULT 0,
  dispute_score DECIMAL(5,2) DEFAULT 0,
  repayment_score DECIMAL(5,2) DEFAULT 0,
  community_trust_score DECIMAL(5,2) DEFAULT 0,
  engagement_score DECIMAL(5,2) DEFAULT 0,
  composite_score DECIMAL(5,2) DEFAULT 0,
  eligible_products TEXT[] DEFAULT '{}',
  last_updated TIMESTAMP DEFAULT NOW()
);

-- LOANS, SAVINGS, INSURANCE
CREATE TABLE loans (
  loan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  amount BIGINT, -- in kobo
  interest_rate DECIMAL(5,2),
  repayment_schedule JSONB,
  amount_repaid BIGINT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'active', -- active, completed, defaulted
  disbursed_at TIMESTAMP,
  due_date TIMESTAMP
);

CREATE TABLE savings_plans (
  savings_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  squad_savings_account_id VARCHAR(100),
  target_amount BIGINT,
  current_amount BIGINT DEFAULT 0,
  frequency VARCHAR(10), -- daily or weekly
  auto_debit_amount BIGINT,
  goal_description TEXT,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE insurance_policies (
  policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  product_name VARCHAR(100),
  provider VARCHAR(100),
  premium_amount BIGINT, -- in kobo per period
  frequency VARCHAR(10), -- monthly
  status VARCHAR(20) DEFAULT 'active', -- active, lapsed, claimed
  started_at TIMESTAMP DEFAULT NOW()
);

-- AI ASSISTANT
CREATE TABLE ai_interactions (
  interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  input_type VARCHAR(10), -- text or voice
  input_content TEXT,
  response_content TEXT,
  language_detected VARCHAR(20),
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE learning_prompts (
  prompt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  prompt_text TEXT,
  trigger_activity TEXT,
  shown_at TIMESTAMP,
  dismissed BOOLEAN DEFAULT FALSE
);

-- AGENTS
CREATE TABLE agents (
  agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(20) REFERENCES users(user_id),
  agent_status VARCHAR(20) DEFAULT 'active', -- active, suspended
  location_lga VARCHAR(100),
  commission_rate DECIMAL(5,4) DEFAULT 0.005, -- 0.5%
  total_earned BIGINT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent_transactions (
  agent_txn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(agent_id),
  user_id VARCHAR(20) REFERENCES users(user_id),
  transaction_type VARCHAR(20), -- cash_in, cash_out, onboarding
  amount BIGINT,
  commission_earned BIGINT,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## SQUAD API INTEGRATION REFERENCE

**Authentication:** Bearer token in header
```
Authorization: Bearer {SQUAD_SECRET_KEY}
Content-Type: application/json
```

**Sandbox base URL:** `https://sandbox-api-d.squadco.com`

**Webhook verification (MANDATORY):**
```javascript
const crypto = require('crypto');
const hash = crypto
  .createHmac('sha512', process.env.SQUAD_SECRET_KEY)
  .update(JSON.stringify(req.body))
  .digest('hex')
  .toUpperCase();
if (hash !== req.headers['x-squad-encrypted-body']) {
  return res.status(401).json({ error: 'Invalid signature' });
}
```

**Key endpoints:**

| Action | Method | Endpoint |
|---|---|---|
| Create virtual account | POST | `/virtual-account` |
| Create dynamic VA (escrow) | POST | `/virtual-account/create-dynamic-virtual-account` |
| Account name lookup | POST | `/payout/account/lookup` |
| Transfer/payout | POST | `/payout/transfer` |
| Requery transfer | POST | `/payout/requery` |
| Get transactions | GET | `/virtual-account/customer/transactions/{id}` |
| Get wallet balance | GET | `/merchant/balance` |
| Send airtime (VAS) | POST | `/vending/purchase/airtime` |

**Webhook events to handle:**
- `charge_successful` — inbound payment confirmed
- `transfer_successful` — outbound payout confirmed
- `transfer_failed` — outbound payout failed

---

## ML SERVICE ENDPOINTS

All ML endpoints are on a separate FastAPI service.

| Endpoint | Input | Output |
|---|---|---|
| `POST /ml/transcribe` | `{audio_url: string}` | `{text: string, language: string}` |
| `POST /ml/extract-skills` | `{text: string}` | `{tags: string[]}` |
| `POST /ml/analyse-media` | `{media_url: string, claimed_skills: string[]}` | `{human_present: bool, detected_activities: string[], confidence: float}` |
| `POST /ml/parse-job` | `{description: string}` | `{tags: string[], location: string, budget: number}` |
| `POST /ml/match-workers` | `{job_id: string, viewer_user_id: string}` | `{ranked_workers: [{user_id, score, reasons}]}` |
| `POST /ml/extract-agreement` | `{messages: Message[]}` | `{price: number, scope: string, timeline: string}` |
| `POST /ml/analyse-dispute` | `{dispute_id: string}` | `{summary: string, recommendation: string, confidence: float, reasons: string[]}` |
| `POST /ml/categorise-entry` | `{text: string}` | `{type: string, amount: number, category: string, tags: object}` |
| `POST /ml/financial-score` | `{user_id: string}` | `{composite_score: float, eligible_products: string[], suggestions: string[]}` |
| `POST /ml/assistant` | `{user_id: string, message: string, language: string}` | `{response: string}` |
| `POST /ml/assistant/voice` | `{user_id: string, audio_url: string}` | `{response_audio_url: string, response_text: string}` |
| `GET /ml/learning-prompt/{user_id}` | — | `{prompt: string, trigger: string}` |

---

## ENVIRONMENT VARIABLES NEEDED

```env
# Squad
SQUAD_SECRET_KEY=
SQUAD_PUBLIC_KEY=
SQUAD_BASE_URL=https://sandbox-api-d.squadco.com

# Dojah
DOJAH_APP_ID=
DOJAH_PRIVATE_KEY=
DOJAH_BASE_URL=https://api.dojah.io

# SMS (Termii)
TERMII_API_KEY=
TERMII_SENDER_ID=

# Media
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# AI
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
ELEVENLABS_API_KEY=

# Database
DATABASE_URL=

# Redis
REDIS_URL=

# App
JWT_SECRET=
ML_SERVICE_URL=http://localhost:8001
FRONTEND_URL=http://localhost:3000
```

---

## CODING CONVENTIONS

- All amounts stored in **kobo** (multiply naira by 100 before storing)
- All timestamps in UTC
- User IDs always in format `ECO-XXXX-XXXX` (uppercase)
- All API responses follow format: `{ success: bool, data: any, error: string | null }`
- Never log BVN, NIN, or KYC values — log only masked versions or reference IDs
- All Squad webhook handlers must verify HMAC signature before processing
- Use database transactions for any operation that touches both escrow and job status simultaneously
- Every Squad API call must have idempotency key where supported

---

## CURRENT BUILD STATUS

Track progress here as modules are completed:

- [ ] Module 1: Entry & Authentication
- [ ] Module 2: Wallet & Money Movement
- [ ] Module 3: Intent & Verification Routing
- [ ] Module 4: Work Profile & Skill System
- [ ] Module 5: Community Circles
- [ ] Module 6: Recommendation Graph
- [ ] Module 7: Job Posting & Matching
- [ ] Module 8: Job Chat & Agreement System
- [ ] Module 9: Escrow & Payment Release
- [ ] Module 10: Dispute Resolution
- [ ] Module 11: Financial Tracking
- [ ] Module 12: Behavioral Financial Identity
- [ ] Module 13: Loans, Savings & Insurance
- [ ] Module 14: AI Assistant & Learning Layer
- [ ] Module 15: Agent Portal

---

## WHAT THIS IS NOT

- Not a payments app (Squad handles payments — we build on top of it)
- Not a job marketplace (no global listings — community-first, local-first)
- Not a credit bureau (we build behavioral identity, we don't replace CRMS)
- Not a social network (connections exist only to establish trust for economic activity)

---

## DEMO PRIORITY ORDER

If time runs out, build in this order:

1. Onboarding + wallet (Module 1 + 2) — non-negotiable
2. Work profile + skill extraction (Module 4) — shows AI
3. Job posting + matching (Module 7) — shows intelligence
4. Chat + escrow + release (Module 8 + 9) — shows Squad integration
5. Financial identity dashboard (Module 12) — shows the big vision
6. Recommendation graph (Module 6) — shows differentiation
7. Community circles (Module 5) — shows local-first thinking
8. Everything else — build if time allows
