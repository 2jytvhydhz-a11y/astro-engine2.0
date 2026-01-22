from fastapi import FastAPI, HTTPException
from datetime import datetime
import swisseph as swe

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Swiss Ephemeris: usa i file effemeridi locali (repo)
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
    # Validazioni base
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=422, detail="lat/lon out of range")

    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date/time format. Use YYYY-MM-DD and HH:MM")

    # Julian day (trattato come UT per semplicità)
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

    result = {}

    try:
        for name, planet in planets.items():
            xx, _ = swe.calc_ut(jd, planet)  # xx[0]=lon, xx[1]=lat, xx[2]=dist...
            lon_p = float(xx[0])
            result[name] = {
                "longitude": lon_p,
                "sign": zodiac_sign(lon_p),
            }

        houses, ascmc = swe.houses(jd, lat, lon)
        asc_sign = zodiac_sign(float(ascmc[0]))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SwissEphemeris error: {str(e)}")

    return {
        "planets": result,
        "ascendant": asc_sign
    }

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

from pydantic import BaseModel

class ReadingRequest(BaseModel):
    birth_profile: dict
    topic: str  # es: "love", "career", "money", "personal"

@app.post("/readings")
def generate_reading(data: ReadingRequest):
    birth_profile = data.birth_profile
    chart = birth_profile["chart"]

    planets = chart["planets"]

    sun = next(p["sign"] for p in planets if p["key"] == "sun")
    moon = next(p["sign"] for p in planets if p["key"] == "moon")
    asc = chart["ascendant"]["sign"]

       if data.topic == "love":
        text = f"""
LOVE & RELATIONSHIPS — Your Pattern

CORE THEME
With Sun in {sun}, you approach love with intention and standards: you don’t waste energy on what feels shallow.
With Moon in {moon}, you need emotional truth — not perfect words, but real presence.
With Ascendant in {asc}, you can appear intense or magnetic even when you’re quiet. People feel you before they understand you.

WHAT YOU NEED (NOT WHAT YOU WANT)
• Consistency: someone who shows up the same way in calm and chaos.
• Emotional bravery: honesty without drama.
• Depth: connection that grows, not a loop that repeats.

YOUR STRENGTH IN LOVE
You love like a builder: slowly, seriously, and with loyalty.
When you commit, you invest fully — and that makes relationships transformative for you.

YOUR BLIND SPOT
You can test people without meaning to: you watch, you wait, you measure.
If they don’t “pass”, you detach fast — sometimes before giving them a clear chance to meet you.

HOW TO WIN IN RELATIONSHIPS (PRACTICAL)
1) Say what you need early (in simple words). Not hints.
2) Don’t confuse intensity with compatibility.
3) Choose partners who are calm under pressure — that’s your real safety.

TODAY’S PROMPT
“What would make me feel emotionally safe this week — and have I said it clearly?”
"""

    elif data.topic == "career":
        text = f"""
CAREER — Your Path

CORE THEME
Sun in {sun} gives you long-term ambition: you’re built for mastery, not quick wins.
Moon in {moon} adds creative pride: you need to feel seen for what you uniquely bring.
Ascendant in {asc} makes your style powerful — people read you as capable, strategic, and hard to influence.

WHAT YOU NEED TO THRIVE
• A role where you can grow in responsibility.
• Clear metrics: progress must be measurable.
• Autonomy: you work best when trusted, not micromanaged.

YOUR NATURAL ADVANTAGE
You can endure what others quit.
When you decide a goal matters, you become consistent — and consistency is your superpower.

YOUR RISK
Over-control. You can carry everything alone and silently burn out.
Your success increases when you delegate and ask earlier.

HOW TO LEVEL UP (PRACTICAL)
1) Pick one skill to become “top 5%” at in 90 days.
2) Build a visible proof trail (portfolio, numbers, results).
3) Don’t wait for confidence — let repetition create it.

TODAY’S PROMPT
“What is the one task I avoid because it would actually move my life forward?”
"""

    else:
        text = f"""
CORE BLUEPRINT — Who You Are

CORE THEME
Sun in {sun} shows your direction: how you build a life that feels solid and meaningful.
Moon in {moon} shows your emotional needs: what refuels you and what drains you.
Ascendant in {asc} shows how the world experiences you first: your “aura” and approach to new situations.

YOUR INNER ENGINE
You’re not here for surface-level living.
You evolve through real experiences, real choices, and relationships that change you for the better.

WHAT HELPS YOU MOST
• A structure that protects your energy
• A small circle of real people
• Goals that aren’t random — goals that match who you are

THIS WEEK’S FOCUS
Choose one area (love, work, health, money) and make a single clear decision.
Your life improves fast when your decisions become clean.

TODAY’S PROMPT
“What am I tolerating that I already know I should change?”
"""

    return {
        "topic": data.topic,
        "text": text.strip()
    }
