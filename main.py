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

sun = chart["planets"]["sun"]["sign"]
moon = chart["planets"]["moon"]["sign"]
asc = chart["ascendant"]["sign"]


    if data.topic == "love":
        text = f"""
You love deeply and selectively.
With Sun in {sun} and Moon in {moon}, you seek emotional loyalty
but also intensity. Relationships transform you.
Your Ascendant in {asc} makes others perceive you as magnetic.
"""
    elif data.topic == "career":
        text = f"""
Your vocation grows through discipline and intuition.
Sun in {sun} gives ambition, Moon in {moon} creativity.
Your Ascendant in {asc} pushes you to lead in your own way.
"""
    else:
        text = f"""
Your chart shows a complex and evolving inner world.
Sun in {sun}, Moon in {moon}, Ascendant in {asc}.
This is a foundation for growth.
"""

    return {
        "topic": data.topic,
        "text": text.strip()
    }
