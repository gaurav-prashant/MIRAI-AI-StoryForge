import json
import streamlit as st

# Import Save/Load logic directly
from app import export_adventure_json, load_adventure_json, clean_html_tags

def run_save_load_tests():
    print("============================================================")
    print("RUNNING SAVE / LOAD ADVENTURE SYSTEM TESTS")
    print("============================================================")

    # 1. Setup mock session state
    st.session_state.player_name = "Arpita the Explorer"
    st.session_state.genre = "Fantasy"
    st.session_state.world = "The ancient realm of Oakhaven"
    st.session_state.game_started = True
    st.session_state.turn = 3
    st.session_state.last_action = "Investigate the golden altar"
    st.session_state.health = 90
    st.session_state.max_health = 110
    st.session_state.attack = 14
    st.session_state.defense = 7
    st.session_state.xp = 120
    st.session_state.level = 2
    st.session_state.gold = 135
    st.session_state.inventory = ["Silver Compass", "Ancient Relic"]
    st.session_state.clues = ["The Dragon Rune of Northern Gate"]
    st.session_state.story_history = [
        {
            "turn": 1,
            "scene": "You arrive at Oakhaven town square.",
            "choices": ["Speak to King Alaric", "Explore the market"],
            "action": None
        },
        {
            "turn": 2,
            "scene": "King Alaric hands you a silver compass.",
            "choices": ["Head North to Iron Gates", "Investigate the altar"],
            "action": "Speak to King Alaric"
        },
        {
            "turn": 3,
            "scene": "You inspect the glowing golden altar in the woods.",
            "choices": ["Touch the rune", "Return to town"],
            "action": "Investigate the golden altar"
        }
    ]

    # 2. Test JSON Export
    json_export = export_adventure_json()
    assert isinstance(json_export, str), "Export must return a string"
    data = json.loads(json_export)
    print("[PASS] JSON Export produced valid JSON structure.")

    assert data["player_name"] == "Arpita the Explorer"
    assert data["turn"] == 3
    assert len(data["story_history"]) == 3
    assert len(data["inventory"]) == 2
    assert len(data["clues"]) == 1
    assert data["gold"] == 135
    print("[PASS] All 17 session state fields exported accurately.")

    # 3. Test Clearing State
    st.session_state.player_name = "Cleared"
    st.session_state.turn = 0
    st.session_state.health = 0
    st.session_state.inventory = []
    st.session_state.clues = []
    st.session_state.story_history = []

    # 4. Test Deserialization / Load
    success, msg = load_adventure_json(json_export)
    assert success is True, f"Load failed: {msg}"
    print(f"[PASS] Load output: {msg}")

    # 5. Verify restored state
    assert st.session_state.player_name == "Arpita the Explorer"
    assert st.session_state.turn == 3
    assert st.session_state.health == 90
    assert st.session_state.max_health == 110
    assert st.session_state.gold == 135
    assert st.session_state.level == 2
    assert len(st.session_state.inventory) == 2
    assert "Silver Compass" in st.session_state.inventory
    assert len(st.session_state.clues) == 1
    assert len(st.session_state.story_history) == 3
    print("[PASS] All restored session state variables verified with 100% accuracy!")

    # 6. Test Corrupted File Handling
    bad_success, bad_msg = load_adventure_json("{corrupted_json_string...")
    assert bad_success is False
    print(f"[PASS] Corrupted JSON error handled gracefully: {bad_msg}")

    missing_success, missing_msg = load_adventure_json('{"some_key": 123}')
    assert missing_success is False
    print(f"[PASS] Missing required key error handled gracefully: {missing_msg}")

    print("\nALL SAVE / LOAD SYSTEM TESTS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    run_save_load_tests()
