import re
import os
import time
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from tools import get_weather, get_weather_forecast, web_search

load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME", "mistral-openorca")
llm_pipe = OllamaLLM(model=MODEL_NAME)

# --- Category Detection ---
def detect_category(question: str) -> str:
    q = question.lower()
    if any(word in q for word in [
        "weather", "temperature", "humidity", "rain", "forecast", "climate", "wind", "sunny", "cloudy", "storm", "snow"
    ]):
        return "Weather"
    if any(word in q for word in [
        "ipl", "cricket", "football", "soccer", "tennis", "nba", "nfl", "fifa", "world cup", "sports", "score", "match", "player", "tournament"
    ]):
        return "Sports"
    if any(word in q for word in [
        "prime minister", "president", "government", "election", "vote", "parliament", "politics", "minister", "mla", "mp", "political", "party"
    ]):
        return "Politics"
    if any(word in q for word in [
        "history", "science", "math", "who", "what", "when", "where", "why", "how", "population", "country", "general knowledge"
    ]):
        return "General Knowledge"
    return "Other"

# --- Flexible Weather Forecast Intent Detection, including sunny, cloudy, windy ---
def get_weather_intent(question: str) -> str | None:
    q = question.lower()
    # Rain intent
    if (
        ("rain" in q and any(t in q for t in ["today", "tomorrow", "tonight", "now"]))
        or re.search(r"(gonna|going to) rain", q)
        or re.search(r"will it rain", q)
        or re.search(r"chance of rain", q)
        or re.search(r"rain expected", q)
        or re.search(r"raining today", q)
        or re.search(r"precipitation", q)
    ):
        return "rain"
    # Sunny intent
    if (
        ("sunny" in q and any(t in q for t in ["today", "tomorrow", "tonight", "now"]))
        or re.search(r"(gonna|going to) be sunny", q)
        or re.search(r"will it be sunny", q)
        or re.search(r"sunny expected", q)
        or re.search(r"clear skies", q)
    ):
        return "sunny"
    # Cloudy intent
    if (
        ("cloudy" in q and any(t in q for t in ["today", "tomorrow", "tonight", "now"]))
        or re.search(r"(gonna|going to) be cloudy", q)
        or re.search(r"will it be cloudy", q)
        or re.search(r"cloudy expected", q)
        or re.search(r"overcast", q)
        or re.search(r"clouds", q)
    ):
        return "cloudy"
    # Windy intent
    if (
        ("windy" in q and any(t in q for t in ["today", "tomorrow", "tonight", "now"]))
        or re.search(r"(gonna|going to) be windy", q)
        or re.search(r"will it be windy", q)
        or re.search(r"windy expected", q)
        or re.search(r"strong winds", q)
        or re.search(r"gusty", q)
        or re.search(r"wind speed", q)
    ):
        return "windy"
    # Snow intent
    if (
        ("snow" in q and any(t in q for t in ["today", "tomorrow", "tonight", "now"]))
        or re.search(r"(gonna|going to) snow", q)
        or re.search(r"will it snow", q)
        or re.search(r"chance of snow", q)
        or re.search(r"snow expected", q)
    ):
        return "snow"
    return None

def answer_weather_forecast(city: str, intent: str) -> str:
    forecast = get_weather_forecast(city)
    forecast_l = forecast.lower()
    if intent == "rain":
        if any(word in forecast_l for word in ["rain", "showers", "drizzle", "thunder"]):
            return f"Yes, rain is expected today in {city}. {forecast}"
        else:
            return f"No, rain is not expected today in {city}. {forecast}"
    if intent == "sunny":
        if any(word in forecast_l for word in ["sunny", "clear"]):
            return f"Yes, it will be sunny today in {city}. {forecast}"
        else:
            return f"No, it will not be sunny today in {city}. {forecast}"
    if intent == "cloudy":
        if any(word in forecast_l for word in ["cloudy", "overcast", "clouds"]):
            return f"Yes, it will be cloudy today in {city}. {forecast}"
        else:
            return f"No, it will not be cloudy today in {city}. {forecast}"
    if intent == "windy":
        if any(word in forecast_l for word in ["windy", "strong winds", "gusty"]):
            return f"Yes, it will be windy today in {city}. {forecast}"
        else:
            return f"No, it will not be windy today in {city}. {forecast}"
    if intent == "snow":
        if any(word in forecast_l for word in ["snow", "blizzard"]):
            return f"Yes, snow is expected today in {city}. {forecast}"
        else:
            return f"No, snow is not expected today in {city}. {forecast}"
    return forecast

def is_weather_related(question: str) -> bool:
    keywords = [
        "weather", "temperature", "humidity", "rain", "wind", "forecast",
        "sunny", "cloudy", "storm", "snow", "precipitation", "climate"
    ]
    return any(word in question.lower() for word in keywords)

def is_time_sensitive(question: str) -> bool:
    q = question.lower()
    if re.search(r"\b(19|20)\d{2}\b", q):
        return True
    keywords = [
        "who won", "winner", "final", "score", "beat", "defeat", "defeated",
        "trophy", "title", "champion", "match", "fixture", "result",
        "ipl", "fifa", "world cup", "uefa", "olympics", "nba", "nfl", "mlb", "nhl", "grand slam",
        "nobel", "oscars", "academy awards", "emmys", "grammys", "ballon d'or", "golden globes",
        "president", "prime minister", "chief minister", "current", "mla", "mp", "member of parliament",
        "election", "vote", "polls"
    ]
    return any(term in q for term in keywords)

def extract_city(question: str) -> str | None:
    q = question.lower()
    # Try to find "in <city>", "for <city>", or "of <city>"
    m = re.search(r"\b(?:in|for|of)\s+([a-zA-Z\s\-\.]+)", q)
    if m:
        city = m.group(1)
    else:
        # Try to catch patterns like "weather forecast <city>"
        m2 = re.search(r"forecast(?:\s+in)?\s+([a-zA-Z\s\-\.]+)", q)
        if m2:
            city = m2.group(1)
        else:
            # Try to catch patterns like "<city> weather"
            m3 = re.search(r"([a-zA-Z\s\-\.]+)\s+weather", q)
            if m3:
                city = m3.group(1)
            else:
                return None
    # Remove leading prepositions and common time words
    city = re.sub(r"^(in|for|of)\s+", "", city, flags=re.I)
    city = re.sub(r"\b(this week|today|tomorrow|tonight|now|next week|week)\b", "", city, flags=re.I)
    city = city.strip(" ,.-")
    # Final cleanup: only allow letters, spaces, hyphens, dots
    city = re.sub(r"[^a-zA-Z\s\-\.]", "", city)
    if 1 <= len(city) <= 64:
        return city.title()
    return None

def get_best_query(user_input: str) -> str:
    q = user_input.strip()
    low = q.lower()
    m = re.search(r"who\s+won\s+(the\s+)?(.+?)\s+in\s+(\d{4})\??", low)
    if m:
        event = m.group(2)
        year = m.group(3)
        if "ipl" in event:
            return f"IPL {year} winner"
        if "world cup" in event and "fifa" not in event:
            return f"FIFA World Cup {year} winner"
        return f"{event.strip().upper()} {year} winner"
    m_ipl = re.search(r"\bipl\b\s*(\d{4})", low)
    if m_ipl:
        return f"IPL {m_ipl.group(1)} winner"
    m_fifa = re.search(r"\bfifa\s+world\s+cup\b\s*(\d{4})", low)
    if m_fifa:
        return f"FIFA World Cup {m_fifa.group(1)} winner"
    m_year = re.search(r"(\d{4})", low)
    if "winner" in low and m_year:
        cleaned = re.sub(r"[^\w\s-]", "", q)
        return cleaned
    return q

DIRECT_PROMPT = (
    "You are a smart factual assistant.\n"
    "Answer the user's question using your own knowledge ONLY. "
    "If you are not certain, say you don't know.\n"
    "Output style rules:\n"
    "- For general knowledge questions, respond in ONE short sentence with ONLY the core fact.\n"
    "- Do NOT add background, history, dates, or explanations unless explicitly requested.\n"
    "- If the user asks for code, provide the complete code.\n"
    "Question: {q}\n"
    "Answer:"
)

COMPOSE_PROMPT = (
    "You are a smart factual assistant.\n"
    "Web search info:\n{info}\n"
    "Question: {q}\n"
    "Answer with a rich, multi-sentence factual summary using all relevant details from the web search info. "
    "For sports, include scores, venues, player names, and awards. "
    "For history and current events, summarize key facts, dates, people, and implications. "
    "For science and tech, summarize key concepts and applications. "
    "Do not include source lists or prefaces. Write the answer only.\n"
    "Answer:"
)

def llm_direct_answer(question: str) -> str:
    prompt = DIRECT_PROMPT.format(q=question)
    generated = llm_pipe.invoke(prompt)
    answer = generated.rsplit("Answer:", 1)[-1].strip() if "Answer:" in generated else generated.strip()
    return postprocess_concise(answer, question)

def llm_compose_answer(question: str, web_result: str) -> str:
    prompt = COMPOSE_PROMPT.format(info=web_result, q=question)
    generated = llm_pipe.invoke(prompt)
    answer = generated.rsplit("Answer:", 1)[-1].strip() if "Answer:" in generated else generated.strip()
    return answer if answer else "Sorry, I couldn't find an answer."

def postprocess_concise(answer: str, question: str) -> str:
    first = re.split(r"(?<=[.!?])\s+", answer.strip(), maxsplit=1)[0]
    first = re.sub(r"^(the answer is|it is|it's)\s+", "", first, flags=re.I)
    first = re.sub(r"\s+", " ", first).strip()
    return first if first else "I don't know."

def agent_streamlit_response(user_input: str):
    category = detect_category(user_input)
    weather_intent = get_weather_intent(user_input)
    if weather_intent:
        city = extract_city(user_input)
        if not city:
            answer = "Please specify the city for the forecast."
            tool = "Weather"
        else:
            answer = answer_weather_forecast(city, weather_intent)
            tool = "Weather"
    elif is_weather_related(user_input):
        city = extract_city(user_input)
        if not city:
            if "forecast" in user_input.lower():
                answer = "Please specify the city for the forecast."
            else:
                answer = "Please specify the city for the weather."
            tool = "Weather"
        elif "forecast" in user_input.lower():
            answer = get_weather_forecast(city)
            tool = "Weather"
        else:
            answer = get_weather(city)
            tool = "Weather"
    elif is_time_sensitive(user_input):
        query = get_best_query(user_input)
        serp_result = web_search(query)
        if not serp_result or "Sorry" in serp_result:
            answer = "Sorry, I couldn't find an answer."
            tool = "Search"
        else:
            answer = llm_compose_answer(user_input, serp_result)
            tool = "Search"
    else:
        answer = llm_direct_answer(user_input)
        tool = "LLM"
    return answer, category, tool

if __name__ == "__main__":
    print("⚡🧠 Raychel AI (Type 'exit' to quit)")
    from datetime import datetime
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("Agent: Goodbye!")
            break
        start_time = time.time()
        answer, category, tool = agent_streamlit_response(user_input)
        elapsed = time.time() - start_time
        now = datetime.now().strftime("%H:%M")
        print(f"[{now}] 🤖 Agent ({category}, {tool}, took {elapsed:.2f}s): {answer}")