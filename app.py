import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from google import genai

# ----------------------------
# 🌙 Page Config
# ----------------------------
st.set_page_config(
    page_title="DreamWalker 🌙",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------
# 🔑 API Key Setup
# ----------------------------
API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found. Add it in Streamlit Secrets or as an environment variable.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ----------------------------
# 🌌 Assets & Styling
# ----------------------------
SPACE_BG_URL = "https://upload.wikimedia.org/wikipedia/commons/2/2e/ESO_-Milky_Way_Arch.jpg"
local_astronaut = Path("assets/astronaut.png")
ASTRONAUT_SRC = "assets/astronaut.png" if local_astronaut.exists() else "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Emu_space_suit.png/512px-Emu_space_suit.png"

# Add custom CSS for background and layout
st.markdown(f"""
<style>
.stApp {{
    background: url('{SPACE_BG_URL}') no-repeat center center fixed;
    background-size: cover;
    color: #e9e6ff;
}}
.stApp::before {{
    content: "";
    position: fixed;
    inset: 0;
    background: radial-gradient(ellipse at center, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.85) 100%);
    z-index: -1;
}}
.hero {{
    text-align: center;
    padding-top: 2rem;
}}
.hero h1 {{
    font-size: 3rem;
    background: linear-gradient(135deg, #fff, #9a6bff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
textarea {{
    background: rgba(10,7,17,0.65) !important;
    color: #efeaff !important;
}}
.panel {{
    background: rgba(15,10,25,0.7);
    border: 1px solid rgba(154,107,255,0.35);
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,.35);
    backdrop-filter: blur(3px);
}}
#astro-wrapper {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 1000;
}}
#astro {{
    position: absolute;
    width: clamp(70px, 9vw, 120px);
    opacity: .9;
    filter: drop-shadow(0 8px 18px rgba(0,0,0,.45));
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 🧑‍🚀 Floating Astronaut (JS)
# ----------------------------
astro_html = """
<div id="astro-wrapper">
  <img id="astro" src="{ASTRONAUT_SRC}" alt="astronaut" />
</div>
<script>
  const astro = document.getElementById('astro');
  function driftAstronaut() {{
    const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    const margin = 80;
    const x = Math.floor(Math.random() * (vw - margin * 2)) + margin;
    const y = Math.floor(Math.random() * (vh - margin * 2)) + margin;
    astro.style.transform = `translate(${x}px, ${y}px) rotate(${Math.random() * 12 - 6}deg)`;
  }}
  astro.style.transition = "transform 7s ease-in-out";
  driftAstronaut();
  setInterval(driftAstronaut, 8000);
  window.addEventListener('resize', driftAstronaut);
</script>
"""
components.html(astro_html, height=0)

# ----------------------------
# 🧠 AI Functions
# ----------------------------
def generate_story(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # latest stable free model (Oct 2025)
            contents=prompt
        )
        return response.text
    except Exception as e:
        st.error(f"❌ Gemini API Error: {e}")
        return ""

def build_prompt(dream_text: str, tone: str | None) -> str:
    tone_line = f"Preferred storytelling tone: {tone}." if tone else "Use a neutral, cinematic tone."
    return f"""
You are DreamWalker — a legendary interpreter of dreams.
1. Analyze the dream symbolically and psychologically.
2. Then write a 2–3 paragraph cinematic story inspired by it.

OUTPUT:
1) Psychological Interpretation:
- Emotions:
- Symbols:
- Meaning:
2) Cinematic Story:
[Story here]

{tone_line}

Dream:
\"\"\"{dream_text}\"\"\"
"""

def build_continue_prompt(story: str, tone: str | None) -> str:
    tone_line = f"Maintain tone: {tone}." if tone else "Maintain the same tone."
    return f"Continue this story in 1–2 paragraphs. {tone_line}\n\nStory so far:\n\"\"\"{story}\"\"\""

def build_restyle_prompt(story: str, tone: str) -> str:
    return f"Rewrite the following story in a {tone} tone while preserving its plot:\n\n\"\"\"{story}\"\"\""

# ----------------------------
# 🌙 UI
# ----------------------------
st.markdown("""
<div class="hero">
    <h1>🌙 DreamWalker</h1>
    <p>Turn your dreams into cinematic stories — woven by AI, interpreted by psychology.</p>
</div>
""", unsafe_allow_html=True)

dream = st.text_area("Describe your dream", height=200, placeholder="I was flying over a city made of glass...")
tone = st.selectbox("Story tone (optional)", ["", "Mystical", "Dark", "Poetic", "Mythic", "Hopeful", "Melancholic"], index=0)

col1, col2, col3 = st.columns(3)
generate = col1.button("✨ Interpret & Weave")
continue_story = col2.button("🪄 Continue the Dream")
restyle_story = col3.button("🎨 Restyle Story")

if "interpretation" not in st.session_state:
    st.session_state.interpretation = ""
if "story" not in st.session_state:
    st.session_state.story = ""

# ----------------------------
# 🚀 Button Actions
# ----------------------------
if generate:
    if not dream.strip():
        st.warning("Please describe your dream first.")
    else:
        with st.spinner("Weaving your dream... ✨"):
            full_text = generate_story(build_prompt(dream.strip(), tone))
        if "2) Cinematic Story:" in full_text:
            parts = full_text.split("2) Cinematic Story:")
            st.session_state.interpretation = parts[0].replace("1) Psychological Interpretation:", "").strip()
            st.session_state.story = parts[1].strip()
        else:
            st.session_state.interpretation = "Could not parse properly. Full response:\n\n" + full_text
            st.session_state.story = ""

if continue_story and st.session_state.story:
    with st.spinner("Continuing your dream... 🪄"):
        extra = generate_story(build_continue_prompt(st.session_state.story, tone))
    st.session_state.story += "\n\n" + extra

if restyle_story and st.session_state.story:
    with st.spinner("Restyling your story 🎨..."):
        restyled = generate_story(build_restyle_prompt(st.session_state.story, tone or "Poetic"))
    st.session_state.story = restyled.strip()

# ----------------------------
# 📜 Results
# ----------------------------
st.write("---")
left, right = st.columns(2)

with left:
    st.subheader("🧠 Psychological Interpretation")
    if st.session_state.interpretation:
        st.markdown(f"<div class='panel'>{st.session_state.interpretation}</div>", unsafe_allow_html=True)
    else:
        st.caption("Your dream interpretation will appear here.")

with right:
    st.subheader("📖 Cinematic Story")
    if st.session_state.story:
        st.markdown(f"<div class='panel'>{st.session_state.story}</div>", unsafe_allow_html=True)
        st.download_button(
            "📥 Download Story (.txt)",
            data=st.session_state.story.encode("utf-8"),
            file_name="dreamwalker_story.txt",
            mime="text/plain"
        )
    else:
        st.caption("Your story will appear here.")

# ----------------------------
# 📌 Footer
# ----------------------------
st.markdown("""
<div class="footer">
Built with ❤️ using Streamlit + Gemini • Your dreams are never stored or shared.
</div>
""", unsafe_allow_html=True)
