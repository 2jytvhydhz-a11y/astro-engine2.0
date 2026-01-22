from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Any
import swisseph as swe

# ------------------
# APP SETUP
# ------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

swe.set_ephe_path(".")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def zodiac_sign(longitude: float) -> str:
    longitude = longitude % 360.0
    return SIGNS[int(longitude // 30)]

# ------------------
# ROOT
# ------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "docs": "/docs",
        "example": "/chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5"
    }

# ------------------
# CHART ENDPOINT
# ------------------
@app.get("/chart")
def calculate_chart(date: str, time: str, lat: float, lon: float):
    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(422, "Invalid date/time format")

    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60)

    planet_map = {
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

    planets = {}
    for name, code in planet_map.items():
        pos, _ = swe.calc_ut(jd, code)
        planets[name] = {
            "longitude": pos[0],
            "sign": zodiac_sign(pos[0]),
        }

    _, ascmc = swe.houses(jd, lat, lon)

    return {
        "planets": planets,
        "ascendant": {
            "longitude": ascmc[0],
            "sign": zodiac_sign(ascmc[0])
        }
    }

# ------------------
# READINGS
# ------------------
from pydantic import BaseModel

class ReadingRequest(BaseModel):
    birth_profile: Dict[str, Any]
    topic: str

def sign(chart, key):
    try:
        return chart["planets"][key]["sign"]
    except:
        return "Unknown"

def reading_block(title, paragraphs):
    body = "\n\n".join(paragraphs)
    return f"{title}\n\n{body}"

@app.post("/readings")
def generate_reading(data: ReadingRequest):
    chart = data.birth_profile.get("chart", {})
    topic = (data.topic or "general").lower()

    sun = sign(chart, "sun")
    moon = sign(chart, "moon")
    mercury = sign(chart, "mercury")
    venus = sign(chart, "venus")
    mars = sign(chart, "mars")
    saturn = sign(chart, "saturn")
    asc = chart.get("ascendant", {}).get("sign", "Unknown")

    if topic == "love":
        text = reading_block(
            "LOVE & RELATIONSHIPS — Your Emotional Pattern",
            [
                f"You love with intention. Sun in {sun} makes you selective: you don’t give yourself easily, but when you do, it’s real. You need relationships that feel meaningful, not casual.",
                f"Moon in {moon} reveals your emotional hunger. You need safety, loyalty, and emotional presence. When this is missing, you instinctively pull back or protect yourself.",
                f"Venus in {venus} shows how you express love: this is your true love language. You desire depth, consistency, and emotional authenticity, not surface-level affection.",
                f"Mars in {mars} describes attraction and desire. You’re drawn to intensity, chemistry, and emotional truth — passion fades quickly if the connection lacks substance.",
                f"Saturn in {saturn} highlights your fear: abandonment, loss of control, or emotional exposure. Love becomes transformative once you stop testing and start expressing.",
            ]
        )

    elif topic == "career":
        text = reading_block(
            "CAREER & PURPOSE — How You Build Success",
            [
                f"Sun in {sun} gives you long-term ambition. You’re not built for shortcuts — you succeed by mastering your craft over time.",
                f"Mercury in {mercury} defines how you think and work. Your mind focuses on strategy, analysis, and improvement rather than improvisation.",
                f"Mars in {mars} fuels your drive. When motivated, you work with intensity and discipline; when blocked, frustration builds fast.",
                f"Jupiter expands your potential through learning, vision, and calculated risks. Growth comes when you trust your competence.",
                f"Saturn reveals where you feel judged or limited — and where real authority is built through consistency.",
            ]
        )

    elif topic == "personal":
        text = reading_block(
            "PERSONAL GROWTH — Your Inner Architecture",
            [
                f"Your Sun in {sun} defines who you are becoming. Growth for you means responsibility, structure, and purpose.",
                f"Moon in {moon} shows how you process emotions. You feel deeply, even when you appear controlled or distant.",
                f"Ascendant in {asc} shapes how you face life. You don’t rush — you observe, evaluate, and then act decisively.",
                f"Saturn marks your inner critic. Growth accelerates when you stop carrying everything alone.",
                f"Your power lies in integration: mind, emotion, and action aligned.",
            ]
        )

    elif topic == "money":
        text = reading_block(
            "MONEY & SECURITY — Your Relationship with Stability",
            [
                f"Sun in {sun} seeks control and long-term safety with money.",
                f"Moon in {moon} links spending to emotions — comfort and reassurance matter.",
                f"Venus in {venus} reveals what you value enough to invest in.",
                f"Saturn shows financial fear patterns and discipline.",
                f"Wealth grows when structure replaces impulse.",
            ]
        )

    elif topic == "communication":
        text = reading_block(
            "COMMUNICATION — How You Express Yourself",
            [
                f"Mercury in {mercury} defines your communication style.",
                f"Moon in {moon} colors your tone emotionally.",
                f"Ascendant in {asc} shapes first impressions.",
                f"You’re most powerful when clarity replaces silence.",
                f"Say less, but say it directly.",
            ]
        )

    else:
        text = reading_block(
            "CORE BLUEPRINT — Who You Are",
            [
                f"Sun in {sun}, Moon in {moon}, Ascendant in {asc} form your core identity.",
                f"Your life theme is integration: depth with direction.",
                f"You are not random — your patterns repeat until understood.",
                f"Once aligned, you become unstoppable.",
            ]
        )

    return {
        "topic": topic,
        "text": text
    }

# ------------------
# RUN
# ------------------
if __name__ == "__main__":
    import os, uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
