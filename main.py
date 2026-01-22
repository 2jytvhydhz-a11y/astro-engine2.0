from fastapi import FastAPI, HTTPException
from datetime import datetime
import swisseph as swe

# --------------------
# App
# --------------------
app = FastAPI()

# Swiss Ephemeris setup
swe.set_ephe_path(".")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def zodiac_sign(longitude: float) -> str:
    longitude = longitude % 360
    return SIGNS[int(longitude // 30)]

# --------------------
# Root
# --------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "try": "/docs",
        "example": "/chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5"
    }

# --------------------
# Chart endpoint
# --------------------
@app.get("/chart")
def calculate_chart(date: str, time: str, lat: float, lon: float):
    try:
        # Parse datetime (UT)
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

        # Julian day
        jd = swe.julday(
            dt.year,
            dt.month,
            dt.day,
            dt.hour + dt.minute / 60.0
        )

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
            xx, _ = swe.calc_ut(jd, planet)
            lon_p = float(xx[0])
            result[name] = {
                "longitude": lon_p,
                "sign": zodiac_sign(lon_p)
            }

        # Houses & Ascendant
        houses, ascmc = swe.houses(jd, lat, lon)
        asc_sign = zodiac_sign(ascmc[0])

        return {
            "planets": result,
            "ascendant": asc_sign
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
