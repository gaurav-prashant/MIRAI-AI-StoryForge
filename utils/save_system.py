import html
import json
import re
import streamlit as st


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



def export_adventure_json():
    """Serializes all relevant session_state keys into a clean JSON string."""
    save_data = {
        "version": "2.0",
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
        "relationships": st.session_state.get("relationships", {}),
        "character_memories": st.session_state.get("character_memories", []),
        "quests": st.session_state.get("quests", []),
        "active_quest": st.session_state.get("active_quest", None),
        "story_events": st.session_state.get("story_events", []),
        "achievements": st.session_state.get("unlocked_achievements", []),
        "is_ending": st.session_state.get("is_ending", False),
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
        st.session_state["is_ending"] = bool(data.get("is_ending", False))

        # Sanitize story history
        raw_history = data.get("story_history", [])
        clean_history = []
        if isinstance(raw_history, list):
            for item in raw_history:
                if isinstance(item, dict):
                    sc_en = clean_html_tags(item.get("narration_en", "") or item.get("scene", ""))
                    sc_hi = clean_html_tags(item.get("narration_hi", "") or item.get("scene_hindi", ""))
                    clean_item = {
                        "turn": int(item.get("turn", 1)),
                        "scene": sc_en,
                        "scene_hindi": sc_hi,
                        "narration_en": sc_en,
                        "narration_hi": sc_hi,
                        "choices": [clean_html_tags(c) for c in item.get("choices", []) if clean_html_tags(c)],
                        "action": clean_html_tags(item.get("action", "")) if item.get("action") else None,
                        "image_url": str(item.get("image_url", "")) if item.get("image_url") else None
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

        # Restore Advanced RPG State (with safe fallbacks for old save files)
        st.session_state["relationships"] = data.get("relationships", {}) if isinstance(data.get("relationships"), dict) else {}
        st.session_state["character_memories"] = data.get("character_memories", []) if isinstance(data.get("character_memories"), list) else []
        st.session_state["quests"] = data.get("quests", []) if isinstance(data.get("quests"), list) else []
        st.session_state["active_quest"] = data.get("active_quest", None) if isinstance(data.get("active_quest"), dict) else None
        st.session_state["story_events"] = data.get("story_events", []) if isinstance(data.get("story_events"), list) else []
        if "achievements" in data and isinstance(data["achievements"], list):
            st.session_state["unlocked_achievements"] = data["achievements"]

        st.session_state["music_enabled"] = True

        return True, f"Adventure loaded! Character: {st.session_state['player_name']} (Turn {st.session_state['turn']})"


    except json.JSONDecodeError:
        return False, "File is corrupted or not a valid JSON file."
    except Exception as e:
        return False, f"Failed to load adventure: {type(e).__name__}: {str(e)}"
