from fastapi import FastAPI
from datetime import datetime
import os
import uvicorn
import swisseph as swe

app = FastAPI(title="Astro Engine 2.0", version="2.0")

# Ephemeris path (ok anche così per ora)
swe.set_ephe_path(".")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN
}

def norm360(x: float) -> float:
    x = x % 360.0
    return x if x >= 0 else x + 360.0

def sign_info(longitude: float):
    lon = norm360(longitude)
    sign_index = int(lon // 30)
    sign = SIGNS[sign_index]
    deg_in_sign = lon - (sign_index * 30)

    d = int(deg_in_sign)
    m_float = (deg_in_sign - d) * 60
    m = int(m_float)
    s = int(round((m_float - m) * 60))

    # normalizzazione secondi/minuti
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    if d == 30:
        d = 29
        m = 59
        s = 59

    formatted = f"{d:02d}°{m:02d}'{s:02d}\" {sign}"

    return {
        "longitude": round(lon, 6),
        "sign": sign,
        "degree_in_sign": round(deg_in_sign, 6),
        "formatted": formatted
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {
        "ok": True,
        "try": "/docs",
        "example": "/chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5"
    }

@app.get("/chart")
def calculate_chart(date: str, time: str, lat: float, lon: float):
    """
    date: YYYY-MM-DD
    time: HH:MM
    lat/lon: coordinate in gradi (es. Roma 41.9, 12.5)
    Nota: trattiamo il datetime come UT per semplicità (poi aggiungiamo timezone dopo).
    """

    # Parse input
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    # Julian day UT
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    # (opzionale) topocentrico: migliora Luna/Asc un filo
    try:
        swe.set_topo(lon, lat, 0)
    except Exception:
        pass

    # Pianeti: long eclittica
    planets_out = {}
    for name, p in PLANETS.items():
        xx, _ = swe.calc_ut(jd, p)
        lon_ecl = float(xx[0])
        planets_out[name] = sign_info(lon_ecl)

    # Case
    # swe.houses ritorna: (cusps[1..12], ascmc[0..])
    cusps, ascmc = swe.houses(jd, lat, lon)

    houses_out = []
    for i in range(1, 13):
        houses_out.append({
            "house": i,
            "cusp": sign_info(float(cusps[i]))
        })

    # Angoli principali (ASC/MC ecc)
    # ascmc: 0=ASC, 1=MC, 2=ARMC, 3=Vertex, 4=Equasc, 5=Coasc1, 6=Coasc2, 7=Polar asc
    asc = float(ascmc[0])
    mc = float(ascmc[1])

    # Per IC e DSC calcolo semplice: opposti
    dsc = norm360(asc + 180.0)
    ic = norm360(mc + 180.0)

    angles_out = {
        "asc": sign_info(asc),
        "mc": sign_info(mc),
        "dsc": sign_info(dsc),
        "ic": sign_info(ic)
    }

    return {
        "meta": {
            "input": {"date": date, "time": time, "lat": lat, "lon": lon},
            "julian_day_ut": jd,
            "note": "Datetime interpretato come UT (timezone non gestito ancora)."
        },
        "planets": planets_out,
        "angles": angles_out,
        "houses": houses_out
    }

if __name__ == "__main__":
    # IMPORTANTISSIMO per Railway: usare la PORT dell'ambiente
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
