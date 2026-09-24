"""
MongoDB Database Service — coordinates connections and handles user progress storage,
quiz logging, exercise submissions, certificate generation, and KPI calculations.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from src.config import settings

# Level definitions metadata for seeding
LEVEL_META = [
    {"level_id": 1, "title": "Blockchain Fundamentals", "total_lessons": 2},
    {"level_id": 2, "title": "Wallet Development",       "total_lessons": 2},
    {"level_id": 3, "title": "Smart Contract Development","total_lessons": 2},
    {"level_id": 4, "title": "DeFi Fundamentals",        "total_lessons": 1},
    {"level_id": 5, "title": "DAO Governance",            "total_lessons": 1},
    {"level_id": 6, "title": "MOR Finance Protocols",    "total_lessons": 1},
    {"level_id": 7, "title": "Ecosystem Track",           "total_lessons": 20},
]

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Any = None

db_instance = Database()

def _ensure_connected():
    """Ensure db_instance.client is active and connected to the current running event loop."""
    needs_connect = False
    if db_instance.client is None or db_instance.db is None:
        needs_connect = True
    else:
        try:
            loop = db_instance.client.get_io_loop()
            if loop.is_closed():
                needs_connect = True
            else:
                import asyncio
                try:
                    current_loop = asyncio.get_running_loop()
                    if loop != current_loop:
                        needs_connect = True
                except RuntimeError:
                    pass
        except Exception:
            needs_connect = True

    if needs_connect:
        db_instance.client = AsyncIOMotorClient(settings.mongodb_uri)
        db_name = "devjobs"
        if "/" in settings.mongodb_uri.split("://")[1]:
            path = settings.mongodb_uri.split("://")[1].split("/")[1]
            if "?" in path:
                db_name = path.split("?")[0]
            elif path:
                db_name = path
        db_instance.db = db_instance.client[db_name]

def get_collection():
    """Retrieve the primary user data collection."""
    _ensure_connected()
    return db_instance.db["developer_academy_users"]

def get_forum_collection():
    """Retrieve the forum threads collection."""
    _ensure_connected()
    return db_instance.db["developer_academy_forum"]

def get_hackathons_collection():
    """Retrieve the hackathons collection."""
    _ensure_connected()
    return db_instance.db["developer_academy_hackathons"]

async def connect_to_mongo():
    """Initialize the MongoDB client connection."""
    print("🔌 Connecting to MongoDB...")
    db_instance.client = AsyncIOMotorClient(settings.mongodb_uri)
    # Parse DB name from URI (falls back to 'devjobs' or 'developer_academy')
    db_name = "devjobs"
    if "/" in settings.mongodb_uri.split("://")[1]:
        path = settings.mongodb_uri.split("://")[1].split("/")[1]
        if "?" in path:
            db_name = path.split("?")[0]
        elif path:
            db_name = path
    db_instance.db = db_instance.client[db_name]
    print(f"✅ Connected to MongoDB. Database: '{db_name}'")
    # A given testnet transaction hash should only ever count once, no matter who submits it.
    await db_instance.db["developer_academy_leaderboard"].create_index("txHash", unique=True)
    # Aggregated job postings are de-duplicated by canonical URL / title+company key.
    await db_instance.db["developer_academy_jobs"].create_index("urlKey", unique=True, sparse=True)
    await db_instance.db["developer_academy_jobs"].create_index("keys")
    # await seed_forum_threads()
    # await seed_hackathons()


async def close_mongo_connection():
    """Close the MongoDB client connection."""
    if db_instance.client:
        db_instance.client.close()
        db_instance.client = None
        db_instance.db = None
        print("🛑 Closed MongoDB connection.")

def get_leaderboard_collection():
    """Retrieve the leaderboard submissions collection."""
    _ensure_connected()
    return db_instance.db["developer_academy_leaderboard"]

def get_jobs_collection():
    """Retrieve the aggregated job postings collection."""
    _ensure_connected()
    return db_instance.db["developer_academy_jobs"]

def get_aggregator_state_collection():
    """Retrieve the aggregator run-lock / last-result state collection."""
    _ensure_connected()
    return db_instance.db["developer_academy_aggregator_state"]

def build_user_levels(active_track: str, completed_ids: List[str]):
    t_id = (active_track or "fundamentals").lower().strip()
    from src.services.lessons import LESSONS_DB, get_track_lessons
    
    computed_levels = []
    
    if t_id == "fundamentals":
        gen_levels_meta = [
            (1, "Blockchain Fundamentals & Web3 Core"),
            (2, "Smart Contract Architecture"),
            (3, "Token Standards & Asset Engineering"),
            (4, "Protocol Security & Vulnerability Audits"),
            (5, "DeFi Fundamentals & Liquidity Mechanics"),
            (6, "MOR Finance Protocols & Governance"),
        ]
        for lvl_id, title in gen_levels_meta:
            lvl_lessons = [l for l in LESSONS_DB.values() if l.level_id == lvl_id]
            completed_cnt = sum(1 for l in lvl_lessons if l.id in completed_ids)
            computed_levels.append({
                "level_id": lvl_id,
                "title": title,
                "total_lessons": len(lvl_lessons),
                "completed_lessons": completed_cnt,
                "is_unlocked": False,
                "completed_at": datetime.now(timezone.utc) if completed_cnt >= len(lvl_lessons) and len(lvl_lessons) > 0 else None
            })
    else:
        if t_id in ("polkadot", "substrate"):
            chain_name = "Polkadot / Substrate"
        elif t_id == "fullstack":
            chain_name = "Full Stack Web3"
        else:
            chain_name = t_id.capitalize()
        t_lessons = get_track_lessons(t_id)
        
        chain_levels_meta = [
            (1, f"{chain_name} Architecture & Core Principles", [t_lessons[0]] if len(t_lessons) > 0 else []),
            (2, f"{chain_name} Environment Setup & Tooling", [t_lessons[1]] if len(t_lessons) > 1 else []),
            (3, f"{chain_name} Starter Project 1 (GitHub Repo)", [t_lessons[2]] if len(t_lessons) > 2 else []),
            (4, f"{chain_name} Starter Project 2 (Full-Stack DApp)", [t_lessons[3]] if len(t_lessons) > 3 else []),
            (5, f"{chain_name} Capstone & Testnet Deployment", [t_lessons[4]] if len(t_lessons) > 4 else []),
        ]
        for lvl_id, title, lvl_lessons in chain_levels_meta:
            completed_cnt = sum(1 for l in lvl_lessons if l.id in completed_ids)
            computed_levels.append({
                "level_id": lvl_id,
                "title": title,
                "total_lessons": len(lvl_lessons),
                "completed_lessons": completed_cnt,
                "is_unlocked": False,
                "completed_at": datetime.now(timezone.utc) if completed_cnt >= len(lvl_lessons) and len(lvl_lessons) > 0 else None
            })
            
    for i in range(len(computed_levels)):
        if i == 0:
            computed_levels[i]["is_unlocked"] = True
        else:
            prev = computed_levels[i-1]
            if prev["completed_lessons"] >= prev["total_lessons"] and prev["total_lessons"] > 0:
                computed_levels[i]["is_unlocked"] = True

    total_lessons_curriculum = sum(l["total_lessons"] for l in computed_levels)
    total_completed_lessons = sum(l["completed_lessons"] for l in computed_levels)
    overall_pct = round(total_completed_lessons / total_lessons_curriculum * 100, 1) if total_lessons_curriculum > 0 else 0.0

    return computed_levels, overall_pct

def create_default_user_dict(user_id: str, auth_type: str) -> Dict[str, Any]:
    """Generate the initial schema for a new user."""
    completed_ids: List[str] = []
    levels, overall_pct = build_user_levels("fundamentals", completed_ids)
    return {
        "_id": user_id,
        "user_id": user_id,
        "auth_type": auth_type,
        "xp": 0,
        "streak_days": 1,
        "current_level": 1,
        "overall_pct": overall_pct,
        "active_track": "fundamentals",
        "levels": levels,
        "last_active": datetime.now(timezone.utc),
        "registered_at": datetime.now(timezone.utc),
        "certificates": [],
        "quiz_attempts": [],
        "exercises_submitted": [],
        "github_activities": [],
        "mentor_chat_sessions": [],
        "hackathons_registered": [],
        "hackathon_submissions": {},
        "deployed_contracts": [],
        "deployed_contracts_count": 0
    }

async def get_or_create_user(user_id: str, auth_type: str = "demo") -> Dict[str, Any]:
    """Retrieve an existing user by direct ID, linked GitHub, or linked wallet, or create one if not found."""
    coll = get_collection()
    
    # 1. Try finding by matching _id directly
    user = await coll.find_one({"_id": user_id})
    
    # 2. If not found, try searching on linked fields
    if not user:
        if user_id.startswith("wallet-"):
            addr = user_id.replace("wallet-", "").lower()
            user = await coll.find_one({"wallet_address": addr})
        elif user_id.startswith("gh-"):
            uname = user_id.replace("gh-", "")
            user = await coll.find_one({"github_username": uname})
            
    # 3. Create if still not found
    if not user:
        user = create_default_user_dict(user_id, auth_type)
        if user_id.startswith("wallet-"):
            user["wallet_address"] = user_id.replace("wallet-", "").lower()
        elif user_id.startswith("gh-"):
            user["github_username"] = user_id.replace("gh-", "")
        await coll.insert_one(user)
    else:
        # Backward compatibility / link updates
        updated = False
        updates = {}
        if "hackathons_registered" not in user:
            user["hackathons_registered"] = []
            updates["hackathons_registered"] = []
            updated = True
        if "hackathon_submissions" not in user:
            user["hackathon_submissions"] = {}
            updates["hackathon_submissions"] = {}
            updated = True
        if user_id.startswith("wallet-") and "wallet_address" not in user:
            user["wallet_address"] = user_id.replace("wallet-", "").lower()
            updates["wallet_address"] = user_id.replace("wallet-", "").lower()
            updated = True
        elif user_id.startswith("gh-") and "github_username" not in user:
            user["github_username"] = user_id.replace("gh-", "")
            updates["github_username"] = user_id.replace("gh-", "")
            updated = True
        if "active_track" not in user:
            user["active_track"] = "fundamentals"
            updates["active_track"] = "fundamentals"
            updated = True

        # Build dynamic levels matching active track
        completed_ids = user.get("completed_lesson_ids", [])
        track = user.get("active_track", "fundamentals")
        levels_list, overall_pct = build_user_levels(track, completed_ids)
        
        user["levels"] = levels_list
        user["overall_pct"] = overall_pct
        updates["levels"] = levels_list
        updates["overall_pct"] = overall_pct
        updated = True

        if updated:
            await coll.update_one({"_id": user["_id"]}, {"$set": updates})
            
    return user

async def save_user_progress(user_id: str, progress_update: Dict[str, Any]):
    """Update progress metrics in the user document."""
    coll = get_collection()
    await coll.update_one(
        {"_id": user_id},
        {"$set": progress_update}
    )

async def log_quiz_attempt(user_id: str, lesson_id: str, score: float, level_id: int):
    """Add a quiz completion record and award XP."""
    coll = get_collection()
    attempt = {
        "lesson_id": lesson_id,
        "level_id": level_id,
        "score": score,
        "attempted_at": datetime.now(timezone.utc)
    }
    
    # Fetch user to calculate XP reward (e.g. 50 XP for completing a quiz)
    user = await get_or_create_user(user_id)
    # Check if they already attempted this lesson's quiz
    previous_attempt = next((q for q in user.get("quiz_attempts", []) if q["lesson_id"] == lesson_id), None)
    xp_to_add = 0
    if not previous_attempt and score >= 70.0: # passed
        xp_to_add = 50

    await coll.update_one(
        {"_id": user_id},
        {
            "$push": {"quiz_attempts": attempt},
            "$inc": {"xp": xp_to_add},
            "$set": {"last_active": datetime.now(timezone.utc)}
        }
    )
    if score >= 70.0:
        await complete_lesson_for_user(user_id, level_id, lesson_id)

async def log_exercise_submission(user_id: str, lesson_id: str, code: str, passed: bool, level_id: int):
    """Add a coding exercise submission record and award XP."""
    coll = get_collection()
    submission = {
        "lesson_id": lesson_id,
        "level_id": level_id,
        "code": code,
        "passed": passed,
        "submitted_at": datetime.now(timezone.utc)
    }
    
    # Fetch user to check if this is their first passed attempt for this exercise
    user = await get_or_create_user(user_id)
    previous_pass = next((s for s in user.get("exercises_submitted", []) if s["lesson_id"] == lesson_id and s["passed"]), None)
    xp_to_add = 0
    if not previous_pass and passed:
        xp_to_add = 100 # 100 XP for coding exercise completion

    await coll.update_one(
        {"_id": user_id},
        {
            "$push": {"exercises_submitted": submission},
            "$inc": {"xp": xp_to_add},
            "$set": {"last_active": datetime.now(timezone.utc)}
        }
    )
    if passed:
        await complete_lesson_for_user(user_id, level_id, lesson_id)

async def issue_certificate(user_id: str, level_id: int, title: str, track_id: Optional[str] = None):
    """Issue a completed course / level certificate."""
    coll = get_collection()
    
    # Check if certificate already exists
    user = await get_or_create_user(user_id)
    resolved_track = track_id or user.get("active_track", "fundamentals")
    
    # Prevent duplicate certificate for the same track or exact level title
    exists = any(
        c.get("track_id") == resolved_track or 
        (c.get("level_id") == level_id and c.get("level_title") == title)
        for c in user.get("certificates", [])
    )
    if exists:
        return

    cert = {
        "certificate_id": f"cert-{resolved_track}-{level_id}-{int(datetime.now(timezone.utc).timestamp())}",
        "track_id": resolved_track,
        "level_id": level_id,
        "level_title": title,
        "issued_at": datetime.now(timezone.utc),
        "recipient": user_id
    }
    await coll.update_one(
        {"_id": user_id},
        {"$push": {"certificates": cert}}
    )

async def log_github_activity(user_id: str, message: str, commit_sha: str):
    """Log simulated or fetched Github activity."""
    coll = get_collection()
    activity = {
        "commit_sha": commit_sha,
        "message": message,
        "committed_at": datetime.now(timezone.utc)
    }
    await coll.update_one(
        {"_id": user_id},
        {
            "$push": {"github_activities": activity},
            "$set": {"last_active": datetime.now(timezone.utc)}
        }
    )

async def log_mentor_chat(user_id: str, session_id: str):
    """Update AI mentor chat interactions logs."""
    coll = get_collection()
    user = await get_or_create_user(user_id)
    sessions = user.get("mentor_chat_sessions", [])
    
    existing = next((s for s in sessions if s["session_id"] == session_id), None)
    if existing:
        await coll.update_one(
            {"_id": user_id, "mentor_chat_sessions.session_id": session_id},
            {
                "$inc": {"mentor_chat_sessions.$.messages_count": 1},
                "$set": {
                    "mentor_chat_sessions.$.last_chat_at": datetime.now(timezone.utc),
                    "last_active": datetime.now(timezone.utc)
                }
            }
        )
    else:
        new_session = {
            "session_id": session_id,
            "messages_count": 1,
            "last_chat_at": datetime.now(timezone.utc)
        }
        await coll.update_one(
            {"_id": user_id},
            {
                "$push": {"mentor_chat_sessions": new_session},
                "$set": {"last_active": datetime.now(timezone.utc)}
            }
        )

async def get_kpis() -> Dict[str, Any]:
    """Aggregate core metrics across the entire developer_academy_users collection."""
    coll = get_collection()
    
    # 1. Registered Users
    registered_users = await coll.count_documents({})
    
    # 2. Active Learners (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_learners = await coll.count_documents({"last_active": {"$gte": seven_days_ago}})
    
    # 3. Course Completions (Users with overall_pct >= 100%)
    course_completions = await coll.count_documents({"overall_pct": {"$gte": 100.0}})
    
    # 4. Quiz Scores (Average of all passing quiz attempts)
    pipeline_quizzes = [
        {"$unwind": "$quiz_attempts"},
        {"$group": {"_id": None, "avg_score": {"$avg": "$quiz_attempts.score"}}}
    ]
    cursor_quizzes = coll.aggregate(pipeline_quizzes)
    quizzes_res = await cursor_quizzes.to_list(length=1)
    avg_quiz_score = round(quizzes_res[0]["avg_score"], 1) if quizzes_res else 0.0
    
    # 5. Coding Exercises Submitted (Total count)
    pipeline_exercises = [
        {"$project": {"count": {"$size": {"$ifNull": ["$exercises_submitted", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]
    cursor_exercises = coll.aggregate(pipeline_exercises)
    exercises_res = await cursor_exercises.to_list(length=1)
    coding_exercises = exercises_res[0]["total"] if exercises_res else 0
    
    # 6. Certificates Generated (Total count)
    pipeline_certs = [
        {"$project": {"count": {"$size": {"$ifNull": ["$certificates", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]
    cursor_certs = coll.aggregate(pipeline_certs)
    certs_res = await cursor_certs.to_list(length=1)
    certificates_issued = certs_res[0]["total"] if certs_res else 0
    
    # 7. GitHub Activity (Total count)
    pipeline_github = [
        {"$project": {"count": {"$size": {"$ifNull": ["$github_activities", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]
    cursor_github = coll.aggregate(pipeline_github)
    github_res = await cursor_github.to_list(length=1)
    github_activity = github_res[0]["total"] if github_res else 0
    
    # 8. AI Mentor Sessions (Total sessions count)
    pipeline_sessions = [
        {"$project": {"count": {"$size": {"$ifNull": ["$mentor_chat_sessions", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]
    cursor_sessions = coll.aggregate(pipeline_sessions)
    sessions_res = await cursor_sessions.to_list(length=1)
    ai_mentor_sessions = sessions_res[0]["total"] if sessions_res else 0
    
    # 9. Deployed Smart Contracts (Total count)
    pipeline_deployments = [
        {"$project": {"count": {"$size": {"$ifNull": ["$deployed_contracts", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]
    cursor_deployments = coll.aggregate(pipeline_deployments)
    deployments_res = await cursor_deployments.to_list(length=1)
    db_deployments = deployments_res[0]["total"] if deployments_res else 0
    try:
        from src.api.arbitrum import SEEDED_DEPLOYMENTS
        seeded_deps = len(SEEDED_DEPLOYMENTS)
    except Exception:
        seeded_deps = 0
    total_deployed_contracts = max(db_deployments, seeded_deps)

    return {
        "registered_users": registered_users,
        "active_learners": active_learners,
        "course_completion": course_completions,
        "avg_quiz_score": avg_quiz_score,
        "coding_exercises": coding_exercises,
        "certificates_issued": certificates_issued,
        "github_activity": github_activity,
        "ai_mentor_sessions": ai_mentor_sessions,
        "deployed_contracts": total_deployed_contracts
    }



async def complete_lesson_for_user(user_id: str, level_id: int, lesson_id: str):
    """
    Mark a lesson as completed for the user, update completed_lessons counts per level,
    recalculate overall_pct, unlock next levels, and issue certificates.
    """
    coll = get_collection()
    user = await get_or_create_user(user_id)
    
    # We will track completed lesson ids in a field `completed_lesson_ids`.
    completed_ids = user.get("completed_lesson_ids", [])
    if lesson_id not in completed_ids:
        completed_ids.append(lesson_id)
    
    # Recalculate level progress dynamically based on active_track
    active_track = user.get("active_track", "fundamentals")
    levels, overall_pct = build_user_levels(active_track, completed_ids)
    
    # Find current level: highest unlocked level
    unlocked_levels = [lvl["level_id"] for lvl in levels if lvl["is_unlocked"]]
    current_level = max(unlocked_levels) if unlocked_levels else 1
    
    # Update fields in DB
    await coll.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "completed_lesson_ids": completed_ids,
                "levels": levels,
                "overall_pct": overall_pct,
                "current_level": current_level,
                "last_active": datetime.now(timezone.utc)
            }
        }
    )
    
    # Certificates are ONLY conferred once the user finishes the course (100% of track modules completed)!
    total_lessons_in_track = sum(l.get("total_lessons", 0) for l in levels)
    completed_lessons_in_track = sum(l.get("completed_lessons", 0) for l in levels)
    track_fully_completed = total_lessons_in_track > 0 and completed_lessons_in_track >= total_lessons_in_track

    if track_fully_completed:
        track_display = {
            "aptos": "Aptos Move Certified Developer",
            "starknet": "Starknet Cairo & ZK Certified Developer",
            "solana": "Solana Anchor Certified Developer",
            "polkadot": "Polkadot & Substrate Certified Developer",
            "substrate": "Polkadot & Substrate Certified Developer",
            "fundamentals": "EVM Smart Contract Security Specialist",
            "ethereum": "EVM Smart Contract Security Specialist",
            "fullstack": "Full Stack Blockchain Developer"
        }.get(active_track.lower(), f"{active_track.capitalize()} Certified Developer")
        
        await issue_certificate(user_id, level_id, track_display, track_id=active_track.lower())
        
    return await get_or_create_user(user_id)

async def seed_forum_threads():
    """Seed initial official threads for the Developer Academy community forum."""
    coll = get_forum_collection()
    await coll.delete_many({})
    print("🌱 Seeding official forum threads in MongoDB...")
    threads = [
        {
            "_id": "thread-1",
            "thread_id": "thread-1",
            "title": "Welcome to MOR Developer Academy Community Forum",
            "author": "@mor_academy",
            "category": "Announcement",
            "content": "Welcome to the MOR Developer Academy community forum! This is the official space to ask questions, share insights, collaborate on smart contract exercises, and discuss Web3 engineering across Arbitrum, Base, Optimism, Solana, Aptos, and Polkadot. Review the guidelines on the right and feel free to start a new discussion.",
            "tags": ["welcome", "community", "announcement", "guidelines"],
            "replies_count": 0,
            "views_count": 0,
            "likes_count": 0,
            "created_at": "2026-08-20T08:00:00Z",
            "comments": []
        },
        {
            "_id": "thread-2",
            "thread_id": "thread-2",
            "title": "Kenyatta University Cohort (KU_COHORT_2026_01) Discussion & Resources",
            "author": "@mor_academy",
            "category": "Discussion",
            "content": "Official discussion channel for Kenyatta University cohort students (KU_COHORT_2026_01). Use this thread to coordinate on multi-chain curriculum exercises, office hours, and technical questions.",
            "tags": ["university", "cohort", "discussion", "resources"],
            "replies_count": 0,
            "views_count": 0,
            "likes_count": 0,
            "created_at": "2026-08-22T10:00:00Z",
            "comments": []
        },
        {
            "_id": "thread-3",
            "thread_id": "thread-3",
            "title": "Multi-Chain Sandbox IDE & Compiler Feedback",
            "author": "@mor_academy",
            "category": "Question",
            "content": "Have questions or feedback on compiling smart contracts with the Multi-Chain Sandbox IDE? Share your code snippets, gas optimization questions, or compiler suggestions here.",
            "tags": ["sandbox", "compiler", "solidity", "rust", "feedback"],
            "replies_count": 0,
            "views_count": 0,
            "likes_count": 0,
            "created_at": "2026-08-24T14:00:00Z",
            "comments": []
        }
    ]
    await coll.insert_many(threads)
    print("🌱 Official forum threads seeded successfully.")

async def seed_hackathons():
    """Seed initial hackathons in MongoDB."""
    coll = get_hackathons_collection()
    await coll.delete_many({})
    print("🌱 Seeding hackathons in MongoDB...")
    hacks = [
            {
                "_id": "hack-1",
                "hackathon_id": "hack-1",
                "title": "MOR Finance DeFi Innovation Hack",
                "description": "Build the next generation of DeFi protocols that solve real-world problems. Build protocols, yield optimizers, or dApps that advance the DeFi ecosystem.",
                "prize_pool": "$25,000",
                "start_date": "2026-08-15",
                "end_date": "2026-08-17",
                "status": "ongoing",
                "ecosystems": ["Ethereum", "Arbitrum", "Optimism"],
                "rules": [
                    "Teams can have 1 to 5 members.",
                    "Code must be submitted on a public GitHub repo before the deadline.",
                    "All smart contracts must be deployed to a testnet.",
                    "Include a 3-minute video presentation."
                ],
                "tracks": ["DeFi Protocols", "Yield Optimization", "Lending & Borrowing", "Derivatives"],
                "milestones": [
                    {"title": "Registration Opens", "date": "2026-07-15"},
                    {"title": "Registration Closes", "date": "2026-08-14"},
                    {"title": "Hackathon Starts", "date": "2026-08-15 9:00 AM UTC"},
                    {"title": "Hackathon Ends", "date": "2026-08-17 9:00 AM UTC"},
                    {"title": "Winners Announced", "date": "2026-08-20"}
                ]
            },
            {
                "_id": "hack-2",
                "hackathon_id": "hack-2",
                "title": "MOR Agentic AI Hackathon",
                "description": "Build autonomous AI agents that run on top of Morpheus decentralized compute networks. Design custom agent logic, wallets, or inference pools.",
                "prize_pool": "$50,000",
                "start_date": "2026-08-25",
                "end_date": "2026-08-28",
                "status": "ongoing",
                "ecosystems": ["Solana", "Arbitrum", "Base"],
                "rules": [
                    "Must be fully functional on testnet.",
                    "Must include integration with Morpheus smart contracts.",
                    "Open to teams of up to 4 members."
                ],
                "tracks": ["AI Agent Logic", "Compute Proofs", "Agent Wallets"],
                "milestones": [
                    {"title": "Registration Opens", "date": "2026-08-01"},
                    {"title": "Hackathon Starts", "date": "2026-08-25"},
                    {"title": "Hackathon Ends", "date": "2026-08-28"}
                ]
            },
            {
                "_id": "hack-3",
                "hackathon_id": "hack-3",
                "title": "Base Build in Public Hack",
                "description": "Create consumer dApps on Base. Focus on social integrations, identity, or gaming tools that leverage Base layer-2 scaling.",
                "prize_pool": "$20,000",
                "start_date": "2026-08-01",
                "end_date": "2026-08-10",
                "status": "ongoing",
                "ecosystems": ["Base", "Optimism"],
                "rules": [
                    "Must deploy to Base Goerli / Sepolia.",
                    "Project must be open source."
                ],
                "tracks": ["Social dApps", "Consumer Tech", "NFTs & Gaming"],
                "milestones": [
                    {"title": "Hackathon Starts", "date": "2026-08-01"},
                    {"title": "Hackathon Ends", "date": "2026-08-10"}
                ]
            },
            {
                "_id": "hack-4",
                "hackathon_id": "hack-4",
                "title": "Web3 Student Challenge",
                "description": "A beginner-friendly hackathon for students worldwide to build dApps using HTML, CSS, JavaScript, and Solidity.",
                "prize_pool": "$15,000",
                "start_date": "2026-09-01",
                "end_date": "2026-09-15",
                "status": "upcoming",
                "ecosystems": ["Polygon", "Base", "Solana"],
                "rules": [
                    "Must be a student or recent graduate.",
                    "Individual submissions only.",
                    "Submission must be fully functional."
                ],
                "tracks": ["Social dApps", "NFTs & Gaming", "Public Goods"],
                "milestones": [
                    {"title": "Registration Opens", "date": "2026-08-01"},
                    {"title": "Hackathon Starts", "date": "2026-09-01"},
                    {"title": "Hackathon Ends", "date": "2026-09-15"}
                ]
            },
            {
                "_id": "hack-5",
                "hackathon_id": "hack-5",
                "title": "NFT Builders Jam",
                "description": "Focus on building new NFT utility, dynamic metadata, or gaming assets using the ERC-721 and ERC-1155 standards.",
                "prize_pool": "$10,000",
                "start_date": "2026-09-20",
                "end_date": "2026-09-22",
                "status": "upcoming",
                "ecosystems": ["Avalanche", "Solana", "Ethereum"],
                "rules": [
                    "Open to anyone.",
                    "Up to 3 members per team.",
                    "Must use ERC-721A or custom ERC-1155."
                ],
                "tracks": ["NFT Utilities", "On-chain Games", "Dynamic Metadata"],
                "milestones": [
                    {"title": "Registration Opens", "date": "2026-08-20"},
                    {"title": "Hackathon Starts", "date": "2026-09-20"},
                    {"title": "Hackathon Ends", "date": "2026-09-22"}
                ]
            },
            {
                "_id": "hack-6",
                "hackathon_id": "hack-6",
                "title": "Arbitrum Orbit Hyperchain Jam",
                "description": "Deploy Orbit chains and build high-frequency DeFi applications on custom execution layer-3 nodes.",
                "prize_pool": "$40,000",
                "start_date": "2026-06-10",
                "end_date": "2026-06-12",
                "status": "completed",
                "ecosystems": ["Arbitrum"],
                "rules": [
                    "Must deploy a custom Orbit node.",
                    "Submission must include throughput metric charts."
                ],
                "tracks": ["Orbit Deployments", "Custom Gas Tokens", "Layer 3 Apps"],
                "milestones": [
                    {"title": "Hackathon Starts", "date": "2026-06-10"},
                    {"title": "Winners Announced", "date": "2026-06-15"}
                ]
            },
            {
                "_id": "hack-7",
                "hackathon_id": "hack-7",
                "title": "Solana Speedrun Game Jam",
                "description": "Build fast, on-chain games using Anchor, Rust, and Solana high-throughput transactions.",
                "prize_pool": "$30,000",
                "start_date": "2026-05-15",
                "end_date": "2026-05-17",
                "status": "completed",
                "ecosystems": ["Solana"],
                "rules": [
                    "Open-source Rust programs.",
                    "Must include a playable web build."
                ],
                "tracks": ["On-chain Arcade", "Dynamic Game State", "Solana Composability"],
                "milestones": [
                    {"title": "Hackathon Starts", "date": "2026-05-15"},
                    {"title": "Winners Announced", "date": "2026-05-20"}
                ]
            }
        ]
    await coll.insert_many(hacks)
    print("🌱 Seeding hackathons complete.")

