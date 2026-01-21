
from fastapi import FastAPI
import swisseph as swe
from datetime import datetime

app = FastAPI()

swe.set_ephe_path(".")

SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

def zodiac_sign(longitude):
    return SIGNS[int(longitude // 30)]

@app.get("/chart")
def calculate_chart(date: str, time: str, lat: float, lon: float):
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60)

    planets = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mercury": swe.MERCURY,
        "venus": swe.VENUS,
        "mars": swe.MARS,
        "jupiter": swe.JUPITER,
        "saturn": swe.SATURN
    }

    result = {}

    for name, planet in planets.items():
        lon, _, _ = swe.calc_ut(jd, planet)
        result[name] = {
            "longitude": lon,
            "sign": zodiac_sign(lon)
        }

    houses, ascmc = swe.houses(jd, lat, lon)
    asc_sign = zodiac_sign(ascmc[0])

    return {
        "planets": result,
        "ascendant": asc_sign
    }
