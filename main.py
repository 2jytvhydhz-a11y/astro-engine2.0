from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal, List, Tuple
from datetime import datetime, date
from zoneinfo import ZoneInfo
import hashlib
import random

import swisseph as swe

# Optional deps (recommended)
# pip install timezonefinder
try:
    from timezonefinder import TimezoneFinder  # type: ignore
except Exception:
    TimezoneFinder = None


# -----------------------------
# App
# -----------------------------
app = FastAPI(title="AstroFlow API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    print(f"[REQ] {request.method} {request.url.path} origin={origin}", flush=True)
    response = await call_next(request)
    print(f"[RES] {request.method} {request.url.path} -> {response.status_code}", flush=True)
    return response


# -----------------------------
# Swiss Ephemeris setup
# -----------------------------
swe.set_ephe_path(".")


# -----------------------------
# Constants
# -----------------------------
Lang = Literal["en", "it", "es"]
Depth = Literal["standard", "deep"]

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
    "purpose",
}

PLANETS = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]

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

ELEMENT = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

MODALITY = {
    "Aries": "cardinal", "Cancer": "cardinal", "Libra": "cardinal", "Capricorn": "cardinal",
    "Taurus": "fixed", "Leo": "fixed", "Scorpio": "fixed", "Aquarius": "fixed",
    "Gemini": "mutable", "Virgo": "mutable", "Sagittarius": "mutable", "Pisces": "mutable",
}

PLANET_WEIGHT = {
    "sun": 3.0, "moon": 3.0, "ascendant": 2.6,
    "mercury": 2.0, "venus": 2.0, "mars": 2.0,
    "jupiter": 1.6, "saturn": 1.9,
    "uranus": 1.1, "neptune": 1.1, "pluto": 1.2,
}

PLANET_NAMES = {
    "en": {
        "sun":"Sun","moon":"Moon","mercury":"Mercury","venus":"Venus","mars":"Mars",
        "jupiter":"Jupiter","saturn":"Saturn","uranus":"Uranus","neptune":"Neptune","pluto":"Pluto",
        "ascendant":"Ascendant"
    },
    "it": {
        "sun":"Sole","moon":"Luna","mercury":"Mercurio","venus":"Venere","mars":"Marte",
        "jupiter":"Giove","saturn":"Saturno","uranus":"Urano","neptune":"Nettuno","pluto":"Plutone",
        "ascendant":"Ascendente"
    },
    "es": {
        "sun":"Sol","moon":"Luna","mercury":"Mercurio","venus":"Venus","mars":"Marte",
        "jupiter":"Júpiter","saturn":"Saturno","uranus":"Urano","neptune":"Neptuno","pluto":"Plutón",
        "ascendant":"Ascendente"
    },
}

I18N = {
    "en": {
        "titles": {
            "personal": "PERSONAL GROWTH — Your Inner Blueprint",
            "love": "LOVE & RELATIONSHIPS — Your Bond Pattern",
            "career": "CAREER & DIRECTION — Your Work Signature",
            "money": "MONEY & RESOURCES — Your Material Flow",
            "shadow": "EMOTIONAL PATTERNS — Your Inner Shadow",
            "strengths": "STRENGTHS & WEAKNESSES — Your Power Balance",
            "communication": "COMMUNICATION — How You’re Understood",
            "timing": "TIMING — When to Push, When to Wait",
            "health": "HEALTH & ENERGY — How You Recharge",
            "friendships": "FRIENDSHIPS — Your Social Style",
            "purpose": "PURPOSE — What You’re Here to Build",
        },
        "sec": {
            "core":"THE CORE",
            "engine":"YOUR EMOTIONAL ENGINE",
            "mind":"YOUR MIND & VOICE",
            "drive":"HOW YOU ACT UNDER PRESSURE",
            "love":"YOUR LOVE PATTERN",
            "money":"YOUR VALUE & MONEY PATTERN",
            "shadow":"YOUR SHADOW LOOP",
            "strengths":"YOUR POWER MOVES",
            "timing":"YOUR TIMING LEVER",
            "health":"YOUR ENERGY HYGIENE",
            "social":"YOUR SOCIAL DNA",
            "purpose":"YOUR NORTH STAR",
            "wow":"WOW PRACTICE (1 minute)",
        },
        "fallback_soft": "Some parts are more fluid right now — not because they’re vague, but because your chart expresses them through nuance.",
    },
    "it": {
        "titles": {
            "personal": "CRESCITA PERSONALE — La tua mappa interiore",
            "love": "AMORE & RELAZIONI — Il tuo pattern di legame",
            "career": "CARRIERA & DIREZIONE — La tua firma nel lavoro",
            "money": "DENARO & RISORSE — Il tuo flusso materiale",
            "shadow": "PATTERN EMOTIVI — La tua ombra interiore",
            "strengths": "PUNTI DI FORZA & DEBOLEZZE — Il tuo equilibrio",
            "communication": "COMUNICAZIONE — Come ti fai capire davvero",
            "timing": "TEMPI — Quando spingere, quando aspettare",
            "health": "SALUTE & ENERGIA — Come ti ricarichi",
            "friendships": "AMICIZIE — Il tuo stile sociale",
            "purpose": "SCOPO — Cosa sei qui per costruire",
        },
        "sec": {
            "core":"IL NUCLEO",
            "engine":"IL TUO MOTORE EMOTIVO",
            "mind":"MENTE & VOCE",
            "drive":"COME AGISCI SOTTO PRESSIONE",
            "love":"IL TUO PATTERN D’AMORE",
            "money":"VALORE & DENARO",
            "shadow":"IL LOOP D’OMBRA",
            "strengths":"LE TUE MOSSE POTENTI",
            "timing":"LA LEVA DEL TEMPO",
            "health":"IGIENE ENERGETICA",
            "social":"DNA SOCIALE",
            "purpose":"LA TUA STELLA POLARE",
            "wow":"WOW PRACTICE (1 minuto)",
        },
        "fallback_soft": "Alcune parti qui sono più “sottili”: non perché siano vaghe, ma perché nel tuo tema funzionano per sfumature.",
    },
    "es": {
        "titles": {
            "personal": "CRECIMIENTO PERSONAL — Tu mapa interior",
            "love": "AMOR & RELACIONES — Tu patrón de vínculo",
            "career": "CARRERA & DIRECCIÓN — Tu firma profesional",
            "money": "DINERO & RECURSOS — Tu flujo material",
            "shadow": "PATRONES EMOCIONALES — Tu sombra interior",
            "strengths": "FORTALEZAS & DEBILIDADES — Tu equilibrio",
            "communication": "COMUNICACIÓN — Cómo te entienden de verdad",
            "timing": "TIEMPOS — Cuándo empujar, cuándo esperar",
            "health": "SALUD & ENERGÍA — Cómo recargas",
            "friendships": "AMISTADES — Tu estilo social",
            "purpose": "PROPÓSITO — Lo que viniste a construir",
        },
        "sec": {
            "core":"EL NÚCLEO",
            "engine":"TU MOTOR EMOCIONAL",
            "mind":"MENTE & VOZ",
            "drive":"CÓMO ACTÚAS BAJO PRESIÓN",
            "love":"TU PATRÓN DE AMOR",
            "money":"VALOR & DINERO",
            "shadow":"TU BUCLE DE SOMBRA",
            "strengths":"TUS MOVIMIENTOS DE PODER",
            "timing":"TU PALANCA DE TIEMPO",
            "health":"HIGIENE ENERGÉTICA",
            "social":"ADN SOCIAL",
            "purpose":"TU ESTRELLA POLAR",
            "wow":"WOW PRACTICE (1 minuto)",
        },
        "fallback_soft": "Algunas partes aquí son más sutiles: no porque sean vagas, sino porque en tu carta se expresan por matices.",
    },
}

# Topic focus weights: what to prioritize and what to include
TOPIC_FOCUS = {
    "personal":  ["core","engine","mind","drive","strengths","wow"],
    "love":      ["core","engine","love","mind","shadow","wow"],
    "career":    ["core","mind","drive","strengths","money","wow"],
    "money":     ["core","money","drive","mind","shadow","wow"],
    "shadow":    ["core","engine","shadow","mind","drive","wow"],
    "strengths": ["core","strengths","mind","drive","engine","wow"],
    "communication":["core","mind","engine","shadow","strengths","wow"],
    "timing":    ["core","timing","drive","mind","engine","wow"],
    "health":    ["core","health","engine","mind","drive","wow"],
    "friendships":["core","social","mind","engine","shadow","wow"],
    "purpose":   ["core","purpose","drive","mind","strengths","wow"],
}


# -----------------------------
# Helpers
# -----------------------------
def clamp_lang(lang: Optional[str]) -> str:
    lang = (lang or "en").lower().strip()
    return lang if lang in ("en","it","es") else "en"

def clamp_topic(topic: Optional[str]) -> str:
    t = (topic or "").lower().strip()
    return t if t in TOPICS else "personal"

def sign_name(sign_en: str, lang: str) -> str:
    if not sign_en:
        return ""
    try:
        idx = SIGNS_EN.index(sign_en.capitalize())
    except Exception:
        return sign_en
    if lang == "it":
        return SIGNS_IT[idx]
    if lang == "es":
        return SIGNS_ES[idx]
    return SIGNS_EN[idx]

def planet_name(p: str, lang: str) -> str:
    p = (p or "").lower().strip()
    return PLANET_NAMES.get(lang, PLANET_NAMES["en"]).get(p, p.capitalize())

def stable_rng(*parts: str) -> random.Random:
    seed = "|".join([p for p in parts if p is not None])
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))

def pick(rng: random.Random, items: List[str]) -> str:
    return items[rng.randrange(0, len(items))]

def zodiac_sign_index(longitude: float) -> int:
    lon = float(longitude) % 360.0
    return int(lon // 30)

def normalize_sign_en(s: str) -> str:
    if not s:
        return ""
    s2 = s.strip().lower()
    for en in SIGNS_EN:
        if en.lower() == s2:
            return en
    return s.strip().capitalize()

def safe_get_sign(chart: Dict[str, Any], key: str) -> str:
    if not chart:
        return ""
    if key == "ascendant":
        asc = chart.get("ascendant")
        if isinstance(asc, dict):
            return str(asc.get("sign") or "")
        if isinstance(asc, str):
            return asc
        return ""
    planets = chart.get("planets")
    if isinstance(planets, dict):
        v = planets.get(key)
        if isinstance(v, dict):
            return str(v.get("sign") or "")
        if isinstance(v, str):
            return v
        return ""
    if isinstance(planets, list):
        for p in planets:
            if isinstance(p, dict) and (p.get("key") == key or p.get("name") == key):
                return str(p.get("sign") or "")
    return ""

def chart_signature(chart: Dict[str, Any]) -> str:
    # Used to stabilize variation per user/profile
    bits = []
    for k in PLANETS + ["ascendant"]:
        bits.append(f"{k}:{normalize_sign_en(safe_get_sign(chart, k)).lower()}")
    return "|".join(bits)


# -----------------------------
# Worldwide birth time handling
# -----------------------------
class BirthInput(BaseModel):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    city: Optional[str] = None
    country: Optional[str] = None
    tz: Optional[str] = None  # IANA tz name (optional override)
    lat: Optional[float] = None
    lon: Optional[float] = None

def parse_local_datetime(b: BirthInput) -> datetime:
    try:
        return datetime.strptime(f"{b.date} {b.time}", "%Y-%m-%d %H:%M")
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid birth date/time. Use YYYY-MM-DD and HH:MM")

def resolve_tz_name(b: BirthInput) -> str:
    # 1) Se il frontend / supabase passa → usala
    if b.tz:
        return b.tz
    # 2) NIENTE TimezoneFinder
    # Se non arriva tz, falliamo esplicitamente
    raise HTTPEException(
        status_code=422,
        detail="Missing timezone. Pass birth.tz (e.g Europe/Rome)"
    )
    
def local_to_utc(b: BirthInput) -> datetime:
    local_dt = parse_local_datetime(b)
    tzname = resolve_tz_name(b)
    try:
        tz = ZoneInfo(tzname)
    except Exception:
        raise HTTPException(status_code=422, detail=f"Invalid timezone: {tzname}")
    # Attach timezone then convert to UTC (handles DST correctly)
    aware_local = local_dt.replace(tzinfo=tz)
    utc_dt = aware_local.astimezone(ZoneInfo("UTC"))
    return utc_dt


# -----------------------------
# Chart calculation (Swiss Ephemeris)
# -----------------------------
SWE_PLANETS = {
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

def compute_chart_from_birth(b: BirthInput) -> Dict[str, Any]:
    utc_dt = local_to_utc(b)

    ut_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hour)

    if b.lat is None or b.lon is None:
        raise HTTPException(status_code=422, detail="lat/lon required to compute Ascendant accurately.")

    result: Dict[str, Any] = {"planets": {}, "ascendant": {}}
    for name, planet in SWE_PLANETS.items():
        xx, _ = swe.calc_ut(jd, planet)
        lon_p = float(xx[0])
        idx = zodiac_sign_index(lon_p)
        result["planets"][name] = {"longitude": lon_p, "sign": SIGNS_EN[idx]}

    houses, ascmc = swe.houses(jd, b.lat, b.lon)
    asc_lon = float(ascmc[0])
    asc_idx = zodiac_sign_index(asc_lon)
    result["ascendant"] = {"longitude": asc_lon, "sign": SIGNS_EN[asc_idx]}

    result["meta"] = {
        "birth_local": f"{b.date} {b.time}",
        "tz": resolve_tz_name(b),
        "birth_utc": utc_dt.isoformat(),
        "note": "Ascendant depends strongly on timezone/DST and exact birth time.",
    }
    return result


# -----------------------------
# Narrative intelligence (no fuffa)
# -----------------------------
def element_modality_profile(signs: Dict[str, str]) -> Dict[str, Any]:
    # signs: { planet: "Capricorn", ... , "ascendant": "Scorpio" }
    elem_score = {"fire": 0.0, "earth": 0.0, "air": 0.0, "water": 0.0}
    mod_score = {"cardinal": 0.0, "fixed": 0.0, "mutable": 0.0}

    for p, s in signs.items():
        if not s:
            continue
        w = PLANET_WEIGHT.get(p, 1.0)
        e = ELEMENT.get(s, None)
        m = MODALITY.get(s, None)
        if e: elem_score[e] += w
        if m: mod_score[m] += w

    dom_elem = max(elem_score, key=lambda k: elem_score[k]) if sum(elem_score.values()) > 0 else None
    dom_mod = max(mod_score, key=lambda k: mod_score[k]) if sum(mod_score.values()) > 0 else None

    return {
        "elements": elem_score,
        "modalities": mod_score,
        "dominant_element": dom_elem,
        "dominant_modality": dom_mod,
    }

def key_tensions(signs: Dict[str, str]) -> List[str]:
    # Simple but effective “this feels like you” tensions
    out = []
    sun = signs.get("sun","")
    moon = signs.get("moon","")
    asc = signs.get("ascendant","")
    if sun and moon:
        if ELEMENT.get(sun) != ELEMENT.get(moon):
            out.append("sun_moon_element_mismatch")
        if MODALITY.get(sun) != MODALITY.get(moon):
            out.append("sun_moon_modality_mismatch")
    if moon and asc and ELEMENT.get(moon) != ELEMENT.get(asc):
        out.append("moon_asc_element_mismatch")
    return out

def day_part(local_hour: int) -> str:
    if 5 <= local_hour < 11: return "morning"
    if 11 <= local_hour < 17: return "day"
    if 17 <= local_hour < 22: return "evening"
    return "night"

def season_hint(month: int, hemisphere: Optional[str]) -> str:
    # hemisphere: "north" / "south" / None
    if hemisphere is None:
        return "neutral"
    # crude mapping, good enough for tone hooks
    if hemisphere == "north":
        if month in (12,1,2): return "winter"
        if month in (3,4,5): return "spring"
        if month in (6,7,8): return "summer"
        return "autumn"
    else:
        if month in (12,1,2): return "summer"
        if month in (3,4,5): return "autumn"
        if month in (6,7,8): return "winter"
        return "spring"


def build_section_text(
    rng: random.Random,
    lang: str,
    section_key: str,
    topic: str,
    signs: Dict[str, str],
    profile: Dict[str, Any],
    signature: Dict[str, Any],
    tensions: List[str],
) -> str:
    # We avoid generic adjectives; we talk in behavior + tradeoffs.
    sun = sign_name(signs.get("sun",""), lang)
    moon = sign_name(signs.get("moon",""), lang)
    asc  = sign_name(signs.get("ascendant",""), lang)
    mer  = sign_name(signs.get("mercury",""), lang)
    ven  = sign_name(signs.get("venus",""), lang)
    mar  = sign_name(signs.get("mars",""), lang)
    jup  = sign_name(signs.get("jupiter",""), lang)
    sat  = sign_name(signs.get("saturn",""), lang)
    plu  = sign_name(signs.get("pluto",""), lang)
    nep  = sign_name(signs.get("neptune",""), lang)
    ura  = sign_name(signs.get("uranus",""), lang)

    dom_elem = signature.get("dominant_element")
    dom_mod  = signature.get("dominant_modality")

    # Voice per language
    if lang == "it":
        # Warm, deep, narrative
        if section_key == "core":
            return "\n".join([
                f"Il tuo Sole in {sun} non vive di promesse: vive di prove. Ti rispetti quando fai quello che hai detto.",
                f"La Luna in {moon} non chiede “attenzione”: chiede coerenza emotiva. Se manca, ti indurisci o ti spegni.",
                f"L’Ascendente in {asc} è la tua facciata: sembri controllato, ma dentro senti tutto più a fondo di quanto lasci vedere.",
                "Il punto chiave: non sei “una cosa sola”. Sei un equilibrio tra bisogno di solidità e fame di intensità.",
            ])
        if section_key == "engine":
            line = pick(rng, [
                "Le emozioni non ti travolgono: ti informano. Ma se le ignori troppo a lungo, diventano pressione.",
                "Il tuo cuore è selettivo: si apre quando percepisce presenza reale, non parole giuste.",
                "Senti prima di capire. E quando capisci, non riesci più a fingere.",
            ])
            hook = "Se ti accorgi che stai ‘facendo il forte’, spesso è perché stai proteggendo un bisogno non detto."
            return f"{line}\n{hook}"
        if section_key == "mind":
            return "\n".join([
                f"Mercurio in {mer} indica come pensi e parli: la tua mente vuole chiarezza, non rumore.",
                "Quando sei centrato, sei essenziale: dici il vero senza ferire.",
                "Quando sei sotto pressione, cerchi la frase perfetta e rimandi la conversazione vera.",
            ])
        if section_key == "drive":
            return "\n".join([
                f"Marte in {mar} è il modo in cui agisci: non scatti a caso, costruisci slancio con intenzione.",
                "Sotto stress puoi diventare iper-esigente: prima con te, poi con gli altri.",
                "La tua forza è la disciplina intelligente: piccole mosse ripetute, risultati inevitabili.",
            ])
        if section_key == "love":
            return "\n".join([
                f"Venere in {ven} dice come ami: non ti basta ‘stare bene’, ti serve verità emotiva.",
                f"La Luna in {moon} ti rende sensibile ai micro-segnali: coerenza, tempi, presenza.",
                "Quando qualcosa non torna, non chiedi subito: testi. È lì che perdi energia.",
                "Il tuo upgrade: chiedere prima. In modo semplice. Senza tribunali.",
            ])
        if section_key == "money":
            return "\n".join([
                f"Il denaro per te è sicurezza + libertà. Giove in {jup} mostra dove puoi espanderti.",
                f"Saturno in {sat} chiede regole: se non le crei tu, te le crea la vita (in modo più duro).",
                "Se il tuo flusso è altalenante, non è sfortuna: è identità che non ha ancora una strategia stabile.",
            ])
        if section_key == "shadow":
            base = pick(rng, [
                "La tua ombra non è “cattiva”: è una strategia di sopravvivenza che è diventata abitudine.",
                "Quando ti senti vulnerabile, provi a riprendere controllo. Il costo è la spontaneità.",
                "Il punto cieco non è l’emozione: è la gestione del potere personale.",
            ])
            add = []
            if plu:
                add.append(f"Plutone in {plu} intensifica tutto: se decidi, lo fai sul serio. Ma rischi ‘tutto o niente’.")
            if "sun_moon_element_mismatch" in tensions:
                add.append("Dentro convivono due linguaggi diversi: uno vuole solidità, l’altro vuole respiro. Se non li fai dialogare, si sabotano.")
            return "\n".join([base] + add)
        if section_key == "strengths":
            return "\n".join([
                "Il tuo potere non è essere perfetto. È essere affidabile mentre resti umano.",
                "Quando integri mente + cuore + azione, diventi “impossibile da ignorare”.",
                "La tua mossa vincente: scegliere un obiettivo e togliere tutto il resto.",
            ])
        if section_key == "timing":
            return "\n".join([
                "Il timing per te è una leva: quando spingi troppo presto, consumi energia. Quando aspetti troppo, perdi slancio.",
                f"Giove in {jup} indica quando ‘osare’. Saturno in {sat} indica quando ‘consolidare’.",
                "La regola pratica: espandi solo ciò che sai sostenere.",
            ])
        if section_key == "health":
            return "\n".join([
                "La tua energia non è infinita: funziona a cicli. Se la tratti come una macchina, si ribella.",
                "Ti ricarichi quando riduci stimoli e torni a una routine minima ma vera.",
                "Igiene energetica: sonno, cibo, movimento, confini. Non è glamour. È potere.",
            ])
        if section_key == "social":
            return "\n".join([
                "Nelle amicizie non cerchi quantità: cerchi qualità. Poche persone, ma vere.",
                "Se senti incoerenza, ti allontani senza spiegare troppo. È protezione, non freddezza.",
                "Il tuo equilibrio: dire una cosa in più prima di sparire.",
            ])
        if section_key == "purpose":
            return "\n".join([
                "Il tuo scopo non è “fare tanto”. È costruire qualcosa che regge nel tempo e ti somiglia.",
                "La bussola: impatto reale, reputazione pulita, crescita sostenibile.",
                "Quando smetti di dimostrare e inizi a scegliere, la direzione diventa ovvia.",
            ])
        if section_key == "wow":
            return pick(rng, [
                "Oggi: scrivi UNA frase vera che eviti da settimane. Poi fai UNA micro-azione coerente (10 minuti).",
                "Oggi: scegli un confine semplice e rispettalo. Non spiegarti troppo. La coerenza fa più rumore delle parole.",
                "Oggi: togli una cosa. Solo una. Il tuo focus è la tua magia.",
            ])

    if lang == "es":
        # Warm, fluid
        if section_key == "core":
            return "\n".join([
                f"Sol en {sun}: tu identidad no vive de ideas, vive de resultados. Te respetas cuando cumples lo que prometes.",
                f"Luna en {moon}: tu mundo emocional necesita coherencia real, no palabras bonitas.",
                f"Ascendente en {asc}: pareces controlado, pero por dentro sientes más profundo de lo que muestras.",
                "Clave: tu fuerza nace cuando alineas lo que sientes con lo que haces.",
            ])
        if section_key == "wow":
            return pick(rng, [
                "Hoy: di una verdad en UNA frase. Sin historia. Luego haz UNA acción pequeña que la respete.",
                "Hoy: elige un límite simple y cúmplelo. La coherencia te devuelve poder.",
            ])
        # For brevity, map the rest to EN-ish but still Spanish tone
        # (you can expand later without touching architecture)
        return I18N["es"]["fallback_soft"]

    # EN (default): direct but deep
    if section_key == "core":
        return "\n".join([
            f"Sun in {sun} is your identity engine: you don’t run on vibes — you run on outcomes.",
            f"Moon in {moon} is your emotional truth: you need consistency, not just intensity.",
            f"Ascendant in {asc} is your social armor: you look composed while carrying more depth than people assume.",
            "Your edge is integration: when mind + heart + action align, you become undeniable.",
        ])
    if section_key == "engine":
        return pick(rng, [
            "Your emotions don’t overwhelm you — they inform you. But ignored feelings become pressure.",
            "You read micro-signals. When something is off, you feel it before you can explain it.",
            "Your heart is selective: it opens for presence, not performance.",
        ])
    if section_key == "mind":
        return "\n".join([
            f"Mercury in {mer} shapes your thinking: you want clarity, not noise.",
            "When centered, you speak clean truth without cruelty.",
            "Under stress, you chase the perfect sentence and delay the real conversation.",
        ])
    if section_key == "drive":
        return "\n".join([
            f"Mars in {mar} is your action style: intentional, improvement-driven, not random.",
            "Under pressure you can become demanding — first with yourself, then with others.",
            "Your strength is intelligent discipline: small repeated moves that compound.",
        ])
    if section_key == "love":
        return "\n".join([
            f"Venus in {ven} shows your love pattern: you don’t want ‘nice’. You want real.",
            f"Moon in {moon} makes you sensitive to consistency: timing, effort, follow-through.",
            "When something feels unclear, you may test instead of asking — that’s where energy leaks.",
            "Upgrade: ask early, simply, once. No courtroom. Just truth.",
        ])
    if section_key == "money":
        return "\n".join([
            f"Money for you is security + freedom. Jupiter in {jup} shows where expansion is natural.",
            f"Saturn in {sat} demands structure: if you don’t build rules, life builds them for you.",
            "If your flow swings, it’s rarely luck — it’s identity without a stable strategy yet.",
        ])
    if section_key == "shadow":
        base = pick(rng, [
            "Your shadow isn’t ‘bad’ — it’s an old survival strategy that became a habit.",
            "When you feel vulnerable, you reach for control. The cost is spontaneity.",
            "The blind spot isn’t emotion — it’s power management.",
        ])
        add = []
        if plu:
            add.append(f"Pluto in {plu} intensifies your inner stakes: you transform in ‘all-in’ moments — watch the all-or-nothing reflex.")
        if "sun_moon_element_mismatch" in tensions:
            add.append("Two inner languages coexist: one wants stability, the other wants space. If they don’t talk, they sabotage.")
        return "\n".join([base] + add)
    if section_key == "strengths":
        return "\n".join([
            "Your power isn’t perfection — it’s reliability with emotional honesty.",
            "When you integrate mind + heart + action, you become impossible to ignore.",
            "Your power move: pick one outcome and remove everything else.",
        ])
    if section_key == "timing":
        return "\n".join([
            "Timing is leverage: push too early and you burn energy; wait too long and you lose momentum.",
            f"Jupiter in {jup} shows when to expand. Saturn in {sat} shows when to consolidate.",
            "Rule: only expand what you can sustain.",
        ])
    if section_key == "health":
        return "\n".join([
            "Your energy runs in cycles. Treat it like a machine and it pushes back.",
            "You recharge by reducing inputs and returning to a minimal, real routine.",
            "Energy hygiene: sleep, food, movement, boundaries. Not glamorous — powerful.",
        ])
    if section_key == "social":
        return "\n".join([
            "You don’t do ‘many friends’. You do real ones.",
            "If you sense inconsistency, you step back fast — protection, not coldness.",
            "Your balance: say one more thing before disappearing.",
        ])
    if section_key == "purpose":
        return "\n".join([
            "Purpose isn’t ‘do more’. It’s build what lasts — and looks like you.",
            "Compass: real impact, clean reputation, sustainable growth.",
            "When you stop proving and start choosing, direction becomes obvious.",
        ])
    if section_key == "wow":
        return pick(rng, [
            "Today: write ONE avoided truth in one sentence. Then do ONE 10-minute action that matches it.",
            "Today: set one simple boundary and keep it. Don’t over-explain. Consistency is loud.",
            "Today: remove one thing. Focus is your magic.",
        ])

    return I18N[lang]["fallback_soft"]


def build_wow_reading(
    topic: str,
    lang: str,
    chart: Dict[str, Any],
    depth: str = "standard",
    now_iso: Optional[str] = None,
) -> Dict[str, Any]:
    lang = clamp_lang(lang)
    topic = clamp_topic(topic)
    depth = depth if depth in ("standard","deep") else "standard"

    # Extract signs
    signs: Dict[str, str] = {}
    for p in PLANETS:
        signs[p] = normalize_sign_en(safe_get_sign(chart, p))
    signs["ascendant"] = normalize_sign_en(safe_get_sign(chart, "ascendant"))

    sig = element_modality_profile(signs)
    tens = key_tensions(signs)

    # Seed: stable per user chart + topic + lang, but with controlled variation
    # We allow variation by day-part if now_iso provided.
    base_sig = chart_signature(chart)
    day_key = ""
    if now_iso:
        try:
            now_dt = datetime.fromisoformat(now_iso.replace("Z","+00:00"))
            day_key = now_dt.strftime("%Y-%m-%d")
        except Exception:
            day_key = ""
    rng = stable_rng(base_sig, topic, lang, day_key)

    title = I18N[lang]["titles"].get(topic, I18N[lang]["titles"]["personal"])

    # Sections to include
    focus = TOPIC_FOCUS.get(topic, TOPIC_FOCUS["personal"]).copy()
    # If deep, add 1–2 extra sections depending on topic
    if depth == "deep":
        extra_map = {
            "love": ["money"],
            "career": ["shadow"],
            "money": ["strengths"],
            "shadow": ["engine"],
            "purpose": ["timing"],
            "communication": ["social"],
            "personal": ["purpose"],
        }
        for k in extra_map.get(topic, ["shadow"]):
            if k not in focus and k != "wow":
                focus.insert(-1, k)

    sections = []
    for key in focus:
        if key == "wow":
            continue
        sec_title = I18N[lang]["sec"].get(key, key.upper())
        txt = build_section_text(
            rng=rng,
            lang=lang,
            section_key=key,
            topic=topic,
            signs=signs,
            profile={},
            signature=sig,
            tensions=tens,
        )
        sections.append({"key": key, "title": sec_title, "text": txt})

    wow = build_section_text(
        rng=rng,
        lang=lang,
        section_key="wow",
        topic=topic,
        signs=signs,
        profile={},
        signature=sig,
        tensions=tens,
    )

    # Backward compatible full text
    joined = [title, ""]
    for s in sections:
        joined.append(f"{s['title']}\n{s['text']}")
        joined.append("")
    joined.append(f"{I18N[lang]['sec']['wow']}\n{wow}")
    text = "\n".join(joined).strip()

    return {
        "topic": topic,
        "lang": lang,
        "depth": depth,
        "title": title,
        "sections": sections,
        "wow_practice": wow,
        "text": text,  # frontend compatibility
        "meta": {
            "dominant_element": sig.get("dominant_element"),
            "dominant_modality": sig.get("dominant_modality"),
            "tensions": tens,
        }
    }


# -----------------------------
# API Models
# -----------------------------
class ChartRequest(BaseModel):
    birth: BirthInput

class ReadingRequest(BaseModel):
    birth_profile: Dict[str, Any] = Field(default_factory=dict)
    topic: str
    lang: Optional[Lang] = "en"
    depth: Optional[Depth] = "standard"
    now_iso: Optional[str] = None  # optional: allow daily variation or time-aware hooks


# -----------------------------
# API Endpoints
# -----------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "try": "/docs",
        "note": "For accurate ascendant worldwide, send birth.lat, birth.lon and birth.tz (IANA) from city autocomplete."
    }

@app.post("/chart")
def chart_from_birth(payload: ChartRequest):
    chart = compute_chart_from_birth(payload.birth)
    return chart

@app.post("/readings")
def readings(payload: ReadingRequest):
    lang = clamp_lang(payload.lang)
    topic = clamp_topic(payload.topic)

    birth_profile = payload.birth_profile or {}
    chart = birth_profile.get("chart") or {}

    # If chart is missing, we cannot read. Keep it explicit.
    if not chart:
        raise HTTPException(status_code=422, detail="birth_profile.chart is required")

    out = build_wow_reading(
        topic=topic,
        lang=lang,
        chart=chart,
        depth=(payload.depth or "standard"),
        now_iso=payload.now_iso,
    )

    print(f"[READINGS] topic={topic} lang={lang} depth={payload.depth}", flush=True)
    print(f"[READINGS] preview={out['text'][:160]}", flush=True)

    return out


# Railway / container entry
if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
