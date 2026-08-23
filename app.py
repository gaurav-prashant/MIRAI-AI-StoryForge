import html
import json
import re
import textwrap
import urllib.parse
import streamlit as st
from utils.gemini import generate_content
from utils.save_system import export_adventure_json, load_adventure_json, clean_html_tags
from utils.image_generator import generate_scene_image, get_image_bytes, create_scene_images_zip
from utils.audio_manager import render_audio_components, get_background_track_for_genre, render_background_music, render_tts_widget
from utils.game_state import (
    init_default_game_state,
    get_default_genre_quest,
    apply_choice_consequences,
    build_compact_game_state_summary,
    evaluate_ending,
)




# =========================================================
# HELPER FUNCTIONS FOR HTML CLEANING
# =========================================================

def clean_html_tags(text):
    """Strips script, audio, style tags (and inner content) as well as HTML tags from story text."""
    if not text:
        return ""
    s = str(text)
    s = html.unescape(s)
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r'<audio[^>]*>.*?</audio>', '', s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r'<[^>]*>', '', s)
    return html.unescape(s).strip()


# =========================================================
# SAVE / LOAD ADVENTURE SYSTEM
# =========================================================

def export_adventure_json():
    """Serializes all relevant session_state keys into a clean JSON string."""
    save_data = {
        "version": "1.0",
        "saved_at_turn": st.session_state.get("turn", 0),
        "player_name": st.session_state.get("player_name", ""),
        "genre": st.session_state.get("genre", "Fantasy"),
        "world": st.session_state.get("world", ""),
        "game_started": st.session_state.get("game_started", False),
        "turn": st.session_state.get("turn", 0),
        "last_action": st.session_state.get("last_action", ""),
        "story_history": st.session_state.get("story_history", []),
        "health": st.session_state.get("health", 100),
        "max_health": st.session_state.get("max_health", 100),
        "attack": st.session_state.get("attack", 10),
        "defense": st.session_state.get("defense", 5),
        "xp": st.session_state.get("xp", 0),
        "level": st.session_state.get("level", 1),
        "gold": st.session_state.get("gold", 50),
        "inventory": st.session_state.get("inventory", []),
        "clues": st.session_state.get("clues", []),
    }
    return json.dumps(save_data, indent=2, ensure_ascii=False)


def load_adventure_json(file_content):
    """Parses JSON save file and restores st.session_state gracefully."""
    try:
        data = json.loads(file_content)
        if not isinstance(data, dict):
            return False, "Invalid save file format. Expected JSON object."

        # Validate required keys
        required_keys = ["player_name", "genre", "world", "story_history"]
        for key in required_keys:
            if key not in data:
                return False, f"Corrupted save file. Missing required key: '{key}'"

        # Restore state via dictionary assignment
        st.session_state["player_name"] = clean_html_tags(str(data.get("player_name", "")))
        st.session_state["genre"] = str(data.get("genre", "Fantasy"))
        st.session_state["world"] = clean_html_tags(str(data.get("world", "")))
        st.session_state["game_started"] = bool(data.get("game_started", True))
        st.session_state["turn"] = int(data.get("turn", 1))
        st.session_state["last_action"] = clean_html_tags(str(data.get("last_action", "")))

        # Sanitize story history
        raw_history = data.get("story_history", [])
        clean_history = []
        if isinstance(raw_history, list):
            for item in raw_history:
                if isinstance(item, dict):
                    clean_item = {
                        "turn": int(item.get("turn", 1)),
                        "scene": clean_html_tags(item.get("scene", "")),
                        "choices": [clean_html_tags(c) for c in item.get("choices", []) if clean_html_tags(c)],
                        "action": clean_html_tags(item.get("action", "")) if item.get("action") else None
                    }
                    clean_history.append(clean_item)

        st.session_state["story_history"] = clean_history

        # Restore RPG Stats
        st.session_state["health"] = int(data.get("health", 100))
        st.session_state["max_health"] = int(data.get("max_health", 100))
        st.session_state["attack"] = int(data.get("attack", 10))
        st.session_state["defense"] = int(data.get("defense", 5))
        st.session_state["xp"] = int(data.get("xp", 0))
        st.session_state["level"] = int(data.get("level", 1))
        st.session_state["gold"] = int(data.get("gold", 50))
        st.session_state["inventory"] = [clean_html_tags(i) for i in data.get("inventory", []) if clean_html_tags(i)]
        st.session_state["clues"] = [clean_html_tags(c) for c in data.get("clues", []) if clean_html_tags(c)]

        return True, f"Adventure loaded! Character: {st.session_state['player_name']} (Turn {st.session_state['turn']})"

    except json.JSONDecodeError:
        return False, "File is corrupted or not a valid JSON file."
    except Exception as e:
        return False, f"Failed to load adventure: {type(e).__name__}: {str(e)}"







# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="MirAI AI StoryForge",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Neon Cyberpunk & Mythic Celestial AAA Studio UI
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700;900&family=Cinzel:wght@500;700;800;900&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600;700&family=Rajdhani:wght@500;600;700&display=swap');

    html, body, .stApp {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        letter-spacing: 0.015em;
        color: #e2ebf8;
    }

    [data-testid="stExpanderToggleIcon"], [data-testid="stExpanderIcon"], .stIcon {
        font-family: inherit !important;
    }

    header[data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"]       { display: none !important; }
    #MainMenu, footer               { visibility: hidden; }


    [data-testid="stCustomComponentV1"],
    iframe[title="streamlit.components.v1.html"],
    iframe[srcdoc*="audio"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        width: 0px !important;
        min-height: 0px !important;
        max-height: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }

    /* --- CELESTIAL OBSIDIAN & SOLAR AMBER DEEP BACKGROUND --- */
    .stApp {
        background:
            radial-gradient(circle 800px at 10% 10%, rgba(255, 195, 60, 0.07) 0%, transparent 60%),
            radial-gradient(circle 900px at 90% 85%, rgba(0, 195, 255, 0.06) 0%, transparent 65%),
            linear-gradient(165deg, #060810 0%, #0c1020 40%, #070a14 100%) !important;
        color: #e2ebf8;
        min-height: 100vh;
    }

    /* --- SIDEBAR ALWAYS VISIBLE & EXPANDED --- */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: none !important;
        margin-left: 0 !important;
        left: 0 !important;
        width: 21rem !important;
        min-width: 21rem !important;
        background: linear-gradient(180deg, rgba(8, 12, 24, 0.96) 0%, rgba(4, 7, 16, 0.98) 100%) !important;
        border-right: 1px solid rgba(255, 215, 0, 0.15) !important;
        box-shadow: 6px 0 35px rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(16px);
    }
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarContent"],
    div[data-testid="stSidebarUserContent"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }


    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        background: rgba(10, 16, 32, 0.95) !important;
        border: 1px solid #ffd700 !important;
        border-radius: 6px !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.4) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] svg,
    button[data-testid="stSidebarCollapseButton"] {
        color: #ffd700 !important;
        fill: #ffd700 !important;
    }
    [data-testid="stSidebar"] * { color: #a4bedc !important; }
    [data-testid="stSidebar"] label {
        font-family: 'Cinzel', serif !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.14em !important;
        color: #ffd700 !important;
    }


    /* --- INPUT FIELDS & SELECTBOXES --- */
    .stTextInput input, .stTextArea textarea {
        background: rgba(10, 16, 32, 0.85) !important;
        color: #f0f6ff !important;
        border: 1px solid rgba(255, 215, 0, 0.25) !important;
        border-radius: 6px !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.98rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: rgba(255, 215, 0, 0.75) !important;
        box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.18), 0 0 25px rgba(255, 195, 0, 0.20) !important;
        outline: none !important;
    }
    div[data-baseweb="select"] > div {
        background: rgba(10, 16, 32, 0.85) !important;
        border: 1px solid rgba(255, 215, 0, 0.25) !important;
        border-radius: 6px !important;
        color: #f0f6ff !important;
    }

    /* --- BUTTONS & CHOICES --- */
    .stButton > button, .stFormSubmitButton > button {
        background: linear-gradient(135deg, #182236 0%, #243554 50%, #162842 100%) !important;
        color: #ffd700 !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.14em !important;
        border: 1px solid rgba(255, 215, 0, 0.38) !important;
        border-radius: 5px !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 18px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.12) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #283754 0%, #364d75 50%, #204068 100%) !important;
        box-shadow: 0 0 28px rgba(255, 215, 0, 0.50), 0 0 50px rgba(0, 195, 255, 0.25) !important;
        color: #ffffff !important;
        border-color: rgba(255, 235, 120, 0.9) !important;
        transform: translateY(-2px) !important;
    }

    /* --- TITLE & HEADINGS --- */
    .forge-title {
        font-family: 'Cinzel Decorative', 'Cinzel', serif;
        font-weight: 900;
        font-size: 2.6rem;
        background: linear-gradient(135deg, #fff5d6 0%, #ffd700 35%, #ff9d00 70%, #00e5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.05em;
        line-height: 1.15;
        filter: drop-shadow(0 0 25px rgba(255, 215, 0, 0.35));
        margin-bottom: 0.4rem;
        text-transform: uppercase;
    }
    .forge-sub {
        font-family: 'Outfit', sans-serif;
        font-size: 1.02rem;
        color: #8da4c4;
        letter-spacing: 0.05em;
        margin-bottom: 1.6rem;
        font-weight: 400;
    }

    /* --- NARRATIVE CARDS --- */
    .parchment-card {
        background: linear-gradient(145deg, rgba(12, 18, 34, 0.92) 0%, rgba(6, 10, 22, 0.96) 100%);
        border: 1px solid rgba(255, 215, 0, 0.16);
        border-left: 4px solid #ffd700;
        border-radius: 4px 10px 10px 4px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 35px rgba(0,0,0,0.75), inset 0 1px 0 rgba(255, 215, 0, 0.08);
        position: relative;
        transition: all 0.3s ease;
    }
    .parchment-card:hover {
        border-left-color: #ffee77;
        box-shadow: 0 14px 45px rgba(0,0,0,0.85), 0 0 25px rgba(255, 215, 0, 0.12);
    }
    .turn-emblem {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 215, 0, 0.08);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 3px;
        padding: 3px 14px;
        font-family: 'Cinzel', serif;
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #ffd700;
        margin-bottom: 16px;
    }
    .action-scroll {
        background: rgba(0, 30, 60, 0.5);
        border-left: 2px solid rgba(0, 229, 255, 0.5);
        border-radius: 0 4px 4px 0;
        padding: 10px 16px;
        margin-bottom: 16px;
        font-family: 'Outfit', sans-serif;
        color: #79a2cb;
        font-size: 0.92rem;
    }
    .story-prose {
        font-family: 'Outfit', sans-serif;
        font-size: 1.12rem;
        line-height: 1.85;
        color: #e2ebf8;
        letter-spacing: 0.015em;
    }

    /* --- METRICS & DASHBOARD --- */
    [data-testid="stMetricLabel"] {
        font-family: 'Cinzel', serif !important;
        font-size: 0.68rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        color: #7d96b8 !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Cinzel', serif !important;
        font-weight: 900 !important;
        font-size: 1.45rem !important;
        color: #ffd700 !important;
        text-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
    }

    /* --- PROGRESS BARS --- */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #ff3b3b, #ff8000, #ffd700) !important;
        border-radius: 3px !important;
        box-shadow: 0 0 14px rgba(255, 120, 0, 0.5);
    }
    .stProgress > div > div {
        background: rgba(10, 16, 32, 0.8) !important;
        border-radius: 3px !important;
    }

    /* --- EXPANDER DASHBOARD CARDS --- */
    [data-testid="stExpander"] {
        border: 1px solid rgba(255, 215, 0, 0.22) !important;
        border-radius: 8px !important;
        background: rgba(10, 16, 32, 0.85) !important;
        margin-bottom: 12px !important;
        overflow: hidden !important;
        backdrop-filter: blur(10px);
    }

    [data-testid="stExpander"] summary {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 12px !important;
        padding: 12px 16px !important;
        min-height: 48px !important;
        box-sizing: border-box !important;
    }

    [data-testid="stExpanderToggleIcon"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        width: 20px !important;
        height: 20px !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #ffd700 !important;
    }

    [data-testid="stExpander"] summary div,
    [data-testid="stExpander"] summary p {
        flex: 1 1 auto !important;
        font-family: 'Cinzel', serif !important;
        font-weight: 700 !important;
        font-size: 0.90rem !important;
        line-height: 1.4 !important;
        color: #ffd700 !important;
        margin: 0 !important;
        padding: 0 !important;
        letter-spacing: 0.04em !important;
        white-space: normal !important;
        word-break: break-word !important;
    }

    .ach-badge {
        display: inline-block;
        background: rgba(20, 30, 55, 0.85);
        border: 1px solid rgba(255, 215, 0, 0.32);
        border-radius: 3px;
        padding: 4px 14px;
        margin-bottom: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: #ffd700;
        letter-spacing: 0.04em;
    }

    [data-testid="stAlert"] {
        background: rgba(12, 18, 35, 0.90) !important;
        border: 1px solid rgba(255, 215, 0, 0.28) !important;
        border-radius: 6px !important;
        color: #b0cded !important;
    }

    hr { border-color: rgba(255, 215, 0, 0.12) !important; }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #05070e; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 215, 0, 0.30); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 215, 0, 0.55); }
    </style>
    """,
    unsafe_allow_html=True,
)







# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "game_started": False,
    "story_history": [],
    "turn": 0,
    "player_name": "",
    "genre": "Fantasy",
    "world": "",
    "last_action": "",

    # RPG PLAYER STATS
    "health": 100,
    "max_health": 100,
    "attack": 10,
    "defense": 5,
    "xp": 0,
    "level": 1,
    "gold": 50,
    "inventory": [],
    "clues": [],
    "is_ending": False,
    "ending_data": None,

    # AUDIO SYSTEM STATS
    "music_enabled": False,
    "music_volume": 50,

    "sfx_enabled": True,
    "pending_sfx": None,
    "pending_sfx_key": None,
    "last_played_sfx_key": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

init_default_game_state()


# Retroactively clean any existing history items in session_state
if "story_history" in st.session_state and st.session_state.story_history:
    for item in st.session_state.story_history:
        if "scene" in item and item["scene"]:
            item["scene"] = clean_html_tags(item["scene"])
        if "action" in item and item["action"]:
            item["action"] = clean_html_tags(item["action"])
        if "choices" in item and item["choices"]:
            item["choices"] = [clean_html_tags(c) for c in item["choices"]]



# =========================================================
# FALLBACK CONTENT
# =========================================================

def fallback_story(player_name, genre, world):
    return {
        "scene": (
            f"{player_name} stands at the edge of an unfamiliar "
            f"world. The atmosphere is tense, and something hidden "
            f"seems to be watching from the shadows. In this "
            f"{genre.lower()} adventure, the world around you is "
            f"beginning to reveal a dangerous secret."
        ),
        "choices": [
            "Explore the area and search for hidden clues",
            "Move forward carefully and investigate the danger",
            "Stay hidden and observe what happens next",
        ],
        "health_change": 0,
        "xp_change": 0,
        "gold_change": 0,
        "item": "",
        "clue": "",
    }


# =========================================================
# AI STORY + CHOICES
# =========================================================
def generate_scene_and_choices(
    player_name,
    genre,
    world,
    previous_story="",
    action="",
    current_turn=1,
):
    """
    ONE Gemini request generates:
    - New story scene
    - Exactly 3 choices
    """

    # Build a turn-awareness instruction injected into the prompt
    TOTAL_TURNS = 8
    turns_remaining = TOTAL_TURNS - current_turn
    if current_turn >= TOTAL_TURNS:
        turn_instruction = """\n========================
TURN INSTRUCTION — FINAL SCENE
========================

This is TURN 8, the FINAL TURN of the adventure.
The main conflict MUST reach its climax and resolution in this scene.
The scene should feel like a dramatic, emotional conclusion.
The 3 choices must each offer a meaningfully different final resolution:
- one heroic/brave path
- one investigative/clever path
- one dark/sacrifice path
After the player picks one of these, the adventure ends.
Make this scene epic, memorable, and conclusive.
"""
    elif current_turn == TOTAL_TURNS - 1:  # Turn 7
        turn_instruction = """\n========================
TURN INSTRUCTION — PENULTIMATE SCENE
========================

This is TURN 7, the second-to-last turn.
The story must now build toward its climax.
Raise the stakes. Bring the main conflict to a peak.
The 3 choices should each lead clearly toward the final confrontation.
Do NOT resolve the main conflict yet — save that for Turn 8.
"""
    elif current_turn >= TOTAL_TURNS - 3:  # Turns 5-6
        turn_instruction = f"""\n========================
TURN INSTRUCTION — BUILDING TENSION
========================

This is TURN {current_turn} of 8.
The adventure is approaching its climax.
Begin bringing the main story threads together.
Introduce consequences of earlier decisions.
Raise the emotional stakes. {turns_remaining} turns remain before the final confrontation.
"""
    else:
        turn_instruction = f"""\n========================
TURN INSTRUCTION
========================

This is TURN {current_turn} of 8.
Continue building the story naturally. {turns_remaining} turns remain.
Develop the world, characters, and conflict organically."""

    game_state_summary = build_compact_game_state_summary()

    prompt = f"""
You are the Dungeon Master running a cinematic interactive AI Visual Novel / RPG.

Your job is to continue ONE continuous adventure.
You must remember and respect everything that happened before.

PLAYER:
Name: {player_name}

GENRE:
{genre}

WORLD:
{world}

{turn_instruction}
========================
PERSISTENT GAME STATE
========================
{game_state_summary}

========================
ADVENTURE MEMORY
========================

{previous_story}

========================
PLAYER'S NEW ACTION
========================

{action if action else "The adventure is just beginning."}

========================
CONTINUITY RULES
========================

1. Continue directly from the latest scene.

2. The previous adventure is established history.
   Treat it as TRUE.

3. NEVER restart the story.

4. NEVER create a completely unrelated world.

5. NEVER ignore the player's latest action.

6. The player's latest action MUST have a visible
   consequence in the new scene.

7. Keep all previously established:
   - characters
   - locations
   - enemies
   - objects
   - clues
   - discoveries
   - mysteries
   - important events
   consistent.

8. If the player attacked an enemy, show the
   consequence of that attack.

9. If the player discovered an object or clue,
   remember it in future scenes.

10. If an important character appeared earlier,
    do not randomly replace or forget that character.

11. The new scene should feel like the immediate
    next moment of the adventure.

12. Do NOT summarize previous events.

13. Do NOT repeat the opening scene.

14. Do NOT suddenly move the player to another
    unrelated location.

15. Keep the player's character under player control.
    Never decide the player's next major action.

========================
STORY QUALITY
========================

Create a cinematic and immersive scene.

Include when appropriate:
- danger
- mystery
- discoveries
- consequences
- characters
- clues
- locations
- emotional tension
- meaningful decisions

Keep the scene reasonably short,
around 120-180 words.

========================
CHOICE RULES
========================

Create EXACTLY 3 choices.

Each choice must:

- be a complete player action
- contain at least 5 words
- directly relate to the current scene
- be meaningfully different
- lead toward a different possible consequence
- allow the player to make the decision

Do NOT:
- number choices
- use bullets
- add explanations
- write Choice A/B/C
- use markdown

RPG CONSEQUENCE RULES:

- If this is the beginning of the adventure,
  health_change MUST be 0.
- health_change must normally be between -30 and +10.
- xp_change must normally be between 0 and 50.
- gold_change must normally be between 0 and 30.
- Give a positive reward when the player succeeds.
- Give a health penalty when the player is injured.
- Do not randomly change stats without a story reason.
- If the player discovers an item, put its name in "item".
- If no item is discovered, return an empty string.
- If the player discovers an important clue, put it in "clue".
- If no clue is discovered, return an empty string.
- The consequences MUST match the player's action.

========================
OUTPUT FORMAT
========================
Return ONLY valid JSON.

Use exactly this structure:

{{
    "scene": "The complete cinematic story scene in English",
    "scene_hindi": "The complete cinematic story scene translated in natural, formal Hindi (Devanagari script, maintaining consistent proper names)",

    "choices": [
        "First complete player action",
        "Second complete player action",
        "Third complete player action"
    ],

    "health_change": 0,
    "xp_change": 0,
    "gold_change": 0,
    "item": "",
    "clue": ""
}}


"""

    result = generate_content(prompt)

    # -----------------------------------------------------
    # Clean possible markdown fences
    # -----------------------------------------------------

    cleaned = result.strip()
    
    if not cleaned.startswith("{"):
     raise ValueError(
        f"Gemini did not return valid JSON. Response: {cleaned[:200]}"
    )

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:

        data = json.loads(cleaned)

        scene = clean_html_tags(
            str(data.get("scene", "") or data.get("narration_en", "")).strip()
        )
        scene_hindi = clean_html_tags(
            str(data.get("scene_hindi", "") or data.get("narration_hi", "")).strip()
        )

        choices = data.get(
            "choices",
            []
        )

        if not isinstance(choices, list):
            choices = []

        choices = [
            clean_html_tags(choice)
            for choice in choices
            if clean_html_tags(choice)
        ]

        # Only first 3
        choices = choices[:3]

        # Validate choices
        valid_choices = []

        for choice in choices:

            if len(choice.split()) >= 5:

                valid_choices.append(choice)

        choices = valid_choices

        health_change = int(data.get("health_change", 0) or 0)
        xp_change = int(data.get("xp_change", 0) or 0)
        gold_change = int(data.get("gold_change", 0) or 0)

        item = clean_html_tags(str(data.get("item", "") or "")).strip()
        clue = clean_html_tags(str(data.get("clue", "") or "")).strip()

        # RPG advanced consequence fields — preserved for apply_choice_consequences()
        relationship_change = data.get("relationship_change")
        if not isinstance(relationship_change, dict):
            relationship_change = None

        quest_update = data.get("quest_update")
        if not isinstance(quest_update, dict):
            quest_update = None

        story_event = str(data.get("story_event", "") or "").strip()

        # -------------------------------------------------
        # Fallback if AI returns incomplete choices
        # -------------------------------------------------

        fallback = [
            "Explore the area and search for hidden clues",
            "Move forward carefully and investigate the danger",
            "Stay hidden and observe what happens next",
        ]

        while len(choices) < 3:
            choices.append(fallback[len(choices)])

        if not scene:
            raise ValueError("AI returned an empty scene.")

        return {
            "scene": scene,
            "scene_hindi": scene_hindi,
            "narration_en": scene,
            "narration_hi": scene_hindi,
            "choices": choices[:3],
            "health_change": health_change,
            "xp_change": xp_change,
            "gold_change": gold_change,
            "item": item,
            "clue": clue,
            # Advanced RPG consequence fields
            "relationship_change": relationship_change,
            "quest_update": quest_update,
            "story_event": story_event,
        }

    except Exception as e:

     raise ValueError(
        f"Story generation failed: {type(e).__name__}: {e}"
    ) 


# =========================================================
# BUILD STORY MEMORY
# =========================================================

def build_story_memory():

    memory = ""

    for item in st.session_state.story_history:

        clean_action = clean_html_tags(item.get("action") or "Adventure started")
        clean_scene = clean_html_tags(item["scene"])

        memory += f"""
TURN {item["turn"]}

PLAYER ACTION:
{clean_action}

SCENE:
{clean_scene}

"""

    return memory



# =========================================================
# START NEW ADVENTURE
# =========================================================

def start_adventure(
    player_name,
    genre,
    world,
):
    
     # RESET RPG STATS FOR NEW ADVENTURE

    st.session_state.health = 100
    st.session_state.max_health = 100
    st.session_state.attack = 10
    st.session_state.defense = 5
    st.session_state.xp = 0
    st.session_state.level = 1
    st.session_state.gold = 50
    st.session_state.inventory = []
    st.session_state.clues = []

    result = generate_scene_and_choices(
        player_name=player_name,
        genre=genre,
        world=world,
        previous_story="",
        action="",
    )

    # Initialize RPG Game State for new adventure
    st.session_state["active_quest"] = get_default_genre_quest(genre, player_name)
    st.session_state["relationships"] = {}
    st.session_state["character_memories"] = []
    st.session_state["story_events"] = []

    # Single source of truth — applies health/xp/gold/inventory/clues/level-up/
    # relationships/quest/story_events exactly once.
    apply_choice_consequences(result)

    # Read-only local for SFX selection below — no state mutation.
    clue = str(result.get("clue", "") or "").strip()

    # Session metadata (not RPG stats — these are safe to set here)
    st.session_state.game_started = True
    st.session_state.player_name = player_name.strip()
    st.session_state.genre = genre
    st.session_state.world = world.strip()
    st.session_state.turn = 1
    st.session_state.last_action = ""

    # Sound Effect for new adventure start

    if clue or genre == "Mystery":
        st.session_state.pending_sfx = "mystery.wav"
    else:
        st.session_state.pending_sfx = None

    if st.session_state.pending_sfx:
        st.session_state.pending_sfx_key = f"turn_1_{st.session_state.pending_sfx}"
    else:
        st.session_state.pending_sfx_key = None

    initial_image_url = generate_scene_image(result["scene"], genre, world, 1)
    sc_en_init = clean_html_tags(result.get("narration_en", "") or result.get("scene", ""))
    sc_hi_init = clean_html_tags(result.get("narration_hi", "") or result.get("scene_hindi", ""))
    st.session_state.story_history = [
        {
            "turn": 1,
            "scene": sc_en_init,
            "scene_hindi": sc_hi_init,
            "narration_en": sc_en_init,
            "narration_hi": sc_hi_init,
            "choices": [clean_html_tags(c) for c in result["choices"]],
            "action": None,
            "image_url": initial_image_url,
        }
    ]




# =========================================================
# PROCESS PLAYER ACTION
# =========================================================

# =========================================================
def process_player_action(action):

    # =====================================================
    # GENERATE NEXT SCENE
    # =====================================================

    previous_story = build_story_memory()

    result = generate_scene_and_choices(
        player_name=st.session_state.player_name,
        genre=st.session_state.genre,
        world=st.session_state.world,
        previous_story=previous_story,
        action=action,
        current_turn=st.session_state.turn + 1,
    )

    # =====================================================
    # NEW TURN
    # =====================================================

    new_turn = st.session_state.turn + 1

    # =====================================================
    # STORY
    # =====================================================

    new_image_url = generate_scene_image(result["scene"], st.session_state.genre, st.session_state.world, new_turn)
    sc_en_next = clean_html_tags(result.get("narration_en", "") or result.get("scene", ""))
    sc_hi_next = clean_html_tags(result.get("narration_hi", "") or result.get("scene_hindi", ""))
    st.session_state.story_history.append(
        {
            "turn": new_turn,
            "scene": sc_en_next,
            "scene_hindi": sc_hi_next,
            "narration_en": sc_en_next,
            "narration_hi": sc_hi_next,
            "choices": [clean_html_tags(c) for c in result["choices"]],
            "action": clean_html_tags(action),
            "image_url": new_image_url,
        }
    )



    # =====================================================
    # RPG CONSEQUENCES — single source of truth
    # =====================================================
    # All stat changes (health, xp, gold, inventory, clues, level-up,
    # relationships, quest progress, story events) are applied here ONCE.
    apply_choice_consequences(result)

    # Read-only locals used only for SFX selection below — no state mutation.
    health_change = int(result.get("health_change", 0) or 0)
    clue = str(result.get("clue", "") or "").strip()

    # =====================================================
    # SAVE TURN STATE
    # =====================================================

    st.session_state.turn = new_turn

    st.session_state.last_action = action



    # =====================================================
    # CHECK END CONDITIONS
    # =====================================================
    _maybe_trigger_ending()

    # Determine Sound Effect for this turn if not ending
    if not st.session_state.get("is_ending"):
        lower_act = (action or "").lower()
        lower_scene = (result.get("scene") or "").lower()
        if clue or "clue" in lower_act or "investigate" in lower_act or "mystery" in lower_act or st.session_state.genre == "Mystery":
            st.session_state.pending_sfx = "mystery.wav"
        elif health_change < 0 or any(kw in lower_act or kw in lower_scene for kw in ["fight", "attack", "danger", "battle", "ambush", "strike", "flee", "monster", "weapon"]):
            st.session_state.pending_sfx = "action.wav"
        else:
            st.session_state.pending_sfx = None

        if st.session_state.pending_sfx:
            st.session_state.pending_sfx_key = f"turn_{new_turn}_{st.session_state.pending_sfx}"
        else:
            st.session_state.pending_sfx_key = None


def _maybe_trigger_ending():
    """Evaluate whether the adventure should end, compute the ending, and set is_ending flag.
    The EARLIEST the adventure can end is after Turn 8.
    The ONLY exception before Turn 8 is if the player's health reaches 0.
    """
    if st.session_state.get("is_ending"):
        return  # Already ended

    turn   = st.session_state.turn
    health = st.session_state.health

    # Only allow ending before Turn 8 if the player is dead
    if turn < 8 and health > 0:
        return

    # Trigger ending at Turn 8+ or if health == 0
    if turn >= 8 or health <= 0:
        st.session_state.is_ending = True
        st.session_state.ending_data = compute_ending()
        st.session_state.pending_sfx = "ending.wav"
        st.session_state.pending_sfx_key = f"turn_{turn}_ending.wav"


def compute_ending():
    """
    Determine which of 4 endings the player receives, based on actual journey stats.
    Returns a dict with ending_type, title, emoji, description, summary, and outcome.
    """
    health     = st.session_state.health
    max_health = st.session_state.max_health
    level      = st.session_state.level
    xp         = st.session_state.xp
    gold       = st.session_state.gold
    clues      = st.session_state.clues
    inventory  = st.session_state.inventory
    turn       = st.session_state.turn
    player     = st.session_state.player_name or "Hero"
    genre      = st.session_state.genre or "Fantasy"

    clue_count = len(clues)
    item_count = len(inventory)
    health_pct = health / max(max_health, 1)

    # ── Scoring logic ────────────────────────────────────────────────────────
    # Each factor contributes points to determine the ending bucket.
    score = 0
    score += clue_count * 15        # Clues are key for mystery ending
    score += item_count * 8         # Items show exploration
    score += (level - 1) * 20       # Level up = mastery
    score += int(health_pct * 30)   # Survival matters
    score += min(turn, 10) * 3      # Longevity of adventure

    history = st.session_state.get("story_history", [])
    actions = " ".join(
        str(h.get("action") or "").lower() for h in history
    )
    # Bonus points: player made brave/heroic choices
    brave_keywords = ["fight", "attack", "charge", "defend", "rescue", "save", "protect", "confront", "challenge"]
    mystery_keywords = ["clue", "investigate", "search", "examine", "inspect", "solve", "hidden", "secret", "discover"]
    dark_keywords = ["betray", "abandon", "flee", "steal", "hide", "run", "retreat", "ignore"]

    brave_score   = sum(1 for kw in brave_keywords  if kw in actions) * 6
    mystery_score = sum(1 for kw in mystery_keywords if kw in actions) * 6 + clue_count * 10
    dark_score    = sum(1 for kw in dark_keywords   if kw in actions) * 8

    # ── Ending determination ─────────────────────────────────────────────────
    story_items_str = ", ".join(inventory[:5]) if inventory else "nothing"
    clue_str        = "; ".join(clues[:3])      if clues      else "none"

    # ⭐ Secret / Kingdom Ending — highest reward: 4+ items AND 3+ clues AND health ≥ 60% AND level ≥ 3
    if item_count >= 4 and clue_count >= 3 and health_pct >= 0.6 and level >= 3:
        return {
            "ending_type": "kingdom",
            "emoji": "👑",
            "title": "Sovereign of the Realm",
            "subtitle": "KINGDOM ENDING — BEST ENDING",
            "color": "#ffd700",
            "description": (
                f"{player} did not merely survive the adventure — they mastered every aspect of it. "
                f"By gathering every clue, item, and secret {st.session_state.world or 'the realm'} concealed, "
                f"they proved themselves worthy of the highest honour. "
                f"The {genre} realm now bows before its greatest champion."
            ),
            "outcome": (
                f"With {item_count} treasures collected, {clue_count} mysteries solved, and level {level} achieved, "
                f"{player} was crowned sovereign and ushered in a new golden age "
                f"for {st.session_state.world or 'the realm'}."
            ),
        }

    # 🔍 Mystery / Special Ending — investigative path, 2+ clues
    if mystery_score >= brave_score and mystery_score >= dark_score and clue_count >= 2:
        return {
            "ending_type": "mystery",
            "emoji": "🔮",
            "title": "Truth Beneath the Veil",
            "subtitle": "MYSTERY ENDING",
            "color": "#c080ff",
            "description": (
                f"{player} chose the path of the investigator, seeking truth over glory. "
                f"Piece by piece, they assembled the hidden puzzle of {st.session_state.world or 'this world'}, "
                f"revealing a secret that will change everything. "
                f"Some truths, once known, cannot be unlearned."
            ),
            "outcome": (
                f"Armed with {clue_count} discovered clues — '{clue_str}' — "
                f"{player} exposed the great mystery at the heart of the adventure."
            ),
        }

    # 😈 Bad / Dark Ending — health = 0, dark choices dominated, or very low score
    if health <= 0 or (dark_score > brave_score and dark_score > mystery_score) or score < 25:
        return {
            "ending_type": "bad",
            "emoji": "🌑",
            "title": "Consumed by Darkness",
            "subtitle": "BAD ENDING",
            "color": "#ff4444",
            "description": (
                f"The darkness that lurked in the shadows of {st.session_state.world or 'this realm'} "
                f"finally caught up with {player}. "
                f"Whether by choices made in haste or wounds that never healed, "
                f"the adventure ended not in triumph, but in sorrow."
            ),
            "outcome": (
                f"{player} fell with {health} HP remaining, level {level}, "
                f"carrying {story_items_str}. The realm mourns what could have been."
            ),
        }

    # 🏆 Good / Hero Ending — default triumphant victory
    return {
        "ending_type": "good",
        "emoji": "🏆",
        "title": "Hero of the Realm",
        "subtitle": "GOOD ENDING",
        "color": "#00d4ff",
        "description": (
            f"{player} faced every challenge {st.session_state.world or 'the realm'} could throw at them "
            f"and emerged victorious. Through courage, wit, and persistence, "
            f"the adventure reached its triumphant conclusion. "
            f"The people of this world are forever grateful."
        ),
        "outcome": (
            f"Standing tall at level {level} with {health}/{max_health} HP, "
            f"{player} completed {turn} turns, gathered {item_count} items, "
            f"and leaves behind a legacy that will never be forgotten."
        ),
    }


def build_adventure_summary_text():
    """Returns a plain-text summary of the full adventure for download."""
    ending = st.session_state.get("ending_data") or {}
    lines = []
    lines.append("=" * 60)
    lines.append("MiraI StoryForge — Adventure Summary")
    lines.append("=" * 60)
    lines.append(f"Character : {st.session_state.player_name}")
    lines.append(f"Genre     : {st.session_state.genre}")
    lines.append(f"World     : {st.session_state.world}")
    lines.append(f"Ending    : {ending.get('emoji','')} {ending.get('title','')} ({ending.get('subtitle','')})")
    lines.append("")
    lines.append("── Final Stats ─────────────────────────────────────────")
    lines.append(f"Turns Played  : {st.session_state.turn}")
    lines.append(f"Health        : {st.session_state.health}/{st.session_state.max_health}")
    lines.append(f"Level         : {st.session_state.level}")
    lines.append(f"XP            : {st.session_state.xp}")
    lines.append(f"Gold          : {st.session_state.gold}")
    lines.append(f"Inventory     : {', '.join(st.session_state.inventory) if st.session_state.inventory else 'None'}")
    lines.append(f"Clues Found   : {len(st.session_state.clues)}")
    for c in st.session_state.clues:
        lines.append(f"  • {c}")
    lines.append("")
    lines.append("── Ending ──────────────────────────────────────────────")
    lines.append(ending.get("description", ""))
    lines.append("")
    lines.append(ending.get("outcome", ""))
    lines.append("")
    lines.append("── Story Log ───────────────────────────────────────────")
    for h in st.session_state.story_history:
        lines.append(f"\nTurn {h['turn']}:")
        if h.get("action"):
            lines.append(f"  You chose: {h['action']}")
        lines.append(f"  {h['scene']}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("Generated by MiraI StoryForge")
    lines.append("=" * 60)
    return "\n".join(lines)



# =========================================================
# ADVENTURE DASHBOARD
# =========================================================

def render_adventure_dashboard():
    """Renders the Premium Better Adventure Dashboard using existing st.session_state."""
    health = st.session_state.health
    max_health = st.session_state.max_health
    health_ratio = max(0.0, min(1.0, health / max_health if max_health > 0 else 0))

    level = st.session_state.level
    xp = st.session_state.xp
    xp_for_next = level * 100
    xp_ratio = max(0.0, min(1.0, xp / xp_for_next if xp_for_next > 0 else 0))

    inventory_items = st.session_state.inventory
    inventory_count = len(inventory_items)

    clues_list = st.session_state.clues
    clues_count = len(clues_list)

    scenes_count = len(st.session_state.story_history)
    player_name = st.session_state.player_name or "Hero"
    world_name = st.session_state.world or "Unknown Realm"
    genre = st.session_state.genre or "Fantasy"

    # Compute Achievements dynamically without creating duplicate state
    achievements = []
    if st.session_state.turn >= 1:
        achievements.append("🚀 Genesis (Began Journey)")
    if level >= 2:
        achievements.append("⭐ Ascendant (Level 2+)")
    if st.session_state.gold >= 75:
        achievements.append("🪙 Wealthy Explorer (75+ Gold)")
    if inventory_count >= 1:
        achievements.append("🎒 Item Collector")
    if clues_count >= 1:
        achievements.append("🔎 Master Sleuth")
    if scenes_count >= 5:
        achievements.append("📜 Epic Veteran (5+ Scenes)")
    achievements_count = len(achievements)

    # Dynamic Current Quest
    if clues_list:
        current_quest = f"Investigate Clue: '{clues_list[-1]}'"
    elif scenes_count <= 1:
        current_quest = f"Explore the {genre} world of {world_name}"
    else:
        current_quest = f"Uncover secrets & survive in {world_name} (Turn {st.session_state.turn})"

    # --- DASHBOARD HEADER & HERO CARDS ---
    st.subheader("🛡️ Adventure Dashboard")

    # 🎭 Character Name & 🌍 World
    st.markdown(f"### 🎭 {player_name}")
    st.caption(f"🌍 **World:** {world_name} ({genre})")

    # 🎯 Current Quest Display
    q = st.session_state.get("active_quest")
    if q and isinstance(q, dict):
        q_status = q.get("status", "ACTIVE")
        status_color = "#00e5ff" if q_status == "ACTIVE" else ("#00ffaa" if q_status == "COMPLETED" else "#ff6060")
        st.markdown(f"**🎯 Quest:** `{q.get('title', 'Current Quest')}` <span style='color:{status_color}; font-weight:bold; font-size:0.8rem;'>[{q_status}]</span>", unsafe_allow_html=True)
        if q.get("description"):
            st.caption(q.get("description"))
        for obj in q.get("objectives", []):
            is_comp = obj.get("completed")
            icon = "✓" if is_comp else "○"
            clr = "#00ffaa" if is_comp else "#7fbfcf"
            st.markdown(f"<div style='color:{clr}; font-family:monospace; font-size:0.8rem; margin-left:8px;'>{icon} {obj.get('text')}</div>", unsafe_allow_html=True)
    else:
        st.info(f"🎯 **Current Quest:** {current_quest}")

    st.write(f"❤️ **Health:** `{health}/{max_health}`")
    st.progress(health_ratio)

    # 📈 Adventure Progress / XP
    st.write(f"📈 **Adventure Progress (Level {level} XP):** `{xp}/{xp_for_next}`")
    st.progress(xp_ratio)

    # Core Stats Grid
    st.markdown("### 📊 Player Metrics")
    m1, m2 = st.columns(2)
    with m1:
        st.metric("⚔️ Attack", st.session_state.attack)
        st.metric("⭐ Level", level)
        st.metric("🎒 Inventory", inventory_count)
        st.metric("🏆 Achievements", achievements_count)
    with m2:
        st.metric("🛡️ Defense", st.session_state.defense)
        st.metric("🪙 Gold", st.session_state.gold)
        st.metric("🔎 Clues Found", clues_count)
        st.metric("📜 Scenes", scenes_count)

    st.divider()

    # Detailed Expanders
    with st.expander(f"🎒 Inventory Items ({inventory_count})"):
        if inventory_items:
            for item in inventory_items:
                st.write(f"🔹 {item}")
        else:
            st.caption("Inventory is empty.")

    with st.expander(f"🔎 Clues Discovered ({clues_count})"):
        if clues_list:
            for clue in clues_list:
                st.write(f"🔍 {clue}")
        else:
            st.caption("No clues found yet.")

    rels = st.session_state.get("relationships", {})
    with st.expander(f"🤝 Character Relationships ({len(rels)})"):
        if rels:
            for char_name, rdata in rels.items():
                trust_val = rdata.get("trust", 0)
                t_clr = "#00ffaa" if trust_val >= 0 else "#ff6060"
                st.markdown(f"**{char_name}** — Trust: <span style='color:{t_clr}; font-weight:bold;'>{trust_val:+d}</span>", unsafe_allow_html=True)
                for ev in rdata.get("events", []):
                    st.caption(f"  • {ev}")
        else:
            st.caption("No character interactions recorded yet.")

    with st.expander(f"🏆 Achievements ({achievements_count})"):
        if achievements:
            for ach in achievements:
                st.markdown(f"<div class='ach-badge'>🏅 {ach}</div>", unsafe_allow_html=True)
        else:
            st.caption("Complete actions to unlock achievements.")



# =========================================================
# HEADER
# =========================================================

st.markdown('<div class="forge-title">🎭 MirAI StoryForge</div>', unsafe_allow_html=True)
st.markdown('<div class="forge-sub">Where Gemini becomes your Dungeon Master — every choice rewrites fate.</div>', unsafe_allow_html=True)




# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<p style="font-family:Orbitron,monospace;font-size:0.82rem;color:#00c8ff;letter-spacing:0.14em;'
        'text-transform:uppercase;border-bottom:1px solid rgba(0,180,255,0.18);'
        'padding-bottom:8px;margin-bottom:1rem;">// MISSION CONFIG</p>',
        unsafe_allow_html=True,
    )

    player_name = st.text_input(
        "👤 Character Name",
        value=st.session_state.player_name,
        placeholder="Enter your character name",
    )

    genres = [
        "Fantasy",
        "Mystery",
        "Sci-Fi",
        "Horror",
        "Adventure",
    ]

    current_genre = (
        st.session_state.genre
        if st.session_state.genre in genres
        else "Fantasy"
    )

    genre = st.selectbox(
        "📚 Choose Genre",
        genres,
        index=genres.index(
            current_genre
        ),
    )
    st.session_state.genre = genre

    world = st.text_area(
        "🌍 Describe Your World",
        value=st.session_state.world,
        placeholder=(
            "Example: An ancient kingdom "
            "surrounded by mysterious forests."
        ),
        height=120,
    )

    st.divider()

    st.markdown(
        '<p style="font-family:Orbitron,monospace;font-size:0.82rem;color:#00c8ff;letter-spacing:0.14em;'
        'text-transform:uppercase;border-bottom:1px solid rgba(0,180,255,0.18);'
        'padding-bottom:8px;margin-bottom:1rem;">// AUDIO CONTROLS</p>',
        unsafe_allow_html=True,
    )

    bg_track_name = get_background_track_for_genre(st.session_state.genre)
    st.markdown(f"<div style='font-family:Share Tech Mono,monospace;font-size:0.82rem;color:#00c8ff;margin-bottom:8px;'>🎵 <b>Track:</b> <code>{bg_track_name}</code></div>", unsafe_allow_html=True)

    col_aud1, col_aud2 = st.columns(2)
    with col_aud1:
        st.session_state.music_enabled = st.checkbox("🎵 Music On/Off", value=st.session_state.music_enabled, key="chk_music_on")
    with col_aud2:
        st.session_state.sfx_enabled = st.checkbox("🔔 SFX On/Off", value=st.session_state.sfx_enabled, key="chk_sfx_on")

    st.session_state.music_volume = st.slider(
        "🔊 Volume",
        min_value=0,
        max_value=100,
        value=st.session_state.music_volume,
        step=5,
        key="audio_volume_slider"
    )

    render_background_music(
        genre=st.session_state.genre,
        music_enabled=st.session_state.music_enabled,
        volume_pct=st.session_state.music_volume,
    )

    st.divider()


    start_game = st.button(
        "🎬 START ADVENTURE",
        use_container_width=True,
        type="primary",
    )

    if st.session_state.game_started:
        st.divider()
        render_adventure_dashboard()

    st.divider()
    with st.expander("💾 Save / Load System", expanded=False):
        if st.session_state.game_started:
            save_json_data = export_adventure_json()
            safe_name = st.session_state.player_name.lower().replace(" ", "_") or "hero"
            file_name = f"storyforge_{safe_name}_turn{st.session_state.turn}.json"
            st.download_button(
                label="💾 Save Adventure (JSON)",
                data=save_json_data,
                file_name=file_name,
                mime="application/json",
                use_container_width=True,
                key="btn_download_sidebar"
            )

            sidebar_zip_data = create_scene_images_zip(st.session_state.story_history)
            if sidebar_zip_data:
                st.download_button(
                    label="📦 Download All Scene Images (ZIP)",
                    data=sidebar_zip_data,
                    file_name=f"storyforge_scenes_turn_1_to_{st.session_state.turn}.zip",
                    mime="application/zip",
                    key="btn_dl_all_zip_sidebar",
                    use_container_width=True,
                )

        else:
            st.caption("Start an adventure first to save your state.")

        st.divider()

        uploaded_save_file = st.file_uploader(
            "📂 Load Save File (.json)",
            type=["json"],
            key="load_save_file_sidebar"
        )
        if uploaded_save_file is not None:
            if st.button("🚀 Restore Adventure", use_container_width=True, key="btn_restore_sidebar"):
                try:
                    str_content = uploaded_save_file.getvalue().decode("utf-8")
                    success, msg = load_adventure_json(str_content)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")
                except Exception as ex:
                    st.error(f"⚠️ Failed to read file: {ex}")




# =========================================================
# START GAME BUTTON
# =========================================================

if start_game:

    if not player_name.strip():

        st.error(
            "Please enter your character name."
        )

    elif not world.strip():

        st.error(
            "Please describe your world."
        )

    else:

        try:

            with st.spinner(
                "🎭 The Dungeon Master is creating your world..."
            ):
                st.session_state.music_enabled = True
                start_adventure(
                    player_name,
                    genre,
                    world,
                )


            st.rerun()

        except Exception as e:

            st.error(
                "⚠️ Gemini could not generate the adventure."
            )

            st.info(
                "Please wait a little and try again."
            )

            st.caption(
                        f"Technical details: {type(e).__name__}: {e}"
            )


# =========================================================
# GAME SCREEN
# =========================================================

if st.session_state.game_started:

    # =========================================================
    # ENDING SCREEN (shown instead of game UI when ended)
    # =========================================================
    if st.session_state.get("is_ending") and st.session_state.get("ending_data"):
        e = st.session_state.ending_data
        color = e.get("color", "#ffd700")
        emoji = e.get("emoji", "🏆")
        title = e.get("title", "The End")
        subtitle = e.get("subtitle", "ENDING")
        description = e.get("description", "")
        outcome = e.get("outcome", "")

        # Cinematic ending card
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #0a0a1a 0%, #0d0520 50%, #0a0a1a 100%);
            border: 2px solid {color};
            border-radius: 16px;
            padding: 2.5rem 2rem;
            margin: 1rem 0 2rem;
            text-align: center;
            box-shadow: 0 0 60px {color}33, 0 0 20px {color}22;
        ">
            <div style="font-size:5rem;margin-bottom:0.5rem;">{emoji}</div>
            <p style="
                font-family:'Orbitron',monospace;
                font-size:0.85rem;
                color:{color};
                letter-spacing:0.3em;
                text-transform:uppercase;
                margin:0 0 0.4rem;
                opacity:0.85;
            ">{subtitle}</p>
            <h1 style="
                font-family:'Rajdhani',sans-serif;
                font-size:2.4rem;
                font-weight:900;
                color:#ffffff;
                margin:0 0 1.5rem;
                text-shadow: 0 0 20px {color}88;
            ">{title}</h1>
            <p style="
                font-family:'Rajdhani',sans-serif;
                font-size:1.1rem;
                color:#c0d8f0;
                line-height:1.7;
                max-width:700px;
                margin:0 auto 1rem;
            ">{description}</p>
            <p style="
                font-family:'Share Tech Mono',monospace;
                font-size:0.9rem;
                color:{color};
                opacity:0.9;
                margin:0 auto;
                max-width:650px;
            ">{outcome}</p>
        </div>
        """, unsafe_allow_html=True)

        # ── Final Stats ───────────────────────────────────────────────────
        st.markdown("### 📊 Final Adventure Stats")
        fs_col1, fs_col2, fs_col3, fs_col4 = st.columns(4)
        with fs_col1:
            st.metric("⏱️ Turns Played", st.session_state.turn)
            st.metric("❤️ Health", f"{st.session_state.health}/{st.session_state.max_health}")
        with fs_col2:
            st.metric("⭐ Level", st.session_state.level)
            st.metric("✨ XP", st.session_state.xp)
        with fs_col3:
            st.metric("🔎 Clues Found", len(st.session_state.clues))
            st.metric("🪙 Gold", st.session_state.gold)
        with fs_col4:
            # Compute achievements count same way as dashboard
            _ach_count = 0
            if st.session_state.turn >= 1: _ach_count += 1
            if st.session_state.level >= 2: _ach_count += 1
            if st.session_state.level >= 3: _ach_count += 1
            if len(st.session_state.clues) >= 1: _ach_count += 1
            if len(st.session_state.inventory) >= 3: _ach_count += 1
            if st.session_state.health == st.session_state.max_health: _ach_count += 1
            if st.session_state.turn >= 5: _ach_count += 1
            st.metric("🏆 Achievements", _ach_count)
            st.metric("🎒 Items", len(st.session_state.inventory))

        if st.session_state.inventory:
            st.markdown("**🎒 Items Collected:** " + " · ".join(f"`{i}`" for i in st.session_state.inventory))
        if st.session_state.clues:
            st.markdown("**🔎 Clues Discovered:** " + " · ".join(f"`{c}`" for c in st.session_state.clues))

        st.divider()

        # ── Ending action buttons (2 rows × 2 cols) ───────────────────────────
        end_col1, end_col2 = st.columns(2)
        with end_col1:
            if st.button("🔄 PLAY AGAIN", use_container_width=True, key="btn_play_again"):
                for k in list(DEFAULTS.keys()):
                    st.session_state[k] = DEFAULTS[k]
                st.session_state["is_ending"] = False
                st.session_state["ending_data"] = None
                st.rerun()

        with end_col2:
            # Save Final Adventure JSON
            save_json_data = export_adventure_json()
            _safe_name = st.session_state.player_name.lower().replace(" ", "_") or "hero"
            st.download_button(
                label="💾 SAVE FINAL ADVENTURE",
                data=save_json_data,
                file_name=f"storyforge_{_safe_name}_final_turn{st.session_state.turn}.json",
                mime="application/json",
                key="btn_dl_save_ending",
                use_container_width=True,
            )

        end_col3, end_col4 = st.columns(2)
        with end_col3:
            summary_text = build_adventure_summary_text()
            safe_name = st.session_state.player_name.lower().replace(" ", "_") or "hero"
            st.download_button(
                label="📥 DOWNLOAD ADVENTURE SUMMARY",
                data=summary_text.encode("utf-8"),
                file_name=f"storyforge_{safe_name}_adventure_summary.txt",
                mime="text/plain",
                key="btn_dl_summary",
                use_container_width=True,
            )

        with end_col4:
            ending_zip = create_scene_images_zip(st.session_state.story_history)
            if ending_zip:
                _safe2 = st.session_state.player_name.lower().replace(" ", "_") or "hero"
                st.download_button(
                    label="📦 DOWNLOAD ALL SCENE IMAGES",
                    data=ending_zip,
                    file_name=f"storyforge_{_safe2}_all_scenes.zip",
                    mime="application/zip",
                    key="btn_dl_all_zip_ending",
                    use_container_width=True,
                )
            else:
                st.info("Generate scene images to enable ZIP download.")

        st.divider()
        # Render audio for ending screen before stopping UI execution
        sfx_to_play_end = None
        if (
            st.session_state.get("sfx_enabled")
            and st.session_state.get("pending_sfx")
            and st.session_state.get("pending_sfx_key")
        ):
            if st.session_state.get("pending_sfx_key") != st.session_state.get("last_played_sfx_key"):
                sfx_to_play_end = st.session_state.pending_sfx
                st.session_state.last_played_sfx_key = st.session_state.pending_sfx_key

        render_audio_components(
            genre=st.session_state.get("genre", "Fantasy"),
            music_enabled=st.session_state.get("music_enabled", True),
            volume_pct=st.session_state.get("music_volume", 50),
            sfx_to_play=sfx_to_play_end,
        )
        st.stop()



    st.divider()

    col1, col2 = st.columns(
        [3.5, 1],
        gap="large",
    )


    # =====================================================
    # STORY
    # =====================================================

    with col1:

        st.markdown('<p style="font-family:Orbitron,monospace;font-size:0.82rem;color:#00c8ff;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:1rem;">// TRANSMISSION LOG</p>', unsafe_allow_html=True)

        if st.session_state.story_history:
            for item in st.session_state.story_history:
                clean_scene_text = clean_html_tags(item.get("narration_en", "") or item.get("scene", ""))
                clean_scene_hindi = clean_html_tags(item.get("narration_hi", "") or item.get("scene_hindi", ""))
                if clean_scene_text and not clean_scene_hindi:
                    clean_scene_hindi = f"सिमुलेशन दृश्य: {clean_scene_text}"

                clean_action_text = clean_html_tags(item["action"]) if item.get("action") else ""

                st.markdown(f"#### 🌙 Turn {item['turn']}")

                if clean_action_text:
                    st.info(f"🎮 **You chose:** {clean_action_text}")

                if item.get("image_url"):
                    st.image(
                        item["image_url"],
                        caption=f"🎨 Turn {item['turn']} — Scene Illustration",
                        use_container_width=True,
                    )
                    img_bytes = get_image_bytes(item["image_url"])
                    if img_bytes:
                        char_name = st.session_state.player_name.lower().replace(" ", "_") if st.session_state.get("player_name") else "hero"
                        st.download_button(
                            label="⬇️ Download Scene Image",
                            data=img_bytes,
                            file_name=f"storyforge_{char_name}_turn_{item['turn']}_scene.png",
                            mime="image/png",
                            key=f"dl_img_btn_turn_{item['turn']}",
                            use_container_width=True,
                        )


                st.markdown(f"🇬🇧 **English**\n\n{clean_scene_text}")
                st.markdown(f"🇮🇳 **हिंदी**\n\n{clean_scene_hindi}")

                render_tts_widget(clean_scene_text, clean_scene_hindi, item["turn"])
                st.divider()




        # =================================================
        # CURRENT CHOICES & SCENE IMAGE GENERATOR
        # =================================================

        if st.session_state.story_history:
            current_scene = st.session_state.story_history[-1]
            choices = current_scene.get("choices", [])

            # Generate / Regenerate Scene Image Button
            img_btn_label = "🔄 Regenerate Scene Image" if current_scene.get("image_url") else "🎨 Generate Scene Image"
            if st.button(img_btn_label, use_container_width=True, key=f"btn_gen_img_turn_{st.session_state.turn}"):
                with st.spinner("🎨 Generating scene illustration..."):
                    try:
                        import random
                        fresh_seed = random.randint(10000, 999999)
                        is_regen = bool(current_scene.get("image_url"))
                        curr_img_url = current_scene.get("image_url")
                        # Pass the last-used gallery index so the fallback always picks a DIFFERENT image
                        last_gidx = current_scene.get("last_gallery_idx")
                        _out = {}
                        new_img = generate_scene_image(
                            current_scene["scene"],
                            st.session_state.genre,
                            st.session_state.world,
                            st.session_state.turn,
                            seed=fresh_seed,
                            is_regeneration=is_regen,
                            current_image_url=curr_img_url,
                            exclude_fallback_index=last_gidx,
                            _out=_out,
                        )
                        if new_img:
                            current_scene["image_url"] = new_img
                            st.session_state.story_history[-1]["image_url"] = new_img
                            # Store the fallback index used so next regeneration avoids the same image
                            if 'fallback_index' in _out:
                                current_scene["last_gallery_idx"] = _out['fallback_index']
                                st.session_state.story_history[-1]["last_gallery_idx"] = _out['fallback_index']
                        else:
                            st.warning("Unable to generate a new scene image right now. Please try again.")
                    except Exception as err_ex:
                        print(f"[REGEN ERROR]: {err_ex}")
                        st.warning("Unable to generate a new scene image right now. Please try again.")
                st.rerun()





            st.markdown('<p style="font-family:Orbitron,monospace;font-size:0.82rem;color:#00d4ff;letter-spacing:0.12em;text-transform:uppercase;margin:1.5rem 0 0.3rem;">// SELECT ACTION</p>', unsafe_allow_html=True)

            st.markdown('<p style="color:#1a4060;font-family:Share Tech Mono,monospace;font-size:0.85rem;margin-bottom:1rem;">&gt; Every command alters the simulation.</p>', unsafe_allow_html=True)


            if choices:

                for i, choice in enumerate(
                    choices
                ):

                    if st.button(
                        f"⚔️ {choice}",
                        key=(
                            f"choice_"
                            f"{st.session_state.turn}_"
                            f"{i}"
                        ),
                        use_container_width=True,
                    ):

                        try:

                            with st.spinner(
                                "🤖 The Dungeon Master is thinking..."
                            ):

                                process_player_action(
                                    choice
                                )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                "⚠️ Gemini is temporarily unavailable."
                            )

                            st.info(
                                "Please try again later."
                            )

                            st.caption(
                                f"Technical details: "
                                f"{type(e).__name__}"
                            )


            # =================================================
            # CUSTOM ACTION
            # =================================================

            st.markdown('<p style="font-family:Orbitron,monospace;font-size:0.78rem;color:#0090b0;letter-spacing:0.12em;text-transform:uppercase;margin:1.5rem 0 0.3rem;">&gt;_ INPUT COMMAND</p>', unsafe_allow_html=True)

            with st.form(
                "custom_action_form",
                clear_on_submit=True,
            ):

                custom_action = st.text_area(
                    "Describe your action",
                    placeholder=(
                        "Example: I secretly enter "
                        "the castle through the "
                        "northern gate."
                    ),
                    height=100,
                )

                submit_custom = (
                    st.form_submit_button(
                        "⚔️ TAKE ACTION",
                        use_container_width=True,
                    )
                )

            if submit_custom:

                if not custom_action.strip():

                    st.warning(
                        "Please describe what you want to do."
                    )

                else:

                    try:

                        with st.spinner(
                            "🤖 The Dungeon Master is thinking..."
                        ):

                            process_player_action(
                                custom_action.strip()
                            )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "⚠️ Gemini is temporarily unavailable."
                        )

                        st.info(
                            "Please try again later."
                        )

                        st.caption(
                            f"Technical details: "
                            f"{type(e).__name__}"
                        )


    # =====================================================
    # PLAYER PANEL
    # =====================================================

    with col2:

        render_adventure_dashboard()

        st.divider()


        # =================================================
        # ADVENTURE LOG
        # =================================================

        st.subheader(
            "📜 Adventure Log"
        )

        st.write(
            "Scenes discovered: "
            f"**{len(st.session_state.story_history)}**"
        )

        if st.session_state.last_action:

            st.write(
                "**Last action:**"
            )

            st.caption(
                st.session_state.last_action
            )

        else:

            st.write(
                "Last action: **None**"
            )

        st.divider()

        # =================================================
        # CURRENT CHOICES
        # =================================================

        st.subheader(
            "🎯 Current Choices"
        )

        current_choices = (
            st.session_state.story_history[-1].get("choices", [])
            if st.session_state.get("story_history")
            else []
        )

        for index, choice in enumerate(
            current_choices,
            start=1,
        ):

            st.write(
                f"**{index}.** {choice}"
            )

        # =================================================
        # SAVE / LOAD SYSTEM
        # =================================================

        st.subheader("💾 Save & Load")

        save_data_json = export_adventure_json()
        char_name = st.session_state.player_name.lower().replace(" ", "_") or "hero"
        save_filename = f"storyforge_{char_name}_turn{st.session_state.turn}.json"

        st.download_button(
            label="💾 Save Adventure (JSON)",
            data=save_data_json,
            file_name=save_filename,
            mime="application/json",
            use_container_width=True,
            key="btn_download_col2"
        )

        all_zip_bytes = create_scene_images_zip(st.session_state.story_history)
        if all_zip_bytes:
            st.download_button(
                label="📦 Download All Scene Images (ZIP)",
                data=all_zip_bytes,
                file_name=f"storyforge_{char_name}_scenes_turn_1_to_{st.session_state.turn}.zip",
                mime="application/zip",
                key="btn_download_zip_single_col2",
                use_container_width=True
            )


        with st.expander("📂 Load Saved Adventure", expanded=False):
            col2_uploaded_file = st.file_uploader(
                "Upload Save File (.json)",
                type=["json"],
                key="load_save_file_col2"
            )
            if col2_uploaded_file is not None:
                if st.button("🚀 Restore Save Data", use_container_width=True, key="btn_restore_col2"):
                    try:
                        file_str = col2_uploaded_file.getvalue().decode("utf-8")
                        ok, message = load_adventure_json(file_str)
                        if ok:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(f"⚠️ {message}")
                    except Exception as err:
                        st.error(f"⚠️ Error reading file: {err}")

        st.divider()

        # =================================================
        # RESTART
        # =================================================

        if st.button(
            "🔄 Restart Adventure",
            use_container_width=True,
        ):


            for key in list(
                st.session_state.keys()
            ):
                if key in DEFAULTS:
                    del st.session_state[key]

            st.rerun()


else:
    st.markdown(
        """
        <div style="
            background: linear-gradient(140deg, rgba(8, 16, 36, 0.96) 0%, rgba(4, 8, 22, 0.98) 100%);
            border: 1px solid rgba(0, 229, 255, 0.45);
            border-left: 5px solid #00e5ff;
            border-radius: 6px;
            padding: 32px 38px;
            margin: 1.5rem 0 2rem;
            box-shadow: 0 12px 45px rgba(0,0,0,0.85), 0 0 30px rgba(0, 229, 255, 0.20);
        ">
            <p style="font-family:'Cinzel Decorative','Cinzel',serif;font-size:1.65rem;font-weight:900;
                      background:linear-gradient(90deg,#00f3ff,#0090ff,#ffd700);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      background-clip:text;margin:0 0 14px;letter-spacing:0.08em;text-transform:uppercase;filter:drop-shadow(0 0 15px rgba(0,243,255,0.45));">INITIALIZE STORY</p>
            <p style="font-family:'JetBrains Mono',monospace;font-size:1.02rem;font-weight:600;
                      color:#00f3ff;line-height:1.8;margin:0;text-shadow: 0 0 14px rgba(0,243,255,0.40);">
                &gt; System online. Gemini AI dungeon master ready.<br>
                &gt; Configure your operative in the sidebar panel.<br>
                &gt; Awaiting deployment orders...
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    feat_col1, feat_col2, feat_col3 = st.columns(3)

    with feat_col1:
        st.markdown(
            """
            <div style="background:rgba(8, 14, 30, 0.95);border:1px solid rgba(255, 215, 0, 0.35);
                        border-top:3px solid #ffd700;border-radius:8px;padding:22px;min-height:135px;box-shadow:0 8px 30px rgba(0,0,0,0.7);">
                <div style="font-size:1.8rem;margin-bottom:10px;">🔮</div>
                <div style="font-family:'Cinzel',serif;color:#ffd700;font-size:0.88rem;font-weight:800;
                            text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;text-shadow:0 0 12px rgba(255,215,0,0.4);">AI Dungeon Master</div>
                <div style="font-family:'Outfit',sans-serif;color:#e6f2ff;font-size:0.95rem;font-weight:500;line-height:1.65;">
                    Dynamic cinematic scenes, adaptive choices &amp; persistent memory across every transmission.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with feat_col2:
        st.markdown(
            """
            <div style="background:rgba(8, 14, 30, 0.95);border:1px solid rgba(255, 215, 0, 0.35);
                        border-top:3px solid #ffd700;border-radius:8px;padding:22px;min-height:135px;box-shadow:0 8px 30px rgba(0,0,0,0.7);">
                <div style="font-size:1.8rem;margin-bottom:10px;">⚔️</div>
                <div style="font-family:'Cinzel',serif;color:#ffd700;font-size:0.88rem;font-weight:800;
                            text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;text-shadow:0 0 12px rgba(255,215,0,0.4);">RPG Engine</div>
                <div style="font-family:'Outfit',sans-serif;color:#e6f2ff;font-size:0.95rem;font-weight:500;line-height:1.65;">
                    Level up, earn XP &amp; credits, collect tech, discover intel and unlock achievements.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with feat_col3:
        st.markdown(
            """
            <div style="background:rgba(8, 14, 30, 0.95);border:1px solid rgba(255, 215, 0, 0.35);
                        border-top:3px solid #ffd700;border-radius:8px;padding:22px;min-height:135px;box-shadow:0 8px 30px rgba(0,0,0,0.7);">
                <div style="font-size:1.8rem;margin-bottom:10px;">🌐</div>
                <div style="font-family:'Cinzel',serif;color:#ffd700;font-size:0.88rem;font-weight:800;
                            text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;text-shadow:0 0 12px rgba(255,215,0,0.4);">Infinite Worlds</div>
                <div style="font-family:'Outfit',sans-serif;color:#e6f2ff;font-size:0.95rem;font-weight:500;line-height:1.65;">
                    Fantasy, Sci-Fi, Mystery, Horror &mdash; or build your own simulation from scratch.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('<p style="font-family:\'Cinzel\',serif;font-size:0.95rem;font-weight:800;color:#ffd700;letter-spacing:0.14em;text-transform:uppercase;margin-top:2.4rem;margin-bottom:0.4rem;text-shadow:0 0 12px rgba(255,215,0,0.35);">&gt;&gt; SIMULATION PRESETS</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-family:\'Outfit\',sans-serif;font-size:0.95rem;font-weight:500;color:#c0d8f5;margin-bottom:1.2rem;">Select a world template to auto-configure your operative.</p>', unsafe_allow_html=True)

    p_col1, p_col2, p_col3 = st.columns(3)

    with p_col1:
        if st.button("🔮 High Fantasy Realm", use_container_width=True):
            st.session_state.player_name = "Aethelgard the Brave"
            st.session_state.genre = "Fantasy"
            st.session_state.world = "An ancient realm of floating crystalline islands, dragon lords, and forgotten magic."
            st.rerun()

    with p_col2:
        if st.button("🚀 Cyberpunk Neon City", use_container_width=True):
            st.session_state.player_name = "V-7 Cyber Hunter"
            st.session_state.genre = "Sci-Fi"
            st.session_state.world = "A sprawling mega-city drenched in rain and neon, ruled by rogue AI corporations."
            st.rerun()

    with p_col3:
        if st.button("🏚️ Gothic Mystery Mansion", use_container_width=True):
            st.session_state.player_name = "Detective Vance"
            st.session_state.genre = "Mystery"
            st.session_state.world = "A fog-shrouded Victorian estate where aristocratic guests vanish without a trace."
            st.rerun()



# =========================================================
# AUDIO RENDERER (Runs on every rerun, handles missing files gracefully)
# =========================================================
sfx_to_play = None
if (
    st.session_state.get("sfx_enabled")
    and st.session_state.get("pending_sfx")
    and st.session_state.get("pending_sfx_key")
):
    if st.session_state.get("pending_sfx_key") != st.session_state.get("last_played_sfx_key"):
        sfx_to_play = st.session_state.pending_sfx
        st.session_state.last_played_sfx_key = st.session_state.pending_sfx_key

render_audio_components(
    genre=st.session_state.get("genre", "Fantasy"),
    music_enabled=st.session_state.get("music_enabled", True),
    volume_pct=st.session_state.get("music_volume", 50),
    sfx_to_play=sfx_to_play,
)

