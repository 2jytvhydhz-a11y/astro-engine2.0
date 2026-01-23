from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal
from datetime import datetime
import swisseph as swe
import hashlib
import random
from typing import Any, Dict, List

PLANET_KEYS = ["sun","moon","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto"]

SIGN_TRAITS = {
    "aries":      {"tone":"direct", "drive":"bold", "love":"chase", "work":"lead"},
    "taurus":     {"tone":"steady", "drive":"patient", "love":"loyalty", "work":"build"},
    "gemini":     {"tone":"curious", "drive":"quick", "love":"talk", "work":"variety"},
    "cancer":     {"tone":"protective", "drive":"caring", "love":"bond", "work":"support"},
    "leo":        {"tone":"warm", "drive":"proud", "love":"romance", "work":"shine"},
    "virgo":      {"tone":"precise", "drive":"improve", "love":"acts", "work":"optimize"},
    "libra":      {"tone":"harmonious", "drive":"balanced", "love":"partnership", "work":"mediate"},
    "scorpio":    {"tone":"intense", "drive":"focused", "love":"depth", "work":"transform"},
    "sagittarius":{"tone":"free", "drive":"explore", "love":"adventure", "work":"expand"},
    "capricorn":  {"tone":"serious", "drive":"achieve", "love":"commit", "work":"structure"},
    "aquarius":   {"tone":"original", "drive":"innovate", "love":"space", "work":"disrupt"},
    "pisces":     {"tone":"sensitive", "drive":"flow", "love":"merge", "work":"create"},
}

def trait(sign: str, key: str, default: str = "") -> str:
    return SIGN_TRAITS.get(sign, {}).get(key, default)

def stable_rng(seed_str: str) -> random.Random:
    h = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))

def pick(rng: random.Random, items: List[str]) -> str:
    return items[rng.randrange(0, len(items))]

def normalize_planets(chart: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Returns planets as dict: { 'sun': {'sign':'capricorn'}, ... }
    Accepts either chart['planets'] as dict or list.
    """
    raw = chart.get("planets")
    out: Dict[str, Dict[str, str]] = {}

    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                sign = (v.get("sign") or "").lower().strip()
            else:
                sign = str(v).lower().strip()
            if k:
                out[str(k).lower().strip()] = {"sign": sign}
        return out

    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            key = (item.get("key") or item.get("name") or "").lower().strip()
            sign = (item.get("sign") or "").lower().strip()
            if key:
                out[key] = {"sign": sign}
        return out

    return out

def get_asc_sign(chart: Dict[str, Any]) -> str:
    asc = chart.get("ascendant")
    if isinstance(asc, dict):
        return (asc.get("sign") or "").lower().strip()
    if isinstance(asc, str):
        return asc.lower().strip()
    return ""
    def describe_placement(planet: str, sign: str) -> str:
    if not sign:
        return ""
    if planet == "sun":
        return f"Sun in {sign.title()}: identity runs on {trait(sign,'drive','your rhythm')} and {trait(sign,'tone','clarity')}."
    if planet == "moon":
        return f"Moon in {sign.title()}: emotional needs center on {trait(sign,'love','connection')} and consistency."
    if planet == "venus":
        return f"Venus in {sign.title()}: love style moves toward {trait(sign,'love','connection')} and away from its opposite."
    if planet == "mars":
        return f"Mars in {sign.title()}: action style is {trait(sign,'drive','momentum')}—you pursue what matters directly."
    if planet == "mercury":
        return f"Mercury in {sign.title()}: communication prefers {trait(sign,'tone','clarity')} and that processing style."
    if planet == "saturn":
        return f"Saturn in {sign.title()}: growth edge is mastering {trait(sign,'work','structure')} with patience."
    if planet == "jupiter":
        return f"Jupiter in {sign.title()}: expansion happens when you lean into {trait(sign,'work','growth')} and take bigger swings."
    return f"{planet.title()} in {sign.title()}."

def generate_love(birth_profile: Dict[str, Any], lang: str="en") -> str:
    chart = birth_profile.get("chart") or {}
    planets = normalize_planets(chart)
    asc = get_asc_sign(chart)
    rng = stable_rng(f"{birth_profile.get('birthDate','')}-love")

    sun = planets.get("sun", {}).get("sign","")
    moon = planets.get("moon", {}).get("sign","")
    venus = planets.get("venus", {}).get("sign","")
    mars = planets.get("mars", {}).get("sign","")
    mercury = planets.get("mercury", {}).get("sign","")

    title = pick(rng, [
        "LOVE & RELATIONSHIPS — Your Emotional Pattern",
        "LOVE — How You Bond, Trust, and Choose",
        "LOVE — What You Need, What You Give, What You Avoid",
    ])

    lines = [title, "", "YOUR LOVE BLUEPRINT"]
    if sun: lines.append(describe_placement("sun", sun))
    if moon: lines.append(describe_placement("moon", moon))
    if venus: lines.append(describe_placement("venus", venus))
    if mars: lines.append(describe_placement("mars", mars))
    if mercury: lines.append(describe_placement("mercury", mercury))
    if asc: lines.append(f"Ascendant in {asc.title()}: it shapes first impressions and how you protect your heart.")

    lines += ["", "3 MICRO-ACTIONS"]
    actions = [
        "State one non-negotiable early (boundaries prevent chaos).",
        "Ask for one concrete behavior (compatibility shows in actions).",
        "When triggered, pause before replying (respond from values, not adrenaline).",
    ]
    rng.shuffle(actions)
    lines.extend([f"- {a}" for a in actions])

    return "\n".join(lines)

def generate_career(birth_profile: Dict[str, Any], lang: str="en") -> str:
    chart = birth_profile.get("chart") or {}
    planets = normalize_planets(chart)
    asc = get_asc_sign(chart)
    rng = stable_rng(f"{birth_profile.get('birthDate','')}-career")

    sun = planets.get("sun", {}).get("sign","")
    mars = planets.get("mars", {}).get("sign","")
    saturn = planets.get("saturn", {}).get("sign","")
    jupiter = planets.get("jupiter", {}).get("sign","")
    mercury = planets.get("mercury", {}).get("sign","")

    title = pick(rng, [
        "CAREER & DIRECTION — Your Path",
        "CAREER — Where You Win and Why",
        "CAREER — Your Work Signature",
    ])

    lines = [title, "", "YOUR WORK SIGNATURE"]
    if sun: lines.append(describe_placement("sun", sun))
    if mercury: lines.append(describe_placement("mercury", mercury))
    if mars: lines.append(describe_placement("mars", mars))

    lines += ["", "SCALE vs STABILITY"]
    if jupiter: lines.append(describe_placement("jupiter", jupiter))
    if saturn: lines.append(describe_placement("saturn", saturn))
    if asc: lines.append(f"Ascendant in {asc.title()}: it colors how others perceive your competence.")

    lines += ["", "3 CAREER MOVES"]
    moves = [
        "Pick roles that reward your natural pace (fast vs deep).",
        "Turn one strength into a repeatable system (portfolio → proof → offer).",
        "Track one KPI weekly (output, money, users) to avoid emotional drifting.",
    ]
    rng.shuffle(moves)
    lines.extend([f"- {m}" for m in moves])

    return "\n".join(lines)

app = FastAPI(title="AstroFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Middleware: request logging
# -----------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    print(f"[REQ] {request.method} {request.url.path} origin={origin}")
    response = await call_next(request)
    print(f"[RES] {request.method} {request.url.path} -> {response.status_code}")
    return response

# -----------------------------
# CORS
# -----------------------------
# -----------------------------
# Swiss Ephemeris setup
# -----------------------------
swe.set_ephe_path(".")

SIGNS_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
SIGNS_IT = [
    "Ariete", "Toro", "Gemelli", "Cancro", "Leone", "Vergine",
    "Bilancia", "Scorpione", "Sagittario", "Capricorno", "Acquario", "Pesci"
]
SIGNS_ES = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
]

def zodiac_sign_index(longitude: float) -> int:
    lon = float(longitude) % 360.0
    return int(lon // 30)

def sign_name(sign_en: str, lang: str) -> str:
    """Input sign is expected in EN. Output in requested lang."""
    try:
        idx = SIGNS_EN.index(sign_en.capitalize())
    except Exception:
        # If already localized or unknown, return as-is
        return sign_en
    if lang == "it":
        return SIGNS_IT[idx]
    if lang == "es":
        return SIGNS_ES[idx]
    return SIGNS_EN[idx]

def pretty_planet_name(p: str, lang: str) -> str:
    p = (p or "").lower().strip()
    names = {
        "en": {
            "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
            "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
            "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto",
            "ascendant": "Ascendant"
        },
        "it": {
            "sun": "Sole", "moon": "Luna", "mercury": "Mercurio", "venus": "Venere",
            "mars": "Marte", "jupiter": "Giove", "saturn": "Saturno",
            "uranus": "Urano", "neptune": "Nettuno", "pluto": "Plutone",
            "ascendant": "Ascendente"
        },
        "es": {
            "sun": "Sol", "moon": "Luna", "mercury": "Mercurio", "venus": "Venus",
            "mars": "Marte", "jupiter": "Júpiter", "saturn": "Saturno",
            "uranus": "Urano", "neptune": "Neptuno", "pluto": "Plutón",
            "ascendant": "Ascendente"
        }
    }
    return names.get(lang, names["en"]).get(p, p.capitalize())

def safe_get_sign(chart: Dict[str, Any], key: str) -> str:
    """
    Supports multiple shapes:
    - chart["planets"] as dict:
        { "sun": { "sign": "Capricorn" }, ... }
    - chart["planets"] as list:
        [ { "key": "sun", "sign": "capricorn" }, ... ]
    - chart["ascendant"] as dict or string
    """

    if not chart:
        return ""

    # Special case: ascendant
    if key == "ascendant":
        asc = chart.get("ascendant")
        if isinstance(asc, dict):
            return str(asc.get("sign") or "")
        if isinstance(asc, str):
            return asc
        return ""

    planets = chart.get("planets")

    # Case 1: planets is a dict
    if isinstance(planets, dict):
        v = planets.get(key)
        if isinstance(v, dict):
            return str(v.get("sign") or "")
        if isinstance(v, str):
            return v
        return ""

    # Case 2: planets is a list
    if isinstance(planets, list):
        for p in planets:
            if not isinstance(p, dict):
                continue
            if p.get("key") == key:
                return str(p.get("sign") or "")
        return ""

    return ""

def normalize_sign_en(s: str) -> str:
    # Normalize to EN titlecase if it matches known EN signs
    if not s:
        return ""
    s2 = s.strip().lower()
    for en in SIGNS_EN:
        if en.lower() == s2:
            return en
    # if it's not EN (maybe IT/ES) keep as-is
    return s.strip()

def clamp_lang(lang: Optional[str]) -> str:
    lang = (lang or "en").lower().strip()
    if lang not in ("en", "it", "es"):
        return "en"
    return lang

# -----------------------------
# API: Root
# -----------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "try": "/docs",
        "example_chart": "/chart?date=1998-01-01&time=12:30&lat=41.9&lon=12.5&tz_offset=1",
        "example_reading": "POST /readings { birth_profile:{chart:{...}}, topic:'love', lang:'it' }"
    }

# -----------------------------
# API: Chart (Swiss Ephemeris)
# -----------------------------
@app.get("/chart")
def calculate_chart(
    date: str,
    time: str,
    lat: float,
    lon: float,
    tz_offset: float = 0.0
):
    """
    date: YYYY-MM-DD
    time: HH:MM (local time)
    tz_offset: hours to convert local->UT (e.g. Italy winter = +1, summer = +2)
              We compute UT = local_time - tz_offset
    """
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=422, detail="lat/lon out of range")

    try:
        dt_local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date/time format. Use YYYY-MM-DD and HH:MM")

    # Convert local time -> UT
    ut_hour = (dt_local.hour + dt_local.minute / 60.0) - float(tz_offset)
    jd = swe.julday(dt_local.year, dt_local.month, dt_local.day, ut_hour)

    planets = {
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

    result = {}

    try:
        for name, planet in planets.items():
            xx, _ = swe.calc_ut(jd, planet)  # xx[0]=lon
            lon_p = float(xx[0])
            idx = zodiac_sign_index(lon_p)
            result[name] = {"longitude": lon_p, "sign": SIGNS_EN[idx]}

        # Houses / Ascendant
        houses, ascmc = swe.houses(jd, lat, lon)
        asc_lon = float(ascmc[0])
        asc_idx = zodiac_sign_index(asc_lon)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SwissEphemeris error: {str(e)}")

    return {
        "planets": result,
        "ascendant": {"longitude": asc_lon, "sign": SIGNS_EN[asc_idx]},
        "meta": {
            "tz_offset": tz_offset,
            "note": "Ascendant depends strongly on timezone and exact birth time."
        }
    }

# -----------------------------
# Readings (WOW, multi-planet)
# -----------------------------
Lang = Literal["en", "it", "es"]

class ReadingRequest(BaseModel):
    birth_profile: Dict[str, Any] = Field(default_factory=dict)
    topic: str
    lang: Optional[Lang] = "en"

TOPICS = {
    "love",
    "career",
    "money",
    "personal",
    "timing",
    "strengths",
    "shadow",
    "communication",
    "health",
    "friendships",
    "purpose"
}

def t(lang: str, key: str) -> str:
    # Small i18n dictionary for section labels.
    D = {
        "en": {
            "title_love": "LOVE & RELATIONSHIPS — Your Emotional Pattern",
            "title_career": "CAREER & DIRECTION — Your Path",
            "title_money": "MONEY & STABILITY — Your Flow",
            "title_personal": "PERSONAL GROWTH — Your Inner Blueprint",
            "title_timing": "TIMING — Your Momentum",
            "title_strengths": "STRENGTHS — What You Do Best",
            "title_shadow": "SHADOW PATTERNS — What Blocks You",
            "title_communication": "COMMUNICATION — How To Be Understood",
            "title_health": "HEALTH & ENERGY — How You Recharge",
            "title_friendships": "FRIENDSHIPS — Your Social Style",
            "title_purpose": "PURPOSE — What You’re Here To Build",
            "core": "THE CORE (how you’re wired)",
            "mind": "YOUR MIND PATTERN (how you think)",
            "heart": "YOUR HEART PATTERN (how you love)",
            "drive": "YOUR DRIVE (how you act)",
            "growth": "YOUR GROWTH EDGE (what expands you)",
            "lesson": "YOUR DEEP LESSON (what matures you)",
            "wow": "WOW PRACTICE (1 minute)",
        },
        "it": {
            "title_love": "AMORE & RELAZIONI — Il tuo schema emotivo",
            "title_career": "CARRIERA & DIREZIONE — La tua strada",
            "title_money": "DENARO & STABILITÀ — Il tuo flusso",
            "title_personal": "CRESCITA PERSONALE — Il tuo blueprint interiore",
            "title_timing": "TEMPI — Il tuo ritmo",
            "title_strengths": "PUNTI DI FORZA — Ciò che fai meglio",
            "title_shadow": "OMBRE — Ciò che ti blocca",
            "title_communication": "COMUNICAZIONE — Come farti capire davvero",
            "title_health": "SALUTE & ENERGIA — Come ti ricarichi",
            "title_friendships": "AMICIZIE — Il tuo stile sociale",
            "title_purpose": "SCOPO — Cosa sei qui per costruire",
            "core": "IL NUCLEO (come sei fatto dentro)",
            "mind": "IL TUO MODO DI PENSARE (pattern mentale)",
            "heart": "IL TUO MODO DI AMARE (pattern del cuore)",
            "drive": "LA TUA SPINTA (come agisci)",
            "growth": "LA TUA ESPANSIONE (cosa ti fa crescere)",
            "lesson": "LA TUA LEZIONE PROFONDA (cosa ti rende maturo)",
            "wow": "WOW PRACTICE (1 minuto)",
        },
        "es": {
            "title_love": "AMOR & RELACIONES — Tu patrón emocional",
            "title_career": "CARRERA & DIRECCIÓN — Tu camino",
            "title_money": "DINERO & ESTABILIDAD — Tu flujo",
            "title_personal": "CRECIMIENTO PERSONAL — Tu blueprint interior",
            "title_timing": "TIEMPOS — Tu ritmo",
            "title_strengths": "FORTALEZAS — Lo que haces mejor",
            "title_shadow": "SOMBRA — Lo que te bloquea",
            "title_communication": "COMUNICACIÓN — Cómo ser entendido de verdad",
            "title_health": "SALUD & ENERGÍA — Cómo recargas",
            "title_friendships": "AMISTADES — Tu estilo social",
            "title_purpose": "PROPÓSITO — Lo que viniste a construir",
            "core": "EL NÚCLEO (cómo estás hecho por dentro)",
            "mind": "TU MENTE (patrón mental)",
            "heart": "TU CORAZÓN (patrón afectivo)",
            "drive": "TU IMPULSO (cómo actúas)",
            "growth": "TU EXPANSIÓN (lo que te hace crecer)",
            "lesson": "TU LECCIÓN PROFUNDA (lo que te madura)",
            "wow": "WOW PRACTICE (1 minuto)",
        }
    }
    return D.get(lang, D["en"]).get(key, key)

def build_wow_reading(
    topic: str,
    lang: str,
    sun: str,
    moon: str,
    asc: str,
    mercury: str,
    venus: str,
    mars: str,
    jupiter: str,
    saturn: str,
    extras: Dict[str, str]
) -> str:
    # Localized signs
    sunL = sign_name(sun, lang)
    moonL = sign_name(moon, lang)
    ascL = sign_name(asc, lang)
    merL = sign_name(mercury, lang)
    venL = sign_name(venus, lang)
    marL = sign_name(mars, lang)
    jupL = sign_name(jupiter, lang)
    satL = sign_name(saturn, lang)

    # Optional outer planets
    urL = sign_name(extras.get("uranus", ""), lang)
    neL = sign_name(extras.get("neptune", ""), lang)
    plL = sign_name(extras.get("pluto", ""), lang)

    # Choose title key by topic
    title_key = f"title_{topic}"
    title = t(lang, title_key) if title_key in (t(lang, k) for k in []) else t(lang, title_key)
    # (fallback if missing)
    if "title_" + topic not in [
        "title_love","title_career","title_money","title_personal","title_timing",
        "title_strengths","title_shadow","title_communication","title_health","title_friendships","title_purpose"
    ]:
        title = t(lang, "title_personal")

    # Core “wow” style: short bold headers + dense punchy paragraphs.
    # We keep it deterministic: planet->meaning is generalized but feels personal.
    if lang == "it":
        base = f"""{title}

{t(lang,'core')}  Sole in {sunL} è il tuo motore: non vivi di “idee”, vivi di risultati. Ti rispetti quando fai ciò che hai detto che avresti fatto.  
Luna in {moonL} è il tuo cuore: hai bisogno di sentirti visto, valorizzato, scelto — non a parole, ma nei fatti.  
Ascendente in {ascL} è la tua maschera sociale: dai un’immagine equilibrata e “a posto”, ma dentro lavori molto più a fondo di quanto la gente immagini.

{t(lang,'mind')}  Mercurio in {merL} ti rende lucido e strategico: pensi in modo concreto, tagli il superfluo, vai dritto al punto.  
Il rischio? Quando sei sotto pressione, la mente diventa “controllo”: cerchi la mossa perfetta e rimandi quella vera.

{t(lang,'heart')}  Venere in {venL} dice come ami davvero: quando ti leghi, vuoi intensità, lealtà e verità emotiva.  
Non ti interessa il “carino”: ti interessa ciò che regge. Se senti ambiguità, ti chiudi o testi — perché per te fiducia = sicurezza.

{t(lang,'drive')}  Marte in {marL} è la tua modalità d’azione: ti muovi con precisione, migliorando passo dopo passo.  
Se qualcosa non torna, lo aggiusti. Se qualcosa è vago, lo rendi chiaro. La tua forza è la disciplina intelligente, non la fretta.

{t(lang,'growth')}  Giove in {jupL} è dove cresci: quando smetti di giocare piccolo e inizi a prenderti spazio.  
La fortuna per te arriva quando ti esponi con stile: presenza, reputazione, decisioni pulite.

{t(lang,'lesson')}  Saturno in {satL} è la lezione: impari a non portare tutto da solo.  
La tua maturità è emotiva: dire ciò che provi prima che diventi durezza. Chiedere prima che diventi distanza."""
        if urL or neL or plL:
            base += "\n\n"
            if urL:
                base += f"Urano in {urL} aggiunge una parte ribelle: quando ti senti stretto, cambi tutto di colpo. Impara a cambiare senza distruggere.\n"
            if neL:
                base += f"Nettuno in {neL} amplifica l’intuizione: senti le persone. Il confine è non assorbire ciò che non è tuo.\n"
            if plL:
                base += f"Plutone in {plL} è il tuo potere: trasformi te stesso quando decidi. Non a metà. Per davvero.\n"

        # Topic-specific “hook”
        if topic == "love":
            base += f"""

{t(lang,'wow')}  Oggi: scegli UNA frase vera che non dici mai.  
Tipo: “Io ho bisogno di chiarezza” / “Io voglio costanza” / “Io non mi accontento”.  
Dilla (a voce o scritta) senza spiegarti troppo. È così che smetti di testare e inizi a creare legami reali."""
        elif topic == "career":
            base += f"""

{t(lang,'wow')}  Oggi: fai una mossa da “Capricorno che guida”, non da “Capricorno che aspetta”.  
Scrivi 1 obiettivo misurabile (piccolo ma reale) e fai 1 azione di 20 minuti che lo avvicina.  
La tua magia non è motivazione: è traiettoria."""
        elif topic == "money":
            base += f"""

{t(lang,'wow')}  Oggi: scegli un “no” che ti salva soldi e un “sì” che ti fa crescere.  
No = taglio di una spesa automatica.  
Sì = una micro-decisione che aumenta valore (skill, portfolio, strumento).  
Il tuo denaro segue la tua identità: solida, non impulsiva."""
        else:
            base += f"""

{t(lang,'wow')}  Oggi: nomina il sentimento in UNA frase (senza storia).  
Poi fai UNA cosa che lo rispetta.  
Il tuo “wow” nasce quando smetti di essere forte per abitudine e inizi a essere vero per scelta."""
        return base.strip()

    if lang == "es":
        base = f"""{title}

{t(lang,'core')}  Sol en {sunL} es tu motor: no vives de “ideas”, vives de resultados. Te respetas cuando haces lo que dijiste que harías.  
Luna en {moonL} es tu corazón: necesitas sentirte visto, valorado, elegido — no con palabras, sino con hechos.  
Ascendente en {ascL} es tu máscara social: pareces equilibrado y “en control”, pero por dentro vas mucho más profundo de lo que la gente imagina.

{t(lang,'mind')}  Mercurio en {merL} te vuelve estratégico: piensas con precisión, cortas lo innecesario y vas al punto.  
El riesgo: bajo presión, la mente se convierte en control. Buscas la jugada perfecta y pospones la real.

{t(lang,'heart')}  Venus en {venL} muestra cómo amas: cuando te vinculas, quieres intensidad, lealtad y verdad emocional.  
No te interesa lo “bonito”: te interesa lo que se sostiene. Si sientes ambigüedad, te cierras o pruebas — porque para ti confianza = seguridad.

{t(lang,'drive')}  Marte en {marL} es tu forma de actuar: avanzas con método, mejorando paso a paso.  
Si algo no encaja, lo ajustas. Si algo es vago, lo vuelves claro.

{t(lang,'growth')}  Júpiter en {jupL} es donde creces: cuando dejas de jugar pequeño y ocupas tu lugar.  
Tu suerte aparece cuando te expones con estilo: presencia, reputación, decisiones limpias.

{t(lang,'lesson')}  Saturno en {satL} es la lección: aprender a no cargar con todo solo.  
Tu madurez es emocional: decir lo que sientes antes de que se convierta en dureza."""
        if urL or neL or plL:
            base += "\n\n"
            if urL:
                base += f"Urano en {urL} añade rebeldía: cuando te sientes atrapado, cambias todo de golpe. Aprende a cambiar sin destruir.\n"
            if neL:
                base += f"Neptuno en {neL} amplifica la intuición: sientes a la gente. El límite es no absorber lo que no es tuyo.\n"
            if plL:
                base += f"Plutón en {plL} es tu poder: te transformas cuando decides. No a medias.\n"

        base += f"""

{t(lang,'wow')}  Hoy: nombra la emoción en UNA frase (sin historia).  
Luego haz UNA acción que la respete.  
Tu “wow” aparece cuando dejas de ser fuerte por costumbre y empiezas a ser verdadero por elección."""
        return base.strip()

    # EN default
    base = f"""{title}

{t(lang,'core')}  Sun in {sunL} is your identity engine: you don’t live on “ideas”, you live on outcomes. You respect yourself when you do what you said you’d do.  
Moon in {moonL} is your emotional core: you need to feel seen, valued, chosen — not with words, but with real consistency.  
Ascendant in {ascL} is your social armor: you look composed, balanced, “fine”… while inside you’re carrying much more depth than people assume.

{t(lang,'mind')}  Mercury in {merL} makes you strategic: you think in clean lines, cut the noise, and move toward what works.  
Under pressure, this can turn into control: you search for the perfect move and delay the true one.

{t(lang,'heart')}  Venus in {venL} shows how you love: when you attach, you want intensity, loyalty, emotional truth — not casual affection.  
You don’t want “nice”. You want real. When you sense ambiguity, you may pull back or test — because for you, trust equals safety.

{t(lang,'drive')}  Mars in {marL} is your action style: precise, steady, improvement-focused.  
If something is off, you fix it. If something is vague, you clarify it. Your power is intelligent discipline, not rushed intensity.

{t(lang,'growth')}  Jupiter in {jupL} is your expansion: you grow when you stop playing small and let yourself be seen.  
Your luck increases when you show up with style: presence, reputation, clean decisions.

{t(lang,'lesson')}  Saturn in {satL} is your deep lesson: learning not to carry everything alone.  
Your maturity is emotional — saying what you feel before it turns into hardness. Asking before it turns into distance."""
    if urL or neL or plL:
        base += "\n\n"
        if urL:
            base += f"Uranus in {urL} adds a rebellious streak: when you feel boxed in, you change everything fast. Learn to change without burning bridges.\n"
        if neL:
            base += f"Neptune in {neL} amplifies intuition: you read people deeply. The boundary is not absorbing what isn’t yours.\n"
        if plL:
            base += f"Pluto in {plL} is your power: you transform when you decide. Not halfway — for real.\n"

    # Topic hook
    if topic == "love":
        base += f"""

{t(lang,'wow')}  Today: choose ONE sentence you never say out loud.  
“I need clarity.” / “I want consistency.” / “I don’t do half-love.”  
Say it (voice or text) without over-explaining. That’s how you stop testing and start creating real bonds."""
    elif topic == "career":
        base += f"""

{t(lang,'wow')}  Today: make one move like someone who leads — not someone who waits.  
Write 1 measurable outcome, then do 20 minutes that moves it forward.  
Your magic isn’t motivation. It’s trajectory."""
    elif topic == "money":
        base += f"""

{t(lang,'wow')}  Today: pick one “NO” that saves money, and one “YES” that grows your value.  
NO = cut one automatic expense.  
YES = one micro-investment in skill, tool, or output.  
Your money follows identity: solid, not impulsive."""
    else:
        base += f"""

{t(lang,'wow')}  Today: name the feeling in ONE sentence (no story).  
Then take ONE action that matches truth.  
Your “wow” begins when you stop being strong by habit and start being real by choice."""
    return base.strip()

@app.post("/readings")
def generate_reading(data: ReadingRequest):
    lang = clamp_lang(data.lang)
    topic = (data.topic or "").lower().strip()
    if topic not in TOPICS:
        # keep it safe
        topic = "personal"

    birth_profile = data.birth_profile or {}
    chart = (birth_profile.get("chart") or {})

    # Extract signs (EN ideally)
    sun = normalize_sign_en(safe_get_sign(chart, "sun"))
    moon = normalize_sign_en(safe_get_sign(chart, "moon"))
    asc = normalize_sign_en(safe_get_sign(chart, "ascendant"))

    mercury = normalize_sign_en(safe_get_sign(chart, "mercury"))
    venus = normalize_sign_en(safe_get_sign(chart, "venus"))
    mars = normalize_sign_en(safe_get_sign(chart, "mars"))
    jupiter = normalize_sign_en(safe_get_sign(chart, "jupiter"))
    saturn = normalize_sign_en(safe_get_sign(chart, "saturn"))

    # Extras if present
    extras = {
        "uranus": normalize_sign_en(safe_get_sign(chart, "uranus")),
        "neptune": normalize_sign_en(safe_get_sign(chart, "neptune")),
        "pluto": normalize_sign_en(safe_get_sign(chart, "pluto")),
    }

    # Fallbacks if missing (avoid ugly "Sun in ")
    def fb(x: str) -> str:
        return x if x else "Unknown"

    text = generate_reading_text(
    payload.topic,
    payload.birth_profile,
    payload.lang
)

    print("DEBUG BACKEND → topic:", topic, flush=True)
    print("DEBUG BACKEND → text preview:", text[:120], flush=True)

    return {
        "topic": topic,
        "lang": lang,
        "text": text
    }

# Railway / container entry
if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
