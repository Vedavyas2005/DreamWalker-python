import os
import math
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

# ----------------------
# Page config
# ----------------------
st.set_page_config(
    page_title="DreamWalker",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------
# API Key loading
# ----------------------
import google.generativeai as genai
import streamlit as st

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


# ----------------------
# Style & assets
# ----------------------
# Space background (real NASA/ESA space photo, public-domain/CC)
SPACE_BG_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/2/2e/ESO_-"
    "Milky_Way_Arch.jpg"
)

# Try local astronaut first, else a public-domain fallback
local_astronaut = Path("assets/astronaut.png")
if local_astronaut.exists():
    ASTRONAUT_SRC = "assets/astronaut.png"
else:
    # Fallback: NASA EVA suit render (public-domain like content)
    ASTRONAUT_SRC = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Emu_space_suit.png/512px-Emu_space_suit.png"
    )

# Inject CSS
try:
    with open("static/styles.css", "r", encoding="utf-8") as f:
        custom_css = f.read()
except FileNotFoundError:
    custom_css = ""

custom_css = custom_css.replace("__SPACE_BG_URL__", SPACE_BG_URL)
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# ----------------------
# Floating astronaut via HTML + JS
# ----------------------
astro_html = """
<div id="astro-wrapper">
  <img id="astro" src="{ASTRONAUT_SRC}" alt="astronaut" />
</div>
<script>
  const astro = document.getElementById('astro');
  const wrapper = document.getElementById('astro-wrapper');

  function driftAstronaut() {{
    const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

    // Keep astronaut inside viewport margins
    const margin = 80;
    const x = Math.floor(Math.random() * (vw - margin*2)) + margin;
    const y = Math.floor(Math.random() * (vh - margin*2)) + margin;

    astro.style.transform = `translate(${x}px, ${y}px) rotate(${Math.random()*12-6}deg)`;
  }}

  // Smooth transition
  astro.style.transition = "transform 7s ease-in-out";
  driftAstronaut();
  setInterval(driftAstronaut, 8000);

  // Resize handler keeps it in bounds
  window.addEventListener('resize', () => {{
    driftAstronaut();
  }});
</script>
"""
components.html(astro_html, height=0)  # injects fixed overlay without taking space

# ----------------------
# Gemini helpers
# ----------------------
def call_gemini(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(prompt)
    return getattr(resp, "text", "").strip()

def build_prompt(dream_text: str, tone: str | None) -> str:
    tone_line = f"Preferred storytelling tone: {tone}." if tone else "Use a neutral, cinematic tone."
    return f"""
You are DreamWalker — an ancient dream interpreter and storyteller.
Analyze the user's dream from a psychological and symbolic perspective,
then write a cinematic short story version (2–3 paragraphs), vivid but concise.

OUTPUT STRICT FORMAT:
1) Psychological Interpretation:
- Emotions:
- Symbols:
- Meaning:
2) Cinematic Story:
[Write 2–3 paragraphs of evocative prose.]

Guidelines:
- Be respectful and empathetic.
- Do not invent personal facts about the user.
- Keep it PG-13.

{tone_line}

Dream:
\"\"\"{dream_text}\"\"\"
""".strip()

def build_continue_prompt(previous_story: str, tone: str | None) -> str:
    tone_line = f"Maintain tone: {tone}." if tone else "Maintain the same tone."
    return f"""
Continue the following dream story seamlessly for 1–2 paragraphs.
Preserve continuity, imagery, and flow. {tone_line}

Story so far:
\"\"\"{previous_story}\"\"\"
""".strip()

def build_restyle_prompt(previous_story: str, tone: str) -> str:
    return f"""
Rewrite the following story into the specified tone and voice. Keep the plot intact,
enhance imagery, and ensure cohesion. Tone: {tone}

Story:
\"\"\"{previous_story}\"\"\"
""".strip()

# ----------------------
# UI
# ----------------------
st.markdown(
    """
<div class="hero">
  <div class="brand">🌙 DreamWalker</div>
  <div class="tagline">Turn your dreams into stories.</div>
  <div class="subtle">Private by design • Real space background • No data stored</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.container():
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.write("### Describe your dream")
        dream = st.text_area(
            " ",
            height=220,
            placeholder="I was running through a silent forest while the stars were falling like snow...",
            label_visibility="collapsed",
        )

        st.write("### Story tone (optional)")
        tone = st.selectbox(
            "Pick a style",
            ["", "Mystical", "Dark", "Poetic", "Mythic", "Hopeful", "Melancholic"],
            index=0,
            help="Choose how the story should feel.",
        )

        colA, colB, colC = st.columns([1, 1, 1])
        gen_clicked = colA.button("✨ Interpret & Weave", use_container_width=True)
        cont_clicked = colB.button("🪄 Continue the Dream", use_container_width=True)
        restyle_clicked = colC.button("🎨 Restyle Story", use_container_width=True, disabled=False)

    with right:
        st.write("### Privacy")
        st.info("We do not store your dreams. Everything is processed in memory and cleared when you refresh.", icon="🔒")
        st.write("### Tips")
        st.markdown(
            "- Be as descriptive as you can.\n"
            "- Include places, people, colors, feelings.\n"
            "- One dream at a time gives best results."
        )

# Session state for results
if "interpretation" not in st.session_state:
    st.session_state.interpretation = ""
if "story" not in st.session_state:
    st.session_state.story = ""

# Generate
if gen_clicked:
    if not dream or not dream.strip():
        st.warning("Please describe your dream first.")
    else:
        with st.spinner("Weaving your dream into meaning and story..."):
            prompt = build_prompt(dream.strip(), tone if tone else None)
            full = call_gemini(prompt)
        # Parse strict sections
        interp, story = "", ""
        if "2) Cinematic Story:" in full:
            parts = full.split("2) Cinematic Story:")
            interp = parts[0].replace("1) Psychological Interpretation:", "").strip()
            story = parts[1].strip()
        else:
            # Fallback if model didn't follow exact format
            interp = "Could not parse sections strictly. Here's the full response:\n\n" + full
            story = ""
        st.session_state.interpretation = interp
        st.session_state.story = story

# Continue
if cont_clicked:
    if not st.session_state.story:
        st.warning("Generate a story first, then continue it.")
    else:
        with st.spinner("Extending your dream..."):
            cont_prompt = build_continue_prompt(st.session_state.story, tone if tone else None)
            more = call_gemini(cont_prompt)
        st.session_state.story = (st.session_state.story + "\n\n" + more).strip()

# Restyle
if restyle_clicked:
    if not st.session_state.story:
        st.warning("Generate a story first, then restyle it.")
    else:
        with st.spinner("Restyling your story..."):
            restyle_prompt = build_restyle_prompt(st.session_state.story, tone or "Poetic")
            restyled = call_gemini(restyle_prompt)
        st.session_state.story = restyled.strip()

# ----------------------
# Results
# ----------------------
st.write("---")
res_left, res_right = st.columns([1, 1], gap="large")

with res_left:
    st.subheader("🧠 Psychological Interpretation")
    if st.session_state.interpretation:
        st.markdown(f"<div class='panel'>{st.session_state.interpretation}</div>", unsafe_allow_html=True)
    else:
        st.caption("Your interpretation will appear here.")

with res_right:
    st.subheader("📖 Cinematic Story")
    if st.session_state.story:
        st.markdown(f"<div class='panel prose'>{st.session_state.story}</div>", unsafe_allow_html=True)
        st.download_button(
            "📥 Download Story (.txt)",
            data=st.session_state.story.encode("utf-8"),
            file_name="dreamwalker_story.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.caption("Your story will appear here.")

st.markdown(
    """
<div class="footer">
  <span>Built with Streamlit • Powered by Gemini • Space imagery © respective owners (public domain/CC).</span>
</div>
""",
    unsafe_allow_html=True,
)
