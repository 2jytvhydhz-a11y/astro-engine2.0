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

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI()


class ReadingRequest(BaseModel):
    birth_profile: Dict[str, Any] = {}
    topic: str


@app.post("/readings")
def generate_reading(data: ReadingRequest):
    birth_profile = data.birth_profile or {}
    chart = (birth_profile.get("chart") or {})

    planets = chart.get("planets") or {}

    def get_sign(key: str, fallback: str = "Unknown") -> str:
        """Supports raw planets dict: planets['sun'] = {'sign': 'Capricorn'}."""
        v = planets.get(key)
        if isinstance(v, dict):
            return v.get("sign") or fallback
        return fallback

    sun = get_sign("sun")
    moon = get_sign("moon")
    asc = (chart.get("ascendant") or {}).get("sign") or "Unknown"

    topic = (data.topic or "").lower().strip() or "general"

    def format_reading(
        title: str,
        core: str,
        strength: str,
        challenge: str,
        practical: str,
        reflection: str
    ) -> str:
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

    elif topic == "timing":
        text = format_reading(
            "TIMING — Your Momentum",
            f"With Sun in {sun}, you thrive when you plan and build steadily. With Moon in {moon}, your energy comes in waves — creativity needs cycles. With Ascendant in {asc}, you move best when you feel focused and emotionally clear.",
            "Your best timing is structure + intuition: plan the steps, then act when your inner signal is ‘yes’.",
            "Waiting for the perfect emotional state can delay opportunities. Over-analysis can quietly become stagnation.",
            "This week: choose one action that creates momentum in 30–60 minutes. Do it first. Let the mood arrive after the movement.",
            "Ask: ‘What’s one step I can take today that makes tomorrow easier?’"
        )

    elif topic == "strengths":
        text = format_reading(
            "STRENGTHS — What You Do Best",
            f"Your Sun in {sun} gives you a drive toward competence and purpose. Your Moon in {moon} shows how you recharge emotionally. Your Ascendant in {asc} shows how you take initiative and how others experience your presence.",
            "You learn fast when you care. You go deep, notice patterns, and improve systems instead of repeating mistakes. When you commit, you’re consistent.",
            "Your strength becomes a trap when you expect too much from yourself or from others. High standards are powerful, but they need flexibility.",
            "This week: identify ONE underused strength (clarity, discipline, intuition, courage). Use it intentionally in a real situation.",
            "Ask: ‘What would change if I trusted my strongest quality and used it on purpose?’"
        )

    elif topic == "shadow":
        text = format_reading(
            "SHADOW PATTERNS — What Blocks You",
            f"With Sun in {sun}, your shadow can be over-control or perfectionism. With Moon in {moon}, it can be emotional reactivity or seeking validation. With Ascendant in {asc}, you may protect yourself by staying guarded or intense.",
            "You’re self-aware enough to change quickly once you name the pattern. Your depth is an advantage: you transform instead of repeating cycles.",
            "When you feel unsafe or uncertain, you might test people, withdraw, or overthink. That creates distance exactly when you want connection.",
            "Name the emotion in one sentence (no story). Then choose one action: speak clearly, set a boundary, or ask directly.",
            "Ask: ‘What am I trying to protect — and what would healthier protection look like?’"
        )

    elif topic == "communication":
        text = format_reading(
            "COMMUNICATION — How To Be Understood",
            f"Your Sun in {sun} speaks with purpose. Your Moon in {moon} speaks from emotion. Your Ascendant in {asc} shapes first impressions — you can come across as intense, private, or very direct.",
            "When you communicate clearly, you become magnetic: people trust you. You can be persuasive without forcing, especially when you’re calm.",
            "Your challenge is assuming others can read your signals. If you don’t say what you need, people will guess — and guess wrong.",
            "Use this formula: ‘I feel ___ about ___. I need ___. Can we ___?’ One sentence each. No drama, just clarity.",
            "Ask: ‘What’s the simplest truthful version of what I’m trying to say?’"
        )

    # NEW TOPICS (12 total)

    elif topic == "health":
        text = format_reading(
            "HEALTH & ENERGY — How You Recharge",
            f"With Sun in {sun}, your body responds well to routine and structure. With Moon in {moon}, your nervous system is influenced by emotions and environment. With Ascendant in {asc}, you may push through until your body forces a pause.",
            "When you honor rhythm (sleep, food, movement), you become unstoppable. Small routines give you stability and confidence.",
            "You may ignore early signals, then crash. Or you may over-correct: strict for a week, then nothing.",
            "Pick a 3-part reset: 1) consistent wake time, 2) 20-min walk, 3) hydration rule. Keep it simple for 7 days.",
            "Ask: ‘What does my body need that I keep postponing?’"
        )

    elif topic == "friendships":
        text = format_reading(
            "FRIENDSHIPS — Your Social Style",
            f"With Sun in {sun}, you value loyalty and long-term bonds. With Moon in {moon}, you need warmth and recognition. With Ascendant in {asc}, you can seem selective — because you are.",
            "You’re a high-quality friend: protective, honest, and present when it matters. You don’t do superficial bonds for long.",
            "You may disappear when overwhelmed and assume people will understand. Or you may expect others to show the same depth you show — immediately.",
            "This week: nurture one bond with a simple action (voice note, invite, check-in). Consistency builds trust more than intensity.",
            "Ask: ‘Do I want closeness — and am I acting like I do?’"
        )

    elif topic == "purpose":
        text = format_reading(
            "PURPOSE — What You’re Here To Build",
            f"With Sun in {sun}, purpose is built through responsibility and mastery. With Moon in {moon}, you need your life to feel emotionally aligned. With Ascendant in {asc}, you’re designed to transform — and to guide others through transformation.",
            "Your purpose isn’t random. It’s created by choosing one path and committing long enough to see results. You’re built for depth, not noise.",
            "The trap is waiting for certainty before starting. You can keep researching forever and call it ‘preparing’.",
            "Choose a 14-day commitment: one skill, one project, one habit. Track progress daily. Momentum will reveal direction.",
            "Ask: ‘If I couldn’t fail, what would I start building immediately?’"
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
