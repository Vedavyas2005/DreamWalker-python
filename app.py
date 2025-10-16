import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# ----------------------------
# ✅ PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="DreamWalker 🌙",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------
# ✅ CONFIGURE GEMINI API
# ----------------------------
API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("🔑 GEMINI_API_KEY not found. Please add it in Streamlit Secrets or .env file.")
    st.stop()

genai.configure(api_key=API_KEY)

# ----------------------------
# ✅ GLOBAL VARIABLES
# ----------------------------
SPACE_BG_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/2/2e/ESO_-Milky_Way_Arch.jpg"
)
local_astronaut = Path("assets/astronaut.png")
if local_astronaut.exists():
    ASTRONAUT_SRC = "assets/astronaut.png"
else:
    ASTRONAUT_SRC = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Emu_space_suit.png/512px-Emu_space_suit.png"
    )

# ----------------------------
# ✅ CUSTOM CSS (INLINE)
# ----------------------------
st.markdown(
    f"""
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
        background: radial-gradient(ellipse at center, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.8) 100%);
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
    .hero p {{
        font-size: 1.2rem;
        opacity: 0.9;
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
    .footer {{
        margin-top: 2rem;
        text-align: center;
        font-size: 0.8rem;
        opacity: 0.7;
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
    """,
    unsafe_allow_html=True
)

# ----------------------------
# ✅ FLOATING ASTRONAUT JS
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
# ✅ GEMINI CALL FUNCTION
# ----------------------------
def call_gemini(prompt: str) -> str:
    try:
        response = genai.generate_text(
            model="models/gemini-1.5-flash",
            prompt=prompt
        )
        return response.candidates[0]['output']
    except Exception as e:
        st.error(f"❌ Gemini API error: {e}")
        return "⚠️ Something went wrong. Please check your API key or model name."
# ----------------------------
# ✅ PROMPT GENERATORS
# ----------------------------
def build_prompt(dream_text: str, tone: str | None) -> str:
    tone_line = f"Preferred storytelling tone: {tone}." if tone else "Use a neutral, cinematic tone."
    return f"""
You are DreamWalker — an ancient dream interpreter and storyteller.
Analyze the following dream psychologically and symbolically,
then rewrite it as a cinematic short story (2–3 paragraphs) full of emotion and atmosphere.

OUTPUT FORMAT:
1) Psychological Interpretation:
- Emotions:
- Symbols:
- Meaning:
2) Cinematic Story:
[Story paragraphs here]

{tone_line}

Dream:
\"\"\"{dream_text}\"\"\"
""".strip()

def build_continue_prompt(story: str, tone: str | None) -> str:
    tone_line = f"Maintain tone: {tone}." if tone else "Maintain the same tone."
    return f"""
Continue this dream story seamlessly for 1–2 paragraphs. {tone_line}

Story so far:
\"\"\"{story}\"\"\"
""".strip()

def build_restyle_prompt(story: str, tone: str) -> str:
    return f"""
Rewrite the following story in a {tone} tone. Keep the plot intact, improve imagery and language.

Story:
\"\"\"{story}\"\"\"
""".strip()

# ----------------------------
# ✅ UI - HERO SECTION
# ----------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🌙 DreamWalker</h1>
        <p>Turn your dreams into stories — interpreted by AI and woven into cinematic narratives.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# ✅ INPUT FORM
# ----------------------------
dream = st.text_area("Describe your dream", height=200, placeholder="I was running through a dark forest under falling stars...")
tone = st.selectbox("Story tone (optional)", ["", "Mystical", "Dark", "Poetic", "Mythic", "Hopeful", "Melancholic"], index=0)

col1, col2, col3 = st.columns(3)
generate = col1.button("✨ Interpret & Weave")
continue_story = col2.button("🪄 Continue the Dream")
restyle_story = col3.button("🎨 Restyle Story")

# ----------------------------
# ✅ SESSION STATE INIT
# ----------------------------
if "interpretation" not in st.session_state:
    st.session_state.interpretation = ""
if "story" not in st.session_state:
    st.session_state.story = ""

# ----------------------------
# ✅ BUTTON LOGIC
# ----------------------------
if generate:
    if not dream.strip():
        st.warning("Please describe your dream first.")
    else:
        with st.spinner("Weaving your dream... ✨"):
            prompt = build_prompt(dream.strip(), tone if tone else None)
            full_response = call_gemini(prompt)

        # Parse output
        if "2) Cinematic Story:" in full_response:
            parts = full_response.split("2) Cinematic Story:")
            st.session_state.interpretation = parts[0].replace("1) Psychological Interpretation:", "").strip()
            st.session_state.story = parts[1].strip()
        else:
            st.session_state.interpretation = "Could not parse properly:\n\n" + full_response
            st.session_state.story = ""

if continue_story:
    if not st.session_state.story:
        st.warning("Generate a story first!")
    else:
        with st.spinner("Continuing your dream... 🪄"):
            cont_prompt = build_continue_prompt(st.session_state.story, tone if tone else None)
            more_text = call_gemini(cont_prompt)
        st.session_state.story = (st.session_state.story + "\n\n" + more_text).strip()

if restyle_story:
    if not st.session_state.story:
        st.warning("Generate a story first!")
    else:
        with st.spinner("Restyling your story 🎨..."):
            restyle_prompt = build_restyle_prompt(st.session_state.story, tone or "Poetic")
            restyled = call_gemini(restyle_prompt)
        st.session_state.story = restyled.strip()

# ----------------------------
# ✅ RESULTS SECTION
# ----------------------------
st.write("---")
left, right = st.columns(2)

with left:
    st.subheader("🧠 Psychological Interpretation")
    if st.session_state.interpretation:
        st.markdown(f"<div class='panel'>{st.session_state.interpretation}</div>", unsafe_allow_html=True)
    else:
        st.caption("Your dream analysis will appear here.")

with right:
    st.subheader("📖 Cinematic Story")
    if st.session_state.story:
        st.markdown(f"<div class='panel'>{st.session_state.story}</div>", unsafe_allow_html=True)
        st.download_button(
            "📥 Download Story (.txt)",
            data=st.session_state.story.encode("utf-8"),
            file_name="dreamwalker_story.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.caption("Your story will appear here.")

# ----------------------------
# ✅ FOOTER
# ----------------------------
st.markdown(
    """
    <div class="footer">
        Built with ❤️ using Streamlit + Gemini • Your dreams are never stored or shared.
    </div>
    """,
    unsafe_allow_html=True
)
