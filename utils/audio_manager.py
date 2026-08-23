"""
MIRAI StoryForge Audio Manager
==============================
- Background music: st.audio() (native HTML5 player in sidebar)
- SFX: st.audio() with a small container (no HTML injection)
- No st.components.v1.html (deprecated in current Streamlit)
- No raw HTML strings displayed to user
- No base64 strings shown to user
"""
import os
import base64
import streamlit as st
import streamlit.components.v1 as components



AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "audio")

GENRE_MUSIC_MAP = {
    "Fantasy":   "background_fantasy.wav",
    "Mystery":   "background_mystery.wav",
    "Horror":    "background_horror.wav",
    "Sci-Fi":    "background_scifi.wav",
    "Adventure": "background_adventure.wav",
}

SFX_MAP = {
    "action":  "action.wav",
    "mystery": "mystery.wav",
    "ending":  "ending.wav",
    # Also accept bare filenames directly
    "action.wav":  "action.wav",
    "mystery.wav": "mystery.wav",
    "ending.wav":  "ending.wav",
}


def get_audio_filepath(filename: str) -> str:
    return os.path.join(AUDIO_DIR, filename)


def get_audio_bytes(filename: str) -> bytes:
    """Returns raw bytes of audio file, or None if missing/unreadable."""
    if not filename:
        return None
    filepath = get_audio_filepath(filename)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        return data if data else None
    except Exception:
        return None


def get_background_track_for_genre(genre: str) -> str:
    """Returns the filename for the genre's background music track."""
    return GENRE_MUSIC_MAP.get(genre, "background_fantasy.wav")


def get_audio_base64(filename: str) -> str:
    """Returns a base64 data URI string for the given audio file, or None."""
    data = get_audio_bytes(filename)
    if not data:
        return None
    ext = os.path.splitext(filename)[1].lower()
    mime_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
    b64_str = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{b64_str}"


def play_sfx(filename_or_key: str, volume_pct: int = 70):
    """
    Plays a one-time SFX using st.audio() in a zero-height container.
    Does NOT render any HTML code as text.
    Does NOT return anything.
    """
    if not filename_or_key:
        return

    filename = SFX_MAP.get(filename_or_key, filename_or_key)
    audio_bytes = get_audio_bytes(filename)
    if not audio_bytes:
        return

    ext = os.path.splitext(filename)[1].lower()
    fmt = "audio/wav" if ext == ".wav" else "audio/mp3"

    try:
        # Hide the SFX player with CSS so it doesn't appear as a visible widget
        st.markdown(
            "<style>[data-testid='stAudio']{display:none!important;height:0!important;overflow:hidden!important;}</style>",
            unsafe_allow_html=True,
        )
        st.audio(audio_bytes, format=fmt, autoplay=True)
    except Exception:
        pass


def render_background_music(genre: str, music_enabled: bool, volume_pct: int):
    """
    Renders background music in the sidebar as a native HTML5 audio player.
    Visible controls allow the user to press Play — required due to browser autoplay policy.
    """
    if not music_enabled:
        return
    bg_track = get_background_track_for_genre(genre)
    bg_bytes = get_audio_bytes(bg_track)
    if not bg_bytes:
        return
    try:
        ext = os.path.splitext(bg_track)[1].lower()
        fmt = "audio/wav" if ext == ".wav" else "audio/mp3"
        st.audio(bg_bytes, format=fmt, loop=True)
    except Exception:
        pass


def render_audio_components(genre: str, music_enabled: bool, volume_pct: int, sfx_to_play: str = None):
    """
    Entry point called from app.py on every rerun.
    Handles SFX only (background music is rendered in sidebar via render_background_music).
    Does NOT return anything. Does NOT display HTML/JS as text.
    """
    if sfx_to_play and st.session_state.get("sfx_enabled", True):
        play_sfx(sfx_to_play, volume_pct)


def render_tts_widget(scene_text: str, scene_hindi_text: str, turn_num: int):
    """
    Renders a Text-to-Speech control panel for a story scene using the
    browser's built-in Web Speech API (supports English and Hindi narration).

    Controls: Read / Pause / Resume / Stop + Speed slider + Language Voice Selector.
    Renders via components.html() without displaying any source code.
    """
    import json

    en_text = scene_text.strip() if scene_text else ""
    hi_text = scene_hindi_text.strip() if scene_hindi_text else ""

    if not en_text and not hi_text:
        return

    safe_en = json.dumps(en_text)
    safe_hi = json.dumps(hi_text)

    uid = f"tts_{turn_num}"

    widget_html = f"""
<div id="{uid}_container" style="
    background: linear-gradient(135deg, rgba(0,30,60,0.85) 0%, rgba(0,10,30,0.9) 100%);
    border: 1px solid rgba(0,200,255,0.18);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 8px 0 12px 0;
    font-family: 'Share Tech Mono', 'Courier New', monospace;
    display: flex;
    flex-direction: column;
    gap: 8px;
">
  <div style="font-size:0.72rem; color:#00a8d0; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:2px;">
    🔊 Story Narration (Voice Output)
  </div>

  <!-- Voice Language Selector -->
  <div style="display:flex; gap:12px; align-items:center; font-size:0.75rem; color:#7fbfcf; margin-bottom:4px;">
    <span>Voice Language:</span>
    <label style="cursor:pointer; color:#00e5ff;">
      <input type="radio" name="{uid}_lang" value="en" checked style="accent-color:#00c8ff;"> 🇬🇧 English Voice
    </label>
    <label style="cursor:pointer; color:#00e5ff;">
      <input type="radio" name="{uid}_lang" value="hi" style="accent-color:#00c8ff;"> 🇮🇳 Hindi Voice
    </label>
    <label style="cursor:pointer; color:#00e5ff;">
      <input type="radio" name="{uid}_lang" value="both" style="accent-color:#00c8ff;"> 🌐 Both
    </label>
  </div>

  <!-- Control buttons row -->
  <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
    <button id="{uid}_read" onclick="{uid}_start()" style="
        background:rgba(0,200,255,0.12); color:#00e5ff; border:1px solid rgba(0,200,255,0.35);
        border-radius:5px; padding:4px 12px; cursor:pointer; font-size:0.8rem;
        font-family:inherit; transition:background 0.2s;">
      ▶ Read
    </button>
    <button id="{uid}_pause" onclick="{uid}_pause()" disabled style="
        background:rgba(0,200,255,0.06); color:#888; border:1px solid rgba(0,200,255,0.15);
        border-radius:5px; padding:4px 12px; cursor:pointer; font-size:0.8rem;
        font-family:inherit; transition:background 0.2s;">
      ⏸ Pause
    </button>
    <button id="{uid}_resume" onclick="{uid}_resume()" disabled style="
        background:rgba(0,200,255,0.06); color:#888; border:1px solid rgba(0,200,255,0.15);
        border-radius:5px; padding:4px 12px; cursor:pointer; font-size:0.8rem;
        font-family:inherit; transition:background 0.2s;">
      ▶ Resume
    </button>
    <button id="{uid}_stop" onclick="{uid}_stop()" disabled style="
        background:rgba(0,200,255,0.06); color:#888; border:1px solid rgba(0,200,255,0.15);
        border-radius:5px; padding:4px 12px; cursor:pointer; font-size:0.8rem;
        font-family:inherit; transition:background 0.2s;">
      ⏹ Stop
    </button>

    <!-- Speed control -->
    <label style="color:#7fbfcf; font-size:0.72rem; margin-left:8px;">
      Speed:
      <input type="range" id="{uid}_speed" min="0.5" max="2.0" step="0.1" value="1.0"
        style="vertical-align:middle; width:80px; accent-color:#00c8ff; cursor:pointer;">
      <span id="{uid}_speed_val" style="color:#00e5ff;">1.0×</span>
    </label>
  </div>

  <!-- Status line -->
  <div id="{uid}_status" style="font-size:0.68rem; color:#456878; font-style:italic;">
    Click ▶ Read to hear story narration.
  </div>
</div>

<script>
(function() {{
  var TEXT_EN_{uid} = {safe_en};
  var TEXT_HI_{uid} = {safe_hi};

  var speaking_{uid} = false;
  var paused_{uid} = false;
  var cachedVoices = [];

  function getSynth() {{
    return window.speechSynthesis || (window.parent && window.parent.speechSynthesis);
  }}

  function loadVoices() {{
    var synth = getSynth();
    if (synth && synth.getVoices) {{
      cachedVoices = synth.getVoices() || [];
    }}
  }}

  loadVoices();
  var synthObj = getSynth();
  if (synthObj && typeof synthObj.onvoiceschanged !== 'undefined') {{
    synthObj.onvoiceschanged = loadVoices;
  }}

  function getVoiceForLang(synth, langPrefix) {{
    var voices = (synth && synth.getVoices) ? (synth.getVoices() || []) : [];
    if (!voices || voices.length === 0) voices = cachedVoices;

    for (var i = 0; i < voices.length; i++) {{
      var v = voices[i];
      if (v.lang && v.lang.toLowerCase().startsWith(langPrefix)) return v;
    }}
    for (var j = 0; j < voices.length; j++) {{
      var v2 = voices[j];
      if (v2.lang && v2.lang.toLowerCase().includes(langPrefix)) return v2;
    }}
    return null;
  }}

  function setBtn(readOn, pauseOn, resumeOn, stopOn) {{
    var readBtn   = document.getElementById("{uid}_read");
    var pauseBtn  = document.getElementById("{uid}_pause");
    var resumeBtn = document.getElementById("{uid}_resume");
    var stopBtn   = document.getElementById("{uid}_stop");
    if (readBtn)   {{ readBtn.disabled   = !readOn;   readBtn.style.color   = readOn   ? "#00e5ff" : "#888"; readBtn.style.background   = readOn   ? "rgba(0,200,255,0.18)" : "rgba(0,200,255,0.06)"; }}
    if (pauseBtn)  {{ pauseBtn.disabled  = !pauseOn;  pauseBtn.style.color  = pauseOn  ? "#00e5ff" : "#888"; pauseBtn.style.background  = pauseOn  ? "rgba(0,200,255,0.18)" : "rgba(0,200,255,0.06)"; }}
    if (resumeBtn) {{ resumeBtn.disabled = !resumeOn; resumeBtn.style.color = resumeOn ? "#00e5ff" : "#888"; resumeBtn.style.background = resumeOn ? "rgba(0,200,255,0.18)" : "rgba(0,200,255,0.06)"; }}
    if (stopBtn)   {{ stopBtn.disabled   = !stopOn;   stopBtn.style.color   = stopOn   ? "#ff6060" : "#888"; stopBtn.style.background   = stopOn   ? "rgba(255,60,60,0.14)"  : "rgba(0,200,255,0.06)"; }}
  }}

  function setStatus(msg) {{
    var el = document.getElementById("{uid}_status");
    if (el) el.textContent = msg;
  }}

  function createUtterance(synth, text, langCode, rate) {{
    var utt = new SpeechSynthesisUtterance(text);
    utt.rate = rate;
    utt.pitch = 1.0;
    if (langCode === "hi") {{
      utt.lang = "hi-IN";
      var hiVoice = getVoiceForLang(synth, "hi");
      if (hiVoice) utt.voice = hiVoice;
    }} else {{
      utt.lang = "en-US";
      var enVoice = getVoiceForLang(synth, "en");
      if (enVoice) utt.voice = enVoice;
    }}
    return utt;
  }}

  window["{uid}_start"] = function() {{
    var synth = getSynth();
    if (!synth) {{ setStatus("Speech Synthesis not supported in this browser."); return; }}

    try {{
      synth.cancel();

      var speedEl = document.getElementById("{uid}_speed");
      var rate = speedEl ? parseFloat(speedEl.value) : 1.0;

      var modeEl = document.querySelector('input[name="{uid}_lang"]:checked');
      var mode = modeEl ? modeEl.value : "en";

      var queue = [];
      if (mode === "en") {{
        if (TEXT_EN_{uid}) queue.push({{ text: TEXT_EN_{uid}, lang: "en" }});
      }} else if (mode === "hi") {{
        if (TEXT_HI_{uid}) queue.push({{ text: TEXT_HI_{uid}, lang: "hi" }});
        else if (TEXT_EN_{uid}) queue.push({{ text: TEXT_EN_{uid}, lang: "en" }});
      }} else if (mode === "both") {{
        if (TEXT_EN_{uid}) queue.push({{ text: TEXT_EN_{uid}, lang: "en" }});
        if (TEXT_HI_{uid}) queue.push({{ text: TEXT_HI_{uid}, lang: "hi" }});
      }}

      if (queue.length === 0) {{
        setStatus("No story narration text available.");
        return;
      }}

      var playIdx = 0;
      function playNext() {{
        if (playIdx >= queue.length) {{
          speaking_{uid} = false; paused_{uid} = false;
          setBtn(true, false, false, false);
          setStatus("Narration complete.");
          return;
        }}

        var item = queue[playIdx];
        var utt = createUtterance(synth, item.text, item.lang, rate);

        utt.onstart = function() {{
          speaking_{uid} = true; paused_{uid} = false;
          setBtn(false, true, false, true);
          setStatus("▶ Speaking (" + (item.lang === "hi" ? "Hindi Voice" : "English Voice") + ")...");
        }};
        utt.onpause = function() {{
          paused_{uid} = true;
          setBtn(false, false, true, true);
          setStatus("⏸ Paused.");
        }};
        utt.onresume = function() {{
          paused_{uid} = false;
          setBtn(false, true, false, true);
          setStatus("▶ Speaking (" + (item.lang === "hi" ? "Hindi Voice" : "English Voice") + ")...");
        }};
        utt.onend = function() {{
          playIdx++;
          playNext();
        }};
        utt.onerror = function(e) {{
          playIdx++;
          if (playIdx >= queue.length) {{
            speaking_{uid} = false; paused_{uid} = false;
            setBtn(true, false, false, false);
            setStatus("Speech error: " + (e.error || "unknown"));
          }} else {{
            playNext();
          }}
        }};

        synth.speak(utt);
      }}

      playNext();

    }} catch(err) {{
      setStatus("Error: " + err.message);
    }}
  }};

  window["{uid}_pause"] = function() {{
    var synth = getSynth();
    if (synth && speaking_{uid} && !paused_{uid}) {{
      synth.pause();
    }}
  }};

  window["{uid}_resume"] = function() {{
    var synth = getSynth();
    if (synth && paused_{uid}) {{
      synth.resume();
    }}
  }};

  window["{uid}_stop"] = function() {{
    var synth = getSynth();
    if (synth) {{
      synth.cancel();
      speaking_{uid} = false; paused_{uid} = false;
      setBtn(true, false, false, false);
      setStatus("Stopped.");
    }}
  }};

  var speedEl = document.getElementById("{uid}_speed");
  if (speedEl) {{
    speedEl.addEventListener("input", function() {{
      var valEl = document.getElementById("{uid}_speed_val");
      if (valEl) valEl.textContent = parseFloat(speedEl.value).toFixed(1) + "x";
    }});
  }}
}})();
</script>
"""
    components.html(widget_html, height=140, scrolling=False)

