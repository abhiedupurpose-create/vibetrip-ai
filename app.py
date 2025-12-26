import streamlit as st
import google.generativeai as genai
from serpapi import GoogleSearch
import json
import datetime
import random
import urllib.parse
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="VibeTrip AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ADVANCED CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        font-size: 18px;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a1c2e 0%, #0f1016 100%);
        color: #E0E0E0;
    }
    
    /* HERO IMAGE */
    .hero-container {
        position: relative;
        width: 100%;
        height: 350px; 
        overflow: hidden;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-bottom: -60px;
    }
    .hero-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0.8;
    }
    .hero-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 60%;
        background: linear-gradient(to top, #0f1016 10%, transparent 100%);
    }
    
    /* MODERN GLASS CARDS - FIXED ALIGNMENT */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        height: 100%;
        min-height: 320px; /* Increased to ensure alignment */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        border: 1px solid rgba(255, 75, 75, 0.5);
    }
    
    /* SMALLER GLASS CARD FOR METRICS */
    .glass-metric {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        text-align: center;
        height: 100%;
    }
    
    /* TYPOGRAPHY */
    .price-tag { font-size: 28px; font-weight: 800; color: #4CAF50; margin: 10px 0; }
    .name-header { font-size: 22px; font-weight: 700; color: #FFD700; line-height: 1.3; min-height: 60px; }
    .desc-text { font-size: 16px; color: #ccc; margin-bottom: 15px; flex-grow: 1; }
    
    /* LINKS BUTTONS */
    .booking-btn {
        display: block;
        background-color: rgba(255, 75, 75, 0.1);
        color: #FF4B4B;
        text-decoration: none;
        font-size: 15px;
        font-weight: bold;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #FF4B4B;
        transition: all 0.3s;
        text-align: center;
        margin-top: auto; /* Pushes button to bottom */
    }
    .booking-btn:hover {
        background-color: #FF4B4B;
        color: white;
    }

    /* MAIN BUTTON */
    .stButton>button {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9068 100%);
        color: white;
        border: none;
        padding: 18px 30px;
        font-size: 20px;
        border-radius: 12px;
        width: 100%;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }
    
    /* METRIC TEXT */
    .metric-label { font-size: 14px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 24px; font-weight: bold; color: #fff; margin-top: 5px; }
    .total-value { color: #FFD700; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    if "GEMINI_API_KEY" in st.secrets and "SERPAPI_KEY" in st.secrets:
        st.success("✅ Systems Online")
        gemini_key = st.secrets["GEMINI_API_KEY"]
        serp_key = st.secrets["SERPAPI_KEY"]
    else:
        gemini_key = st.text_input("Gemini Key", type="password")
        serp_key = st.text_input("SerpAPI Key", type="password")

    st.divider()
    
    destination = st.text_input("Destination", value="Goa")
    origin = st.text_input("Starting From", value="Mumbai")
    
    currency_str = st.selectbox("Currency", ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"])
    # Extract symbol safely
    currency_symbol = currency_str.split("(")[1].strip(")")
    
    travel_date = st.date_input("Start Date", datetime.date.today() + datetime.timedelta(days=30))
    duration = st.slider("Duration (Days)", 2, 30, 3)
    budget = st.number_input(f"Total Budget ({currency_symbol})", value=20000, step=1000)
    travelers = st.selectbox("Group", ["Solo", "Couple", "Family", "Friends"])

# --- HELPER FUNCTIONS ---

def get_fast_image(query):
    """Uses Pollinations AI for instant, free images"""
    clean_query = urllib.parse.quote(query + " cinematic travel 4k aesthetic")
    return f"https://image.pollinations.ai/prompt/{clean_query}?width=1200&height=600&nologo=true"

def create_booking_link(query):
    """Generates a clean Google Search link"""
    clean_text = re.sub(r'[^\w\s]', '', query)
    base = "https://www.google.com/search?q="
    final_query = urllib.parse.quote(clean_text.strip())
    return f"{base}{final_query}"

def get_live_data(dest, orig, duration, budget, curr_sym, travelers, vibe, constraint, amaze_mode, g_key, s_key):
    genai.configure(api_key=g_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    search_modifier = "hidden gems offbeat" if amaze_mode else "top rated popular"
    transport_mode = "flights trains buses" 
    
    queries = [
        f"{search_modifier} hotels in {dest} for {travelers} price",
        f"{transport_mode} from {orig} to {dest} price",
        f"must do experiences in {dest} {vibe}"
    ]
    
    search_context = ""
    for q in queries:
        try:
            params = {"engine": "google", "q": q, "api_key": s_key, "num": 4}
            search = GoogleSearch(params)
            results = search.get_dict()
            snippets = [r.get("snippet", "") + f" (Price: {r.get('price', 'Check Site')})" for r in results.get("organic_results", [])]
            search_context += f"\nSearch '{q}': " + " | ".join(snippets)
        except:
            continue

    prompt = f"""
    Act as a Travel Expert.
    User: Trip to {dest} from {orig} ({duration} days). Budget: {budget} {curr_sym}. Group: {travelers}.
    Vibe: "{vibe}" | Constraints: "{constraint}"
    
    REAL DATA: {search_context}
    
    Task: Create a JSON plan in {curr_sym}.
    
    LOGIC CHECKS:
    1. **Budget Check**: If {budget} is tight, provide a helpful "budget_tip".
    2. **Transport**: Suggest 2 options.
    3. **Misc Costs**: Include "Shopping & Misc".
    
    OUTPUT JSON FORMAT:
    {{
      "budget_tip": null (or string),
      "hero_hook": "Short 5-word catchy hook",
      "summary": "Detailed 2-sentence overview.",
      "vibe_events": [{{ "title": "Event Name", "description": "Why it fits" }}],
      "transport": [{{ "type": "Flight/Train", "name": "Provider", "price": "1500", "details": "Duration/Info" }}],
      "stay": [{{ "name": "Hotel Name", "price": "5000", "rating": "4.5", "features": "Pool, AC" }}],
      "itinerary": [{{ "day": 1, "theme": "Title", "morning": "...", "afternoon": "...", "evening": "..." }}],
      "costs": {{ "transport": "500", "stay": "1000", "food": "500", "shopping_misc": "200", "total": "2200" }}
    }}
    """
    
    for _ in range(2):
        try:
            response = model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "")
            return json.loads(clean_json)
        except:
            continue
            
    return {"error": "AI is taking a break. Please try again."}

# --- MAIN UI ---

st.markdown("<h1 style='text-align: center; font-size: 70px; margin-bottom: 10px;'>✨ VibeTrip</h1>", unsafe_allow_html=True)

# INPUTS
c1, c2 = st.columns(2)
with c1:
    vibe = st.text_area("Your Vibe ✨", placeholder="I want art, street food, and chaos...", height=100)
with c2:
    cons = st.text_area("Constraints 🚫", placeholder="No museums, no walking > 2km...", height=100)

amaze_me = st.toggle("🤯 Amaze Me! (Hidden Gems Mode)")

if st.button("🚀 Curate My Experience"):
    if not gemini_key or not serp_key:
        st.error("⚠️ Please enter API Keys in the sidebar to proceed.")
        st.stop()
        
    with st.status("🔮 Unlocking the Vibe...", expanded=True) as status:
        st.write("🌍 Analyzing routes & rates...")
        st.write("🏨 Auditing availability...")
        if amaze_me:
            st.write("🕵️‍♂️ Going off the beaten path...")
        
        hero_image = get_fast_image(destination)
        
        data = get_live_data(destination, origin, duration, budget, currency_symbol, travelers, vibe, cons, amaze_me, gemini_key, serp_key)
        
        status.update(label="✨ Vibe Unlocked!", state="complete", expanded=False)

    if "error" in data:
        st.error(data["error"])
    else:
        # --- HERO SECTION ---
        st.markdown(f"""
        <div class="hero-container">
            <img src="{hero_image}" class="hero-img">
            <div class="hero-overlay"></div>
        </div>
        <div style="padding: 20px; position: relative; z-index: 2; margin-top: -100px;">
            <h1 style="margin:0; font-size: 50px; text-shadow: 0 4px 8px black;">{destination}</h1>
            <p style="font-size: 20px; color: #FF4B4B; font-weight: bold; background: rgba(0,0,0,0.6); display: inline-block; padding: 5px 15px; border-radius: 20px;">
                // {data.get('hero_hook', 'Your Curated Escape')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- BUDGET INSIGHT ---
        if data.get('budget_tip'):
            st.info(f"💡 **Travel Insight:** {data.get('budget_tip')}")

        st.markdown(f"<p style='font-size: 20px; margin-top: 20px;'>{data.get('summary')}</p>", unsafe_allow_html=True)
        st.divider()

        # --- SIGNATURE EXPERIENCES ---
        st.subheader("🌟 Signature Experiences")
        v_cols = st.columns(3)
        icons = ["✨", "🌊", "💎", "🔥", "🌴"]
        
        for i, event in enumerate(data.get('vibe_events', [])[:3]):
            current_icon = icons[i % len(icons)]
            with v_cols[i]:
                st.markdown(f"""
                <div class="glass-card">
                    <div>
                        <div style="font-size: 30px; margin-bottom: 10px;">{current_icon}</div>
                        <div class="name-header">{event.get('title')}</div>
                        <p class="desc-text">{event.get('description')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # --- TRANSPORT & STAY (FIXED ALIGNMENT) ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("🚌 Getting There")
            for t in data.get('transport', []):
                link = create_booking_link(f"book {t.get('type')} {t.get('name')} from {origin} to {destination}")
                st.markdown(f"""
                <div class="glass-card">
                    <div>
                        <div class="name-header">{t.get('type')} {t.get('name')}</div>
                        <div class="price-tag">{currency_symbol} {t.get('price')}</div>
                        <p class="desc-text">{t.get('details')}</p>
                    </div>
                    <a href="{link}" target="_blank" class="booking-btn">Check Rates ↗</a>
                </div>
                <br>
                """, unsafe_allow_html=True)

        with c2:
            st.subheader("🏨 The Stay")
            for s in data.get('stay', []):
                link = create_booking_link(f"book hotel {s.get('name')} {destination}")
                st.markdown(f"""
                <div class="glass-card">
                    <div>
                        <div class="name-header">{s.get('name')} <span style='font-size:16px'>({s.get('rating')}⭐)</span></div>
                        <div class="price-tag">{currency_symbol} {s.get('price')}</div>
                        <p class="desc-text">{s.get('features')}</p>
                    </div>
                    <a href="{link}" target="_blank" class="booking-btn">View Deal ↗</a>
                </div>
                <br>
                """, unsafe_allow_html=True)

        # --- ITINERARY ---
        st.divider()
        st.subheader("📅 Daily Itinerary")
        for day in data.get('itinerary', []):
            with st.expander(f"Day {day.get('day')} : {day.get('theme')}", expanded=True):
                c_a, c_b, c_c = st.columns(3)
                c_a.markdown(f"**🌅 Morning**\n\n{day.get('morning')}")
                c_b.markdown(f"**☀️ Afternoon**\n\n{day.get('afternoon')}")
                c_c.markdown(f"**🌙 Evening**\n\n{day.get('evening')}")

        # --- COSTS (NEW GLASS STYLE) ---
        st.divider()
        st.subheader(f"💰 Estimated Investment ({currency_symbol})")
        costs = data.get('costs', {})
        cols = st.columns(5)
        
        metrics = [
            ("✈️ Transport", 'transport', ''), 
            ("🏨 Stay", 'stay', ''), 
            ("🍹 Food", 'food', ''), 
            ("🛍️ Misc", 'shopping_misc', ''), 
            ("✨ TOTAL", 'total', 'total-value')
        ]
        
        for col, (label, key, extra_class) in zip(cols, metrics):
            val = costs.get(key, '0')
            with col:
                st.markdown(f"""
                <div class="glass-metric">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value {extra_class}">{currency_symbol} {val}</div>
                </div>
                """, unsafe_allow_html=True)