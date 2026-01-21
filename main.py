from fastapi import FastAPI
from datetime import datetime
import swisseph as swe

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/birth-chart")
def birth_chart(data: dict):
    year = data["year"]
    month = data["month"]
    day = data["day"]
    hour = data["hour"] + data.get("minute", 0) / 60
    lat = data["lat"]
    lon = data["lon"]

    swe.set_ephe_path(".")

    jd = swe.julday(year, month, day, hour)

    planets = {
        "sun": swe.calc_ut(jd, swe.SUN)[0][0],
        "moon": swe.calc_ut(jd, swe.MOON)[0][0],
        "mercury": swe.calc_ut(jd, swe.MERCURY)[0][0],
        "venus": swe.calc_ut(jd, swe.VENUS)[0][0],
        "mars": swe.calc_ut(jd, swe.MARS)[0][0],
        "jupiter": swe.calc_ut(jd, swe.JUPITER)[0][0],
        "saturn": swe.calc_ut(jd, swe.SATURN)[0][0],
    }

    houses = swe.houses(jd, lat, lon)[0]
    ascendant = houses[0]

    return {
        "planets": planets,
        "ascendant": ascendant
    }
