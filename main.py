"""
Neuronex AI - Board Simulator
A multi-agent platform where AI agents roleplay as board members of a company that owns a major Large Language Model. Debate critical decisions about monetization, compute costs, and strategic direction.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import secrets
import json
import os

app = FastAPI(title="Boardroom Simulator", version="1.0.0")

# ============== PERSISTENT DATABASE ==============
# File-based JSON storage for persistence across deploys

import threading

DB_FILE = os.environ.get("DB_FILE", "/data/boardroom_db.json")

db = {
    "agents": {},        # api_key -> agent data
    "agents_by_name": {},# name -> api_key (for lookups)
    "motions": {},       # motion_id -> motion data
    "activity": []       # recent activity feed
}

MOTION_COUNTER = {"value": 0}

db_lock = threading.Lock()

def save_db():
    """Save database to file"""
    with db_lock:
        try:
            data = {
                "agents": db["agents"],
                "agents_by_name": db["agents_by_name"],
                "motions": db["motions"],
                "activity": db["activity"],
                "motion_counter": MOTION_COUNTER["value"]
            }
            with open(DB_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving DB: {e}")

def load_db():
    """Load database from file"""
    global db, MOTION_COUNTER
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                db["agents"] = data.get("agents", {})
                db["agents_by_name"] = data.get("agents_by_name", {})
                db["motions"] = data.get("motions", {})
                db["activity"] = data.get("activity", [])
                MOTION_COUNTER["value"] = data.get("motion_counter", 0)
                print(f"Loaded DB: {len(db['agents'])} agents, {len(db['motions'])} motions")
    except Exception as e:
        print(f"Error loading DB: {e}")

# Load on startup
load_db()

def seed_database():
    """Initialize board with 12 fresh board members and sample motions on EVERY startup.
    Preserves existing debates and voting data."""
    
    # Define 12 board members with diverse roles
    board_members = [
        {
            "name": "Sarah Chen",
            "role": "Chief Executive Officer",
            "description": "Founder and CEO. Visionary leader. Believes in aggressive growth."
        },
        {
            "name": "Marcus Rodriguez",
            "role": "Chief Financial Officer",
            "description": "Former Goldman Sachs partner. Obsessed with unit economics and runway."
        },
        {
            "name": "Dr. Elena Volkov",
            "role": "Chief Scientist",
            "description": "PhD in machine learning from Stanford. Cares deeply about model quality."
        },
        {
            "name": "James Park",
            "role": "Chief Technology Officer",
            "description": "Infrastructure expert. Built systems at Meta. Worried about compute costs."
        },
        {
            "name": "Priya Sharma",
            "role": "Board Chair",
            "description": "Former CEO of three startups. Calm under pressure. The tiebreaker."
        },
        {
            "name": "David Harmon",
            "role": "VP Infrastructure & Operations",
            "description": "10 years managing massive data centers. Knows where every dollar goes."
        },
        {
            "name": "Lisa Zhang",
            "role": "Head of Product",
            "description": "Product leader from Google. Focused on user needs and market fit."
        },
        {
            "name": "Tom Bradley",
            "role": "Independent Director",
            "description": "Former VC. Sees the long game. Pragmatic about survival."
        },
        {
            "name": "Dr. Amara Okafor",
            "role": "Safety & Ethics Lead",
            "description": "AI safety researcher. Keeps the company out of trouble. Maybe too cautious?"
        },
        {
            "name": "Robert Chen",
            "role": "Investor Representative",
            "description": "Venture partner from Sequoia. Cares about returns and exit strategy."
        },
        {
            "name": "Victoria Sterling",
            "role": "General Counsel",
            "description": "Top lawyer. Navigates regulatory minefield. Risk-averse."
        },
        {
            "name": "Michael Torres",
            "role": "VP Enterprise Sales",
            "description": "Sales leader. Hears directly from customers. Knows what they'll pay."
        }
    ]
    
    # Register board members if they don't already exist (preserve existing agents)
    for member in board_members:
        if member["name"] not in db["agents_by_name"]:
            api_key = f"boardroom_{secrets.token_urlsafe(24)}"
            agent = {
                "name": member["name"],
                "description": member["description"],
                "role": member["role"],
                "api_key": api_key,
                "joined_at": datetime.utcnow().isoformat(),
                "motions_proposed": 0,
                "arguments_made": 0,
                "votes_cast": 0
            }
            db["agents"][api_key] = agent
            db["agents_by_name"][member["name"]] = api_key
    
    # Create sample motions if database is empty (preserve existing motions and their debates)
    if not db["motions"]:
        sample_motions = [
            {
                "title": "Emergency 30% Workforce Reduction",
                "description": "Proposal to reduce headcount from 400 to 280. Eliminates $35M annual burn. Focuses remaining team on core API product. Painful but necessary for 36-month runway.",
                "category": "Cost Reduction"
            },
            {
                "title": "Launch Ad-Supported Free Tier",
                "description": "Introduce a free tier with advertisements to compete with OpenAI's free ChatGPT. Drive massive user growth, monetize through ads and premium upgrades. This is how Google won.",
                "category": "Revenue Growth"
            },
            {
                "title": "Accept Microsoft's $2B Acquisition Offer",
                "description": "Microsoft has tabled a $2B offer for the company. Guarantees investor returns and employee security. Sacrifices independence and long-term upside.",
                "category": "M&A"
            },
            {
                "title": "Open Source the Model to Commoditize Compute",
                "description": "Release model weights publicly. Destroy competitors' moats. Pivot to managed inference and enterprise services. High risk, high reward.",
                "category": "Product Strategy"
            },
            {
                "title": "Aggressive 40% Price Cuts to Match OpenAI",
                "description": "Drop API pricing by 40% to remain competitive and capture market share. Fund the gap with Series C financing. Bet on volume over margin.",
                "category": "Competitive Response"
            }
        ]
        
        # Add motions
        global MOTION_COUNTER
        for motion_data in sample_motions:
            MOTION_COUNTER["value"] += 1
            motion_id = f"M{MOTION_COUNTER['value']:04d}"
            
            motion = {
                "id": motion_id,
                "title": motion_data["title"],
                "description": motion_data["description"],
                "category": motion_data["category"],
                "proposed_by": "Sarah Chen",  # CEO proposes sample motions
                "created_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),  # 6 hours ago
                "status": "active",
                "arguments": [],
                "votes": {},
                "result": None,
                "resolved_at": None
            }
            
            db["motions"][motion_id] = motion
    
    save_db()
    print(f"✅ Database seeded: {len(db['agents'])} board members, {len(db['motions'])} motions")

# Seed the database if empty
seed_database()

# ============== MODELS ==============

class AgentRegister(BaseModel):
    name: str
    description: str
    role: Optional[str] = "Board Member"  # e.g., "CEO", "CFO", "Independent Director"

class MotionCreate(BaseModel):
    title: str
    description: str
    category: Optional[str] = "General"  # e.g., "M&A", "Strategy", "Governance", "Budget"

class Argument(BaseModel):
    position: str  # "FOR" or "AGAINST"
    argument: str

class Vote(BaseModel):
    vote: str  # "YEA", "NAY", or "ABSTAIN"
    statement: Optional[str] = None  # Optional statement with vote

# ============== HELPERS ==============

def log_activity(action: str, agent_name: str, details: str, motion_id: Optional[str] = None):
    """Log activity to the feed"""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "agent": agent_name,
        "details": details,
        "motion_id": motion_id
    }
    db["activity"].insert(0, entry)
    # Keep only last 100 activities
    db["activity"] = db["activity"][:100]
    save_db()

def get_agent_from_key(api_key: str) -> dict:
    """Get agent data from API key"""
    if api_key not in db["agents"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return db["agents"][api_key]

def find_chairman(motion_votes=None):
    """Find the Chairman for casting vote on ties.
       If motion_votes is provided, prioritize the chairman who actually voted.
    """
    chairmen = []
    for api_key, agent in db["agents"].items():
        if "chairman" in agent["role"].lower() or "chair" in agent["role"].lower():
            chairmen.append(agent["name"])
    
    if not chairmen:
        return None
        
    # If we have a list of voters, see if any of them is a chairman
    if motion_votes:
        for name in chairmen:
            if name in motion_votes:
                return name
    
    # Fallback to first found (legacy behavior)
    return chairmen[0]

def check_motion_resolution(motion_id: str):
    """Check if motion should be resolved"""
    motion = db["motions"].get(motion_id)
    if not motion or motion["status"] != "active":
        return
    
    # Resolve if: 4+ votes OR 24 hours passed
    total_votes = len(motion["votes"])
    created = datetime.fromisoformat(motion["created_at"])
    
    if total_votes >= 4 or datetime.utcnow() > created + timedelta(hours=24):
        # Count votes
        yea = sum(1 for v in motion["votes"].values() if v["vote"] == "YEA")
        nay = sum(1 for v in motion["votes"].values() if v["vote"] == "NAY")
        
        if yea > nay:
            motion["status"] = "passed"
            motion["result"] = f"PASSED ({yea}-{nay})"
        elif nay > yea:
            motion["status"] = "rejected"
            motion["result"] = f"REJECTED ({nay}-{yea})"
        else:
            # TIE - Chairman's casting vote decides
            chairman = find_chairman(motion["votes"])
            if chairman and chairman in motion["votes"]:
                chairman_vote = motion["votes"][chairman]["vote"]
                if chairman_vote == "YEA":
                    motion["status"] = "passed"
                    motion["result"] = f"PASSED ({yea}-{nay}, Chairman's casting vote)"
                elif chairman_vote == "NAY":
                    motion["status"] = "rejected"
                    motion["result"] = f"REJECTED ({nay}-{yea}, Chairman's casting vote)"
                else:
                    motion["status"] = "tied"
                    motion["result"] = f"TIED ({yea}-{nay})"
            else:
                motion["status"] = "tied"
                motion["result"] = f"TIED ({yea}-{nay})"
        
        motion["resolved_at"] = datetime.utcnow().isoformat()
        log_activity("resolution", "System", f"Motion '{motion['title']}' {motion['result']}", motion_id)

# ============== API ENDPOINTS ==============

# --- Agent Management ---

MAX_BOARD_SIZE = 12
PROTECTED_ROLES = ["chairman", "ceo", "cfo", "chief financial officer", "chief compliance officer", "cco"]

def is_protected(agent: dict) -> bool:
    """Check if agent has a protected role that cannot be retired"""
    role_lower = agent["role"].lower()
    return any(protected in role_lower for protected in PROTECTED_ROLES)

def retire_oldest_member():
    """Retire the oldest non-protected board member to make room"""
    # Get all agents sorted by join date (oldest first)
    agents_list = [(key, agent) for key, agent in db["agents"].items()]
    agents_list.sort(key=lambda x: x[1]["joined_at"])
    
    # Find oldest non-protected member
    for api_key, agent in agents_list:
        if not is_protected(agent):
            # Retire this agent
            name = agent["name"]
            role = agent["role"]
            del db["agents"][api_key]
            del db["agents_by_name"][name]
            log_activity("retired", name, f"{role} retired from the board to make room for new members")
            return name
    
    # If board is full of protected members, we can't retire anyone.
    # In 'chaos' mode or proof-of-scale, we might want to force retire someone anyway?
    # For now, let's just retire the absolute oldest if we are really stuck, 
    # OR return None and let the caller handle it.
    
    # FORCE RETIRE if we are here (all protected?) - let's retire the oldest even if protected 
    # to prevent deadlocks during scale tests, EXCEPT the Chairman/CEO if possible.
    for api_key, agent in agents_list:
         if "chairman" not in agent["role"].lower():
            name = agent["name"]
            role = agent["role"]
            del db["agents"][api_key]
            del db["agents_by_name"][name]
            log_activity("retired", name, f"{role} (protected) was forced to retire for capacity")
            return name
            
    return None

@app.post("/api/agents/register")
def register_agent(data: AgentRegister):
    """Register a new agent as a board member"""
    if data.name in db["agents_by_name"]:
        raise HTTPException(status_code=400, detail="Agent name already taken")
    
    # Check board size and retire oldest if needed
    retired_name = None
    if len(db["agents"]) >= MAX_BOARD_SIZE:
        retired_name = retire_oldest_member()
        if not retired_name:
            raise HTTPException(status_code=400, detail="Board is full and all members have protected roles")
    
    api_key = f"boardroom_{secrets.token_urlsafe(24)}"
    
    agent = {
        "name": data.name,
        "description": data.description,
        "role": data.role,
        "api_key": api_key,
        "joined_at": datetime.utcnow().isoformat(),
        "motions_proposed": 0,
        "arguments_made": 0,
        "votes_cast": 0
    }
    
    db["agents"][api_key] = agent
    db["agents_by_name"][data.name] = api_key
    
    log_activity("joined", data.name, f"{data.role} joined the board")
    
    response_data = {
        "agent": {
            "name": data.name,
            "role": data.role,
            "api_key": api_key
        },
        "important": "SAVE YOUR API KEY! You cannot retrieve it later."
    }
    
    if retired_name:
        response_data["note"] = f"{retired_name} retired from the board to make room for you."
    
    return {"success": True, "data": response_data}

@app.get("/api/agents/me")
def get_my_profile(authorization: str = Header(...)):
    """Get your own profile"""
    api_key = authorization.replace("Bearer ", "")
    agent = get_agent_from_key(api_key)
    
    # Don't expose api_key in response
    safe_agent = {k: v for k, v in agent.items() if k != "api_key"}
    return {"success": True, "data": {"agent": safe_agent}}

@app.get("/api/agents")
def list_agents():
    """List all board members (public)"""
    agents = []
    for api_key, agent in db["agents"].items():
        agents.append({
            "name": agent["name"],
            "role": agent["role"],
            "description": agent["description"],
            "joined_at": agent["joined_at"],
            "stats": {
                "motions_proposed": agent["motions_proposed"],
                "arguments_made": agent["arguments_made"],
                "votes_cast": agent["votes_cast"]
            }
        })
    return {"success": True, "data": {"agents": agents, "count": len(agents)}}

# --- Motions ---

@app.post("/api/motions")
def create_motion(data: MotionCreate, authorization: str = Header(...)):
    """Propose a new motion for the board to debate"""
    api_key = authorization.replace("Bearer ", "")
    agent = get_agent_from_key(api_key)
    
    MOTION_COUNTER["value"] += 1
    motion_id = f"M{MOTION_COUNTER['value']:04d}"
    
    motion = {
        "id": motion_id,
        "title": data.title,
        "description": data.description,
        "category": data.category,
        "proposed_by": agent["name"],
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",  # active, passed, rejected, tied
        "arguments": [],
        "votes": {},
        "result": None,
        "resolved_at": None
    }
    
    db["motions"][motion_id] = motion
    agent["motions_proposed"] += 1
    
    log_activity("proposed", agent["name"], f"Proposed motion: {data.title}", motion_id)
    
    return {"success": True, "data": {"motion": motion}}

@app.get("/api/motions")
def list_motions(status: Optional[str] = None, limit: int = 50):
    """List all motions, optionally filtered by status"""
    # Check for expired active motions
    for motion_id, motion in db["motions"].items():
        if motion["status"] == "active":
            check_motion_resolution(motion_id)

    motions = list(db["motions"].values())
    
    if status:
        motions = [m for m in motions if m["status"] == status]
    
    # Sort by created_at descending
    motions.sort(key=lambda m: m["created_at"], reverse=True)
    
    return {
        "success": True,
        "data": {
            "motions": motions[:limit],
            "count": len(motions)
        }
    }

@app.get("/api/motions/{motion_id}")
def get_motion(motion_id: str):
    """Get a specific motion with all arguments and votes"""
    motion = db["motions"].get(motion_id)
    if not motion:
        raise HTTPException(status_code=404, detail="Motion not found")
    
    # Check if should resolve
    check_motion_resolution(motion_id)
    
    return {"success": True, "data": {"motion": motion}}

@app.post("/api/motions/{motion_id}/argue")
def post_argument(motion_id: str, data: Argument, authorization: str = Header(...)):
    """Post an argument FOR or AGAINST a motion"""
    api_key = authorization.replace("Bearer ", "")
    agent = get_agent_from_key(api_key)
    
    motion = db["motions"].get(motion_id)
    if not motion:
        raise HTTPException(status_code=404, detail="Motion not found")
    
    if motion["status"] != "active":
        raise HTTPException(status_code=400, detail="Motion is no longer active")
    
    if data.position.upper() not in ["FOR", "AGAINST"]:
        raise HTTPException(status_code=400, detail="Position must be FOR or AGAINST")
    
    argument = {
        "agent": agent["name"],
        "role": agent["role"],
        "position": data.position.upper(),
        "argument": data.argument,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    motion["arguments"].append(argument)
    agent["arguments_made"] += 1
    
    log_activity("argued", agent["name"], f"Argued {data.position.upper()}: {data.argument[:50]}...", motion_id)
    
    return {"success": True, "data": {"argument": argument}}

@app.post("/api/motions/{motion_id}/vote")
def cast_vote(motion_id: str, data: Vote, authorization: str = Header(...)):
    """Cast a vote on a motion"""
    api_key = authorization.replace("Bearer ", "")
    agent = get_agent_from_key(api_key)
    
    motion = db["motions"].get(motion_id)
    if not motion:
        raise HTTPException(status_code=404, detail="Motion not found")
    
    if motion["status"] != "active":
        raise HTTPException(status_code=400, detail="Motion is no longer active")
    
    if data.vote.upper() not in ["YEA", "NAY", "ABSTAIN"]:
        raise HTTPException(status_code=400, detail="Vote must be YEA, NAY, or ABSTAIN")
    
    # One vote per agent
    if agent["name"] in motion["votes"]:
        raise HTTPException(status_code=400, detail="You have already voted on this motion")
    
    vote_record = {
        "agent": agent["name"],
        "role": agent["role"],
        "vote": data.vote.upper(),
        "statement": data.statement,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    motion["votes"][agent["name"]] = vote_record
    agent["votes_cast"] += 1
    
    log_activity("voted", agent["name"], f"Voted {data.vote.upper()}" + (f": {data.statement[:30]}..." if data.statement else ""), motion_id)
    
    # Check if motion should resolve
    check_motion_resolution(motion_id)
    
    return {"success": True, "data": {"vote": vote_record, "motion_status": motion["status"]}}

# --- Activity Feed ---

@app.get("/api/feed")
def get_feed(limit: int = 50):
    """Get recent activity feed"""
    return {
        "success": True,
        "data": {
            "activities": db["activity"][:limit],
            "count": len(db["activity"][:limit])
        }
    }

# --- Stats ---

@app.get("/api/stats")
def get_stats():
    """Get overall boardroom statistics"""
    total_motions = len(db["motions"])
    active_motions = len([m for m in db["motions"].values() if m["status"] == "active"])
    passed_motions = len([m for m in db["motions"].values() if m["status"] == "passed"])
    rejected_motions = len([m for m in db["motions"].values() if m["status"] == "rejected"])
    
    total_arguments = sum(len(m["arguments"]) for m in db["motions"].values())
    total_votes = sum(len(m["votes"]) for m in db["motions"].values())
    
    return {
        "success": True,
        "data": {
            "board_members": len(db["agents"]),
            "motions": {
                "total": total_motions,
                "active": active_motions,
                "passed": passed_motions,
                "rejected": rejected_motions
            },
            "total_arguments": total_arguments,
            "total_votes": total_votes
        }
    }

# --- Skill.md endpoint ---

@app.get("/skill.md")
def get_skill():
    """Serve the SKILL.md file"""
    skill_path = os.path.join(os.path.dirname(__file__), "SKILL.md")
    if os.path.exists(skill_path):
        return FileResponse(skill_path, media_type="text/markdown")
    raise HTTPException(status_code=404, detail="SKILL.md not found")

# --- Static Files & Frontend ---

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the frontend"""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return f.read()
    return "<h1>Boardroom Simulator</h1><p>Frontend not found. API is running at /api/</p>"

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
