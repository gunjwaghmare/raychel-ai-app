from dotenv import load_dotenv
load_dotenv()

import os
import requests

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

DEFAULT_TIMEOUT = 12  # seconds
UA = {"User-Agent": "FactualReActAgent/1.2 (+https://example.local)"}

def _extract_best_answer_from_serpapi(data: dict) -> str:
    """
    Aggregate useful text from SerpAPI response in priority order.
    Returns a concise paragraph-like string.
    """
    parts = []

    # Direct answers
    box = data.get("answer_box") or {}
    for key in ("answer", "snippet", "highlighted_snippet"):
        val = box.get(key)
        if val:
            parts.append(str(val))

    # Knowledge graph
    kg = data.get("knowledge_graph") or {}
    for key in ("title", "type", "description"):
        val = kg.get(key)
        if val:
            parts.append(str(val))

    # Sports results
    sr = data.get("sports_results") or {}
    for key in ("game_spotlight", "title", "league", "match_summary"):
        val = sr.get(key)
        if val:
            parts.append(str(val))

    # News/top stories
    ts = data.get("top_stories") or []
    for item in ts[:3]:
        t = item.get("title")
        s = item.get("snippet")
        if t:
            parts.append(t)
        if s:
            parts.append(s)

    nr = data.get("news_results") or []
    for item in nr[:3]:
        t = item.get("title")
        s = item.get("snippet")
        if t:
            parts.append(t)
        if s:
            parts.append(s)

    # Organic results
    org = data.get("organic_results") or []
    for item in org[:3]:
        s = item.get("snippet")
        t = item.get("title")
        if s:
            parts.append(s)
        if t:
            parts.append(t)

    # People also ask
    paa = data.get("related_questions") or []
    for item in paa[:2]:
        a = item.get("answer")
        if a:
            parts.append(a)

    # De-duplicate, preserve order
    seen = set()
    cleaned = []
    for p in parts:
        p = str(p).strip()
        if not p:
            continue
        if p not in seen:
            seen.add(p)
            cleaned.append(p)

    return " ".join(cleaned[:8]) if cleaned else ""

def get_weather(city: str) -> str:
    if not WEATHER_API_KEY:
        return "Sorry, couldn't perform weather lookup (missing WEATHER_API_KEY)."
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
    try:
        r = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT, headers=UA)
    except Exception:
        return f"Sorry, couldn't find weather for {city}."
    if r.status_code != 200:
        return f"Sorry, couldn't find weather for {city}."
    data = r.json()
    try:
        main = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        return f"In {city}, it's currently {main}, {temp}°C (feels like {feels}°C), humidity {humidity}%, wind {wind} m/s."
    except Exception:
        return f"Sorry, couldn't find weather for {city}."

def get_weather_forecast(city: str) -> str:
    if not WEATHER_API_KEY:
        return "Sorry, couldn't perform weather lookup (missing WEATHER_API_KEY)."
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
    try:
        r = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT, headers=UA)
    except Exception:
        return f"Sorry, couldn't find forecast for {city}."
    if r.status_code != 200:
        return f"Sorry, couldn't find forecast for {city}."
    data = r.json()
    try:
        forecasts = []
        for f in data.get("list", [])[:5]:
            dt = f.get("dt_txt", "")
            main = f["weather"][0]["description"].capitalize()
            temp = f["main"]["temp"]
            forecasts.append(f"{dt}: {main}, {temp}°C")
        return f"Forecast for {city}:\n" + "\n".join(forecasts) if forecasts else f"Sorry, couldn't find forecast for {city}."
    except Exception:
        return f"Sorry, couldn't find forecast for {city}."

def _serpapi_request(query: str, engine: str = "google") -> dict:
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "engine": engine,
        "hl": "en",
        "gl": "us",
        "num": "10"
    }
    try:
        r = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT, headers=UA)
        if r.status_code != 200:
            return {}
        return r.json()
    except Exception:
        return {}

def wiki_search(query: str) -> str:
    """
    Wikipedia REST API fallback (no key).
    1) Search most relevant page.
    2) Fetch its summary text.
    Returns a concise paragraph-like text or empty string if nothing found.
    """
    try:
        s_url = "https://en.wikipedia.org/w/rest.php/v1/search/page"
        s_params = {"q": query, "limit": 1}
        s_res = requests.get(s_url, params=s_params, timeout=DEFAULT_TIMEOUT, headers=UA)
        if s_res.status_code != 200:
            return ""
        s_data = s_res.json()
        pages = s_data.get("pages", [])
        if not pages:
            return ""
        key = pages[0].get("key")
        if not key:
            return ""
        sum_url = f"https://en.wikipedia.org/w/rest.php/v1/page/summary/{key}"
        sum_res = requests.get(sum_url, timeout=DEFAULT_TIMEOUT, headers=UA)
        if sum_res.status_code != 200:
            return ""
        j = sum_res.json()
        title = j.get("title") or ""
        desc = j.get("description") or ""
        extract = j.get("extract") or ""
        if title and desc:
            return f"{title} — {desc}. {extract}".strip()
        return (extract or "").strip()
    except Exception:
        return ""

def web_search(query: str) -> str:
    """
    Query SerpAPI (if available) and extract a concise paragraph-like text for LLM composition.
    Fallback to Bing engine via SerpAPI; if both fail or key missing, fallback to Wikipedia REST.
    """
    cleaned_q = query.strip(" '\"<>")

    # Prefer SerpAPI if key exists
    if SERPAPI_KEY:
        data = _serpapi_request(cleaned_q, engine="google")
        text = _extract_best_answer_from_serpapi(data) if data else ""
        if not text:
            data_bing = _serpapi_request(cleaned_q, engine="bing")
            text = _extract_best_answer_from_serpapi(data_bing) if data_bing else ""
        if text:
            return text

    # Fallback to Wikipedia
    wiki_text = wiki_search(cleaned_q)
    if wiki_text:
        return wiki_text

    return "Sorry, couldn't find an answer."