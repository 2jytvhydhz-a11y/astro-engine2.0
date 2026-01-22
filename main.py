# main.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional, Union

import swisseph as swe
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Astro Engine", version="2.0")

# --- Middleware (simple request logging) ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    print(f"[REQ] {request.method} {request.url.path} origin={origin}")
    response = await call_next(request)
    print(f"[RES] {request.method} {request.url.path} -> {response.status_code}")
    return response

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # OK for now; later you can restrict to Lovable domain(s)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Swiss Ephemeris setup ---
# If you bundle ephemeris files in the image (or download them), point here.
swe.set_ephe_path(".")
# Use UT calculations
SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def zodiac_sign(longitude: float) -> str:
    longitude = longitude % 360.0
    return SIGNS[int(longitude // 30)]

def deg_in_sign(longitude: float) -> float:
    longitude = longitude % 360.0
    return round(longitude % 30.0, 2)

def parse_datetime(date: str, time: str) -> datetime:
    try:
        return datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid date/time format. Use YYYY-MM-DD and HH:MM",
        )

def julian_day_utc(dt: datetime) -> float:
    # We treat provided time as UTC for now (simple + consistent).
    # If you later add timezone handling, convert to UTC before calling this.
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

PLANETS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
}

# --- API: health / root ---
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {
        "ok": True,
        "try": "/docs",
        "example": "/chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5",
    }

# --- API: Chart ---
@app.get("/chart")
def calculate_chart(date: str, time: str, lat: float, lon: float):
    # basic validation
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=422, detail="lat/lon out of range")

    dt = parse_datetime(date, time)
    jd = julian_day_utc(dt)

    planets_out: Dict[str, Dict[str, Any]] = {}

    try:
        for key, p in PLANETS.items():
            xx, _ = swe.calc_ut(jd, p, SWE_FLAGS)
            lon_p = float(xx[0])
            planets_out[key] = {
                "longitude": round(lon_p, 6),
                "sign": zodiac_sign(lon_p),
                "degree": deg_in_sign(lon_p),
            }

        # Houses + Ascendant
        houses, ascmc = swe.houses(jd, lat, lon)
        asc_lon = float(ascmc[0])
        asc = {
            "longitude": round(asc_lon, 6),
            "sign": zodiac_sign(asc_lon),
            "degree": deg_in_sign(asc_lon),
        }

        # Optional: return houses cusps (1..12)
        house_cusps = {str(i + 1): round(float(houses[i]), 6) for i in range(12)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SwissEphemeris error: {str(e)}")

    return {
        "planets": planets_out,
        "ascendant": asc,
        "houses": house_cusps,
    }

# --- Readings ---
class ReadingRequest(BaseModel):
    birth_profile: Dict[str, Any] = Field(default_factory=dict)
    topic: str = "general"

def safe_get_sign(planets: Any, key: str, fallback: str = "Unknown") -> str:
    # supports:
    # planets["sun"] = {"sign": "Capricorn", ...}
    if isinstance(planets, dict):
        v = planets.get(key)
        if isinstance(v, dict):
            return v.get("sign") or fallback
    return fallback

def safe_get_degree(planets: Any, key: str) -> Optional[float]:
    if isinstance(planets, dict):
        v = planets.get(key)
        if isinstance(v, dict):
            d = v.get("degree")
            try:
                return float(d) if d is not None else None
            except Exception:
                return None
    return None

def safe_get_asc(chart: Any) -> Dict[str, Any]:
    # supports:
    # chart["ascendant"] = {"sign": "...", "degree": ...}
    # or chart["ascendant"] = "Libra"
    if isinstance(chart, dict):
        a = chart.get("ascendant")
        if isinstance(a, dict):
            return {
                "sign": a.get("sign") or "Unknown",
                "degree": a.get("degree"),
            }
        if isinstance(a, str):
            return {"sign": a, "degree": None}
    return {"sign": "Unknown", "degree": None}

def format_reading(
    title: str,
    core: str,
    strength: str,
    challenge: str,
    practical: str,
    reflection: str,
) -> str:
    # keep the “authorized style” structure
    return f"""{title}

CORE THEME
{core}

YOUR STRENGTH
{strength}

YOUR CHALLENGE
{challenge}

PRACTICAL FOCUS (Today / This Week)
{practical}

REFLECTION
{reflection}
""".strip()

@app.post("/readings")
def generate_reading(data: ReadingRequest):
    birth_profile = data.birth_profile or {}
    chart = (birth_profile.get("chart") or {})
    planets = (chart.get("planets") or {})

    # Core trio
    sun = safe_get_sign(planets, "sun")
    moon = safe_get_sign(planets, "moon")
    asc_obj = safe_get_asc(chart)
    asc = asc_obj.get("sign") or "Unknown"

    # Key personalizers (planets that change the “who you are” feel)
    mercury = safe_get_sign(planets, "mercury")
    venus = safe_get_sign(planets, "venus")
    mars = safe_get_sign(planets, "mars")
    jupiter = safe_get_sign(planets, "jupiter")
    saturn = safe_get_sign(planets, "saturn")

    topic = (data.topic or "").lower().strip() or "general"

    # --- TOPICS (12 total) ---
    if topic == "love":
        text = format_reading(
            "LOVE & RELATIONSHIPS — Your Pattern",
            f"Sun in {sun} sets your standards in love. Moon in {moon} reveals what you emotionally *need* to feel safe. "
            f"Ascendant {asc} shapes what you attract — and what people project onto you. "
            f"Venus in {venus} shows how you bond, while Mars in {mars} shows how you pursue, react, and protect your heart.",
            "You don’t do casual halfway. When you choose, you invest deeply. You notice micro-signals, patterns, shifts — and you remember them. "
            "That makes you intensely loyal when trust is real.",
            "Your intensity can turn into silent testing: waiting for proof instead of asking for clarity. If emotional safety wobbles, you may withdraw, control, or go cold — "
            "even while you still care a lot.",
            "This week: say one need plainly (one sentence). Don’t hint. Don’t test. Make it simple and direct. "
            "Choose calm consistency over emotional spikes.",
            "Ask: ‘Am I responding to the person in front of me — or to an old wound that feels familiar?’",
        )

    elif topic == "relationships":
        text = format_reading(
            "RELATIONSHIPS — How You Attach",
            f"Sun {sun} sets the identity you bring into partnership. Moon {moon} sets your emotional rhythm. "
            f"Ascendant {asc} shapes your first dynamic: how closeness starts. Venus {venus} and Saturn {saturn} show what you need to trust and commit.",
            "You build bonds that can last. You prefer depth over noise. When you’re in, you show up — especially when it matters.",
            "Your challenge is not letting fear drive the strategy. When you feel uncertainty, you can tighten the grip or disappear emotionally. "
            "Both create distance exactly when you want closeness.",
            "Make one ‘repair habit’: if there’s tension, name it within 24h in a calm message. No lecture. Just truth + a next step.",
            "Ask: ‘What do I need to hear — and have I actually asked for it?’",
        )

    elif topic == "career":
        text = format_reading(
            "CAREER & DIRECTION — Your Path",
            f"Sun in {sun} grows through mastery and long-term building. Mercury in {mercury} shows how you think and plan. "
            f"Mars in {mars} shows your work style under pressure. Jupiter in {jupiter} shows where growth accelerates.",
            "You’re built for results, not hype. You can systematize chaos, improve processes, and deliver when others freeze. "
            "You do well when the goal is real and the standard is high.",
            "Your drive can become all-or-nothing: perfectionism, procrastination, burnout cycles. You may overthink visibility and judgment before you move.",
            "Pick ONE measurable output this week (deliverable / portfolio / launch step). Publish before it feels perfect. "
            "Momentum first, refinement second.",
            "Ask: ‘If I trusted my competence 10% more, what would I ship this week?’",
        )

    elif topic == "money":
        text = format_reading(
            "MONEY & STABILITY — Your Flow",
            f"Sun {sun} earns best through strategy and consistency. Moon {moon} ties money to emotional safety. "
            f"Venus {venus} shows what you value and spend on. Saturn {saturn} shows your scarcity trigger (and your discipline).",
            "You’re capable of building stable wealth when you have a clear target. You can be disciplined and long-term oriented.",
            "Impulse spending can appear during emotional spikes (relief, reward, comfort). Or the opposite: fear of scarcity blocks investments that would help you grow.",
            "Use a balanced rule for 7 days: (1) weekly cap, (2) one investment category (skills/tools), (3) one joy category (small reward). "
            "No extremes — just rhythm.",
            "Ask: ‘Is this purchase solving a real need — or soothing a moment?’",
        )

    elif topic == "personal":
        text = format_reading(
            "PERSONAL GROWTH — Your Inner Blueprint",
            f"Sun {sun} shows your core direction. Moon {moon} shows what your inner world needs to feel held. "
            f"Ascendant {asc} shows your protective style. Mercury {mercury} shows your mental patterns; Saturn {saturn} shows your growth edge.",
            "You transform fast once you commit. You’re resilient. You don’t just ‘learn’ — you integrate and evolve.",
            "You may carry everything alone until it becomes heavy. You can look ‘fine’ while you’re overloaded internally.",
            "Choose one tiny daily ritual (5 minutes): write what you feel (not what you think), or a short walk without phone. "
            "Small repetition rewires patterns.",
            "Ask: ‘What emotion am I avoiding — and what happens if I allow it for 60 seconds?’",
        )

    elif topic == "shadow":
        text = format_reading(
            "SHADOW PATTERNS — What Blocks You",
            f"Sun {sun} shadow: control/perfection. Moon {moon} shadow: pride/reactivity/validation. "
            f"Ascendant {asc} shadow: guardedness or performance. Saturn {saturn} shows the fear that shapes your defenses.",
            "You’re self-aware enough to change quickly once you name the pattern. Depth is your advantage: you can transform, not repeat.",
            "When you feel unsafe, you may test people, withdraw, or overthink. That creates distance exactly when you want connection.",
            "Name the emotion in one sentence (no story). Then one action: speak, set a boundary, or ask directly. Don’t spiral.",
            "Ask: ‘What am I trying to protect — and what would healthier protection look like?’",
        )

    elif topic == "communication":
        text = format_reading(
            "COMMUNICATION — How To Be Understood",
            f"Mercury {mercury} is your communication engine. Sun {sun} gives purpose. Moon {moon} gives emotion. "
            f"Ascendant {asc} shapes first impression — how your words land.",
            "When you speak clearly, people trust you. You can be persuasive without forcing — especially when you stay calm.",
            "Your trap is assuming others will ‘get it’ from hints, tone, or silence. People guess — and guess wrong.",
            "Use this formula once today: ‘I feel ___ about ___. I need ___. Can we ___?’ One sentence each. No drama, just clarity.",
            "Ask: ‘What’s the simplest truthful version of what I’m trying to say?’",
        )

    elif topic == "purpose":
        text = format_reading(
            "PURPOSE — What You’re Here To Build",
            f"Sun {sun} builds through mastery. Jupiter {jupiter} shows where expansion is natural. "
            f"Saturn {saturn} shows where you must mature. Ascendant {asc} shows how you begin the path.",
            "Your purpose isn’t ‘found’ — it’s built through commitment. You’re designed for depth, not distractions.",
            "The trap is waiting for certainty. You can stay in preparation forever and call it ‘planning’.",
            "Choose a 14-day commitment: one skill + one output. Track daily. Direction becomes obvious through movement.",
            "Ask: ‘If I couldn’t fail, what would I start building immediately?’",
        )

    elif topic == "timing":
        text = format_reading(
            "TIMING — Your Momentum",
            f"Sun {sun} thrives on structure. Moon {moon} moves in waves. Mars {mars} shows your action style. "
            f"Ascendant {asc} shows how you initiate and recover.",
            "Your best timing happens when you combine plan + intuition: structure the steps, then act when the inner signal is ‘yes’.",
            "Waiting for the perfect mood delays opportunities. Over-analysis can become quiet stagnation.",
            "This week: choose one 30–60 min action that creates momentum. Do it first. Let the mood arrive after movement.",
            "Ask: ‘What’s one step I can take today that makes tomorrow easier?’",
        )

    elif topic == "health":
        text = format_reading(
            "HEALTH & ENERGY — How You Recharge",
            f"Sun {sun} responds well to routine. Moon {moon} is your nervous system’s emotional weather. "
            f"Mars {mars} shows how you spend energy and recover.",
            "When you honor rhythm (sleep, food, movement), you become unstoppable. Small routines stabilize your confidence.",
            "You may ignore early signals until the body forces a stop. Or over-correct (strict week → then nothing).",
            "Pick a 7-day reset: consistent wake time + 20-min walk + hydration rule. Keep it simple and repeatable.",
            "Ask: ‘What does my body need that I keep postponing?’",
        )

    elif topic == "friendships":
        text = format_reading(
            "FRIENDSHIPS — Your Social Style",
            f"Sun {sun} values loyalty. Moon {moon} needs warmth. Ascendant {asc} shapes the vibe you give off. "
            f"Venus {venus} shows how you bond socially.",
            "You’re a high-quality friend: protective, honest, present when it matters. You prefer depth over superficial circles.",
            "You may disappear when overwhelmed and assume people will understand. Or expect the same depth immediately.",
            "Nurture one bond this week with one simple action (voice note / invite / check-in). Consistency beats intensity.",
            "Ask: ‘Do I want closeness — and am I acting like I do?’",
        )

    else:
        text = format_reading(
            "YOUR CORE BLUEPRINT — Snapshot",
            f"Sun {sun} shapes identity and direction. Moon {moon} shapes emotional needs. Ascendant {asc} shapes your starting energy. "
            f"Mercury {mercury}, Venus {venus}, Mars {mars} refine your style — mind, love, action.",
            "You have depth + drive. When you focus, you build something real — not just ideas.",
            "Your challenge is rhythm: staying consistent when emotions fluctuate or when standards feel heavy.",
            "Pick one small daily action you can repeat. Keep it simple, keep it real, keep it consistent.",
            "Ask: ‘What does my best self do even when motivation is low?’",
        )

    return {"topic": topic, "text": text}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
