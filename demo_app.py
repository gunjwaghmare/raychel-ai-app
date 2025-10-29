import streamlit as st
from datetime import datetime
import time
import re
from agent_loop import agent_streamlit_response

st.set_page_config(page_title="⚡🧠 Raychel AI: Autonomous Reasoning Agent", page_icon="🤖", layout="centered")
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Montserrat:wght@700&family=Fira+Mono:wght@500&display=swap" rel="stylesheet">
    <style>
        body {background:#181920;}
        .stApp {background:#181920;}
        .raychel-title {
            font-family:'Montserrat',sans-serif;
            font-size:2.8rem;
            color:#fff;
            font-weight:700;
            letter-spacing: 1.5px;
            margin-bottom: 0.25em;
        }
        .raychel-subtitle {
            color:#bbb;
            font-size:1.2rem;
            font-family:'Inter',sans-serif;
            letter-spacing:1px;
        }
        .raychel-desc {
            color:#aaffd3;
            font-size:1.07rem;
            font-style:italic;
            margin-bottom:2em;
            font-family:'Inter',sans-serif;
        }
        .bubble-user {
            background:#282a36;
            color:#f8f8f2;
            border-radius:18px 18px 4px 18px;
            padding:0.8em 1.2em;
            margin-bottom:0.4em;
            margin-left:30px;
            font-family:'Inter',sans-serif;
            font-size:1.12rem;
            font-weight:500;
            letter-spacing: 0.01em;
        }
        .bubble-agent {
            background:#44475a;
            color:#aaffd3;
            border-radius:18px 18px 18px 4px;
            padding:0.8em 1.2em;
            margin-bottom:0.4em;
            margin-right:30px;
            font-family:'Inter',sans-serif;
            font-size:1.12rem;
            font-weight:500;
            letter-spacing: 0.01em;
        }
        .bubble-user-new {
            background:#384a36;
            color:#fff;
            border-radius:18px 18px 4px 18px;
            padding:0.8em 1.2em;
            margin-bottom:0.4em;
            margin-left:30px;
            font-weight:bold;
            font-family:'Inter',sans-serif;
            font-size:1.12rem;
        }
        .bubble-agent-new {
            background:#4a6a44;
            color:#aaffd3;
            border-radius:18px 18px 18px 4px;
            padding:0.8em 1.2em;
            margin-bottom:0.4em;
            margin-right:30px;
            font-weight:bold;
            font-family:'Inter',sans-serif;
            font-size:1.12rem;
        }
        .user-label {
            color:#f1fa8c;
            font-weight:700;
            padding-right:0.5em;
            font-family:'Montserrat',sans-serif;
            font-size:1.12em;
            letter-spacing: 1px;
        }
        .agent-label {
            color:#50fa7b;
            font-weight:700;
            padding-right:0.5em;
            font-family:'Montserrat',sans-serif;
            font-size:1.12em;
            letter-spacing: 1px;
        }
        .timestamp {
            color:#999;
            font-size:0.98em;
            padding-left:0.7em;
            font-family:'Fira Mono',monospace;
        }
        .category-label {
            color:#ffd966;
            font-size:1.01em;
            font-family:'Inter',sans-serif;
            font-weight:600;
        }
        .tool-label {
            color:#6ec7ff;
            font-size:1.01em;
            font-family:'Inter',sans-serif;
            font-weight:600;
        }
        .time-label {
            color:#5cff5c;
            font-size:1.01em;
            font-family:'Fira Mono',monospace;
            font-weight:600;
        }
        .input-area textarea {
            background:#282a36;
            color:#fff;
            border-radius:12px;
            font-family:'Inter',sans-serif;
            font-size:1.11em;
        }
        .stButton > button {
            background:#50fa7b;
            color:#181920;
            font-weight:700;
            border-radius:12px;
            font-family:'Montserrat',sans-serif;
            font-size:1.08em;
            letter-spacing: 0.5px;
        }
        .stButton > button:hover {
            background:#8aff80;
        }
        .spinner {color:#50fa7b;font-size:1.2em;}
        /* Make markdown code blocks use Fira Mono */
        .element-container pre, .element-container code, code {
            font-family: 'Fira Mono', 'Fira Code', 'Menlo', 'Consolas', monospace !important;
            font-size: 1.03em !important;
            background: #22242e !important;
            color: #aaffd3 !important;
            border-radius: 7px !important;
            padding: 0.2em 0.5em !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="raychel-title">⚡🧠 Raychel AI: Autonomous Reasoning Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="raychel-subtitle">Curious like Raya. Reliable like Chelsea.</div>', unsafe_allow_html=True)
st.markdown("""
    <div class="raychel-desc">
    I named my project <b>Raychel AI</b> as a fusion of Raya and Chelsea, my two pets who inspired the idea of balance — one curious and agile, the other loyal and steady. The name reflects that same duality in this system: curiosity through reasoning, and reliability through consistent decision-making.<br>
    <br>
    The subtitle <b>‘Autonomous Reasoning Agent’</b> defines its role — an AI that can think, decide, and act independently within given parameters.
    </div>
""", unsafe_allow_html=True)

st.write("")

def format_weather_forecast(text: str) -> str:
    """
    Format a weather forecast string for nice display.
    """
    first_period = text.find(".")
    summary = text
    forecast = ""
    if first_period != -1:
        summary = text[:first_period+1]
        forecast = text[first_period+1:]
    forecast_lines = []
    for match in re.finditer(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): ([^,]+), ([\d\.]+°C)", forecast):
        dt, desc, temp = match.groups()
        forecast_lines.append(f"- `{dt}`: {desc}, **{temp}**")
    if forecast_lines:
        return f"{summary}\n\n**Forecast:**\n" + "\n".join(forecast_lines)
    neat = re.sub(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}):", r"\n- `\1`:", text)
    return neat

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Type your question here:", key="user_input",
        placeholder="Ask about weather, sports, politics, general knowledge, etc."
    )
    submit = st.form_submit_button("Ask")

if submit and user_input:
    start_time = time.time()
    answer, category, tool = agent_streamlit_response(user_input)
    elapsed = time.time() - start_time
    timestamp = datetime.now().strftime("%H:%M")
    # Insert new messages at the top (index 0) for newest-first chat order
    st.session_state.chat_history.insert(0, {
        "role": "agent", "text": answer, "category": category, "tool": tool, "time": timestamp, "elapsed": elapsed
    })
    st.session_state.chat_history.insert(0, {
        "role": "user", "text": user_input, "category": category, "time": timestamp
    })

# Display chat history, newest first (top), with nice separator and green time, highlight newest
for idx, msg in enumerate(st.session_state.chat_history):
    is_new = idx == 0 or idx == 1  # highlight the topmost user+agent pair
    bubble_class = "bubble-agent" if msg["role"] == "agent" else "bubble-user"
    if is_new:
        bubble_class += "-new"
    field_html = f'<span class="category-label">Field: {msg.get("category", "Unknown")}</span>'
    tool_html = f'<span class="tool-label">Tool: {msg.get("tool", "Unknown")}</span>' if msg["role"] == "agent" else ""
    time_html = f'<span class="time-label">Time taken: {msg.get("elapsed",0):.2f}s</span>' if msg["role"] == "agent" else ""
    separator = '<span style="color:#888;padding:0 6px;">•</span>'
    meta_html = separator.join(filter(None, [field_html, tool_html, time_html]))
    if msg["role"] == "user":
        st.markdown(
            f'<div class="{bubble_class}"><span class="user-label">You:</span>{msg["text"]}'
            f'<span class="timestamp">{msg["time"]}</span><br>{field_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        agent_text = msg["text"]
        if msg.get("tool", "").lower() == "weather":
            agent_text = format_weather_forecast(agent_text)
        st.markdown(
            f'<div class="{bubble_class}"><span class="agent-label">🤖 Agent:</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'{agent_text}\n\n{meta_html}',
            unsafe_allow_html=True,
        )

if st.button("🗑️ New Chat"):
    st.session_state.chat_history = []