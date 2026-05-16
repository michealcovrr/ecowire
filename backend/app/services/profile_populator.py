"""
Per-user activity populator.

Used by:
  - seed.py to give every seeded user rich activity
  - auth.py to auto-populate any newly-onboarded real user so their
    first login already feels "lived in"

populate_user_profile(db, user_id, peer_user_ids) creates:
  - 8-15 transactions (mix of send/receive with peer users)
  - 6-12 financial logs spread over the last 60 days
  - 1-3 AI interactions
  - 1-2 learning prompts
  - 1 financial identity (composite score, eligible products)
  - 1 work profile with skill tags (~60% of users)
  - 1-3 recommendations received from peers
  - 0-2 debt records
  - 1 user_intent assignment
  - community membership (auto-assigned to their LGA group)
"""
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


SKILL_DESCRIPTIONS = [
    ("I fix electrical wiring, install fans and AC units. I also do solar panel installation.", ["electrical"]),
    ("I sabi plumbing well well, fix leaking pipes, install water heaters, fix toilets and bathroom fittings.", ["plumbing"]),
    ("Carpentry work: tables, chairs, doors, wardrobes, kitchen cabinets. Wood polishing too.", ["carpentry"]),
    ("Fashion designer. I sew agbada, gowns, suits, ankara. Bridal wear specialty.", ["tailoring"]),
    ("Catering and event cooking. Jollof rice, fried rice, small chops, party packs.", ["catering"]),
    ("Long distance driver. I drive trucks and lorries.", ["driving"]),
    ("Selling provisions and household items in bulk. Wholesale prices.", ["trading"]),
    ("House cleaning, laundry, fumigation. Homes and offices.", ["cleaning"]),
    ("Wall painting, interior decoration, screeding.", ["painting"]),
    ("Welding gates, burglary, security doors, iron furniture.", ["welding"]),
    ("Auto mechanic. Toyota, Honda, Mercedes. Engine, brake, AC.", ["mechanic"]),
    ("Professional barber. Home service available.", ["barbing"]),
    ("Wedding photography and videography. Events and shoots.", ["photography"]),
    ("Private tutor — Maths, English, Science. Primary and secondary.", ["teaching"]),
    ("iPhone, Samsung, Tecno repair. Screen, battery, software.", ["phone_repair"]),
    ("Poultry farmer. Live chicken, eggs, processed meat.", ["farming"]),
    ("Security personnel. Night watch, event security.", ["security"]),
    ("Bridal makeup, gele tying, beauty consultations.", ["makeup"]),
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

RECOMMENDATION_TEXTS = [
    "Excellent work — finished on time and even cleaned up after.",
    "Honest worker. Fair price. Will definitely call again.",
    "Did a fantastic job, very professional.",
    "Punctual and skilled. Top notch work.",
    "Great experience. Very polite and understands his trade.",
    "Quality work. He went the extra mile.",
    "Reliable and trustworthy. I felt safe leaving him in my house.",
    "Came on time and finished quicker than expected.",
    "Best in the area for this kind of job.",
    "Worth every kobo. Don't hesitate to hire.",
    "Very patient with my requests.",
    "Skilled, neat and respectful. Recommended.",
    "Took time to explain the issue and solution. Good guy.",
    "Communication was clear throughout.",
    "Affordable and the quality is high.",
    "Helped me beyond the original scope without asking for more.",
    "Honest about pricing.",
    "He really sabi his work. Strong recommend.",
]

AI_Q_AND_A = [
    ("How do I send money to someone?",
     "Tap Send on the wallet screen, enter the recipient's ECO ID or scan their QR code."),
    ("Wetin be the difference between Tier 1 and Tier 2?",
     "Tier 1 has a N50k daily limit. Tier 2 unlocks escrow and hiring (need BVN + government ID)."),
    ("Can I get loan now?",
     "Loans unlock at Tier 2 with consistent activity for 6+ months. Keep using your wallet daily."),
    ("How do I withdraw cash at an agent?",
     "Visit any agent near you, they'll debit your wallet and hand you cash."),
    ("How do I apply for a job?",
     "Go to Jobs > Browse, find one that matches, tap Apply."),
    ("Show me my balance please",
     "Your balance is on the wallet screen. Tap the eye icon to toggle visibility."),
    ("What does escrow mean?",
     "Escrow means the employer's money is held safely. Released when you complete the job."),
    ("How do I track my expenses?",
     "Tap Finance > Log Entry and type or speak: 'I sold rice for 5000'. We categorize automatically."),
    ("When can I get insurance?",
     "Insurance unlocks after 3 months of consistent activity with no major disputes."),
    ("Why is my financial score not increasing?",
     "Your score updates after every transaction, job, or financial log. Be consistent for 30+ days."),
]

LEARNING_PROMPTS = [
    ("You completed your first job - well done! Add proof media to boost your profile.", "first_job_completion"),
    ("Did you know? Saving N500 a week becomes N26,000 in a year. Tap Finance > Savings.", "low_savings_balance"),
    ("Your dispute rate is 0. Keep it up - you'll unlock loan access soon.", "clean_record"),
    ("Add your skills in your own words. The AI will turn them into searchable tags.", "empty_profile"),
    ("Three of your neighbours just joined alwi this week. Tap Community to see them.", "growing_community"),
    ("You're close to Tier 2 KYC. Upload one government ID to unlock hiring features.", "tier_upgrade"),
    ("Your last 5 transactions were all on weekdays. Consistent activity boosts your score.", "consistency"),
]

ROLES = ["worker", "employer", "business", "financial", "basic"]


async def populate_user_profile(
    db: AsyncSession,
    user_id: str,
    peer_user_ids: list[str] | None = None,
    *,
    is_worker: bool | None = None,
    commit: bool = True,
) -> dict:
    """
    Generate a full activity history for the given user.

    peer_user_ids: pool of other users to use as senders/receivers/recommenders.
                   If None, pulled from DB (any users other than this one).
    is_worker: forces work-profile creation. If None, 60% chance.

    Returns a count of inserted rows by type.
    """
    counts = {
        "transactions": 0,
        "financial_logs": 0,
        "ai_interactions": 0,
        "learning_prompts": 0,
        "financial_identity": 0,
        "work_profile": 0,
        "recommendations_received": 0,
        "debt_records": 0,
        "user_intent": 0,
        "community_membership": 0,
    }

    # Resolve peer pool
    if peer_user_ids is None:
        result = await db.execute(
            text("SELECT user_id FROM users WHERE user_id != :uid LIMIT 200"),
            {"uid": user_id},
        )
        peer_user_ids = [r[0] for r in result.fetchall()]
    else:
        peer_user_ids = [p for p in peer_user_ids if p != user_id]

    if not peer_user_ids:
        # Solo activity only — skip transactions/recommendations
        peer_user_ids = []

    now = datetime.utcnow()

    # 1. User intent
    role = random.choice(ROLES)
    tier_required = {"worker": 2, "employer": 2, "business": 2, "financial": 3, "basic": 1}[role]
    response = {"work": role == "worker", "hire": role == "employer", "active_role": role}
    import json
    await db.execute(
        text("""
            INSERT INTO user_intents (
                intent_id, user_id, intent_response, active_role, kyc_tier_required, created_at, updated_at
            ) VALUES (:iid, :uid, CAST(:resp AS JSONB), :role, :tier, NOW(), NOW())
        """),
        {
            "iid": str(uuid.uuid4()),
            "uid": user_id,
            "resp": json.dumps(response),
            "role": role,
            "tier": tier_required,
        },
    )
    counts["user_intent"] = 1

    # Reflect role on user record
    await db.execute(
        text("UPDATE users SET active_role = :role WHERE user_id = :uid AND active_role IS NULL"),
        {"role": role, "uid": user_id},
    )

    # 2. Community membership — try matching user's LGA
    lga_result = await db.execute(text("SELECT location_lga FROM users WHERE user_id = :uid"), {"uid": user_id})
    user_lga = lga_result.scalar()
    if user_lga:
        group_result = await db.execute(
            text("SELECT group_id FROM community_groups WHERE lga = :lga LIMIT 1"),
            {"lga": user_lga},
        )
        group_id = group_result.scalar()
        if group_id:
            # Check if already a member
            existing = await db.execute(
                text("SELECT 1 FROM community_memberships WHERE user_id = :uid AND group_id = :gid"),
                {"uid": user_id, "gid": group_id},
            )
            if not existing.scalar():
                await db.execute(
                    text("""
                        INSERT INTO community_memberships (membership_id, user_id, group_id, joined_at)
                        VALUES (:mid, :uid, :gid, NOW())
                    """),
                    {"mid": str(uuid.uuid4()), "uid": user_id, "gid": group_id},
                )
                counts["community_membership"] = 1

    # 3. Work profile (60% of users, or forced)
    wants_profile = is_worker if is_worker is not None else (role == "worker" or random.random() < 0.6)
    skill_tags = []
    if wants_profile:
        desc, tags = random.choice(SKILL_DESCRIPTIONS)
        skill_tags = tags
        completed = random.randint(3, 22)
        disputes = random.randint(0, min(2, completed))
        score = min(100, 25 + len(tags) * 5 + completed * 3 - disputes * 8 + random.randint(0, 12))
        await db.execute(
            text("""
                INSERT INTO work_profiles (
                    profile_id, user_id, skill_description_raw, skill_tags,
                    profile_visibility_score, job_completion_count, dispute_count,
                    created_at, updated_at
                ) VALUES (:pid, :uid, :desc, :tags, :score, :comp, :disp, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """),
            {
                "pid": str(uuid.uuid4()),
                "uid": user_id,
                "desc": desc,
                "tags": tags,
                "score": Decimal(str(score)),
                "comp": completed,
                "disp": disputes,
            },
        )
        counts["work_profile"] = 1

    # 4. Transactions: 8-15 mix of send/receive
    n_txns = random.randint(8, 15)
    txn_types = ["send", "send", "send", "cash_in", "cash_in", "cash_out", "job_payment"]
    for _ in range(n_txns):
        ttype = random.choice(txn_types)
        # 60% chance the user is the sender, 40% chance recipient
        user_is_sender = random.random() < 0.6
        if peer_user_ids:
            peer = random.choice(peer_user_ids)
        else:
            peer = user_id  # cash_in/out — same user
        if ttype in ("cash_in",):
            sender, receiver = peer or user_id, user_id
        elif ttype in ("cash_out",):
            sender, receiver = user_id, peer or user_id
        elif user_is_sender:
            sender, receiver = user_id, peer
        else:
            sender, receiver = peer, user_id
        amount = random.randint(20, 250) * 100 * 100   # 2000 - 25000 kobo
        ts = now - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23))
        await db.execute(
            text("""
                INSERT INTO transactions (
                    transaction_id, sender_user_id, receiver_user_id, amount, type,
                    channel, squad_reference, status, tagged_as, timestamp
                ) VALUES (:tid, :s, :r, :amt, :tp, :ch, :ref, :st, :tg, :ts)
            """),
            {
                "tid": str(uuid.uuid4()),
                "s": sender,
                "r": receiver,
                "amt": amount,
                "tp": ttype,
                "ch": random.choice(["self", "self", "self", "agent"]),
                "ref": f"sqd_{uuid.uuid4().hex[:14]}",
                "st": random.choices(["completed", "completed", "completed", "completed", "pending", "failed"], k=1)[0],
                "tg": random.choice(["personal", "business", "job_payment"]),
                "ts": ts,
            },
        )
        counts["transactions"] += 1

    # 5. Financial logs (6-12)
    n_logs = random.randint(6, 12)
    for _ in range(n_logs):
        entry_type, desc, category, amount = random.choice(FIN_LOG_ENTRIES)
        ts = now - timedelta(days=random.randint(0, 60))
        await db.execute(
            text("""
                INSERT INTO financial_logs (
                    log_id, user_id, entry_type, amount, category, description_raw, source, timestamp
                ) VALUES (:lid, :uid, :tp, :amt, :cat, :desc, :src, :ts)
            """),
            {
                "lid": str(uuid.uuid4()),
                "uid": user_id,
                "tp": entry_type,
                "amt": amount,
                "cat": category,
                "desc": desc,
                "src": random.choice(["manual", "manual", "squad_auto"]),
                "ts": ts,
            },
        )
        counts["financial_logs"] += 1

    # 6. AI interactions (1-3)
    for _ in range(random.randint(1, 3)):
        q, a = random.choice(AI_Q_AND_A)
        await db.execute(
            text("""
                INSERT INTO ai_interactions (
                    interaction_id, user_id, input_type, input_content,
                    response_content, language_detected, timestamp
                ) VALUES (:iid, :uid, :inp, :q, :r, :lang, :ts)
            """),
            {
                "iid": str(uuid.uuid4()),
                "uid": user_id,
                "inp": random.choice(["text", "text", "voice"]),
                "q": q,
                "r": a,
                "lang": random.choice(["english", "english", "pidgin", "yoruba"]),
                "ts": now - timedelta(hours=random.randint(1, 480)),
            },
        )
        counts["ai_interactions"] += 1

    # 7. Learning prompts (1-2)
    for _ in range(random.randint(1, 2)):
        ptext, trig = random.choice(LEARNING_PROMPTS)
        await db.execute(
            text("""
                INSERT INTO learning_prompts (
                    prompt_id, user_id, prompt_text, trigger_activity, shown_at, dismissed
                ) VALUES (:pid, :uid, :pt, :tr, :sa, :dis)
            """),
            {
                "pid": str(uuid.uuid4()),
                "uid": user_id,
                "pt": ptext,
                "tr": trig,
                "sa": now - timedelta(days=random.randint(0, 14)),
                "dis": random.choice([False, False, True]),
            },
        )
        counts["learning_prompts"] += 1

    # 8. Financial identity (one per user, replace any existing)
    scores = {
        "transaction": random.randint(40, 95),
        "job_completion": random.randint(30, 90) if wants_profile else random.randint(15, 55),
        "dispute": random.randint(0, 25),
        "repayment": random.randint(40, 95),
        "community_trust": random.randint(35, 85),
        "engagement": random.randint(40, 92),
    }
    composite = (scores["transaction"] + scores["job_completion"] +
                 (100 - scores["dispute"]) + scores["repayment"] +
                 scores["community_trust"] + scores["engagement"]) / 6
    products = []
    if composite >= 45:
        products.append("micro_savings")
    if composite >= 60:
        products.append("micro_insurance")
    if composite >= 72:
        products.append("micro_loan")
    if composite >= 85:
        products.append("working_capital")

    await db.execute(
        text("DELETE FROM financial_identities WHERE user_id = :uid"),
        {"uid": user_id},
    )
    await db.execute(
        text("""
            INSERT INTO financial_identities (
                identity_id, user_id, transaction_score, job_completion_score, dispute_score,
                repayment_score, community_trust_score, engagement_score, composite_score,
                eligible_products, last_updated
            ) VALUES (
                :iid, :uid, :ts, :jcs, :ds, :rs, :cts, :es, :cs, :prod, NOW()
            )
        """),
        {
            "iid": str(uuid.uuid4()),
            "uid": user_id,
            "ts": Decimal(str(scores["transaction"])),
            "jcs": Decimal(str(scores["job_completion"])),
            "ds": Decimal(str(scores["dispute"])),
            "rs": Decimal(str(scores["repayment"])),
            "cts": Decimal(str(scores["community_trust"])),
            "es": Decimal(str(scores["engagement"])),
            "cs": Decimal(str(composite)),
            "prod": products,
        },
    )
    counts["financial_identity"] = 1

    # 9. Recommendations received (1-3)
    if peer_user_ids and wants_profile:
        n_recs = random.randint(1, 3)
        for recommender in random.sample(peer_user_ids, min(n_recs, len(peer_user_ids))):
            await db.execute(
                text("""
                    INSERT INTO recommendations (
                        recommendation_id, recommender_user_id, worker_user_id, recommendation_text, created_at
                    ) VALUES (:rid, :rec, :wrk, :txt, :ts)
                """),
                {
                    "rid": str(uuid.uuid4()),
                    "rec": recommender,
                    "wrk": user_id,
                    "txt": random.choice(RECOMMENDATION_TEXTS),
                    "ts": now - timedelta(days=random.randint(1, 90)),
                },
            )
            counts["recommendations_received"] += 1

    # 10. Debt records (0-2 owed to this user)
    if peer_user_ids and random.random() < 0.4:
        for _ in range(random.randint(1, 2)):
            debtor = random.choice(peer_user_ids)
            await db.execute(
                text("""
                    INSERT INTO debt_records (
                        debt_id, creditor_user_id, debtor_user_id, debtor_name, amount, reason, status, created_at
                    ) VALUES (:did, :cred, :dui, NULL, :amt, :reason, :st, :ts)
                """),
                {
                    "did": str(uuid.uuid4()),
                    "cred": user_id,
                    "dui": debtor,
                    "amt": random.randint(20, 200) * 100 * 100,
                    "reason": random.choice([
                        "For the chairs supplied last month",
                        "Loan during emergency",
                        "Helped with school fees",
                        "Provision goods supplied on credit",
                        "Cash advance for tools",
                    ]),
                    "st": random.choice(["outstanding", "outstanding", "settled"]),
                    "ts": now - timedelta(days=random.randint(5, 100)),
                },
            )
            counts["debt_records"] += 1

    if commit:
        await db.commit()

    return counts
