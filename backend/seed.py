"""
Comprehensive seed script for alwi.
Populates every section with realistic Nigerian data so the app feels alive.

Run:
    python seed.py            # add seed data (skips if seed already ran)
    python seed.py --reset    # wipe seeded data first, then re-seed
    python seed.py --wipe     # wipe seeded data only, don't re-seed

Existing user ECO-LLQ0-7RE9 (Ronald Ekom) is preserved.
All seed-generated users have IDs in range ECO-SEED-NNNN.
"""
import asyncio
import sys
import random
import uuid
import ssl as _ssl
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.config import get_settings

settings = get_settings()

_ctx = _ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = _ssl.CERT_NONE
engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"statement_cache_size": 0, "ssl": _ctx},
)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ─── Static Nigerian data pools ──────────────────────────────────────────
FIRST_NAMES = [
    "Adeola", "Chinedu", "Emeka", "Folake", "Ifeanyi", "Kemi", "Lekan", "Mohammed",
    "Ngozi", "Obinna", "Patience", "Rahmat", "Seyi", "Tunde", "Uche", "Victoria",
    "Yusuf", "Zainab", "Aisha", "Bisi", "Chika", "Damilola", "Ebuka", "Funke",
    "Gbenga", "Halima", "Idris", "Joseph", "Kelechi", "Lola", "Maryam", "Nkechi",
    "Olumide", "Peter", "Queen", "Ruth", "Sunday", "Tope", "Usman", "Vivian",
    "Wale", "Yetunde", "Zara", "Abdul", "Blessing", "Chinwe", "Daniel", "Esther",
    "Fatima", "Grace", "Henry", "Ibukun", "James", "Khadija", "Lanre", "Maurice",
    "Nnamdi", "Olabisi", "Precious", "Rashida", "Samuel", "Tolu", "Umar", "Victor",
    "Wasiu", "Yemi", "Zainabu", "Anthony", "Bukola", "Chiamaka", "Dele", "Edith",
    "Femi", "Gloria", "Hauwa", "Isaac", "Jumoke", "Kingsley", "Linda", "Michael",
    "Nasir", "Omolara", "Pius", "Rita", "Sandra", "Taiwo", "Ujunwa", "Vera",
    "Williams", "Yusufu", "Zaharadeen", "Abdullahi", "Bernard", "Christy", "David",
    "Ephraim", "Florence", "Gideon", "Hope", "Innocent", "Justice",
]

LAST_NAMES = [
    "Adeyemi", "Bello", "Chukwu", "Dauda", "Ezeh", "Folarin", "Garba", "Hassan",
    "Ibrahim", "Johnson", "Kalu", "Lawal", "Musa", "Njoku", "Okafor", "Peters",
    "Quadri", "Rasheed", "Salami", "Tijani", "Umeh", "Vaughn", "Williams", "Yakubu",
    "Zubairu", "Adekunle", "Bakare", "Cole", "Dada", "Edet", "Fadipe", "Gowon",
    "Hussaini", "Ifeoma", "Jegede", "Kayode", "Lateef", "Mbanefo", "Nwosu", "Obi",
    "Adesanya", "Eze", "Adebayo", "Adeniyi", "Ogunlesi", "Soyinka", "Achebe",
    "Akinwale", "Babatunde", "Chinwendu", "Egwu", "Fashola", "Gowon", "Hassan",
]

LAGOS_LGAS = [
    ("Yaba",        6.5172, 3.3700),
    ("Surulere",    6.4970, 3.3585),
    ("Ikeja",       6.6018, 3.3515),
    ("Lekki",       6.4474, 3.5550),
    ("Ajah",        6.4647, 3.6065),
    ("Victoria Island", 6.4281, 3.4219),
    ("Lagos Island", 6.4541, 3.3947),
    ("Apapa",       6.4474, 3.3578),
    ("Mushin",      6.5337, 3.3540),
    ("Oshodi",      6.5547, 3.3489),
    ("Ikorodu",     6.6194, 3.5106),
    ("Agege",       6.6151, 3.3209),
    ("Bariga",      6.5447, 3.3848),
    ("Festac",      6.4677, 3.2767),
    ("Gbagada",     6.5536, 3.3879),
    ("Magodo",      6.5990, 3.3902),
    ("Maryland",    6.5683, 3.3690),
    ("Ojota",       6.5817, 3.3796),
    ("Shomolu",     6.5394, 3.3838),
    ("Ojuelegba",   6.5067, 3.3613),
]

SKILL_DESCRIPTIONS = [
    ("I fix electrical wiring, install fans and AC units. I also do solar panel installation.", ["electrical"]),
    ("I sabi plumbing well well, fix leaking pipes, install water heaters, fix toilets and bathroom fittings.", ["plumbing"]),
    ("Carpentry work: tables, chairs, doors, wardrobes, kitchen cabinets. Wood polishing too.", ["carpentry"]),
    ("Fashion designer. I sew agbada, gowns, suits, ankara. Bridal wear specialty.", ["tailoring"]),
    ("Catering and event cooking. Jollof rice, fried rice, small chops, party packs.", ["catering"]),
    ("Long distance driver. I drive trucks and lorries. Lagos to Onitsha, Lagos to Kano.", ["driving"]),
    ("Selling provisions and household items in bulk. Wholesale prices.", ["trading"]),
    ("House cleaning, laundry, fumigation. I serve homes and offices.", ["cleaning"]),
    ("Wall painting, interior decoration, screeding. Houses and shops.", ["painting"]),
    ("Welding gates, burglary, security doors, iron furniture, metal works.", ["welding"]),
    ("Auto mechanic. I fix Toyota, Honda, Mercedes, BMW. Engine, brake, AC.", ["mechanic"]),
    ("Professional barber. Home service available. All hair styles for men and boys.", ["barbing"]),
    ("Wedding photography and videography. Studio shoots and outdoor events.", ["photography"]),
    ("Private tutor for primary and secondary students. Maths, English, Science.", ["teaching"]),
    ("iPhone, Samsung, Tecno phone repair. Screen replacement, battery, software fix.", ["phone_repair"]),
    ("Poultry farmer. Sell live chicken, eggs, and processed meat directly to homes.", ["farming"]),
    ("Security personnel. Night watch, event security, gate man.", ["security"]),
    ("Bridal makeup, gele tying, beauty consultations. Available for weddings and events.", ["makeup"]),
    ("Electrician with 10 years experience. House wiring, generator repair, inverter installation.", ["electrical"]),
    ("Bus driver — danfo and taxi routes. Lagos Mainland to Island daily.", ["driving"]),
    ("Tailor — uniforms for schools, churches, factories. Bulk orders welcomed.", ["tailoring"]),
    ("I sell phone accessories, chargers, cables, earpieces, phone cases.", ["trading"]),
    ("Bricklayer and house builder. Foundation to roofing. Estate developer.", ["carpentry", "welding"]),
    ("Hair stylist for women — braids, weaves, weave-ons, twists, fixings.", ["barbing", "makeup"]),
    ("Computer repair, laptop repair, OS installation, virus removal.", ["phone_repair"]),
    ("Caterer for offices — daily lunch packs. Healthy Nigerian meals.", ["catering"]),
    ("Cleaning service for short-let apartments. Same-day turnaround.", ["cleaning"]),
    ("Fish farmer — catfish and tilapia. Wholesale to restaurants.", ["farming", "trading"]),
    ("Generator technician — Honda, Tigerhead, big diesel sets. Service and repair.", ["mechanic", "electrical"]),
    ("Cake baker — birthdays, weddings, naming ceremonies. Custom designs.", ["catering"]),
]

JOB_DESCRIPTIONS = [
    ("Need an electrician to fix wiring in my shop in Yaba. Two fans not working, plus the AC.", ["electrical"], 15000),
    ("Looking for a plumber to fix leaking pipe in the kitchen. Urgent.", ["plumbing"], 8000),
    ("Need a tailor to make my wedding outfit. Have the fabric already.", ["tailoring"], 25000),
    ("Catering for my baby shower next Saturday. About 50 guests.", ["catering"], 80000),
    ("Need driver to take goods from Idumota to Lekki today.", ["driving"], 12000),
    ("Cleaning service for my 3-bedroom flat once a week.", ["cleaning"], 10000),
    ("Painter needed for new shop in Surulere. Walls and ceiling.", ["painting"], 35000),
    ("Welder to install burglary on 5 windows in Magodo.", ["welding"], 45000),
    ("Toyota Camry serviced — engine oil, filter, brake check.", ["mechanic"], 18000),
    ("Home barber for my two kids every Saturday morning.", ["barbing"], 4000),
    ("Photographer for my engagement shoot. Outdoor location, half day.", ["photography"], 60000),
    ("Maths tutor for SS3 student. WAEC prep. 3 sessions a week.", ["teaching"], 30000),
    ("iPhone 13 screen replacement. Phone working but screen cracked.", ["phone_repair"], 22000),
    ("Need fresh fish — 20kg catfish for an event.", ["farming", "trading"], 50000),
    ("Security guard for my warehouse — night shifts only.", ["security"], 40000),
    ("Bridal makeup for me + 4 bridesmaids on the 28th.", ["makeup"], 70000),
    ("AC installation in 2 rooms. Bring the unit too.", ["electrical"], 55000),
    ("Truck driver for Lagos to Ibadan delivery. Have my own truck.", ["driving"], 25000),
    ("Bulk uniform sewing for our church choir — 30 outfits.", ["tailoring"], 90000),
    ("Inverter installation, 3kva system. Surulere.", ["electrical"], 65000),
    ("Carpenter to build kitchen cabinet. Have the measurements.", ["carpentry"], 48000),
    ("Need someone to paint my children's bedroom blue and white.", ["painting"], 22000),
    ("Restaurant looking for daily cleaner. 7am to 11am.", ["cleaning"], 35000),
    ("Wedding cake — 3 tiers. Vanilla and chocolate. Pickup on Sat.", ["catering"], 45000),
    ("Bus driver needed — daily school run, Ikeja to Magodo.", ["driving"], 60000),
    ("Office furniture — 5 desks, 10 chairs. Plain wood finish.", ["carpentry"], 120000),
    ("Generator repair — won't start. Tigerhead 5kva.", ["mechanic", "electrical"], 15000),
    ("Laptop repair — water damage, won't power on.", ["phone_repair"], 30000),
    ("Need event chairs (200) delivered to Surulere venue.", ["driving", "trading"], 25000),
    ("Hairstylist for daughter's birthday — 6 kids, simple braids.", ["barbing", "makeup"], 20000),
    ("Plumbing — new bathroom installation. Tiles also needed.", ["plumbing"], 95000),
    ("Catfish for stocking my new pond. About 500 fingerlings.", ["farming"], 40000),
    ("Photo booth for wedding reception. Need props and backdrop.", ["photography"], 75000),
    ("Solar panel and inverter for 2-bedroom. Off-grid use.", ["electrical"], 350000),
    ("Phone charging station for my shop — 8 USB ports.", ["electrical", "trading"], 18000),
    ("Tutor for my 10-year-old — common entrance prep. Twice weekly.", ["teaching"], 25000),
    ("Welder to repair broken gate — Festac estate.", ["welding"], 12000),
    ("Carpentry — fix wardrobe door that fell off. Lekki.", ["carpentry"], 8000),
    ("Need someone to drive my mum to hospital appointments weekly.", ["driving"], 15000),
    ("Tailor to alter 3 of my suits. Drop-off and pickup.", ["tailoring"], 9000),
]

RECOMMENDATION_TEXTS = [
    "Excellent work — finished on time and even cleaned up after. Will hire again.",
    "Honest worker. Fair price. Will definitely call again.",
    "Did a fantastic job, very professional. Highly recommend.",
    "Punctual and skilled. The work quality was top notch.",
    "Great experience. Very polite and understands his trade.",
    "Quality work. He went the extra mile to make sure everything was perfect.",
    "Reliable and trustworthy. I felt safe leaving him in my house.",
    "Came on time and finished quicker than expected. Solid work.",
    "Best in the area for this kind of job. No regrets.",
    "Worth every kobo. Don't hesitate to hire.",
    "Very patient with my requests. Did exactly what I wanted.",
    "Skilled, neat and respectful. Recommended.",
    "Took time to explain the issue and the solution. Good guy.",
    "Job was done well. Communication was clear throughout.",
    "Came with all his tools. Professional setup.",
    "Affordable and the quality is high. Will use again.",
    "Helped me beyond the original scope without asking for more.",
    "Honest about pricing, didn't try to overcharge.",
    "I've used him twice now. Same quality both times.",
    "He really sabi his work. Strong recommend.",
]

FIN_LOG_ENTRIES = [
    ("income", "Sold 5 bags of rice today", "trade", 75000),
    ("income", "Got paid for tiling job in Lekki", "service", 120000),
    ("expense", "Bought materials for tailoring orders", "supplies", 35000),
    ("expense", "Fuel for the bike — weekly", "transport", 8000),
    ("income", "Catering for office lunch — 30 packs", "catering", 45000),
    ("expense", "Rent for shop space — monthly", "rent", 80000),
    ("income", "Photography for birthday party", "service", 60000),
    ("expense", "Phone bills and data subscription", "utility", 12000),
    ("income", "Phone repair customer — iPhone screen", "service", 18000),
    ("expense", "Electricity bill for shop", "utility", 25000),
    ("income", "Sold 3 birthday cakes this week", "catering", 30000),
    ("expense", "Bought new sewing machine", "equipment", 95000),
    ("income", "Bus fares — daily takings", "transport", 25000),
    ("expense", "School fees for children", "family", 60000),
    ("income", "Made 8 wig caps this week", "service", 56000),
    ("expense", "Bought ingredients for catering", "supplies", 42000),
    ("income", "Mechanic work — fixed 2 cars", "service", 85000),
    ("expense", "Bought building materials for client", "supplies", 150000),
    ("income", "Wedding makeup gig", "service", 70000),
    ("expense", "Transport for delivery to Ibadan", "transport", 28000),
    ("income", "Generator service — 4 customers", "service", 38000),
    ("expense", "Bought new tools — welding rod & cutting wheel", "equipment", 22000),
    ("income", "Provision sales — Saturday market", "trade", 95000),
    ("expense", "Bought fabric for client suit", "supplies", 18000),
    ("income", "Tutored 3 students — week's pay", "teaching", 40000),
    ("expense", "Paid apprentice — weekly stipend", "labour", 15000),
    ("income", "Hair salon takings — Friday & Sat", "service", 65000),
    ("expense", "Bought hair extensions stock", "supplies", 45000),
]

AI_QUESTIONS = [
    "How do I send money to someone?",
    "Wetin be the difference between Tier 1 and Tier 2?",
    "Can I get loan now?",
    "How long does the OTP take?",
    "Why is my wallet showing zero?",
    "How do I withdraw cash at an agent?",
    "I made a transfer but the person didn't get the money",
    "How do I apply for a job?",
    "What does it mean when my job is in escrow?",
    "Help me set up my work profile",
    "Wahala dey here — my profile no dey save",
    "How do I see workers near me?",
    "Can I delete my account?",
    "What's the maximum I can send daily?",
    "How do I track my expenses?",
    "I want to save money — wetin I go do?",
    "When can I get insurance?",
    "How does the recommendation thing work?",
    "Why is my financial score not increasing?",
    "Show me my balance please",
]

AI_RESPONSES = [
    "To send money, tap Send on the wallet screen, enter the recipient's ECO ID or scan their QR code.",
    "Tier 1 has a ₦50k daily limit. Tier 2 unlocks escrow and hiring (need BVN + government ID).",
    "Loans unlock at Tier 2 with consistent activity for 6+ months. Keep using your wallet daily.",
    "OTP arrives in under 30 seconds via WhatsApp or SMS. If you don't see it, request a new one.",
    "Your wallet shows zero because you haven't received any money yet. Share your account number to receive funds.",
    "Visit any agent near you, give them cash, and they'll credit your wallet instantly. Check the Community tab for nearby agents.",
    "Transfers can take 1–3 minutes. If it's been longer, check Transaction History — failed transfers are auto-refunded.",
    "Go to Jobs → Browse, find a job that matches your skills, then tap Apply. The employer will see your profile.",
    "Escrow means the employer's money is held safely. It's released to you when you complete the job.",
    "Tap Profile → Add Skills, describe what you do in plain words. We'll extract skill tags automatically.",
    "Sorry about that — try logging out and back in. Your profile changes should save when you tap Update.",
    "Open the Community tab. You'll see members within 5km of your location with their skills.",
    "Yes, go to More → Settings → Delete Account. All your data will be wiped after 30 days.",
    "Your daily limit depends on your KYC tier. Tier 1 is ₦50k. Upgrade to Tier 2 for ₦200k.",
    "Tap Finance → Log Entry and just type or speak: 'I sold rice for 5000'. We categorize it for you.",
    "Set up a savings plan in Finance → Savings. Pick a daily or weekly amount.",
    "Insurance unlocks after 3 months of consistent activity with no major disputes.",
    "After a completed job, the employer can recommend you. Those recommendations show up on your profile.",
    "Your score updates after every transaction, job, or financial log. Be consistent for at least 30 days.",
    "Your current balance is in the wallet section. Tap the eye icon to toggle visibility.",
]


def eco_id(n: int) -> str:
    """ECO-SEED-XXXX format for seeded users."""
    return f"ECO-SEED-{n:04d}"


def phone_for(n: int) -> str:
    """Unique fake Nigerian phone number."""
    return f"2348{n:09d}"


def squad_acct_no(n: int) -> str:
    return f"9{n:09d}"


BANK_NAMES = ["GTBank", "Access Bank", "First Bank", "Zenith Bank", "UBA", "Sterling Bank", "Wema Bank"]


# ─── Seed Functions ──────────────────────────────────────────────────────

async def wipe_seed(db: AsyncSession):
    """Wipe all rows referencing seeded users (ECO-SEED-*). Preserves real users."""
    print("Wiping existing seed data...")
    # Order matters: children first
    statements = [
        "DELETE FROM agent_transactions WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM agents WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM learning_prompts WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM ai_interactions WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM insurance_policies WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM savings_plans WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM loans WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM financial_identities WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM debt_records WHERE creditor_user_id LIKE 'ECO-SEED-%' OR debtor_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM financial_logs WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM dispute_evidence WHERE submitted_by_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM disputes WHERE opened_by_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM escrow_records WHERE job_id IN (SELECT job_id FROM jobs WHERE employer_user_id LIKE 'ECO-SEED-%' OR worker_user_id LIKE 'ECO-SEED-%')",
        "DELETE FROM job_agreements WHERE job_id IN (SELECT job_id FROM jobs WHERE employer_user_id LIKE 'ECO-SEED-%' OR worker_user_id LIKE 'ECO-SEED-%')",
        "DELETE FROM chat_messages WHERE sender_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM job_chats WHERE employer_user_id LIKE 'ECO-SEED-%' OR worker_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM job_applications WHERE worker_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM jobs WHERE employer_user_id LIKE 'ECO-SEED-%' OR worker_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM recommendations WHERE recommender_user_id LIKE 'ECO-SEED-%' OR worker_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM user_connections WHERE user_a_id LIKE 'ECO-SEED-%' OR user_b_id LIKE 'ECO-SEED-%'",
        "DELETE FROM community_memberships WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM community_groups WHERE group_name LIKE 'alwi %'",
        "DELETE FROM proof_media WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM work_profiles WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM user_intents WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM transactions WHERE sender_user_id LIKE 'ECO-SEED-%' OR receiver_user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM squad_accounts WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM kyc_records WHERE user_id LIKE 'ECO-SEED-%'",
        "DELETE FROM users WHERE user_id LIKE 'ECO-SEED-%'",
    ]
    for s in statements:
        try:
            await db.execute(text(s))
        except Exception as e:
            print(f"  warn: {s[:60]}... → {e}")
    await db.commit()
    print("Wipe complete.")


async def seed_users(db: AsyncSession, n: int = 100) -> list[str]:
    """Create n users with realistic Nigerian profiles."""
    print(f"Seeding {n} users...")
    user_ids = []
    now = datetime.utcnow()
    roles = ["worker", "employer", "business", "financial", "basic"]
    tiers = [1, 1, 1, 2, 2, 2, 3]   # weighted toward tier 1

    for i in range(n):
        uid = eco_id(i + 1)
        user_ids.append(uid)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        lga, lat, lng = random.choice(LAGOS_LGAS)
        # Spread within ~3km of LGA centre
        lat_jitter = lat + random.uniform(-0.03, 0.03)
        lng_jitter = lng + random.uniform(-0.03, 0.03)
        tier = random.choice(tiers)
        created = now - timedelta(days=random.randint(1, 365))

        await db.execute(
            text("""
                INSERT INTO users (
                    user_id, phone_number, full_name, kyc_type, kyc_value,
                    kyc_tier, kyc_status, active_role, onboarding_channel,
                    location_lat, location_lng, location_lga, preferred_language,
                    created_at, updated_at
                ) VALUES (
                    :uid, :phone, :name, :ktype, :kval,
                    :tier, :kstatus, :role, :channel,
                    :lat, :lng, :lga, :lang,
                    :created, :updated
                )
                ON CONFLICT (user_id) DO NOTHING
            """),
            {
                "uid": uid,
                "phone": phone_for(i + 1),
                "name": f"{first} {last}",
                "ktype": random.choice(["BVN", "NIN"]),
                "kval": "gAAAAA-fake-encrypted-kyc-value",
                "tier": tier,
                "kstatus": f"tier_{tier}",
                "role": random.choice(roles),
                "channel": random.choice(["self", "self", "self", "agent"]),
                "lat": Decimal(str(lat_jitter)),
                "lng": Decimal(str(lng_jitter)),
                "lga": lga,
                "lang": random.choice(["english", "english", "english", "pidgin", "yoruba", "igbo", "hausa"]),
                "created": created,
                "updated": created + timedelta(days=random.randint(0, 30)),
            }
        )

        # KYC record
        await db.execute(
            text("""
                INSERT INTO kyc_records (
                    kyc_id, user_id, kyc_type, kyc_value_encrypted,
                    dojah_reference, verified, tier, verified_at, created_at
                ) VALUES (
                    :kid, :uid, :ktype, :kval, :ref, true, :tier, :vat, :cat
                )
            """),
            {
                "kid": str(uuid.uuid4()),
                "uid": uid,
                "ktype": random.choice(["BVN", "NIN"]),
                "kval": "gAAAAA-fake",
                "ref": f"prembly_{uuid.uuid4().hex[:12]}",
                "tier": tier,
                "vat": created,
                "cat": created,
            }
        )

        # Squad account
        await db.execute(
            text("""
                INSERT INTO squad_accounts (
                    account_id, user_id, squad_virtual_account_id,
                    squad_account_number, squad_bank_name, squad_customer_identifier, created_at
                ) VALUES (:aid, :uid, :vid, :acct, :bank, :cid, :cat)
            """),
            {
                "aid": str(uuid.uuid4()),
                "uid": uid,
                "vid": f"va_{uuid.uuid4().hex[:16]}",
                "acct": squad_acct_no(i + 1),
                "bank": random.choice(BANK_NAMES),
                "cid": uid,
                "cat": created,
            }
        )

    await db.commit()
    print(f"  [OK] {n} users + KYC records + Squad accounts created")
    return user_ids


async def seed_intents(db: AsyncSession, user_ids: list[str]):
    print("Seeding user intents...")
    roles_map = [
        ("worker", 2, {"work": True, "income_activity": "service"}),
        ("employer", 2, {"hire": True, "needs": "casual_labor"}),
        ("business", 2, {"income_activity": "trade", "scale": "small"}),
        ("financial", 3, {"financial_support": True, "need": "loan"}),
        ("basic", 1, {"sending_money": True}),
    ]
    for uid in user_ids:
        role, tier, response = random.choice(roles_map)
        await db.execute(
            text("""
                INSERT INTO user_intents (
                    intent_id, user_id, intent_response, active_role, kyc_tier_required, created_at, updated_at
                ) VALUES (:iid, :uid, CAST(:resp AS JSONB), :role, :tier, NOW(), NOW())
            """),
            {
                "iid": str(uuid.uuid4()),
                "uid": uid,
                "resp": '{"work":' + ('true' if response.get('work') else 'false') + '}',
                "role": role,
                "tier": tier,
            }
        )
    await db.commit()
    print(f"  [OK] {len(user_ids)} intents created")


async def seed_work_profiles(db: AsyncSession, user_ids: list[str], n: int = 70) -> dict[str, list[str]]:
    """Create work profiles. Returns map of user_id -> skill_tags."""
    print(f"Seeding {n} work profiles...")
    workers = random.sample(user_ids, n)
    user_tags = {}
    for uid in workers:
        desc, tags = random.choice(SKILL_DESCRIPTIONS)
        completed = random.randint(0, 25)
        disputes = random.randint(0, min(2, completed))
        score = min(100, 20 + len(tags) * 5 + completed * 3 - disputes * 8 + random.randint(0, 15))
        user_tags[uid] = tags

        await db.execute(
            text("""
                INSERT INTO work_profiles (
                    profile_id, user_id, skill_description_raw, skill_tags,
                    profile_visibility_score, job_completion_count, dispute_count,
                    created_at, updated_at
                ) VALUES (
                    :pid, :uid, :desc, :tags,
                    :score, :completed, :disputes, NOW(), NOW()
                )
            """),
            {
                "pid": str(uuid.uuid4()),
                "uid": uid,
                "desc": desc,
                "tags": tags,
                "score": Decimal(str(score)),
                "completed": completed,
                "disputes": disputes,
            }
        )
    await db.commit()
    print(f"  [OK] {n} work profiles created")
    return user_tags


async def seed_proof_media(db: AsyncSession, user_tags: dict[str, list[str]], n: int = 50):
    print(f"Seeding {n} proof media...")
    chosen = random.sample(list(user_tags.keys()), min(n, len(user_tags)))
    sample_urls = [
        "https://res.cloudinary.com/demo/image/upload/v1/sample.jpg",
        "https://images.unsplash.com/photo-1581094794329-c8112a89af12",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136",
        "https://images.unsplash.com/photo-1521791136064-7986c2920216",
        "https://images.unsplash.com/photo-1518770660439-4636190af475",
    ]
    for uid in chosen:
        tags = user_tags[uid]
        await db.execute(
            text("""
                INSERT INTO proof_media (
                    media_id, user_id, media_url, media_type,
                    human_present, detected_activity_tags, confidence_score, uploaded_at
                ) VALUES (
                    :mid, :uid, :url, :mt, true, :tags, :conf, NOW()
                )
            """),
            {
                "mid": str(uuid.uuid4()),
                "uid": uid,
                "url": random.choice(sample_urls),
                "mt": random.choice(["image", "image", "image", "video"]),
                "tags": tags,
                "conf": Decimal(str(random.randint(65, 95))),
            }
        )
    await db.commit()
    print(f"  [OK] {len(chosen)} proof media items created")


async def seed_community(db: AsyncSession, user_ids: list[str]) -> dict[str, str]:
    """Create community groups (one per LGA) and assign all users."""
    print("Seeding community groups...")
    group_map = {}    # lga -> group_id
    for lga, lat, lng in LAGOS_LGAS:
        gid = str(uuid.uuid4())
        group_map[lga] = gid
        await db.execute(
            text("""
                INSERT INTO community_groups (
                    group_id, group_name, lga, geo_lat, geo_lng, radius_km, created_at
                ) VALUES (:gid, :name, :lga, :lat, :lng, 5, NOW())
            """),
            {
                "gid": gid,
                "name": f"alwi {lga} Network",
                "lga": lga,
                "lat": Decimal(str(lat)),
                "lng": Decimal(str(lng)),
            }
        )

    # Assign each user to their LGA group + 1-2 random extras
    print("  Assigning memberships...")
    membership_count = 0
    for uid in user_ids:
        # Get user's LGA
        result = await db.execute(text("SELECT location_lga FROM users WHERE user_id = :uid"), {"uid": uid})
        row = result.fetchone()
        if not row:
            continue
        user_lga = row[0]
        if user_lga in group_map:
            await db.execute(
                text("INSERT INTO community_memberships (membership_id, user_id, group_id, joined_at) VALUES (:mid, :uid, :gid, NOW())"),
                {"mid": str(uuid.uuid4()), "uid": uid, "gid": group_map[user_lga]}
            )
            membership_count += 1
        # Bonus: 30% chance to join 1 extra group
        if random.random() < 0.3:
            extra_lga = random.choice(list(group_map.keys()))
            if extra_lga != user_lga:
                await db.execute(
                    text("INSERT INTO community_memberships (membership_id, user_id, group_id, joined_at) VALUES (:mid, :uid, :gid, NOW())"),
                    {"mid": str(uuid.uuid4()), "uid": uid, "gid": group_map[extra_lga]}
                )
                membership_count += 1
    await db.commit()
    print(f"  [OK] {len(LAGOS_LGAS)} groups + {membership_count} memberships created")
    return group_map


async def seed_connections(db: AsyncSession, user_ids: list[str], n: int = 250):
    print(f"Seeding {n} user connections...")
    pairs = set()
    types = ["contact", "recommendation", "job_history"]
    for _ in range(n):
        a, b = random.sample(user_ids, 2)
        key = tuple(sorted([a, b]))
        if key in pairs:
            continue
        pairs.add(key)
        await db.execute(
            text("""
                INSERT INTO user_connections (
                    connection_id, user_a_id, user_b_id, connection_type, created_at
                ) VALUES (:cid, :a, :b, :ct, NOW())
            """),
            {"cid": str(uuid.uuid4()), "a": a, "b": b, "ct": random.choice(types)}
        )
    await db.commit()
    print(f"  [OK] {len(pairs)} unique connections created")


async def seed_transactions(db: AsyncSession, user_ids: list[str], n: int = 300):
    print(f"Seeding {n} transactions...")
    types = ["send", "cash_in", "cash_out", "job_payment"]
    tags = ["personal", "business", "job_payment"]
    statuses = ["completed", "completed", "completed", "completed", "pending", "failed"]
    now = datetime.utcnow()
    for _ in range(n):
        ttype = random.choice(types)
        if ttype == "cash_in" or ttype == "cash_out":
            sender = receiver = random.choice(user_ids)
        else:
            sender, receiver = random.sample(user_ids, 2)
        amount = random.randint(50, 200) * 100 * 100   # 5000 - 20000 kobo
        ts = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        await db.execute(
            text("""
                INSERT INTO transactions (
                    transaction_id, sender_user_id, receiver_user_id, amount, type,
                    channel, squad_reference, status, tagged_as, timestamp
                ) VALUES (
                    :tid, :s, :r, :amt, :tp, :ch, :ref, :st, :tg, :ts
                )
            """),
            {
                "tid": str(uuid.uuid4()),
                "s": sender,
                "r": receiver,
                "amt": amount,
                "tp": ttype,
                "ch": random.choice(["self", "self", "self", "agent"]),
                "ref": f"sqd_{uuid.uuid4().hex[:14]}",
                "st": random.choice(statuses),
                "tg": random.choice(tags),
                "ts": ts,
            }
        )
    await db.commit()
    print(f"  [OK] {n} transactions created")


async def seed_jobs_and_recs(db: AsyncSession, user_ids: list[str], user_tags: dict[str, list[str]]) -> list[str]:
    """Create jobs in various states + applications + agreements + escrow + recommendations."""
    print("Seeding jobs (40), applications, agreements, escrow, chats...")
    job_ids = []
    workers = list(user_tags.keys())
    employers = [u for u in user_ids if u not in workers] + random.sample(user_ids, 15)
    statuses = ["open", "open", "open", "matched", "agreement_locked", "funded", "active", "completed", "completed", "completed", "disputed", "cancelled"]
    completed_jobs = []
    now = datetime.utcnow()

    for desc, tags, budget_naira in JOB_DESCRIPTIONS:
        job_id = str(uuid.uuid4())
        job_ids.append(job_id)
        employer = random.choice(employers)
        # Get employer location
        result = await db.execute(text("SELECT location_lat, location_lng, location_lga FROM users WHERE user_id = :uid"), {"uid": employer})
        row = result.fetchone()
        lat, lng, lga = row if row else (6.5, 3.4, "Lagos")
        status = random.choice(statuses)
        worker = random.choice(workers) if status != "open" else None
        created = now - timedelta(days=random.randint(0, 60))

        await db.execute(
            text("""
                INSERT INTO jobs (
                    job_id, employer_user_id, worker_user_id, job_description_raw, job_tags,
                    location_lat, location_lng, location_address, budget, status,
                    created_at, updated_at
                ) VALUES (
                    :jid, :emp, :wrk, :desc, :tags,
                    :lat, :lng, :addr, :budget, :status,
                    :created, :updated
                )
            """),
            {
                "jid": job_id,
                "emp": employer,
                "wrk": worker,
                "desc": desc,
                "tags": tags,
                "lat": Decimal(str(lat)) if lat else None,
                "lng": Decimal(str(lng)) if lng else None,
                "addr": f"{lga}, Lagos",
                "budget": budget_naira * 100,
                "status": status,
                "created": created,
                "updated": created + timedelta(days=random.randint(0, 10)),
            }
        )

        if status in ("completed", "disputed"):
            completed_jobs.append((job_id, employer, worker))

        # Applications: 1-5 random workers applied
        num_apps = random.randint(1, 5)
        applicants = random.sample(workers, min(num_apps, len(workers)))
        for app_worker in applicants:
            app_status = "accepted" if app_worker == worker else random.choice(["applied", "applied", "shortlisted", "rejected"])
            await db.execute(
                text("""
                    INSERT INTO job_applications (
                        application_id, job_id, worker_user_id, status, applied_at
                    ) VALUES (:aid, :jid, :wid, :st, :ts)
                """),
                {"aid": str(uuid.uuid4()), "jid": job_id, "wid": app_worker, "st": app_status, "ts": created + timedelta(hours=random.randint(1, 48))}
            )

        # If matched or beyond, create chat + messages
        if worker and status in ("matched", "agreement_locked", "funded", "active", "completed", "disputed"):
            chat_id = str(uuid.uuid4())
            await db.execute(
                text("""
                    INSERT INTO job_chats (chat_id, job_id, employer_user_id, worker_user_id, chat_type, created_at)
                    VALUES (:cid, :jid, :emp, :wrk, 'job_chat', :ts)
                """),
                {"cid": chat_id, "jid": job_id, "emp": employer, "wrk": worker, "ts": created}
            )
            # Add 5-10 messages
            convo = [
                (employer, f"Hi, I saw your profile. Are you available for this job?"),
                (worker, f"Yes I'm available. When do you want it done?"),
                (employer, f"This weekend if possible. How much?"),
                (worker, f"For this type of work, ₦{budget_naira:,} is fair."),
                (employer, f"OK that works for me."),
                (worker, f"I'll start on Saturday morning. Please confirm address."),
                (employer, f"It's at {lga}. I'll send the gate code separately."),
                (worker, f"Got it. See you on Saturday."),
            ]
            for j, (sender, content) in enumerate(convo[:random.randint(4, 8)]):
                await db.execute(
                    text("""
                        INSERT INTO chat_messages (message_id, chat_id, sender_user_id, message_type, content, timestamp)
                        VALUES (:mid, :cid, :sid, 'text', :content, :ts)
                    """),
                    {"mid": str(uuid.uuid4()), "cid": chat_id, "sid": sender, "content": content, "ts": created + timedelta(hours=j)}
                )

            # Agreement if locked or beyond
            if status in ("agreement_locked", "funded", "active", "completed", "disputed"):
                await db.execute(
                    text("""
                        INSERT INTO job_agreements (
                            agreement_id, job_id, agreed_price, job_scope_summary, timeline,
                            confirmed_by_employer, confirmed_by_worker, locked_at
                        ) VALUES (
                            :aid, :jid, :price, :scope, :time, true, true, :locked
                        )
                    """),
                    {
                        "aid": str(uuid.uuid4()),
                        "jid": job_id,
                        "price": budget_naira * 100,
                        "scope": desc,
                        "time": "Complete within 2-3 days",
                        "locked": created + timedelta(hours=12),
                    }
                )

            # Escrow if funded or beyond
            if status in ("funded", "active", "completed", "disputed"):
                escrow_status = "released" if status == "completed" else ("frozen" if status == "disputed" else "funded")
                funded_at = created + timedelta(hours=14)
                released_at = funded_at + timedelta(days=2) if escrow_status == "released" else None
                await db.execute(
                    text("""
                        INSERT INTO escrow_records (
                            escrow_id, job_id, squad_dva_account_number, amount, status,
                            funded_at, released_at, auto_release_at, created_at
                        ) VALUES (:eid, :jid, :acct, :amt, :st, :fa, :ra, :ar, :ca)
                    """),
                    {
                        "eid": str(uuid.uuid4()),
                        "jid": job_id,
                        "acct": f"DVA{uuid.uuid4().hex[:10].upper()}",
                        "amt": budget_naira * 100,
                        "st": escrow_status,
                        "fa": funded_at,
                        "ra": released_at,
                        "ar": funded_at + timedelta(hours=48),
                        "ca": created,
                    }
                )

    await db.commit()
    print(f"  [OK] {len(job_ids)} jobs + applications + chats + agreements + escrow created")

    # Recommendations from completed jobs + extras
    print("Seeding recommendations...")
    rec_count = 0
    for job_id, employer, worker in completed_jobs:
        if random.random() < 0.7:
            await db.execute(
                text("""
                    INSERT INTO recommendations (
                        recommendation_id, recommender_user_id, worker_user_id,
                        recommendation_text, job_id, created_at
                    ) VALUES (:rid, :rec, :wrk, :txt, :jid, NOW())
                """),
                {
                    "rid": str(uuid.uuid4()),
                    "rec": employer,
                    "wrk": worker,
                    "txt": random.choice(RECOMMENDATION_TEXTS),
                    "jid": job_id,
                }
            )
            rec_count += 1

    # Extra standalone recommendations
    for _ in range(50):
        rec, wrk = random.sample(workers, 2)
        await db.execute(
            text("""
                INSERT INTO recommendations (recommendation_id, recommender_user_id, worker_user_id, recommendation_text, created_at)
                VALUES (:rid, :rec, :wrk, :txt, NOW())
            """),
            {"rid": str(uuid.uuid4()), "rec": rec, "wrk": wrk, "txt": random.choice(RECOMMENDATION_TEXTS)}
        )
        rec_count += 1
    await db.commit()
    print(f"  [OK] {rec_count} recommendations created")

    return job_ids


async def seed_disputes(db: AsyncSession, user_ids: list[str]):
    print("Seeding disputes...")
    # Find disputed jobs
    result = await db.execute(text("SELECT job_id, employer_user_id, worker_user_id FROM jobs WHERE status='disputed'"))
    rows = result.fetchall()
    dispute_count = 0
    for job_id, employer, worker in rows:
        opener = random.choice([employer, worker])
        dispute_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO disputes (
                    dispute_id, job_id, opened_by_user_id, reason_text, ai_summary,
                    ai_recommendation, ai_confidence, status, created_at
                ) VALUES (:did, :jid, :ob, :reason, :sum, :rec, :conf, 'under_review', NOW())
            """),
            {
                "did": dispute_id,
                "jid": job_id,
                "ob": opener,
                "reason": "Worker did not finish job as agreed. The wiring was incomplete.",
                "sum": "Chat history suggests work was partial but worker claims completion. Photographic evidence missing on both sides.",
                "rec": random.choice(["employer_wins", "worker_wins", "escalate"]),
                "conf": Decimal(str(random.randint(60, 90))),
            }
        )
        # Evidence (2-3 items)
        for _ in range(random.randint(2, 3)):
            submitter = random.choice([employer, worker])
            await db.execute(
                text("""
                    INSERT INTO dispute_evidence (
                        evidence_id, dispute_id, submitted_by_user_id, content_type, content, submitted_at
                    ) VALUES (:eid, :did, :sb, 'text', :content, NOW())
                """),
                {
                    "eid": str(uuid.uuid4()),
                    "did": dispute_id,
                    "sb": submitter,
                    "content": random.choice([
                        "He left after only 4 hours, said he'd come back the next day but never did.",
                        "Job was completed. Customer is just trying to avoid payment.",
                        "The materials provided were not enough — that's why job was incomplete.",
                        "I have photos showing the finished work. Will upload soon.",
                    ]),
                }
            )
        dispute_count += 1
    await db.commit()
    print(f"  [OK] {dispute_count} disputes with evidence")


async def seed_financial(db: AsyncSession, user_ids: list[str]):
    print("Seeding financial logs, debts, identities, loans, savings, insurance...")
    now = datetime.utcnow()
    # Financial logs: 300+
    log_count = 0
    for _ in range(300):
        uid = random.choice(user_ids)
        entry_type, desc, category, amount = random.choice(FIN_LOG_ENTRIES)
        ts = now - timedelta(days=random.randint(0, 90))
        await db.execute(
            text("""
                INSERT INTO financial_logs (
                    log_id, user_id, entry_type, amount, category,
                    description_raw, source, timestamp
                ) VALUES (:lid, :uid, :tp, :amt, :cat, :desc, :src, :ts)
            """),
            {
                "lid": str(uuid.uuid4()),
                "uid": uid,
                "tp": entry_type,
                "amt": amount,
                "cat": category,
                "desc": desc,
                "src": random.choice(["manual", "manual", "squad_auto"]),
                "ts": ts,
            }
        )
        log_count += 1

    # Debt records (50)
    for _ in range(50):
        creditor = random.choice(user_ids)
        debtor_uid = random.choice(user_ids) if random.random() < 0.6 else None
        debtor_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" if not debtor_uid else None
        await db.execute(
            text("""
                INSERT INTO debt_records (
                    debt_id, creditor_user_id, debtor_name, debtor_user_id,
                    amount, reason, status, created_at
                ) VALUES (:did, :cred, :dn, :dui, :amt, :reason, :st, NOW())
            """),
            {
                "did": str(uuid.uuid4()),
                "cred": creditor,
                "dn": debtor_name,
                "dui": debtor_uid,
                "amt": random.randint(20, 200) * 100 * 100,
                "reason": random.choice([
                    "For the chairs supplied last month",
                    "Loan for fuel during emergency",
                    "Helped with school fees",
                    "For provision goods supplied on credit",
                    "Cash advance for tools",
                ]),
                "st": random.choice(["outstanding", "outstanding", "outstanding", "settled"]),
            }
        )

    # Financial identities (one per user)
    print("  Building financial identities...")
    for uid in user_ids:
        scores = {k: Decimal(str(random.randint(20, 90))) for k in [
            "transaction", "job_completion", "dispute", "repayment", "community_trust", "engagement"
        ]}
        scores["dispute"] = Decimal(str(random.randint(0, 30)))   # lower is good
        composite = sum(scores.values()) / 6
        products = []
        if composite >= 40:
            products.append("micro_savings")
        if composite >= 55:
            products.append("micro_insurance")
        if composite >= 70:
            products.append("micro_loan")
        if composite >= 85:
            products.append("working_capital")
        await db.execute(
            text("""
                INSERT INTO financial_identities (
                    identity_id, user_id, transaction_score, job_completion_score, dispute_score,
                    repayment_score, community_trust_score, engagement_score, composite_score,
                    eligible_products, last_updated
                ) VALUES (
                    :iid, :uid, :ts, :jcs, :ds, :rs, :cts, :es, :cs,
                    :prod, NOW()
                )
            """),
            {
                "iid": str(uuid.uuid4()),
                "uid": uid,
                "ts": scores["transaction"], "jcs": scores["job_completion"], "ds": scores["dispute"],
                "rs": scores["repayment"], "cts": scores["community_trust"], "es": scores["engagement"],
                "cs": composite,
                "prod": products,
            }
        )

    # Loans (20)
    for _ in range(20):
        uid = random.choice(user_ids)
        amount = random.randint(20, 200) * 1000 * 100
        repaid = int(amount * random.uniform(0, 1))
        disbursed = now - timedelta(days=random.randint(7, 120))
        await db.execute(
            text("""
                INSERT INTO loans (
                    loan_id, user_id, amount, interest_rate, amount_repaid,
                    status, disbursed_at, due_date
                ) VALUES (:lid, :uid, :amt, :rate, :rep, :st, :dis, :due)
            """),
            {
                "lid": str(uuid.uuid4()),
                "uid": uid,
                "amt": amount,
                "rate": Decimal(str(random.choice([5, 7, 10, 12]))),
                "rep": repaid,
                "st": "completed" if repaid >= amount else "active",
                "dis": disbursed,
                "due": disbursed + timedelta(days=90),
            }
        )

    # Savings plans (35)
    for _ in range(35):
        uid = random.choice(user_ids)
        target = random.randint(50, 500) * 1000 * 100
        current = int(target * random.uniform(0.1, 0.95))
        await db.execute(
            text("""
                INSERT INTO savings_plans (
                    savings_id, user_id, squad_savings_account_id, target_amount,
                    current_amount, frequency, auto_debit_amount, goal_description,
                    status, created_at
                ) VALUES (:sid, :uid, :sqd, :tgt, :cur, :freq, :auto, :goal, :st, NOW())
            """),
            {
                "sid": str(uuid.uuid4()),
                "uid": uid,
                "sqd": f"sav_{uuid.uuid4().hex[:12]}",
                "tgt": target,
                "cur": current,
                "freq": random.choice(["daily", "weekly", "weekly"]),
                "auto": random.choice([100, 200, 500, 1000]) * 100,
                "goal": random.choice([
                    "Save for new sewing machine",
                    "School fees fund",
                    "Save for shop rent",
                    "Emergency fund",
                    "Wedding savings",
                    "Capital for trading expansion",
                    "Buy a motorcycle",
                ]),
                "st": "active",
            }
        )

    # Insurance (25)
    for _ in range(25):
        uid = random.choice(user_ids)
        await db.execute(
            text("""
                INSERT INTO insurance_policies (
                    policy_id, user_id, product_name, provider, premium_amount, frequency, status, started_at
                ) VALUES (:pid, :uid, :name, :prov, :prem, 'monthly', :st, NOW())
            """),
            {
                "pid": str(uuid.uuid4()),
                "uid": uid,
                "name": random.choice([
                    "alwi Health Cover", "alwi Life Cover", "alwi Equipment Cover", "alwi Trader's Cover",
                ]),
                "prov": random.choice(["Curacel", "Casava", "ETAP"]),
                "prem": random.randint(500, 5000) * 100,
                "st": random.choice(["active", "active", "active", "lapsed"]),
            }
        )

    await db.commit()
    print(f"  [OK] {log_count} financial logs + 50 debts + {len(user_ids)} identities + 20 loans + 35 savings + 25 insurance")


async def seed_ai_and_agents(db: AsyncSession, user_ids: list[str]):
    print("Seeding AI interactions, learning prompts, agents...")
    now = datetime.utcnow()

    # AI interactions (150)
    for _ in range(150):
        uid = random.choice(user_ids)
        q_idx = random.randint(0, len(AI_QUESTIONS) - 1)
        await db.execute(
            text("""
                INSERT INTO ai_interactions (
                    interaction_id, user_id, input_type, input_content,
                    response_content, language_detected, timestamp
                ) VALUES (:iid, :uid, :inp, :q, :r, :lang, :ts)
            """),
            {
                "iid": str(uuid.uuid4()),
                "uid": uid,
                "inp": random.choice(["text", "text", "voice"]),
                "q": AI_QUESTIONS[q_idx],
                "r": AI_RESPONSES[q_idx],
                "lang": random.choice(["english", "english", "pidgin", "yoruba"]),
                "ts": now - timedelta(hours=random.randint(1, 720)),
            }
        )

    # Learning prompts (100)
    prompts = [
        ("You completed your first job — well done! Try adding proof media to boost your profile.", "first_job_completion"),
        ("Did you know? Saving ₦500 a week becomes ₦26,000 in a year. Tap Finance → Savings to start.", "low_savings_balance"),
        ("Your dispute rate is 0. Keep it up — you'll unlock loan access soon.", "clean_record"),
        ("Add your skills in your own words. The AI will turn them into searchable tags.", "empty_profile"),
        ("Three of your neighbours just joined alwi this week. Tap Community to see them.", "growing_community"),
        ("You're close to Tier 2 KYC. Upload one government ID to unlock hiring features.", "tier_upgrade"),
        ("Track your earnings in plain Pidgin or English — just speak into the Finance log.", "voice_logging"),
        ("Your last 5 transactions were all on weekdays. Consistent activity boosts your score.", "consistency"),
    ]
    for _ in range(100):
        uid = random.choice(user_ids)
        ptext, trig = random.choice(prompts)
        await db.execute(
            text("""
                INSERT INTO learning_prompts (
                    prompt_id, user_id, prompt_text, trigger_activity, shown_at, dismissed
                ) VALUES (:pid, :uid, :pt, :tr, :sa, :dis)
            """),
            {
                "pid": str(uuid.uuid4()),
                "uid": uid,
                "pt": ptext,
                "tr": trig,
                "sa": now - timedelta(days=random.randint(0, 30)),
                "dis": random.choice([False, False, True]),
            }
        )

    # Agents (15) and agent transactions (100)
    agent_ids = []
    agent_users = random.sample(user_ids, 15)
    for au in agent_users:
        aid = str(uuid.uuid4())
        agent_ids.append((aid, au))
        # Get user LGA
        result = await db.execute(text("SELECT location_lga FROM users WHERE user_id = :uid"), {"uid": au})
        lga = result.scalar() or "Lagos"
        await db.execute(
            text("""
                INSERT INTO agents (
                    agent_id, user_id, agent_status, location_lga, commission_rate, total_earned, created_at
                ) VALUES (:aid, :uid, 'active', :lga, 0.005, :te, NOW())
            """),
            {"aid": aid, "uid": au, "lga": lga, "te": random.randint(50, 5000) * 100}
        )

    # Agent transactions
    for _ in range(100):
        aid, agent_user = random.choice(agent_ids)
        user = random.choice(user_ids)
        amount = random.randint(20, 500) * 100 * 100
        commission = int(amount * 0.005)
        await db.execute(
            text("""
                INSERT INTO agent_transactions (
                    agent_txn_id, agent_id, user_id, transaction_type, amount, commission_earned, timestamp
                ) VALUES (:tid, :aid, :uid, :tp, :amt, :comm, :ts)
            """),
            {
                "tid": str(uuid.uuid4()),
                "aid": aid,
                "uid": user,
                "tp": random.choice(["cash_in", "cash_out", "onboarding"]),
                "amt": amount,
                "comm": commission,
                "ts": now - timedelta(days=random.randint(0, 60)),
            }
        )

    await db.commit()
    print(f"  [OK] 150 AI interactions + 100 learning prompts + 15 agents + 100 agent transactions")


async def report(db: AsyncSession):
    print("\n" + "=" * 50)
    print("FINAL ROW COUNTS")
    print("=" * 50)
    tables = [
        "users", "kyc_records", "squad_accounts", "user_intents", "work_profiles",
        "proof_media", "community_groups", "community_memberships", "user_connections",
        "recommendations", "jobs", "job_applications", "job_chats", "chat_messages",
        "job_agreements", "escrow_records", "disputes", "dispute_evidence",
        "transactions", "financial_logs", "debt_records", "financial_identities",
        "loans", "savings_plans", "insurance_policies", "ai_interactions",
        "learning_prompts", "agents", "agent_transactions",
    ]
    for t in tables:
        try:
            r = await db.execute(text(f"SELECT COUNT(*) FROM {t}"))
            print(f"  {t:30s}  {r.scalar():>5}")
        except Exception as e:
            print(f"  {t:30s}  ERROR: {e}")


async def main():
    do_reset = "--reset" in sys.argv
    only_wipe = "--wipe" in sys.argv

    async with Session() as db:
        if do_reset or only_wipe:
            await wipe_seed(db)
            if only_wipe:
                await report(db)
                return

        # Idempotency check
        result = await db.execute(text("SELECT COUNT(*) FROM users WHERE user_id LIKE 'ECO-SEED-%'"))
        existing = result.scalar()
        if existing > 50 and not do_reset:
            print(f"Seed data already exists ({existing} seeded users). Use --reset to re-seed.")
            await report(db)
            return

        random.seed(42)   # reproducible

        user_ids = await seed_users(db, n=100)
        await seed_intents(db, user_ids)
        user_tags = await seed_work_profiles(db, user_ids, n=70)
        await seed_proof_media(db, user_tags, n=50)
        await seed_community(db, user_ids)
        await seed_connections(db, user_ids, n=250)
        await seed_transactions(db, user_ids, n=300)
        await seed_jobs_and_recs(db, user_ids, user_tags)
        await seed_disputes(db, user_ids)
        await seed_financial(db, user_ids)
        await seed_ai_and_agents(db, user_ids)

        await report(db)


if __name__ == "__main__":
    asyncio.run(main())
