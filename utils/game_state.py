"""
MIRAI StoryForge Game State & RPG Consequence Manager
======================================================
Manages:
- Quests & Objectives (ACTIVE, COMPLETED, FAILED)
- Character Relationships & Memory (Trust levels, interaction events)
- Story Events & Choice Consequences
- State-Evaluated Endings (Hero, Dark, True Mystery, Friendship Alliance)
- Compact Game State Summary formatting for AI prompt injection
"""
import streamlit as st


class Quest:
    """Represents an active or historical quest."""
    def __init__(self, quest_id, title, description, objectives=None, status="ACTIVE", rewards=None):
        self.quest_id = quest_id
        self.title = title
        self.description = description
        self.objectives = objectives or []  # List of dicts: {"text": str, "completed": bool}
        self.status = status  # ACTIVE, COMPLETED, FAILED
        self.rewards = rewards or {"xp": 50, "gold": 25}

    def to_dict(self):
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "description": self.description,
            "objectives": self.objectives,
            "status": self.status,
            "rewards": self.rewards,
        }

    @classmethod
    def from_dict(cls, d):
        if not d or not isinstance(d, dict):
            return None
        return cls(
            quest_id=d.get("quest_id", "main_quest"),
            title=d.get("title", "Main Quest"),
            description=d.get("description", ""),
            objectives=d.get("objectives", []),
            status=d.get("status", "ACTIVE"),
            rewards=d.get("rewards", {"xp": 50, "gold": 25}),
        )


def init_default_game_state():
    """Initializes safe defaults for all RPG state variables in session_state."""
    defaults = {
        "relationships": {},  # e.g., {"King Aldous": {"trust": 10, "events": ["helped_king"]}}
        "character_memories": [],  # List of str: "Helped King Aldous at the courtyard"
        "quests": [],  # List of quest dicts
        "active_quest": None,  # Quest dict or None
        "story_events": [],  # List of key story event flags
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_default_genre_quest(genre: str, player_name: str) -> dict:
    """Creates initial genre-aligned quest data."""
    genre = genre or "Fantasy"
    p_name = player_name or "Hero"

    if genre == "Fantasy":
        return Quest(
            quest_id="crown_quest",
            title="The Lost Crystalline Crown",
            description=f"Guide {p_name} to recover the stolen royal artifact before dark magic consumes the realm.",
            objectives=[
                {"text": "Explore the ancient ruins", "completed": True},
                {"text": "Uncover the secret chamber", "completed": False},
                {"text": "Recover the Crystalline Crown", "completed": False},
            ],
            status="ACTIVE",
            rewards={"xp": 100, "gold": 50},
        ).to_dict()
    elif genre == "Sci-Fi":
        return Quest(
            quest_id="core_quest",
            title="Rogue AI Data Core Overdrive",
            description=f"Infiltrate corporate sector 7 and secure the neural core before system lockdown.",
            objectives=[
                {"text": "Bypass security perimeter", "completed": True},
                {"text": "Access main server node", "completed": False},
                {"text": "Extract AI core data", "completed": False},
            ],
            status="ACTIVE",
            rewards={"xp": 120, "gold": 75},
        ).to_dict()
    elif genre == "Mystery":
        return Quest(
            quest_id="mansion_quest",
            title="The Blackwood Estate Vanishings",
            description=f"Investigate the fog-shrouded estate and discover what happened to the missing guests.",
            objectives=[
                {"text": "Inspect the manor hall", "completed": True},
                {"text": "Find hidden manor blueprint", "completed": False},
                {"text": "Identify the perpetrator", "completed": False},
            ],
            status="ACTIVE",
            rewards={"xp": 90, "gold": 40},
        ).to_dict()
    elif genre == "Horror":
        return Quest(
            quest_id="curse_quest",
            title="Breaching the Shadow Ritual",
            description=f"Escape the nightmare dimension and destroy the occult talisman binding the entity.",
            objectives=[
                {"text": "Survive the initial onset", "completed": True},
                {"text": "Locate sanctuary circle", "completed": False},
                {"text": "Banish the shadow entity", "completed": False},
            ],
            status="ACTIVE",
            rewards={"xp": 110, "gold": 30},
        ).to_dict()
    else:  # Adventure
        return Quest(
            quest_id="relic_quest",
            title="Journey to the Sunken Temple",
            description=f"Chart uncharted jungle trails and retrieve the Golden Sun Disc.",
            objectives=[
                {"text": "Cross the perilous river", "completed": True},
                {"text": "Unlock temple doorway", "completed": False},
                {"text": "Claim the Sun Disc", "completed": False},
            ],
            status="ACTIVE",
            rewards={"xp": 100, "gold": 60},
        ).to_dict()


def update_relationship(character: str, trust_change: int, event_desc: str = None):
    """Updates NPC relationship trust level and records memory event."""
    if not character:
        return

    relationships = st.session_state.get("relationships", {})
    if character not in relationships:
        relationships[character] = {"trust": 0, "events": []}

    relationships[character]["trust"] += trust_change

    if event_desc:
        if event_desc not in relationships[character]["events"]:
            relationships[character]["events"].append(event_desc)

        memories = st.session_state.get("character_memories", [])
        mem_entry = f"{character}: {event_desc} (Trust: {relationships[character]['trust']:+d})"
        if mem_entry not in memories:
            memories.append(mem_entry)
        st.session_state["character_memories"] = memories

    st.session_state["relationships"] = relationships


def apply_choice_consequences(result_dict: dict):
    """Applies RPG consequence changes returned by Gemini content generation."""
    if not result_dict or not isinstance(result_dict, dict):
        return

    # 1. Stats updates
    health_chg = int(result_dict.get("health_change", 0) or 0)
    xp_chg = int(result_dict.get("xp_change", 0) or 0)
    gold_chg = int(result_dict.get("gold_change", 0) or 0)

    cur_hp = st.session_state.get("health", 100)
    max_hp = st.session_state.get("max_health", 100)
    st.session_state["health"] = max(0, min(max_hp, cur_hp + health_chg))

    st.session_state["xp"] = max(0, st.session_state.get("xp", 0) + max(0, xp_chg))
    st.session_state["gold"] = max(0, st.session_state.get("gold", 50) + gold_chg)

    # 2. Level Up Evaluation
    cur_level = st.session_state.get("level", 1)
    while st.session_state["xp"] >= (cur_level * 100):
        st.session_state["xp"] -= (cur_level * 100)
        cur_level += 1
        st.session_state["level"] = cur_level
        st.session_state["max_health"] += 10
        st.session_state["health"] = st.session_state["max_health"]
        st.session_state["attack"] = st.session_state.get("attack", 10) + 2
        st.session_state["defense"] = st.session_state.get("defense", 5) + 1

    # 3. Inventory & Clues
    item = result_dict.get("item", "")
    if item:
        inventory = st.session_state.get("inventory", [])
        if item not in inventory:
            inventory.append(item)
            st.session_state["inventory"] = inventory

    clue = result_dict.get("clue", "")
    if clue:
        clues = st.session_state.get("clues", [])
        if clue not in clues:
            clues.append(clue)
            st.session_state["clues"] = clues

    # 4. Relationship & Character Memory
    rel_change = result_dict.get("relationship_change")
    if isinstance(rel_change, dict):
        char_name = rel_change.get("character")
        trust = int(rel_change.get("trust_change", 0) or 0)
        event_str = rel_change.get("event", "")
        if char_name:
            update_relationship(char_name, trust, event_str)

    # 5. Story Events Tracking
    story_event = result_dict.get("story_event")
    if story_event and isinstance(story_event, str):
        events = st.session_state.get("story_events", [])
        if story_event not in events:
            events.append(story_event)
            st.session_state["story_events"] = events

    # 6. Quest Progress Update
    q_update = result_dict.get("quest_update")
    if isinstance(q_update, dict) and q_update:
        cur_quest = st.session_state.get("active_quest")
        if cur_quest and isinstance(cur_quest, dict):
            obj_comp = q_update.get("objective_completed")
            if obj_comp:
                for obj in cur_quest.get("objectives", []):
                    if obj_comp.lower() in obj["text"].lower():
                        obj["completed"] = True

            new_status = q_update.get("status")
            if new_status in ["ACTIVE", "COMPLETED", "FAILED"]:
                cur_quest["status"] = new_status

            st.session_state["active_quest"] = cur_quest


def build_compact_game_state_summary() -> str:
    """Constructs a concise summary of persistent game state for Gemini prompt injection."""
    init_default_game_state()

    hp = st.session_state.get("health", 100)
    max_hp = st.session_state.get("max_health", 100)
    lvl = st.session_state.get("level", 1)
    gold = st.session_state.get("gold", 50)
    inv = ", ".join(st.session_state.get("inventory", [])) or "None"
    clues = ", ".join(st.session_state.get("clues", [])) or "None"

    # Relationships summary
    rels = st.session_state.get("relationships", {})
    rel_lines = []
    for char, data in rels.items():
        rel_lines.append(f"{char} (Trust: {data.get('trust', 0)}, Events: {', '.join(data.get('events', [])) or 'None'})")
    rel_summary = "; ".join(rel_lines) if rel_lines else "No established relationships yet"

    # Active quest summary
    q = st.session_state.get("active_quest")
    if q and isinstance(q, dict):
        objs = [f"{'✓' if o.get('completed') else '○'} {o.get('text')}" for o in q.get("objectives", [])]
        quest_summary = f"{q.get('title')} [{q.get('status')}]: {', '.join(objs)}"
    else:
        quest_summary = "No active quest"

    # Recent story events
    events = ", ".join(st.session_state.get("story_events", [])[-5:]) or "Beginning of adventure"

    summary = f"""GAME STATE SUMMARY:
- Player: {st.session_state.get('player_name', 'Hero')} (Level {lvl}, HP: {hp}/{max_hp}, Gold: {gold})
- Inventory: {inv}
- Discovered Clues: {clues}
- Active Quest: {quest_summary}
- Character Relationships & Memories: {rel_summary}
- Recent Key Events: {events}
"""
    return summary


def evaluate_ending(turn: int, is_death: bool = False) -> dict:
    """
    Evaluates accumulated game state to determine the true story ending.
    Endings:
    - TRUE MYSTERY ENDING (requires >= 2 clues discovered + unraveling truth)
    - FRIENDSHIP / ALLIANCE ENDING (requires high relationship trust >= 15)
    - GOOD / HERO ENDING (high HP/XP + quest completed)
    - BAD / DARK ENDING (low HP or death or quest failed)
    """
    hp = st.session_state.get("health", 100)
    clues = st.session_state.get("clues", [])
    inventory = st.session_state.get("inventory", [])
    relationships = st.session_state.get("relationships", {})
    active_quest = st.session_state.get("active_quest", {})
    quest_status = active_quest.get("status", "ACTIVE") if isinstance(active_quest, dict) else "ACTIVE"

    max_trust = 0
    ally_char = "Ally"
    for char, data in relationships.items():
        t = data.get("trust", 0)
        if t > max_trust:
            max_trust = t
            ally_char = char

    if is_death or hp <= 0 or quest_status == "FAILED":
        return {
            "type": "BAD_DARK_ENDING",
            "title": "💀 BAD / DARK ENDING: The Shadow Overcome",
            "banner": "💀 DARK ENDING",
            "description": "Your strength waned and the simulation's forces overwhelmed your operative. Dark shadows claim the realm.",
        }

    if len(clues) >= 2:
        return {
            "type": "TRUE_MYSTERY_ENDING",
            "title": "🔍 TRUE MYSTERY ENDING: Unravelling the Core Truth",
            "banner": "🔍 TRUE MYSTERY ENDING",
            "description": f"By piecing together the clues ({', '.join(clues)}), you exposed the mastermind behind the crisis and restored absolute order.",
        }

    if max_trust >= 15:
        return {
            "type": "FRIENDSHIP_ALLIANCE_ENDING",
            "title": f"🤝 FRIENDSHIP / ALLIANCE ENDING: Bound with {ally_char}",
            "banner": "🤝 ALLIANCE ENDING",
            "description": f"Through unwavering loyalty and honor, your bond with {ally_char} (Trust: {max_trust}) forged an indomitable alliance that saved the realm.",
        }

    return {
        "type": "GOOD_HERO_ENDING",
        "title": "🏆 GOOD / HERO ENDING: Triumph of the Legend",
        "banner": "🏆 HERO ENDING",
        "description": f"With high resolve (Level {st.session_state.get('level', 1)}, HP: {hp}), your hero triumphed over all obstacles and achieved immortal glory.",
    }
