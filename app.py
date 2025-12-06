# app.py
# AI Vacation Recommendation Chatbot (fast 1-2 day version)
# Requirements: streamlit, openai (optional)
# pip install streamlit openai

import streamlit as st
import os
import random
import urllib.parse

try:
    import openai
except Exception:
    openai = None

st.set_page_config(page_title="AI Vacation Chatbot", layout="wide")

# ---------------------------
# Helper: small rule-based recommender (fallback)
# ---------------------------
DESTINATIONS = {
    "budget": [
        {"city": "Goa, India", "country": "India", "price": 300, "tags": ["beach","budget","relaxation"], "img": "https://source.unsplash.com/800x600/?beach,India"},
        {"city": "Hoi An, Vietnam", "country": "Vietnam", "price": 450, "tags": ["culture","food","budget"], "img": "https://source.unsplash.com/800x600/?HoiAn,Vietnam"}
    ],
    "mid": [
        {"city": "Lisbon, Portugal", "country": "Portugal", "price": 900, "tags": ["city","food","history"], "img": "https://source.unsplash.com/800x600/?Lisbon,Portugal"},
        {"city": "Marrakesh, Morocco", "country": "Morocco", "price": 1100, "tags": ["culture","markets","adventure"], "img": "https://source.unsplash.com/800x600/?Marrakesh,Morocco"}
    ],
    "premium": [
        {"city": "Santorini, Greece", "country": "Greece", "price": 2200, "tags": ["luxury","romance","island"], "img": "https://source.unsplash.com/800x600/?Santorini,Greece"},
        {"city": "Kyoto, Japan", "country": "Japan", "price": 2500, "tags": ["culture","temples","luxury"], "img": "https://source.unsplash.com/800x600/?Kyoto,Japan"}
    ]
}

# ---------------------------
# Helper: OpenAI call (if available)
# ---------------------------
def call_openai_chat(prompt, model="gpt-3.5-turbo", max_tokens=200, temperature=0.7):
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
    if not openai or not api_key:
        return None
    openai.api_key = api_key
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role":"system","content":"You are a helpful travel assistant."},
                      {"role":"user","content":prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        text = resp["choices"][0]["message"]["content"].strip()
        return text
    except Exception as e:
        st.error("OpenAI API call failed: " + str(e))
        return None

# ---------------------------
# Utility: create google maps link
# ---------------------------
def maps_link(city_country):
    q = urllib.parse.quote_plus(city_country)
    return f"https://www.google.com/maps/search/?api=1&query={q}"

# ---------------------------
# UI layout
# ---------------------------
st.title("✈️ AI Vacation Recommendation Chatbot")
st.write("Quick: enter your preferences and get 3 personalized trip recommendations. Works with OpenAI (if you provide an API key) or with a fast fallback.")

col1, col2 = st.columns([2,1])

with col1:
    st.header("Tell me about the trip")
    budget = st.selectbox("Budget (USD)", ["< 500", "500 - 1500", "> 1500"])
    trip_type = st.selectbox("Trip type", ["Relaxation", "Adventure", "Culture", "Luxury", "Solo", "Couple", "Family"])
    city_pref = st.text_input("Destination or country (optional)", placeholder="e.g., Paris or Japan")
    start_date = st.date_input("Start date (optional)", value=None)
    nights = st.number_input("Nights (optional)", min_value=1, max_value=30, value=5)
    n_results = st.slider("Show how many recommendations", 1, 6, 3)
    use_ai = st.checkbox("Use AI-enhanced descriptions (requires OPENAI_API_KEY)", value=True)

with col2:
    st.header("Quick tips")
    st.write("- If you don't have an OpenAI API key, uncheck the AI box to use fast fallback suggestions.")
    st.write("- To get an OpenAI key: create account at platform.openai.com and set it as OPENAI_API_KEY in Streamlit secrets or environment.")
    st.write("- Deploy: push to GitHub and publish on Streamlit Cloud (share.streamlit.io).")

if st.button("Find my stay"):
    with st.spinner("Generating recommendations..."):
        # Choose bucket
        if budget == "< 500":
            bucket = "budget"
        elif budget == "500 - 1500":
            bucket = "mid"
        else:
            bucket = "premium"

        # base choices
        base = DESTINATIONS.get(bucket, DESTINATIONS["mid"])
        # If user provided city, try to include
        recommendations = []
        if city_pref:
            # try to include a matching one (approx)
            for b in base:
                if city_pref.lower() in (b["city"] + " " + b["country"]).lower():
                    recommendations.append(b)
            # if none found, add a city-pref card
            if not recommendations:
                recommendations.append({"city": city_pref, "country": "", "price": int(sum(d["price"] for d in base)/len(base)),
                                        "tags": [trip_type.lower()], "img": f"https://source.unsplash.com/800x600/?{urllib.parse.quote_plus(city_pref)}"})
        # fill with random picks
        idx = 0
        while len(recommendations) < n_results:
            recommendations.append(random.choice(base))
            idx += 1
            if idx > 10:
                break

        # For each recommendation generate an AI description if possible
        final_cards = []
        for rec in recommendations[:n_results]:
            city_country = f"{rec['city']}, {rec['country']}".strip(", ")
            prompt = (f"Write a 2-3 sentence travel blurb for {city_country}. "
                      f"Trip type: {trip_type}. Budget tier: {budget}. Nights: {nights}. "
                      "Include 2 quick 'Top activities' bullet points and a one-line 'Why go' tagline.")
            ai_text = None
            if use_ai:
                ai_text = call_openai_chat(prompt)
            if ai_text is None:
                # fallback short description
                ai_text = f"{rec['city']} is a great {trip_type.lower()} destination. Top activities: {', '.join(rec.get('tags',[])[:2])}. Why go: beautiful sights and local culture."
            # do a little parsing to bullets if available
            final_cards.append({
                "city": rec["city"],
                "location": city_country,
                "price_estimate": rec["price"],
                "img": rec.get("img"),
                "description": ai_text,
                "map_link": maps_link(city_country)
            })

    # Display cards in grid
    cols = st.columns(3)
    for i, card in enumerate(final_cards):
        c = cols[i % 3]
        with c:
            st.image(card["img"], use_column_width=True)
            st.markdown(f"### {card['city']}")
            st.markdown(f"**Estimated cost:** ${card['price_estimate']}")
            st.markdown(card["description"])
            st.markdown(f"[View on map]({card['map_link']})")
            st.markdown("---")

st.markdown("----")
st.caption("Built with Streamlit • Add OPENAI_API_KEY in Streamlit Secrets for AI descriptions.")
