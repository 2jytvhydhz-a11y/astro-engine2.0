from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional, Union
from datetime import datetime
import os

import swisseph as swe

app = FastAPI()

# -----------------------------
# Middleware: simple request logs
# -----------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    print(f"[REQ] {request.method} {request.url.path} origin={origin}")
    response = await call_next(request)
    print(f"[RES] {request.method} {request.url.path} -> {response.status_code}")
    return response

# -----------------------------
# CORS (Lovable web preview + general web)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Swiss Ephemeris setup
# -----------------------------
swe.set_ephe_path(".")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def zodiac_sign(longitude: float) -> str:
    longitude = longitude % 360.0
    return SIGNS[int(longitude // 30)]

# -----------------------------
# API models
# -----------------------------
class ReadingRequest(BaseModel):
    birth_profile: Dict[str, Any] = {}
    topic: str

# -----------------------------
# Helpers: robust chart parsing
# -----------------------------
def _pick_sign(value: Any, fallback: str = "Unknown") -> str:
    """
    Accepts:
    - {"sign": "Capricorn"}  -> "Capricorn"
    - "Capricorn"            -> "Capricorn"
    - None / unknown         -> fallback
    """
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        s = value.get("sign")
        if isinstance(s, str) and s.strip():
            return s.strip()
    return fallback

def _get_chart(birth_profile: Dict[str, Any]) -> Dict[str, Any]:
    return (birth_profile or {}).get("chart") or {}

def _get_planets(chart: Dict[str, Any]) -> Dict[str, Any]:
    return chart.get("planets") or {}

def _planet_sign(planets: Dict[str, Any], key: str, fallback: str = "Unknown") -> str:
    return _pick_sign(planets.get(key), fallback=fallback)

def _asc_sign(chart: Dict[str, Any], fallback: str = "Unknown") -> str:
    # supports chart["ascendant"] = {"sign": "..."} OR "..." OR missing
    return _pick_sign(chart.get("ascendant"), fallback=fallback)

def _normalize_topic(t: str) -> str:
    return (t or "").lower().strip()

# -----------------------------
# Wow-style copy helpers
# -----------------------------
def _title_case(s: str) -> str:
    return (s or "").strip().title()

def _fmt(title: str, blocks: Dict[str, str]) -> str:
    """
    Produces a readable, 'wow' text that still fits nicely in your UI card.
    """
    out = [title.strip(), ""]
    for k, v in blocks.items():
        out.append(k.strip())
        out.append(v.strip())
        out.append("")
    return "\n".join(out).strip()

def _love_reading(sun: str, moon: str, asc: str, mercury: str, venus: str, mars: str, saturn: str, jupiter: str) -> str:
    return _fmt(
        "LOVE & RELATIONSHIPS — Your Emotional Pattern",
        {
            "THE CORE (what’s really going on)":
                f"You don’t do love as a hobby. Sun in {sun} makes you curious and selective: you can flirt, test, observe — "
                f"but you only *stay* where your mind feels alive and your respect grows. Moon in {moon} means you don’t bond through chaos: "
                f"you bond through safety. If the vibe is inconsistent, you don’t explode — you quietly pull back and watch.",

            "HOW YOU THINK + TALK IN LOVE":
                f"Mercury in {mercury} shows your relationship mind: you need clarity. If something feels off, your brain starts running scenarios. "
                f"When you don’t get answers, you try to *read* the person instead of asking directly — and that’s where misunderstandings start.",

            "HOW YOU LOVE (your real love language)":
                f"Venus in {venus} is the way you give and receive affection. You’re not impressed by big words — you’re moved by consistency. "
                f"You want someone who feels emotionally present, not just physically available. When you feel chosen, you become warm, loyal, and deeply devoted.",

            "DESIRE + ATTRACTION (what pulls you in)":
                f"Mars in {mars} describes desire. You’re drawn to real chemistry — but the kind that has *substance*. Passion without depth gets boring fast. "
                f"If someone is intense but unreliable, you’ll feel the pull… and then you’ll start protecting yourself.",

            "THE HIDDEN FEAR (the pattern that messes you up)":
                f"Saturn in {saturn} is where you become guarded. Your fear isn’t ‘being alone’ — it’s investing emotionally and then losing control. "
                f"So sometimes you test people silently: you watch if they show up, if they stay consistent, if they can handle your depth.",

            "WHAT MAKES YOU MAGNETIC (and what to do next)":
                f"Jupiter in {jupiter} shows your growth path in love: you win when you choose honesty over strategy. "
                f"One ‘wow’ move for you: say the need *early* and calmly. Not as a demand — as truth. "
                f"When you stop making people guess, the right ones step closer… and the wrong ones disappear fast.",
        }
    )

def _career_reading(sun: str, moon: str, asc: str, mercury: str, mars: str, saturn: str, jupiter: str, venus: str) -> str:
    return _fmt(
        "CAREER & DIRECTION — Your Real Path",
        {
            "THE CORE (how you’re built to succeed)":
                f"Sun in {sun} means your career grows through identity: you need to feel mentally engaged, not trapped. "
                f"Moon in {moon} means you can’t fake motivation — if the work doesn’t feel emotionally ‘right’, your energy drops. "
                f"Ascendant in {asc} is your public aura: you come off more capable than you think — people sense intensity, depth, or competence even when you’re quiet.",

            "YOUR WORKING BRAIN (how you win)":
                f"Mercury in {mercury} is your strategy engine: you spot patterns fast, you learn quickly, and you’re good at improving systems. "
                f"But it also means overthinking can become procrastination disguised as ‘research’.",

            "DRIVE + EXECUTION (where momentum comes from)":
                f"Mars in {mars} shows how you move. You’re at your best when you have one clear target and a short sprint. "
                f"If goals are vague, you scatter. If goals are concrete, you become unstoppable.",

            "THE BLOCK (the thing that causes stop-and-go)":
                f"Saturn in {saturn} shows the pressure point: you can fear being judged before you’re ready. "
                f"So you over-polish, you delay launches, or you keep improving privately. The truth: you don’t need more skill — you need more exposure.",

            "THE UPGRADE (a practical, real step)":
                f"Jupiter in {jupiter} says growth comes from expansion: publish, ship, show. "
                f"One move that changes everything for you this week: deliver ONE thing that can be seen (portfolio piece, landing, offer, feature, content). "
                f"Not perfect — visible.",

            "YOUR EDGE (why you’ll beat most people)":
                f"Venus in {venus} adds your ‘style advantage’: you can make things feel human, aesthetic, or emotionally resonant. "
                f"When you combine that with your brain + discipline, you create work people remember.",
        }
    )

def _money_reading(sun: str, moon: str, asc: str, venus: str, mars: str, saturn: str, jupiter: str, mercury: str) -> str:
    return _fmt(
        "MONEY & STABILITY — Your Real Money Psychology",
        {
            "THE CORE (how you relate to money)":
                f"Sun in {sun} shows your earning style: you do best with strategy, not luck. "
                f"Moon in {moon} shows your spending triggers: comfort, safety, relief. "
                f"Ascendant in {asc} can make you private about money — but driven to feel in control.",

            "HOW YOU EARN BEST":
                f"Mercury in {mercury} says you make money when you’re using your brain: writing, systems, analysis, communication, problem-solving. "
                f"You’re not built for ‘random hustle’. You’re built for repeatable leverage.",

            "WHERE LEAKS HAPPEN":
                f"Venus in {venus} shows what you buy to feel good (beauty, comfort, experiences, tools, gifts — depends on the sign). "
                f"When emotions spike, your brain looks for a quick ‘reset’ purchase. It’s not weakness — it’s regulation.",

            "MONEY DRIVE (and the risk)":
                f"Mars in {mars} is your financial push: when you want something, you can be intense and decisive. "
                f"The risk is going all-in, then burning out or getting bored. Consistency beats intensity for you.",

            "THE FEAR PATTERN":
                f"Saturn in {saturn} can create scarcity thinking: ‘If I spend, I lose control.’ Or the opposite: ‘I deserve relief now.’ "
                f"Both come from the same place — trying to protect yourself emotionally through money.",

            "THE FIX (simple rule that works)":
                f"Jupiter in {jupiter} says abundance comes from structure + expansion: "
                f"set (1) a weekly cap, (2) a skill/investment bucket, (3) a joy bucket. "
                f"Balanced, not strict. That’s how you become stable *and* motivated.",
        }
    )

def _personal_reading(sun: str, moon: str, asc: str, saturn: str, mercury: str, venus: str, mars: str, jupiter: str) -> str:
    return _fmt(
        "PERSONAL GROWTH — Your Inner Blueprint (the part you don’t show)",
        {
            "THE CORE (how you’re wired)":
                f"Sun in {sun} is your identity engine: you grow when you feel purpose. "
                f"Moon in {moon} is your emotional core: you need real stability, not superficial positivity. "
                f"Ascendant in {asc} is your armor: people don’t get the full you until trust is proven.",

            "WHAT YOU DO WHEN LIFE GETS HEAVY":
                f"Saturn in {saturn} shows your survival strategy: you try to hold it together. "
                f"You become ‘strong’, productive, controlled. From outside it looks fine — inside it can feel like pressure building.",

            "YOUR MIND PATTERN":
                f"Mercury in {mercury} makes you self-aware — but it can also trap you in analysis. "
                f"Sometimes you don’t need more understanding; you need one honest action.",

            "YOUR HEART PATTERN":
                f"Venus in {venus} shows what heals you: closeness, beauty, softness, warmth — in your style. "
                f"You reset fastest when you feel emotionally safe, not when you force discipline.",

            "YOUR COURAGE (what changes everything)":
                f"Mars in {mars} is your move: you transform when you act in small consistent steps instead of waiting for the perfect mood. "
                f"Jupiter in {jupiter} says your growth is bigger than your fear — but only if you stop making it private.",

            "WOW PRACTICE (1 minute)":
                f"Today: name the feeling in ONE sentence (no story). Then do ONE action that matches truth. "
                f"This is the fastest way for you to stop carrying everything alone.",
        }
    )

def _timing_reading(sun: str, moon: str, asc: str, mercury: str, mars: str, saturn: str, jupiter: str, venus: str) -> str:
    return _fmt(
        "TIMING — When You’re Actually At Your Best",
        {
            "THE CORE":
                f"Sun in {sun} likes direction. Moon in {moon} moves in waves. Ascendant in {asc} decides how you start. "
                f"Your best timing is not ‘whenever you feel like it’ — it’s rhythm + commitment.",

            "YOUR ‘GREEN LIGHT’ SIGNAL":
                f"Mercury in {mercury} gives you clarity when you have a plan. When your mind is clear, your anxiety drops. "
                f"You don’t need perfect certainty — you need a clean next step.",

            "YOUR ‘GO’ ENERGY":
                f"Mars in {mars} means momentum comes from action, not motivation. "
                f"If you wait to feel ready, you delay your best windows.",

            "THE DELAY TRAP":
                f"Saturn in {saturn} can make you over-check outcomes before you start. "
                f"That’s why you can feel stuck even when you’re capable.",

            "THE MOVE (this week)":
                f"Jupiter in {jupiter}: pick ONE 30–60 minute action that creates visible progress. Do it first. "
                f"Then reward yourself (Venus in {venus}) — your system learns ‘movement = safety’.",
        }
    )

def _strengths_reading(sun: str, moon: str, asc: str, mercury: str, mars: str, venus: str, jupiter: str, saturn: str) -> str:
    return _fmt(
        "STRENGTHS — What You Do Better Than Most People",
        {
            "YOUR CORE STRENGTH":
                f"Sun in {sun} gives you identity-drive: when you commit, you build real competence. "
                f"Moon in {moon} gives you emotional intelligence in your own style. "
                f"Ascendant in {asc} gives you presence — people feel you even before you speak.",

            "YOUR SUPERPOWER SKILLSET":
                f"Mercury in {mercury} = pattern recognition and strategy. "
                f"Mars in {mars} = execution when the target is clear. "
                f"Venus in {venus} = taste, human connection, value-sense.",

            "GROWTH ADVANTAGE":
                f"Jupiter in {jupiter} means you’re meant to expand beyond comfort. "
                f"You grow fastest when you make your work public and measurable.",

            "THE ONLY THING TO WATCH":
                f"Saturn in {saturn}: high standards. Powerful — but if you demand perfection, you delay the win. "
                f"Your strength becomes unstoppable when it’s consistent instead of extreme.",
        }
    )

def _shadow_reading(sun: str, moon: str, asc: str, saturn: str, mercury: str, mars: str, venus: str, jupiter: str) -> str:
    return _fmt(
        "SHADOW PATTERNS — The Thing That Quietly Blocks You",
        {
            "THE CORE SHADOW":
                f"Sun in {sun} can shadow into ‘I must be impressive to be safe.’ "
                f"Moon in {moon} can shadow into ‘If I don’t feel secure, I pull away.’ "
                f"Ascendant in {asc} can shadow into ‘I’ll show strength instead of need.’",

            "HOW IT SHOWS UP":
                f"Mercury in {mercury}: you think instead of feeling. "
                f"Mars in {mars}: you push, then disappear. "
                f"Venus in {venus}: you want closeness, but you don’t want to risk rejection.",

            "THE ROOT":
                f"Saturn in {saturn}: fear of being exposed, misunderstood, or losing control. "
                f"This is why you can test people silently — and why you can hold pain quietly for too long.",

            "THE FIX (simple, brutal, effective)":
                f"Jupiter in {jupiter}: choose truth over protection. "
                f"One sentence that changes your life: ‘This is what I need.’ "
                f"Not dramatic. Not apologetic. Just real.",
        }
    )

def _communication_reading(sun: str, moon: str, asc: str, mercury: str, venus: str, mars: str, saturn: str, jupiter: str) -> str:
    return _fmt(
        "COMMUNICATION — How To Be Understood (without over-explaining)",
        {
            "YOUR STYLE":
                f"Sun in {sun} speaks with intention. Moon in {moon} speaks from emotion. "
                f"Ascendant in {asc} shapes first impressions: you can come across intense, private, or very direct.",

            "WHAT YOU DO WHEN YOU CARE":
                f"Mercury in {mercury}: you explain, you analyze, you try to be precise. "
                f"Venus in {venus}: you try to keep harmony or meaning. "
                f"Mars in {mars}: when pushed, you can become sharp or abrupt — not because you’re mean, but because you’re protecting your truth.",

            "THE MISUNDERSTANDING TRAP":
                f"Saturn in {saturn}: you may hold back ‘needs’ because you don’t want to feel vulnerable. "
                f"So you hint, you imply, you wait — and people guess wrong.",

            "THE FORMULA (use this and you win)":
                f"Jupiter in {jupiter}: say it clearly. Use: "
                f"‘I feel __ about __. I need __. Can we __?’ "
                f"One sentence each. No essay. No drama. Pure clarity.",
        }
    )

# Bonus topics (you already had these; keeping them)
def _health_reading(sun: str, moon: str, asc: str, mars: str, saturn: str, venus: str, jupiter: str, mercury: str) -> str:
    return _fmt(
        "HEALTH & ENERGY — Your Recharge Blueprint",
        {
            "THE CORE":
                f"Sun in {sun} responds to routine. Moon in {moon} responds to emotional environment. "
                f"Ascendant in {asc} can push you to look ‘fine’ even when you’re depleted.",

            "YOUR ENERGY ENGINE":
                f"Mars in {mars} shows how you burn fuel: you surge, then you need recovery. "
                f"Mercury in {mercury} means mental overload hits your body faster than you expect.",

            "THE RISK":
                f"Saturn in {saturn}: ignoring early signals until your body forces a stop.",

            "THE RESET (7 days)":
                f"Jupiter in {jupiter}: go simple and consistent. "
                f"(1) same wake time, (2) 20-min walk, (3) hydration rule. "
                f"Venus in {venus}: add one small pleasure daily so it’s sustainable.",
        }
    )

def _friendships_reading(sun: str, moon: str, asc: str, venus: str, mercury: str, saturn: str, jupiter: str, mars: str) -> str:
    return _fmt(
        "FRIENDSHIPS — Your Social Truth",
        {
            "THE CORE":
                f"Sun in {sun}: you value people who stimulate your mind and respect you. "
                f"Moon in {moon}: you need loyalty and consistency. "
                f"Ascendant in {asc}: you can look selective because you are.",

            "YOUR FRIENDSHIP STYLE":
                f"Venus in {venus}: you show love through your kind of care (support, presence, gestures). "
                f"Mercury in {mercury}: you connect through honest conversation — not small talk.",

            "THE PROBLEM PATTERN":
                f"Saturn in {saturn}: when overwhelmed you disappear and expect people to understand. "
                f"Mars in {mars}: if you feel disrespected, you cut fast.",

            "THE MOVE":
                f"Jupiter in {jupiter}: one small consistent check-in builds more closeness than rare intensity. "
                f"Do one message today: short, real, warm.",
        }
    )

def _purpose_reading(sun: str, moon: str, asc: str, saturn: str, jupiter: str, mercury: str, mars: str, venus: str) -> str:
    return _fmt(
        "PURPOSE — What You’re Here To Build",
        {
            "THE CORE":
                f"Sun in {sun}: purpose grows through identity — doing what feels true. "
                f"Moon in {moon}: you need emotional alignment, not just money. "
                f"Ascendant in {asc}: you’re designed to start things with intensity and depth.",

            "THE TRAP":
                f"Saturn in {saturn}: waiting for certainty before moving. "
                f"Mercury in {mercury}: researching forever and calling it ‘preparation’.",

            "THE PATH":
                f"Jupiter in {jupiter}: expansion through commitment. "
                f"Mars in {mars}: daily execution. "
                f"Venus in {venus}: create something people actually *feel*.",

            "THE 14-DAY COMMITMENT":
                f"Pick one skill, one project, one habit. Track daily. "
                f"Your purpose becomes obvious after momentum shows you what fits.",
        }
    )

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "try": "/docs",
        "example_chart": "/chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5",
        "example_readings": "POST /readings with { birth_profile: { chart: { planets: {...}, ascendant: {...} } }, topic: 'love' }"
    }

@app.get("/chart")
def calculate_chart(date: str, time: str, lat: float, lon: float):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=422, detail="lat/lon out of range")

    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date/time format. Use YYYY-MM-DD and HH:MM")

    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    planets_map = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mercury": swe.MERCURY,
        "venus": swe.VENUS,
        "mars": swe.MARS,
        "jupiter": swe.JUPITER,
        "saturn": swe.SATURN,
    }

    result = {}
    try:
        for name, planet in planets_map.items():
            xx, _ = swe.calc_ut(jd, planet)
            lon_p = float(xx[0])
            result[name] = {"longitude": lon_p, "sign": zodiac_sign(lon_p)}

        _, ascmc = swe.houses(jd, lat, lon)
        asc_sign = zodiac_sign(float(ascmc[0]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SwissEphemeris error: {str(e)}")

    return {"planets": result, "ascendant": {"sign": asc_sign}}

@app.post("/readings")
def generate_reading(data: ReadingRequest):
    birth_profile = data.birth_profile or {}
    chart = _get_chart(birth_profile)
    planets = _get_planets(chart)

    # core placements (robust)
    sun = _planet_sign(planets, "sun")
    moon = _planet_sign(planets, "moon")
    mercury = _planet_sign(planets, "mercury")
    venus = _planet_sign(planets, "venus")
    mars = _planet_sign(planets, "mars")
    jupiter = _planet_sign(planets, "jupiter")
    saturn = _planet_sign(planets, "saturn")
    asc = _asc_sign(chart)

    topic = _normalize_topic(data.topic) or "general"

    # Route by topic
    if topic == "love":
        text = _love_reading(sun, moon, asc, mercury, venus, mars, saturn, jupiter)
    elif topic == "career":
        text = _career_reading(sun, moon, asc, mercury, mars, saturn, jupiter, venus)
    elif topic == "money":
        text = _money_reading(sun, moon, asc, venus, mars, saturn, jupiter, mercury)
    elif topic == "personal":
        text = _personal_reading(sun, moon, asc, saturn, mercury, venus, mars, jupiter)
    elif topic == "timing":
        text = _timing_reading(sun, moon, asc, mercury, mars, saturn, jupiter, venus)
    elif topic == "strengths":
        text = _strengths_reading(sun, moon, asc, mercury, mars, venus, jupiter, saturn)
    elif topic == "shadow":
        text = _shadow_reading(sun, moon, asc, saturn, mercury, mars, venus, jupiter)
    elif topic == "communication":
        text = _communication_reading(sun, moon, asc, mercury, venus, mars, saturn, jupiter)
    elif topic == "health":
        text = _health_reading(sun, moon, asc, mars, saturn, venus, jupiter, mercury)
    elif topic == "friendships":
        text = _friendships_reading(sun, moon, asc, venus, mercury, saturn, jupiter, mars)
    elif topic == "purpose":
        text = _purpose_reading(sun, moon, asc, saturn, jupiter, mercury, mars, venus)
    else:
        # fallback: give a strong general reading that still feels personal
        text = _fmt(
            "YOUR CORE BLUEPRINT — The Snapshot That Actually Hits",
            {
                "THE CORE":
                    f"Sun in {sun} is who you’re becoming. Moon in {moon} is what you truly need. Ascendant in {asc} is how you move through life.",
                "WHAT YOU DO (the pattern)":
                    f"Mercury in {mercury} makes you think deeply — sometimes too deeply. Venus in {venus} makes you crave real meaning, not superficial comfort. "
                    f"Mars in {mars} gives you a powerful drive when the target is clear.",
                "THE PRESSURE POINT":
                    f"Saturn in {saturn} is where you protect yourself: you’d rather look controlled than feel exposed. That’s strength — but it can become isolation.",
                "THE UPGRADE":
                    f"Jupiter in {jupiter} says your life expands when you choose one honest action over one more round of thinking. "
                    f"Your best self doesn’t wait for perfect confidence — it moves and lets confidence catch up.",
            }
        )

    return {
        "topic": topic,
        "text": text,
        "meta": {
            "sun": sun,
            "moon": moon,
            "ascendant": asc,
            "mercury": mercury,
            "venus": venus,
            "mars": mars,
            "jupiter": jupiter,
            "saturn": saturn,
        }
    }

# -----------------------------
# Local run (Railway uses start command; this is fine to keep)
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
