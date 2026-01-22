from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict
import swisseph as swe

app = FastAPI()

# --- LOG (utile per debug su Railway) ---
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
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Swiss Ephemeris ---
swe.set_ephe_path(".")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def zodiac_sign(longitude: float) -> str:
    longitude = longitude % 360.0
    return SIGNS[int(longitude // 30)]


@app.get("/")
def root():
    return {
        "ok": True,
        "try": "/docs",
        "example": "/chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5"
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

    planets = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mercury": swe.MERCURY,
        "venus": swe.VENUS,
        "mars": swe.MARS,
        "jupiter": swe.JUPITER,
        "saturn": swe.SATURN,
    }

    result: Dict[str, Any] = {}

    try:
        for name, planet in planets.items():
            xx, _ = swe.calc_ut(jd, planet)
            lon_p = float(xx[0])
            result[name] = {"longitude": lon_p, "sign": zodiac_sign(lon_p)}

        houses, ascmc = swe.houses(jd, lat, lon)
        asc_sign = zodiac_sign(float(ascmc[0]))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SwissEphemeris error: {str(e)}")

    # IMPORTANT: ascendant come OGGETTO con sign (per matchare il frontend)
    return {
        "planets": result,
        "ascendant": {"sign": asc_sign}
    }


# -------- READINGS API --------
class ReadingRequest(BaseModel):
    birth_profile: Dict[str, Any] = {}
    topic: str


@app.post("/readings")
def generate_reading(data: ReadingRequest):
    birth_profile = data.birth_profile or {}
    chart = (birth_profile.get("chart") or {})

    planets = chart.get("planets") or {}

    def get_sign(key: str, fallback: str = "Unknown") -> str:
        v = planets.get(key)
        if isinstance(v, dict):
            return v.get("sign") or fallback
        return fallback

    sun = get_sign("sun")
    moon = get_sign("moon")

    asc_obj = chart.get("ascendant") or {}
    asc = asc_obj.get("sign") or "Unknown"

    topic = (data.topic or "").lower().strip() or "general"

    def format_reading(title: str, core: str, strength: str, challenge: str, practical: str, reflection: str) -> str:
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

    if topic == "love":
        text = format_reading(
            "LOVE & RELATIONSHIPS — Your Pattern",
            f"With Sun in {sun}, you approach love with intention and standards. With Moon in {moon}, you need emotional truth and loyalty. With Ascendant in {asc}, you often attract intense connections that trigger growth rather than comfort.",
            "You’re capable of deep commitment. You read between the lines, notice patterns fast, and when you choose someone you can be incredibly steady and protective.",
            "You may test people silently instead of stating what you need. If your emotional safety feels uncertain, you can withdraw, become controlling, or expect the other person to ‘just understand’.",
            "Say your need early and simply. Replace ‘proof’ with clarity: one direct message, one clear boundary, one honest request. Choose calm consistency over emotional spikes.",
            "Ask yourself: ‘Am I reacting to the present person, or to an old pattern that feels familiar?’"
        )
    elif topic == "career":
        text = format_reading(
            "CAREER & DIRECTION — Your Path",
            f"With Sun in {sun}, your career grows through mastery and long-term thinking. With Moon in {moon}, you need work that feels meaningful emotionally, not just profitable. With Ascendant in {asc}, you’re seen as intense, strategic, and capable under pressure.",
            "You’re strong at building systems, improving processes, and turning chaos into structure. You can work alone and still deliver high-level results.",
            "Your drive can become all-or-nothing: either total ambition or total burnout. You may overthink visibility, authority, or ‘being judged’ before you even move.",
            "Pick ONE measurable outcome this week (a deliverable, a portfolio piece, a launch step). Progress beats perfection. Show your work before it feels ready.",
            "Ask: ‘What would I create if I trusted my competence 10% more?’"
        )
    elif topic == "money":
        text = format_reading(
            "MONEY & STABILITY — Your Flow",
            f"With Sun in {sun}, you earn best through consistency and strategy. With Moon in {moon}, spending is tied to emotions (comfort, freedom, reward). With Ascendant in {asc}, you can be private about money, but highly driven to feel in control.",
            "You’re good at planning, saving when you have a clear target, and spotting what’s ‘worth it’ long-term. You can be very disciplined when motivated.",
            "Impulse spending can appear when emotions spike or when you feel you ‘deserve’ relief. Fear of scarcity can also block investments that would actually help you grow.",
            "Use a simple rule: 1) weekly cap, 2) one ‘investment’ category (tools/skills), 3) one ‘joy’ category (small rewards). Balanced, not strict.",
            "Ask: ‘Is this purchase solving a real need, or soothing a moment?’"
        )
    elif topic == "personal":
        text = format_reading(
            "PERSONAL GROWTH — Your Inner Blueprint",
            f"With Sun in {sun}, you evolve through responsibility and purpose. With Moon in {moon}, your emotions need space to be expressed, not managed. With Ascendant in {asc}, you protect your depth — you reveal yourself only when trust is real.",
            "You have strong intuition and self-awareness. When you commit to growth, you transform fast. You’re resilient and bounce back stronger.",
            "You may keep everything inside until it becomes too heavy. The risk is emotional isolation: appearing ‘fine’ while carrying too much alone.",
            "Choose one daily ritual: journaling 5 minutes, a walk without phone, or a short emotional check-in. Tiny repetition is what rewires patterns.",
            "Ask: ‘What feeling am I avoiding — and what would happen if I allowed it for 60 seconds?’"
        )
    else:
        text = format_reading(
            "YOUR CORE BLUEPRINT — Snapshot",
            f"Sun in {sun} shapes your identity and direction. Moon in {moon} shapes your emotional needs. Ascendant in {asc} shapes how you start things and how the world experiences you.",
            "You have a mix of depth and drive. When you focus, you can build something real — not just ideas.",
            "Your challenge is consistency when emotions fluctuate. You don’t need more intensity, you need a clear rhythm.",
            "Pick one small action you can repeat daily. Keep it simple, keep it real, keep it consistent.",
            "Ask: ‘What does my best self do even when motivation is low?’"
        )

    return {"topic": topic, "text": text}


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
