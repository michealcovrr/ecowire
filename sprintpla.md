# 3-DAY SPRINT PLAN

**Team roles:**
- **Mike** — ML Engineer
- **Researcher** — Content, data, testing, pitch
- **Frontend Dev** — All UI screens
- **Backend Dev** — APIs, database, Squad integration

---

## PRE-SPRINT (Before Day 1 starts — do this tonight)

**Everyone:**
- Set up GitHub repo with monorepo structure (frontend + backend + ml as separate folders)
- Agree on tech stack (confirm: Next.js frontend, FastAPI or Node backend, PostgreSQL database, Supabase or Railway for hosting)
- Create Squad sandbox account → get test API keys
- Create Dojah sandbox account → get test API keys
- Set up shared Figma file (frontend dev leads)
- Set up shared Notion or doc for tracking what's done

**Backend Dev:**
- Initialize database with PostgreSQL
- Set up basic project structure
- Configure environment variables

**Mike:**
- Set up Python ML environment
- Download and explore ACLED Nigeria dataset
- Pull OSM Lagos data via Overpass API

**Frontend Dev:**
- Set up Next.js project
- Install Tailwind + shadcn/ui
- Create basic routing structure for all 15 modules

**Researcher:**
- Write the user persona stories (Chuka the electrician, Ngozi the employer, Mama Tunde the agent)
- Start building pitch deck skeleton (problem → solution → demo → economics)
- Compile all key statistics (gig economy size, CBN KYC rules, Squad API docs)

---

## DAY 1 — FOUNDATION

**Goal by end of Day 1:** A user can sign up, pass KYC, get a wallet, send and receive money, and create a work profile. The skeleton database is fully running.

---

### Backend Dev — Day 1

**Morning (Hours 1–5):**
- Set up all database tables:
  - `users_table`
  - `transactions_table`
  - `kyc_table`
  - `squad_accounts_table`
  - `agents_table`
- Build authentication system:
  - Phone number entry → OTP (use Termii or Africa's Talking for SMS)
  - JWT token generation after OTP verified
- Wire up Squad Virtual Account creation:
  - `POST /virtual-account` called on successful KYC
  - Squad account ID stored and linked to user

**Afternoon (Hours 6–10):**
- Build KYC verification endpoint:
  - Accepts BVN or NIN
  - Calls Dojah API to validate
  - Returns name, sets `kyc_tier = 1`
  - Generates unique User ID (`ECO-XXXX-XXXX`)
  - Generates QR code from User ID
- Build wallet money movement endpoints:
  - `POST /wallet/send` → calls Squad Transfer API
  - `GET /wallet/balance` → fetches from Squad
  - `GET /wallet/transactions` → fetches history
  - `POST /wallet/cashin` → agent-triggered top-up
  - `POST /wallet/cashout` → agent-triggered withdrawal
- Set up Squad webhook receiver:
  - Endpoint that receives Squad events
  - HMAC-SHA512 signature verification
  - Handles `charge_successful` event

**Evening (Hours 11–14):**
- Build intent routing endpoints:
  - `POST /user/intent` → saves intent answers, sets `active_role`
  - `GET /user/profile` → returns full user state
- Build work profile endpoints:
  - `POST /profile/skills` → saves raw description + sends to ML for tagging
  - `POST /profile/media` → handles file upload to cloud storage (Cloudinary)
  - `GET /profile/{user_id}` → returns full work profile
- Test all endpoints with Postman

---

### Frontend Dev — Day 1

**Morning (Hours 1–5):**
- Build Module 1 screens:
  - Welcome / entry choice screen
  - Phone number + OTP screen
  - BVN or NIN choice + input screen
  - Wallet created confirmation (shows User ID + QR code)
- Build Module 2 screens:
  - Wallet home (balance, send, receive, history)
  - Send money screen (ID input + amount + confirm)
  - Receive money screen (QR display)
  - Transaction history screen

**Afternoon (Hours 6–10):**
- Build Module 3 screens:
  - Intent questions flow (one question per screen, smooth transitions)
  - KYC upgrade prompt screen
- Build Module 4 screens:
  - Work profile creation (text + voice input UI)
  - Proof upload screen
  - Work profile dashboard

**Evening (Hours 11–14):**
- Connect all Day 1 screens to backend endpoints
- Test full onboarding flow end to end:
  - Sign up → OTP → KYC → Wallet created → Send money → Work profile created
- Fix any broken connections
- Polish mobile responsiveness

---

### Mike (ML) — Day 1

**Morning (Hours 1–5):**
- Set up ML service as a separate FastAPI application
- Build skill tag extraction pipeline:
  - Input: raw text or voice transcript
  - Processing: use a lightweight NLP model (spaCy or a small fine-tuned transformer)
  - Handle English, Pidgin, basic Yoruba/Igbo/Hausa keywords
  - Output: array of structured skill tags
  - Example: "I fix electrical wiring and ceiling fans" → `["electrical", "wiring", "fan-installation", "maintenance"]`
- Expose endpoint: `POST /ml/extract-skills` → returns skill tags

**Afternoon (Hours 6–10):**
- Build voice transcription endpoint:
  - Input: audio file URL
  - Processing: Whisper API (OpenAI) or local Whisper model
  - Output: transcribed text
  - Expose: `POST /ml/transcribe`
- Wire skill extraction to run after transcription automatically
- Build job description parser (same pipeline as skills but for job postings):
  - Expose: `POST /ml/parse-job`

**Evening (Hours 11–14):**
- Start building proof media analyser:
  - Input: image or video URL
  - Use a vision model (GPT-4o vision or Google Vision API)
  - Checks: is a human present? does activity match claimed skill?
  - Output: `{ human_present: bool, detected_activities: [], confidence: float }`
  - Expose: `POST /ml/analyse-media`
- Test all three ML endpoints with sample data

---

### Researcher — Day 1

**Morning (Hours 1–5):**
- Complete pitch deck slides 1–3:
  - Slide 1: The problem (with real Nigerian statistics)
  - Slide 2: Who is affected (user personas with real names and stories)
  - Slide 3: The solution overview (one diagram of all 15 modules)
- Write the official product description (2 paragraphs for submission form)

**Afternoon (Hours 6–10):**
- Create all test user accounts and seed data:
  - 10 fake workers with different skills and locations
  - 5 fake employers
  - 2 fake agents
  - 30 fake transactions between them
  - 20 fake job records (completed, active, disputed)
  - This data will be used to make the demo look real
- Document all CBN KYC tier rules for pitch Q&A preparation

**Evening (Hours 11–14):**
- Write Q&A preparation document (20 hardest questions judges might ask + answers)
- Test the onboarding flow from a real user's perspective and report any UX issues to frontend dev
- Start writing the economic model (revenue streams, unit economics, 12-month projection)

---

## DAY 2 — CORE FEATURES

**Goal by end of Day 2:** Job posting, matching, chat, escrow, and community circles are all working. The social graph and recommendation system are live. Financial identity tracking is running in the background.

---

### Backend Dev — Day 2

**Morning (Hours 1–5):**
- Build community circles system:
  - `POST /community/create-group` → groups users by geo-location
  - `GET /community/nearby` → returns users within radius
  - `GET /community/connections` → returns 1st/2nd degree connections
  - `POST /community/connect` → creates connection between two users
  - Store in `community_groups_table` and `user_connections_table`
- Build social graph endpoints:
  - Graph traversal logic to compute connection degree at query time
  - `GET /graph/degree/{user_a}/{user_b}` → returns 1, 2, 3, or null

**Afternoon (Hours 6–10):**
- Build recommendation system endpoints:
  - `POST /recommendations/give` → stores a recommendation, creates graph link
  - `GET /recommendations/{user_id}` → returns all recommendations with degree computed for the viewer
  - `POST /recommendations/ask` → opens a verification chat between employer and recommender
- Build job system endpoints:
  - `POST /jobs/post` → creates job, sends description to ML for tag extraction
  - `GET /jobs/feed` → returns jobs relevant to worker (filtered by skill + location)
  - `GET /jobs/matches/{job_id}` → returns ranked worker list for employer
  - `POST /jobs/apply` → worker applies to job
  - `POST /jobs/select` → employer selects worker, creates chat channel

**Evening (Hours 11–14):**
- Build chat system:
  - Use Socket.io or Supabase Realtime for live messaging
  - `POST /chat/message` → sends message, stored in `chat_messages_table`
  - `GET /chat/{chat_id}` → returns full message history
  - `POST /chat/confirm-agreement` → locks agreement, triggers escrow prompt
- Build escrow system:
  - `POST /escrow/create` → calls Squad DVA API, creates job-specific escrow account
  - Webhook handler for `charge_successful` → updates job to `funded`
  - `POST /escrow/release` → employer confirms job done → calls Squad Transfer API
  - `POST /escrow/dispute` → freezes funds, creates dispute record
  - `POST /escrow/auto-release` → cron job that runs every hour, auto-releases after 48h timeout

---

### Frontend Dev — Day 2

**Morning (Hours 1–5):**
- Build Module 5 screens:
  - Community circle home (map view + list view)
  - Nearby users view
  - Community member profile view
  - Connect button flow
- Build Module 6 screens:
  - Recommendation section on work profile
  - 1st/2nd/3rd degree display
  - "Ask about this worker" button → opens chat with recommender
  - Write recommendation screen

**Afternoon (Hours 6–10):**
- Build Module 7 screens:
  - Post job screen (plain language input)
  - Job feed screen (cards with title, location, budget, distance)
  - Job details screen
  - Applicants/matches screen (employer view — ranked list)
- Build Module 8 screens:
  - Chat page (messages, voice messages, file sharing)
  - Agreement confirmation button and summary panel
  - "Payment locked" confirmation screen

**Evening (Hours 11–14):**
- Build Module 9 screens:
  - Payment lock screen (escrow deposit)
  - "Job Funded" confirmation screen
  - Job completion screen
  - Employer confirmation screen
  - Payment released confirmation
  - Dispute trigger screen
- Connect all Day 2 screens to backend
- Test full job flow end to end:
  - Post job → match → chat → agree → escrow → complete → release
- Fix any broken connections

---

### Mike (ML) — Day 2

**Morning (Hours 1–5):**
- Build the job matching engine:
  - Input: job tags + job location + viewer's user ID
  - Processing: score each candidate worker by:
    - Skill tag overlap (Jaccard similarity between job tags and worker tags)
    - Geographic distance (haversine formula)
    - Community circle membership (same circle = +20 points)
    - Recommendation degree (1st = +30, 2nd = +15, 3rd = +5)
    - Job completion rate
    - Dispute rate (negative weight)
  - Output: ranked list with match explanation
  - Expose: `POST /ml/match-workers`

**Afternoon (Hours 6–10):**
- Build chat agreement extractor:
  - Input: full chat message history (array of messages)
  - Processing: LLM call with structured prompt to extract:
    - Agreed price
    - Job scope summary
    - Timeline
    - Any special conditions
  - Output: structured JSON agreement summary
  - Expose: `POST /ml/extract-agreement`
- Build dispute analyser:
  - Input: chat history + job record + both users' behavioral histories
  - Processing: LLM summarises the case, flags contradictions, identifies patterns
  - Output: `{ summary: str, recommendation: worker_wins|employer_wins|escalate, confidence: float, reasons: [] }`
  - Expose: `POST /ml/analyse-dispute`

**Evening (Hours 11–14):**
- Build behavioral financial identity scorer:
  - Input: all user activity data (transactions, jobs, disputes, engagement)
  - Processing: weighted composite score calculation
  - Sub-scores: transaction_score, job_completion_score, dispute_score, community_trust_score, engagement_score
  - Output: composite score + eligible products array + improvement suggestions
  - Expose: `POST /ml/financial-score`
- Start building AI assistant:
  - Set up Claude API or GPT-4o as backbone
  - Write the system prompt (platform expert, multilingual, simple language)
  - Expose: `POST /ml/assistant`

---

### Researcher — Day 2

**Morning (Hours 1–5):**
- Complete pitch deck slides 4–7:
  - Slide 4: How it works (the full user journey — Chuka scenario)
  - Slide 5: The technology (Squad API integration diagram, AI layer, social graph)
  - Slide 6: Market size and opportunity
  - Slide 7: Revenue model and unit economics
- Finalize economic model:
  - Transaction fee: 1% on all wallet transfers
  - Escrow fee: 1.5% on job payments
  - Agent commission: 0.5% on cash transactions
  - Loan interest margin: 4–6%/month
  - Insurance take-rate: 15% of premium
  - 12-month projection with conservative assumptions

**Afternoon (Hours 6–10):**
- User test the community circle and job flow with seed data
- Report UX issues to frontend dev
- Write the impact statement:
  - How many users could this reach in year 1?
  - How much informal economic activity could this make visible?
  - How many first-time credit recipients?
- Research: find 3–5 real statistics on Nigeria informal economy credit gap for slide 6

**Evening (Hours 11–14):**
- Start scripting the demo walkthrough (exact screen-by-screen narrative for judges)
- Complete Q&A document (add any new questions from today's build)
- Pre-record a 2-minute backup demo video using seed data and screen recording

---

## DAY 3 — FINANCIAL LAYER, AI, POLISH & DEMO

**Goal by end of Day 3:** Full system working end to end. Financial identity, loans, savings visible. AI assistant live. Demo rehearsed 10 times. Pitch deck locked.

---

### Backend Dev — Day 3

**Morning (Hours 1–5):**
- Build financial tracking endpoints:
  - `POST /finance/log` → saves income/expense entry, sends to ML for categorisation
  - `GET /finance/summary/{user_id}` → returns monthly summary
  - `POST /finance/debt` → creates debt record
  - `GET /finance/debts/{user_id}` → returns outstanding debts
- Build dispute resolution endpoints:
  - `POST /disputes/open` → creates dispute, freezes escrow
  - `POST /disputes/evidence` → submits additional evidence
  - `GET /disputes/{dispute_id}` → returns full dispute record with AI summary
  - `POST /disputes/resolve` → admin/automated resolution, releases funds

**Afternoon (Hours 6–10):**
- Build financial identity endpoints:
  - `GET /identity/score/{user_id}` → runs ML scorer, returns composite score + eligible products
  - `GET /identity/products/{user_id}` → returns available financial products
- Build loans and savings endpoints:
  - `POST /loans/apply` → creates loan record, disburses via Squad Transfer API
  - `GET /loans/{user_id}` → returns active loans and repayment status
  - `POST /loans/repay` → manual repayment trigger
  - `POST /savings/create` → creates savings plan + Squad savings virtual account
  - `GET /savings/{user_id}` → returns savings progress
- Build agent portal endpoints:
  - `GET /agent/users` → returns all users this agent has onboarded
  - `GET /agent/commissions` → returns commission history

**Evening (Hours 11–14):**
- Full system integration test:
  - Run the complete Chuka scenario end to end with real API calls
  - Run the complete Ngozi scenario end to end
  - Run a dispute scenario end to end
- Fix any failing endpoints
- Set up production deploy on Railway or Render
- Make sure public URL is live and stable
- Set up error logging (Sentry or simple console logging)

---

### Frontend Dev — Day 3

**Morning (Hours 1–5):**
- Build Module 11 screens:
  - Financial tracking home
  - Log entry screen (voice + text)
  - Categorised view
  - Debt tracker
- Build Module 12 screens:
  - Financial identity dashboard (progress bar, what's unlocked, what's missing)
  - Improvement suggestions screen
- Build Module 13 screens:
  - Financial products home (loans, savings, insurance — locked/unlocked states)
  - Loan application screen
  - Active loan dashboard
  - Savings plan screen
  - BVN guidance flow

**Afternoon (Hours 6–10):**
- Build Module 14 screens:
  - AI assistant button (always visible, bottom corner)
  - Assistant overlay (voice + text)
  - Daily learning card
- Build Module 15 screens (agent portal):
  - Agent login
  - New user onboarding
  - Cash-in / cash-out
  - Commission dashboard
- Connect all remaining screens to backend

**Evening (Hours 11–14):**
- Full UI polish pass:
  - Consistent colours, typography, spacing across all screens
  - Loading states on every async action
  - Error states on every form
  - Empty states on every list
  - Success animations on key moments (wallet created, job funded, payment released)
- Mobile responsiveness check (open on real Android phone)
- Demo flow test — walk through the exact demo script with researcher and fix any broken paths
- Pre-record backup demo video on polished build

---

### Mike (ML) — Day 3

**Morning (Hours 1–5):**
- Complete AI assistant:
  - Full system prompt written (platform context, user types, all features, multilingual instructions)
  - Voice command routing (user says "show my balance" → system calls correct endpoint)
  - Language detection (auto-detect Pidgin, Yoruba, Igbo, Hausa)
  - TTS response (ElevenLabs or Google TTS)
  - Expose: `POST /ml/assistant/voice` (audio in, audio out)
- Build daily learning prompt generator:
  - Input: user's last 24 hours of activity
  - LLM generates one contextual tip
  - Expose: `GET /ml/learning-prompt/{user_id}`

**Afternoon (Hours 6–10):**
- Integration testing of all ML endpoints with real backend:
  - Skill extraction on 20 sample descriptions
  - Job matching on 5 sample jobs against 10 workers
  - Agreement extraction on 5 sample chat histories
  - Dispute analysis on 3 sample disputes
  - Financial scoring on 10 sample user profiles
- Fix any accuracy issues or crashes
- Make sure all ML endpoints have <2 second response time for demo

**Evening (Hours 11–14):**
- Prepare the ML demo visuals:
  - Screenshot of skill tags extracted from voice input
  - Screenshot of matching engine output with explanations
  - Screenshot of financial score with improvement suggestions
  - Screenshot of dispute analysis summary
- These become slides or live demo moments during pitch
- Help researcher with technical questions in pitch deck
- Rehearse explaining the ML system in 60 seconds to a non-technical judge

---

### Researcher — Day 3

**Morning (Hours 1–5):**
- Finalize pitch deck:
  - Slide 8: Team (names, roles, what each person built)
  - Slide 9: What we built (live demo preview screenshot)
  - Slide 10: Impact projection + ask (HackAcademy integration pitch)
- Lock all statistics — make sure every number has a source
- Prepare the submission documents (whatever the hackathon requires)

**Afternoon (Hours 6–10):**
- Run the full pitch rehearsal as a team — everyone present
- Time it (must be under 5 minutes)
- Identify the 3 weakest moments and fix them
- Prepare the live demo script:
  - Exact sequence of screens to show
  - Who is driving the laptop/phone
  - What to say at each screen
  - What to do if something breaks (fallback to pre-recorded video)
- Do a second full rehearsal

**Evening (Hours 11–14):**
- Final rehearsal with judges playing devil's advocate
- Lock the backup demo video
- Prepare a one-page product summary (leave-behind for judges)
- Make sure the public URL is shared with the whole team
- Rest

---

## DEMO DAY — WHAT YOU SHOW

**The exact 5-minute sequence:**

**0:00–0:30 — The hook**
Open with one sentence: *"93% of Nigerian workers are informal. None of them have a financial identity. We built the system that creates one from how they already live."*

**0:30–1:00 — The problem**
Two sentences about the informal economy credit gap + the trust problem in hiring.

**1:00–3:30 — Live demo**
Walk through Chuka's journey live on screen:
- Chuka signs up → KYC → wallet created → unique ID shown
- Creates work profile → describes skills → AI extracts tags live
- Employer posts job → system matches Chuka → they chat → agree
- Employer locks escrow → Chuka marked funded → job done → released
- Financial identity score updates live → loan eligibility progresses

**3:30–4:00 — Technology**
One slide: Squad APIs used (DVA, Transfer, Webhooks, Virtual Accounts) + AI layer + social graph. Say the real names.

**4:00–4:30 — Economics**
One slide: revenue model + TAM + 12-month projection.

**4:30–5:00 — The close**
*"This isn't just a hackathon project. Every transaction on this platform runs through Squad. Every informal worker who qualifies for a loan becomes a GTCO customer. We are your pipeline into Nigeria's invisible economy."*

---

That is the complete 3-day sprint mapped by role. Do you want me to now generate the actual database schema SQL, or start with the Squad API integration code?