Let's go. Here is every module, fully detailed.

---

# THE COMPLETE MODULE BREAKDOWN

---

## MODULE 1: ENTRY & AUTHENTICATION

**Purpose:** Get the user into the system legally and quickly.

**Frontend Screens:**
- Welcome screen (Create Wallet / I have an ID / Visit Agent)
- Phone number entry + OTP screen
- KYC choice screen ("Do you have BVN or NIN?")
- BVN/NIN input screen
- Wallet created confirmation screen (shows unique ID + QR code)
- Agent portal entry (separate login for agents)

**What happens technically:**
- User enters phone number → system sends OTP → verified
- User enters BVN or NIN → Dojah/Mono API call validates it → name and basic info returned
- System creates user record in database
- Unique User ID generated (format: e.g. `ECO-7X92-LK4`)
- Squad Virtual Account created and linked to this user ID
- Wallet activated at CBN Tier 1 (₦50k/day limit)
- QR code generated from User ID for easy receive/send

**Data stored:**
- `user_id` (unique, system-generated)
- `phone_number`
- `kyc_type` (BVN or NIN)
- `kyc_value` (the number itself, encrypted)
- `kyc_status` (tier_1 / tier_2 / tier_3)
- `squad_virtual_account_id`
- `squad_account_number`
- `created_at`
- `onboarding_channel` (self / agent)

**Agent-specific flow:**
- Agent has a separate portal login
- Agent enters user's phone + BVN/NIN on their behalf
- System flags the record as `agent_onboarded: true`
- Agent's ID is linked to this user record for accountability
- Agent earns commission logged in `agent_commission_table`

**KYC upgrade triggers:**
- Tier 2 unlocked when user tries to access escrow or hiring tools → prompts BVN + one government ID
- Tier 3 unlocked when user applies for loan/insurance → prompts liveness check via Dojah

**AI role:** None at this stage. Pure identity and infrastructure.

---

## MODULE 2: WALLET & MONEY MOVEMENT

**Purpose:** Core financial utility. Every user can send and receive money immediately after entry.

**Frontend Screens:**
- Wallet home screen (balance, send, receive, cash-in/out, history)
- Send money screen (enter recipient ID or scan QR → enter amount → confirm)
- Receive money screen (show own QR code and ID)
- Cash-in screen (agent-assisted top-up)
- Cash-out screen (withdraw to bank or via agent)
- Transaction history screen (all movement, tagged by type)

**What happens technically:**

*Send money:*
- User enters recipient User ID or scans QR
- System validates recipient exists
- Calls Squad Transfer API (`POST /payout/transfer`)
- Debits sender Squad virtual account
- Credits recipient Squad virtual account
- Transaction logged in `transactions_table`

*Receive money:*
- Recipient shares their QR or User ID
- Sender initiates → same flow above in reverse

*Cash-in via agent:*
- Agent receives physical cash from user
- Agent logs cash-in on agent portal
- Backend credits user's Squad virtual account equivalent amount
- Both agent and user get confirmation

*Cash-out via agent:*
- User requests withdrawal
- Agent confirms they have cash available
- System debits user wallet
- Agent hands over physical cash
- Both sides confirmed and logged

**Data stored:**
- `transaction_id`
- `sender_user_id`
- `receiver_user_id`
- `amount`
- `type` (send / receive / cash-in / cash-out / escrow / release)
- `channel` (self / agent)
- `squad_reference`
- `status` (pending / completed / failed)
- `timestamp`
- `tagged_as` (personal / business / job-payment)

**Squad APIs used:**
- `POST /virtual-account` — create account at onboarding
- `POST /payout/transfer` — send money
- `POST /payout/account/lookup` — verify recipient bank/account name before transfer
- `GET /virtual-account/customer/transactions/{id}` — fetch transaction history
- Webhook: `charge_successful` — confirms inbound payments

**AI role:** Light. Tags transaction type automatically based on context (e.g. if transfer follows a completed job, auto-tags as `job-payment`). No user-facing AI at this stage.

---

## MODULE 3: INTENT & VERIFICATION ROUTING

**Purpose:** Route each user to the right features based on what they actually want to do. Upgrade KYC only when needed.

**Frontend Screens:**
- "Unlock more features" trigger screen (shown when user taps loan, job, hire, business)
- Intent questions screen (one question at a time)
- KYC upgrade prompt screen (Tier 2 or Tier 3 based on what they want)
- Routing confirmation screen ("You're set up as a Worker / Employer / Business / Financial User")

**Intent questions flow:**
1. "What are you here to do?" → Work / Hire / Business / Financial support / Just send money
2. "Do you currently make money from any activity?" → Yes / No
3. If yes: "What kind?" → Trade / Service / Transport / Other (voice allowed)
4. "Do you want to hire people?" → Yes / No
5. "Do you need financial support?" → Yes / No

**What happens technically:**
- Answers stored in `user_intent_table`
- System sets `active_role` field (not permanent — updates when user changes intent)
- KYC upgrade triggered if required by chosen role:
  - Worker/Employer → Tier 2 (BVN + one government ID)
  - Loan/Insurance → Tier 3 (liveness check added)
- Relevant modules unlocked based on role

**Data stored:**
- `user_id`
- `intent_response` (JSON of all answers)
- `active_role` (worker / employer / business / financial / basic)
- `kyc_tier_required`
- `intent_updated_at`

**AI role:** Parses voice/text free-form answers and converts to structured intent data. Example: user says *"I want to sell provisions and sometimes deliver goods"* → system tags `business: true`, `transport: true`. No labelling of the person — only routing of features.

---

## MODULE 4: WORK PROFILE & SKILL SYSTEM

**Purpose:** Let workers describe what they can do in their own words, build a visible trust profile without CVs or formal qualifications.

**Frontend Screens:**
- Create work profile screen (voice / text input for skills)
- Proof upload screen (image or video — optional)
- Work profile dashboard (skills, job history, recommendations, proof media, community trust)
- Edit profile screen

**What happens technically:**

*Profile creation:*
- User describes skills via text or voice
- Voice input transcribed via speech-to-text (Whisper API or Google Speech)
- AI extracts structured skill tags from free-form description
- Example: "I fix electrical wiring and install fans" → tags: `electrical`, `installation`, `wiring`, `fan-fitting`
- Tags stored for matching engine use

*Proof upload:*
- User uploads image or video
- Stored in cloud storage (AWS S3 or Cloudinary)
- URL linked to user profile
- AI analyses uploaded content (see AI role below)

**Data stored:**
- `user_id`
- `skill_description_raw` (original text/voice transcript)
- `skill_tags` (array — AI extracted)
- `proof_media` (array of URLs)
- `media_confidence_score` (AI output — is this real proof?)
- `profile_visibility_score` (composite — goes up with proof, recommendations, completions)
- `job_completion_count`
- `dispute_count`
- `profile_created_at`
- `last_updated`

**AI role (important here):**

On skill description:
- Transcribe voice to text
- Extract skill tags from natural language
- Handle local slang and pidgin (e.g. "I sabi fix motor" → `vehicle_repair`)

On proof media upload:
- Detect: is a human present in the video/image?
- Detect: does the visible activity match the claimed skill?
- Detect: is this real content (not a random downloaded clip)?
- Output: `media_verified: true/false` + `detected_activity_tags`
- No automatic rejection — only confidence signals that affect profile score

---

## MODULE 5: COMMUNITY CIRCLES

**Purpose:** Ground the platform in real geographic and social communities. Users are not in a global marketplace — they exist in local networks that mirror real life.

**Frontend Screens:**
- Community circle home screen (map + list view)
- Nearby users view (what they do, not personal details)
- Friends-of-friends view
- Connect/request reference button
- Community member profile view

**What happens technically:**

*Geographic grouping:*
- User's location captured at registration (GPS or agent location)
- Users grouped into LGA/neighbourhood clusters
- Cluster membership stored in `community_groups_table`
- Updated when user moves or changes location

*Social clustering:*
- Optional: user imports contacts (phone numbers)
- System checks which contacts are already on platform
- Builds overlap graph → connects existing users
- No contact data stored permanently — only overlap results

*Community circle display:*
- User sees nearby users (within configurable radius — default 5km)
- Sees friends-of-friends network (2nd degree connections)
- Each visible user shows: name, what they do, distance, connection degree
- No sensitive data visible without explicit connection

**Data stored:**
- `community_group_id`
- `group_name` (e.g. "Yaba/Mainland Network")
- `geo_polygon` (boundary of the cluster)
- `member_user_ids` (array)
- `user_connections_table`:
  - `user_a_id`
  - `user_b_id`
  - `connection_type` (contact / recommendation / job-history)
  - `created_at`

**AI role:**
- Detects natural trust clusters from transaction and job history patterns
- Suggests community links: "3 people in your area have worked with this user"
- No forced connections — suggestions only

---

## MODULE 6: RECOMMENDATION GRAPH

**Purpose:** Replace ratings and reviews with real social proof. Trust is visible, interactive, and socially interpreted — not algorithmically scored.

**Frontend Screens:**
- Recommendation section on work profile (1st/2nd/3rd degree display)
- "Ask about this worker" button → opens chat with recommender
- Write recommendation screen (short text or voice)
- Recommendation received notification

**What happens technically:**

*Giving a recommendation:*
- User A completes a job with Worker B
- After job completion, User A is prompted: "Would you recommend this worker?"
- If yes: writes short recommendation (text or voice)
- Stored in `recommendations_table`
- Link created between User A and Worker B in social graph

*Displaying recommendations:*
- System traverses social graph from the viewer's perspective
- Calculates connection degree to each recommender:
  - Direct connection → **1st degree**
  - Friend of connection → **2nd degree**
  - Further → **3rd degree**
- Displayed in that order — no hidden scores

*"Ask about this worker" flow:*
- Employer clicks button on any recommendation
- System opens a direct chat between employer and recommender
- Tagged as `verification_request` in database
- Recommender gets notification: "Someone wants to ask about a worker you recommended"
- Full conversation logged

**Data stored:**
- `recommendations_table`:
  - `recommendation_id`
  - `recommender_user_id`
  - `worker_user_id`
  - `recommendation_text`
  - `created_at`
  - `job_id` (linked job that generated this)
- `social_graph_table`:
  - `user_a_id`
  - `user_b_id`
  - `relationship_type`
  - `degree` (computed, not stored — calculated at query time)

**AI role:**
- Transcribes voice recommendations to text
- Summarises a recommender's chat feedback: "This conversation indicates a positive experience — job completed on time, good quality"
- Does NOT alter the display order — graph is deterministic

---

## MODULE 7: JOB POSTING & MATCHING

**Purpose:** Connect employers with the right workers based on location, skill, and community trust — not algorithmic black boxes.

**Frontend Screens:**
- Post job screen (plain language input — what, where, budget, when)
- Job feed screen (workers see available jobs nearby)
- Job card (title, location, budget, distance, apply button)
- Job details screen (full description, employer profile, recommendation links)
- Applicants/matches screen (employer sees ranked list of workers)

**What happens technically:**

*Job posting:*
- Employer enters job in plain language or voice
- AI extracts: job type, required skills, location, budget range, urgency
- Job stored and indexed for matching

*Matching engine:*
- Runs when job is posted AND when worker applies
- Matching factors:
  - Skill tag overlap (worker tags vs job required tags)
  - Geographic proximity (worker location vs job location)
  - Community circle membership (same circle = higher priority)
  - Recommendation degree (1st degree connections ranked higher)
  - Job completion rate (workers with higher rates shown first)
  - Dispute history (workers with high dispute rate ranked lower)
- Output: ranked list of workers for employer to review

*Worker job feed:*
- Workers see jobs relevant to their skill tags within their location radius
- Sorted by proximity and skill relevance
- Can filter by budget, distance, job type

**Data stored:**
- `jobs_table`:
  - `job_id`
  - `employer_user_id`
  - `job_description_raw`
  - `job_tags` (AI extracted)
  - `location` (lat/lng)
  - `budget`
  - `status` (open / matched / active / completed / disputed / cancelled)
  - `created_at`
- `job_applications_table`:
  - `application_id`
  - `job_id`
  - `worker_user_id`
  - `status` (applied / shortlisted / accepted / rejected)
  - `applied_at`

**AI role:**
- Extracts job tags from natural language description
- Handles pidgin and informal language
- Powers the matching engine (skill + location + community + trust composite)
- Surfaces best matches to employer with brief explanation: "Matched because: electrician in Yaba, 2nd degree connection, 12 completed jobs"

---

## MODULE 8: JOB CHAT & AGREEMENT SYSTEM

**Purpose:** The structured chat page is where all job negotiations happen and where the official job agreement is formed. It becomes the legal record used in disputes.

**Frontend Screens:**
- Chat page (messages, voice messages, file sharing)
- Agreement confirmation button
- Job scope summary panel (AI-generated from chat)
- Agreed price display (auto-extracted from conversation)
- "Payment locked" confirmation screen

**What happens technically:**

*Chat creation:*
- When employer selects a worker, a dedicated chat channel is created
- Tagged as `job_chat` in database
- Both parties can message, send voice notes, share images/files
- All content stored permanently and linked to job ID

*Agreement confirmation:*
- Either party can propose agreement summary
- AI extracts from conversation: agreed price, job scope, timeline, any conditions
- Displays structured summary for both parties to review
- Both tap "Confirm Agreement" → job state changes to `agreement_locked`
- Neither party can edit chat history after this point

*Pre-job checklist:*
- After agreement locked, system prompts employer: "Lock payment in escrow to begin the job"
- Worker notified: "Waiting for payment to be secured"

**Data stored:**
- `job_chats_table`:
  - `chat_id`
  - `job_id`
  - `employer_user_id`
  - `worker_user_id`
  - `created_at`
- `chat_messages_table`:
  - `message_id`
  - `chat_id`
  - `sender_user_id`
  - `message_type` (text / voice / image / file / system)
  - `content` (text or URL)
  - `timestamp`
- `job_agreements_table`:
  - `agreement_id`
  - `job_id`
  - `agreed_price`
  - `job_scope_summary`
  - `timeline`
  - `confirmed_by_employer` (bool)
  - `confirmed_by_worker` (bool)
  - `locked_at`

**AI role:**
- Extracts agreed price from conversation
- Summarises job scope into structured format
- Detects if agreement has been reached even without explicit confirmation button press
- Flags if conversation contains suspicious patterns (pressure to pay outside platform, threats, coercion)

---

## MODULE 9: ESCROW & PAYMENT RELEASE

**Purpose:** Protect both parties. Worker is guaranteed payment before starting. Employer is guaranteed work before releasing funds. Squad APIs power the entire financial backbone here.

**Frontend Screens:**
- Payment lock screen (employer deposits into escrow)
- "Job Funded" confirmation screen (worker sees payment is secured)
- Job completion screen (worker marks complete)
- Employer confirmation screen (confirm delivery)
- Payment released confirmation screen
- Dispute trigger screen

**What happens technically:**

*Escrow creation:*
- After agreement locked, employer taps "Lock Payment"
- Backend calls Squad Dynamic Virtual Account API to create a job-specific escrow account
- Employer transfers agreed amount to this DVA
- Squad webhook `charge_successful` fires → backend updates job status to `funded`
- Worker notified: "Payment secured — you can begin the job"

*Job completion:*
- Worker marks job complete in app
- Employer receives notification to confirm
- Employer has 48-hour window to confirm or dispute
- If employer confirms → Squad Transfer API releases funds to worker's virtual account
- If employer does nothing within 48 hours → system auto-releases (protects worker)
- If employer opens dispute → funds frozen, dispute module triggered

*Dispute-triggered freeze:*
- Either party opens dispute within confirmation window
- Backend calls Squad API to freeze escrow funds
- Dispute module takes over (Module 10)

**Squad APIs used:**
- `POST /virtual-account/create-dynamic-virtual-account` — creates job-specific escrow account
- Webhook `charge_successful` — confirms employer has funded
- `POST /payout/transfer` — releases payment to worker
- `POST /payout/account/lookup` — verifies worker's account before release
- `POST /payout/requery` — checks payout status
- `x-squad-encrypted-body` HMAC-SHA512 signature verification on all webhooks

**Data stored:**
- `escrow_table`:
  - `escrow_id`
  - `job_id`
  - `squad_dva_account_number`
  - `amount`
  - `status` (pending / funded / released / frozen / refunded)
  - `funded_at`
  - `released_at`
- Updates to `jobs_table` status throughout

**AI role:** None in the payment mechanics — Squad handles this. AI is used in dispute resolution only (Module 10).

---

## MODULE 10: DISPUTE RESOLUTION

**Purpose:** Fair, data-driven resolution of job disagreements using recorded evidence — not he-said-she-said.

**Frontend Screens:**
- Dispute trigger screen (either party opens dispute)
- Evidence submission screen (both parties can add notes/photos)
- Dispute status screen (shows current stage)
- Resolution notification screen

**What happens technically:**

*Dispute opened:*
- Either party taps "Open Dispute"
- Escrow frozen immediately
- Both parties notified
- 48-hour window for both parties to submit additional evidence

*Evidence gathered automatically:*
- Full chat history from job chat
- Agreed job scope from agreement summary
- Payment records from escrow table
- Worker's job completion rate + dispute history
- Employer's payment history + dispute history
- Any proof media submitted by worker (videos/images from profile)

*Resolution logic:*
- AI analyses all evidence → produces structured summary
- Clear-cut cases (e.g. worker never confirmed arrival, employer has 5 previous bad-faith disputes) → automated resolution
- Complex cases → flagged for human review team
- Decision communicated to both parties with reasoning
- Funds released to appropriate party

*Behavioral consequence:*
- Losing party's trust score affected
- Repeat bad-faith disputes → account deprioritisation
- Severe cases → account suspension

**Data stored:**
- `disputes_table`:
  - `dispute_id`
  - `job_id`
  - `opened_by_user_id`
  - `reason_text`
  - `status` (open / under_review / resolved)
  - `resolution` (worker_wins / employer_wins / split / escalated)
  - `resolved_at`
- `dispute_evidence_table`:
  - `evidence_id`
  - `dispute_id`
  - `submitted_by_user_id`
  - `content_type` (text / image / video)
  - `content`
  - `submitted_at`

**AI role:**
- Summarises dispute based on all evidence
- Detects contradictions between chat history and claims
- Flags behavioural patterns (serial disputers, non-delivery patterns)
- Produces recommendation for human reviewer
- For clear-cut cases, outputs automated resolution with explanation

---

## MODULE 11: FINANCIAL TRACKING

**Purpose:** Give every user — especially informal traders and business owners — a simple way to record and understand their financial activity without accounting knowledge.

**Frontend Screens:**
- Financial tracking home (income summary, expense summary, net position)
- Log entry screen (voice or text input)
- Categorised view (by type: sales, expenses, debts, job income)
- Monthly summary screen
- Debt tracker (log and track informal IOUs)

**What happens technically:**

*Logging an entry:*
- User speaks or types: "I sold 10 bags of rice for ₦45,000"
- AI extracts: type=income, amount=45000, category=trade, item=rice
- Stored in `financial_log_table`
- Auto-added to running totals

*Debt tracking:*
- User says: "Emeka owes me ₦8,000 for the chairs"
- System creates a debt record: creditor=user, debtor=Emeka, amount=8000, item=chairs
- Can send in-app reminder to Emeka if he's on platform
- Tracks as outstanding until marked settled

*Automated entries:*
- All Squad wallet transactions automatically imported into financial log
- Tagged by context: job payment, personal transfer, cash-in

**Data stored:**
- `financial_log_table`:
  - `log_id`
  - `user_id`
  - `entry_type` (income / expense / debt_owed / debt_owing)
  - `amount`
  - `category`
  - `description_raw`
  - `ai_extracted_tags`
  - `source` (manual / squad_auto)
  - `timestamp`
- `debt_tracker_table`:
  - `debt_id`
  - `creditor_user_id`
  - `debtor_name` (or `debtor_user_id` if on platform)
  - `amount`
  - `reason`
  - `status` (outstanding / settled)
  - `created_at`

**AI role:**
- Extracts structured data from free-form voice/text entries
- Handles pidgin, Yoruba, Igbo, Hausa inputs
- Categorises entries automatically
- Generates weekly/monthly summary in simple language
- Reads summary aloud in user's preferred language

---

## MODULE 12: BEHAVIORAL FINANCIAL IDENTITY

**Purpose:** Convert real-world economic activity into a financial identity that unlocks access to credit, savings, and insurance — without traditional banking history.

**Frontend Screens:**
- Financial identity dashboard (activity score, what it unlocks, what to improve)
- Credit eligibility progress bar
- "What's missing" screen (specific actions to take to improve eligibility)
- Unlock notification (when a new financial product becomes available)

**What happens technically:**

*Score components:*
- Transaction volume and consistency (Squad wallet data)
- Job completion rate (jobs completed / jobs accepted)
- Dispute rate (disputes opened against user / total jobs)
- Repayment behaviour (if any previous loans taken)
- Community trust signals (recommendation count, degree)
- Platform engagement consistency (days active per month)
- Financial log regularity (how consistently they track)

*Score output:*
- Not shown as a number to user — shown as a progress bar toward next unlock
- Internally stored as a composite score for lender/partner use
- Updates in real time after every transaction, job, or log entry

*Product unlock thresholds:*
- Micro-savings: low threshold (any consistent wallet activity for 30 days)
- Micro-insurance: medium threshold (3+ months activity, no major disputes)
- Micro-loan: higher threshold (6+ months, consistent income, Tier 2 KYC)
- Working capital: highest threshold (business verified, Tier 3 KYC, proven revenue)

**Data stored:**
- `financial_identity_table`:
  - `user_id`
  - `transaction_score`
  - `job_completion_score`
  - `dispute_score`
  - `repayment_score`
  - `community_trust_score`
  - `engagement_score`
  - `composite_score`
  - `eligible_products` (array)
  - `last_updated`

**AI role:**
- Generates the composite score from all inputs
- Identifies which specific behaviours are holding a user back
- Produces plain-language explanation: "You're close to qualifying for a loan. Complete 3 more jobs without disputes and your eligibility unlocks."
- Reads this aloud for voice users

---

## MODULE 13: LOANS, SAVINGS & INSURANCE

**Purpose:** The financial products that the entire behavioral identity system is building toward. Accessed in-app, no bank visits.

**Frontend Screens:**
- Financial products home (loans, savings, insurance — locked/unlocked state)
- Loan eligibility screen (progress + what to improve)
- Loan application screen (amount, purpose, repayment plan shown)
- Active loan dashboard (amount owed, next repayment, history)
- Savings plan screen (set amount, frequency, goal)
- Insurance products screen (available plans, activate in-app)
- BVN guidance flow (for users who need it to qualify)

**What happens technically:**

*Loans:*
- User reaches loan eligibility threshold
- System shows maximum eligible amount based on behavioral score
- User selects amount + repayment period
- Funds disbursed to Squad wallet via Transfer API
- Repayment auto-deducted from future job escrow releases or wallet balance
- Repayment behaviour feeds back into behavioral identity score

*Savings:*
- User sets a daily/weekly auto-save amount
- System creates a dedicated savings virtual account via Squad
- Auto-debit triggers on schedule
- User can set a goal (e.g. "Save ₦50,000 for new tools")
- Progress tracked visually

*Insurance:*
- Eligible users see relevant micro-insurance products
- Activated in-app with monthly premium auto-debited from wallet
- Claims process handled in-app via dispute-style evidence submission
- Partners: existing Nigerian micro-insurance providers (Curacel, Casava, etc.)

*BVN guidance:*
- Users without BVN who want loan access → guided step-by-step flow
- AI assistant walks them through: where to go, what to bring, what happens
- Voice support throughout
- No API needed — pure content and guidance

**Data stored:**
- `loans_table`:
  - `loan_id`
  - `user_id`
  - `amount`
  - `disbursed_at`
  - `repayment_schedule` (JSON)
  - `amount_repaid`
  - `status` (active / completed / defaulted)
- `savings_table`:
  - `savings_id`
  - `user_id`
  - `squad_savings_account_id`
  - `target_amount`
  - `current_amount`
  - `frequency` (daily / weekly)
  - `auto_debit_amount`
- `insurance_table`:
  - `policy_id`
  - `user_id`
  - `product_name`
  - `premium_amount`
  - `frequency`
  - `status` (active / lapsed / claimed)

**AI role:**
- Recommends appropriate financial product based on user's profile
- Explains loan terms in simple language / voice
- Guides BVN acquisition step by step
- Monitors repayment patterns and alerts user before a missed payment

---

## MODULE 14: AI ASSISTANT & LEARNING LAYER

**Purpose:** Embedded intelligence that guides every user at every point — especially users with low literacy or no smartphone experience.

**Frontend Screens:**
- AI assistant button (always visible — bottom corner of every screen)
- Full assistant overlay (voice + text)
- Daily learning card (contextual tip based on today's activity)
- Language preference settings

**What happens technically:**

*Assistant capabilities:*
- Answers questions about any feature in plain language
- Guides users through any flow step by step
- Reads all screen content aloud on request
- Accepts voice input in English, Pidgin, Yoruba, Igbo, Hausa
- Responds in same language user used

*Daily learning prompts:*
- System looks at user's last 24 hours of activity
- Generates one contextual tip based on what they actually did
- Example: user just completed their first escrow job → tip: "Did you know? Every completed job builds your financial score. 5 more jobs and you could qualify for a loan."
- Not generic financial education — tied to real behaviour

*Voice-first mode:*
- For users who cannot read, entire app can be navigated by voice
- Every button and label is readable aloud
- User can say "send money to Chukwuemeka" and system executes
- Navigation commands: "go to my jobs", "show my balance", "help me post a job"

**Data stored:**
- `ai_interactions_table`:
  - `interaction_id`
  - `user_id`
  - `input_type` (text / voice)
  - `input_content`
  - `response_content`
  - `language_detected`
  - `timestamp`
- `learning_prompts_table`:
  - `prompt_id`
  - `user_id`
  - `prompt_text`
  - `trigger_activity`
  - `shown_at`
  - `dismissed` (bool)

**AI role (this module IS the AI):**
- LLM (Claude API or GPT-4o) as the assistant backbone
- Whisper for voice-to-text transcription
- TTS (ElevenLabs or Google TTS) for reading responses aloud
- Language detection automatic
- Intent parsing for voice commands
- Contextual learning prompt generation daily

---

## MODULE 15: AGENT PORTAL

**Purpose:** Physical entry point for users who cannot or will not use a smartphone. Agents are the human infrastructure layer.

**Frontend Screens (separate agent app/portal):**
- Agent login screen
- New user onboarding screen (phone + BVN/NIN entry for user)
- User wallet top-up screen (cash-in)
- User withdrawal screen (cash-out)
- Agent commission dashboard
- Active users list (users this agent has onboarded)
- Job facilitation screen (post/confirm jobs on behalf of users)

**What happens technically:**

*Agent onboarding:*
- Agents are registered separately with higher KYC (Tier 3)
- Agent ID created with elevated permissions
- Commission rate set in system (e.g. 0.5% per transaction facilitated)

*Agent-assisted transactions:*
- Agent receives cash → logs cash-in on portal → user's wallet credited
- User requests withdrawal → agent logs cash-out → user's wallet debited → agent pays physical cash
- All agent actions logged with agent ID for accountability

*Commission tracking:*
- Every transaction facilitated by agent logs a commission record
- Commission accumulated in agent's own wallet
- Agent can withdraw commission via normal cash-out flow

**Data stored:**
- `agents_table`:
  - `agent_id`
  - `user_id` (agents are also platform users)
  - `agent_status` (active / suspended)
  - `location` (their operating area)
  - `commission_rate`
  - `total_earned`
- `agent_transactions_table`:
  - `agent_txn_id`
  - `agent_id`
  - `user_id`
  - `transaction_type` (cash-in / cash-out / onboarding)
  - `amount`
  - `commission_earned`
  - `timestamp`

**AI role:** None. Pure operational portal.

---

That is the complete system — 15 modules, every feature, every screen, every data point, every AI touchpoint, every Squad API call.

Now we can map this to a 3-day sprint. Want me to break down who builds what, in what order, across the 3 days?