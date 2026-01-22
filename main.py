from fastapi import FastAPI
from datetime import datetime
import os
import swisseph as swe

app = FastAPI()

# --- CONFIG ---
swe.set_ephe_path(".")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def zodiac_sign(longitude: float) -> str:
    longitude = longitude % 360
    return SIGNS[int(longitude // 30)]

# --- HEALTH CHECK (fondamentale) ---
@app.get("/")
def root():
    return {"ok": True, "service": "astro-engine", "try": "/docs"}

@app.get("/chart")
def calculate_chart(date: str, time: str, lat: float, lon: float):
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
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
    for name, planet in planets.items():
        lon_p, _, _ = swe.calc_ut(jd, planet)
        result[name] = {"longitude": lon_p, "sign": zodiac_sign(lon_p)}

    houses, ascmc = swe.houses(jd, lat, lon)
    asc_sign = zodiac_sign(ascmc[0])

    return {"planets": result, "ascendant": asc_sign}


# --- AVVIO LOCALE/RAILWAY ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
