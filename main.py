from fastapi import FastAPI
import swisseph as swe
from datetime import datetime

app = FastAPI()

swe.set_ephe_path(".")

SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

def zodiac_sign(longitude: float) -> str:
    longitude = longitude % 360
    return SIGNS[int(longitude // 30)]

@app.get("/")
def root():
    return {"ok": True, "try": "/docs or /chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5"}

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
        xx, _ = swe.calc_ut(jd, planet)   # xx[0]=lon, xx[1]=lat
        lon_p = float(xx[0])
        lat_p = float(xx[1])
        result[name] = {
            "longitude": lon_p,
            "latitude": lat_p,
            "sign": zodiac_sign(lon_p)
        }

    houses, ascmc = swe.houses(jd, lat, lon)
    asc_sign = zodiac_sign(float(ascmc[0]))

    return {
        "planets": result,
        "ascendant": asc_sign
    }

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
