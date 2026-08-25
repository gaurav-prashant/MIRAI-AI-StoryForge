# 🎭 MirAI – AI StoryForge

> **An AI-powered interactive visual novel where every choice changes your adventure.**

MirAI – AI StoryForge is an interactive AI storytelling and RPG experience built with **Python, Streamlit, and Generative AI**.

Instead of following a fixed story, the player creates an adventure by choosing a character, genre, world, and actions. The AI dynamically generates scenes, choices, narration, consequences, quests, character relationships, and visual scene illustrations as the adventure progresses.

---

### 🌐 Live Application

🚀 **[Open MirAI – AI StoryForge](https://mirai-ai-storyforge-7mm669eoywjvwonccqm6tc.streamlit.app/)**

## 🎬 Demo

### 🎥 Project Demo Video

▶️ **[Watch MirAI – AI StoryForge Demo](https://drive.google.com/file/d/14SVZn5zCi9ouPBywd7QLCaOMxfvD4ASF/view?usp=drive_link)**

---

## 🌟 Overview

MirAI combines:

- 🤖 Generative AI
- 🎮 Interactive RPG mechanics
- 📖 Dynamic storytelling
- 🖼️ AI-generated scene illustrations
- 🎨 Cinematic fallback artwork
- 🎵 Background music and sound effects
- 🗣️ English & Hindi narration
- 💾 Save / Load adventures
- 🧠 Story memory and game-state tracking
- 🏆 Multiple possible endings

The goal is to create a storytelling experience that feels less like reading a story and more like **playing inside one**.

---

# ✨ Features

## 🤖  AI-Powered Story Generation

The story is dynamically generated using Gemini.

The AI receives information about:

- Player name
- Selected genre
- Custom world
- Previous story history
- Player's latest action
- Current RPG state
- Quests
- Relationships
- Story events

This allows the story to continue based on what the player has already done.

The application builds story memory from previous turns so that new scenes can remain connected to earlier events.

---

# 🎮  Interactive Choice-Based Gameplay

The player controls the adventure through decisions.

A typical flow is:

```text
Story Scene
     ↓
AI-generated Choices
     ↓
Player Decision
     ↓
Consequences
     ↓
New Scene
     ↓
New Choices
     ↓
Continue Adventure

Every action can influence the next stage of the story.

📚  Multiple Story Genres

Players can choose from different genres:

Genre	Example Worlds
🧙 Fantasy	Ancient kingdoms, magical forests, mysterious ruins
🕵️ Mystery	Victorian mansions, investigations, hidden clues
🚀 Sci-Fi	Space stations, alien worlds, futuristic environments
👻 Horror	Haunted locations, abandoned buildings, dark forests
⚔️ Adventure	Expeditions, dangerous journeys, unexplored worlds

The selected genre influences the story, world-building, quests, audio, and visual presentation.

🌍  Custom World Creation

Players can describe their own world before starting the adventure.

Example:

An ancient kingdom surrounded by mysterious forests,
where forgotten magic has started to return.

MirAI then uses this world description as part of the story-generation context.

❤️  RPG Character System

MirAI includes RPG-style player statistics.

The game tracks:

❤️ Health
⚔️ Attack
🛡️ Defense
⭐ XP
🔺 Level
💰 Gold
🎒 Inventory
🔎 Clues

A new adventure initializes the player's RPG state and updates it as choices produce consequences.

Example starting state:

Health   : 100
Attack   : 10
Defense  : 5
XP       : 0
Level    : 1
Gold     : 50
📈  Dynamic Consequences

Player choices can affect the game state.

Possible consequences include:

Health changes
XP gains
Gold changes
Inventory updates
New clues
Level progression
Quest progress
Relationship changes
Story events

This makes choices more meaningful than simply changing the next paragraph of text.

🎯  Quest System

Each adventure can have an active genre-based quest.

The game maintains quest information along with the story state.

Quest progression can be influenced by the player's decisions and generated story events.

🤝  Character Relationships & Memories

MirAI maintains relationship-related game state.

The system tracks:

Character relationships
Trust
Character memories
Story events

This allows characters and important interactions to become part of the ongoing adventure.

🧠  Story Memory

Previous turns are converted into a structured story memory.

Example:

TURN 1

PLAYER ACTION:
Adventure started

SCENE:
The player arrives at the mysterious location...


TURN 2

PLAYER ACTION:
Investigate the strange door

SCENE:
The door opens and reveals...

This history is provided to the AI when generating subsequent scenes.

As a result, the story can continue from previous events rather than starting from scratch every turn.

🖼️  Dynamic Scene Images

Every story scene can have a corresponding visual illustration.

The image-generation pipeline uses information from the current scene, genre, and world.

Conceptually:

Current Story Scene
        ↓
Scene Image Prompt
        ↓
AI Image Generation
        ↓
Scene Illustration
        ↓
Display in Story

Scene images can also be downloaded individually.

🛡️  Multi-Level Image Fallback System

Image generation depends on an external image-generation service, so MirAI includes a fallback architecture.

If AI image generation fails because of:

HTTP 429 rate limiting
Timeout
Network failure
Invalid response
External service availability

the application can switch to local fallback artwork instead of stopping the story.

              Scene
                │
                ↓
       AI Image Generation
                │
        ┌───────┴───────┐
        │               │
     SUCCESS           FAILURE
        │               │
        ↓               ↓
   AI-generated    Local Fallback
      Image           Artwork
                        │
                        ↓
                Scene Matching
                        │
                        ↓
                 Render Image

The objective is simple:

An image-generation failure should not stop the adventure.

🎨  Cinematic Local Fallback Assets

The project contains local fallback artwork under:

assets/fallbacks/

Genre-specific assets include:

fantasy_*.png
mystery_*.png
cyberpunk_*.png
scifi_*.png
horror_*.png

The fallback library provides cinematic 16:9 artwork that can be displayed when external image generation is unavailable.

♻️  Non-Repeating Fallback Images

MirAI keeps track of fallback assets already used during an adventure.

The selection system prioritizes unused assets so the same image is not repeatedly shown while unused artwork is still available.

Conceptually:

Turn 1 → fantasy_14.png
Turn 2 → fantasy_16.png
Turn 3 → fantasy_4.png
Turn 4 → fantasy_6.png
Turn 5 → fantasy_9.png

This creates more visual variety throughout the adventure.

🔍  Image Duplicate Protection

The image pipeline includes duplicate-detection mechanisms.

It can track image hashes such as:

MD5
SHA256

and perceptual image hashes for visual similarity checking.

This helps reduce repeated or visually duplicated scene artwork.

⚡  Image Performance & Caching

The image system is designed to avoid unnecessary delays when external image generation is unavailable.

Performance techniques include:

Bounded request timeouts
Fast handling of HTTP 429 responses
Local fallback assets
Local asset caching
Cached image bytes
Cached Base64 data
Fast fallback selection
Limited external generation attempts

When local fallback artwork is used, the application can serve the image without waiting for another external generation request.

🎵  Background Music

MirAI includes genre-based background music.

Background audio can be selected according to the current genre.

For example:

Fantasy  → Fantasy atmosphere
Mystery  → Investigation atmosphere
Horror   → Dark atmosphere
Sci-Fi   → Futuristic atmosphere

Music settings can be controlled from the application.

🔊  Sound Effects

The application also supports story-related sound effects.

Sound effects can be triggered by events such as:

Adventure start
Mystery/clue events
Story progression
Ending states
🗣️  English & Hindi Narration

Story scenes can be presented in:

🇬🇧 English

and

🇮🇳 Hindi

The interface displays both versions of the generated scene narration.

🎙️ 19. Text-to-Speech Narration

MirAI includes text-to-speech support for story narration.

Players can listen to the generated story in:

English
Hindi

The narration interface supports playback controls such as:

▶️ Play
⏸️ Pause
▶️ Resume
⏹️ Stop
Speed control

This makes the experience closer to an interactive audio-visual novel.

💾  Save Adventure

Players can save their current adventure as a JSON file.

The save system stores important adventure state including:

Player Name
Genre
World
Current Turn
Story History
Health
Max Health
Attack
Defense
XP
Level
Gold
Inventory
Clues

Example:

Save Adventure
      ↓
Adventure JSON
      ↓
Download / Store
📂  Load Adventure

Previously saved adventures can be loaded again.

The application validates the JSON structure and restores the stored game state.

The load system restores:

Player information
Genre
World
Story history
Current turn
RPG statistics
Inventory
Clues

This allows a player to continue an adventure later.

🖼️  Download Scene Images

Individual scene images can be downloaded from the story interface.

Example filename:

storyforge_player_turn_5_scene.png

This makes it possible to keep important moments from an adventure.

🗜️  Download All Scene Images

MirAI also provides functionality to create a ZIP archive containing the scene images from the adventure.

Adventure
    ↓
Scene Images
    ↓
ZIP Archive
    ↓
Download

📄  Adventure Summary

The application can generate/download an adventure summary containing information about the player's journey.

This provides a convenient way to preserve the narrative outcome.

🏆  Dynamic Endings

The game includes ending evaluation based on the current adventure state.

The ending can depend on factors such as:

Story progression
Player choices
RPG state
Quests
Story events
Relationships

Therefore, the adventure does not have to behave like a single fixed storyline.

🔄  Play Again / New Adventure

Players can restart the experience and create a completely new adventure.

A new adventure resets the required RPG and story state and allows the player to select a new:

Character
Genre
World
🎨  Cinematic UI

MirAI uses a custom Streamlit interface designed to feel like a modern game / visual novel.

The interface includes:

Wide layout
Custom typography
Themed colors
Story panels
RPG statistics
Interactive controls
Image cards
Audio controls
Adventure management controls

The application is designed to provide a more immersive experience than a basic Streamlit application.


🛠️ Tech Stack
Technology	Purpose
🐍 Python	Core application
🎈 Streamlit	Web UI
🤖 Gemini	AI story generation
🖼️ Pollinations	AI scene image generation
🖌️ Pillow	Image processing
🔐 JSON	Adventure save/load
🎵 Audio assets	Music & sound effects
🗣️ TTS	Story narration
🐙 GitHub	Version control
☁️ Streamlit Cloud	Deployment
⚙️ Installation


🚀 Future Improvements

Possible future enhancements include:

🎭 Better character visual consistency
🧠 Longer-term AI memory
🎬 Animated scene transitions
🎙️ More advanced voice narration
🗺️ Interactive world maps
👥 Multiplayer adventures
🧩 More genres
🏪 In-game shops
⚔️ More advanced combat
🏆 Achievements
📊 Player statistics
📱 Improved mobile experience
🎨 More dynamic AI-generated environments


⭐ GitHub Repository

👉 https://github.com/gaurav-prashant/MIRAI-AI-StoryForge


🎭 MIRAI – AI StoryForge

Don't just read the story.

Create it. Choose it. Live it.