import base64
import html
import re
import urllib.parse
import urllib.request

def generate_scene_image(scene_text, genre, world, turn=1):
    """
    Generates a reliable visual novel scene image for the turn.
    Tries Pollinations AI first with strict clean prompt & timeout,
    and falls back to high-speed visual novel scene art or dynamic SVG graphic.
    """
    clean_scene = re.sub(r'[^a-zA-Z0-9 ]+', ' ', html.unescape(str(scene_text)))
    clean_scene = re.sub(r'\s+', ' ', clean_scene).strip()[:100]
    
    clean_genre = re.sub(r'[^a-zA-Z0-9 ]+', '', str(genre)).strip()
    clean_world = re.sub(r'[^a-zA-Z0-9 ]+', '', str(world)).strip()[:50]

    # Clean short prompt
    prompt = f"Cinematic {clean_genre} scene {clean_scene} epic digital art"
    encoded_prompt = urllib.parse.quote(prompt)

    # 1. Try Pollinations AI with short prompt
    pollination_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=450&seed={turn}&nologo=true"
    
    try:
        req = urllib.request.Request(pollination_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200 and 'image' in resp.headers.get('Content-Type', ''):
                img_data = resp.read()
                b64_str = base64.b64encode(img_data).decode('utf-8')
                return f"data:image/jpeg;base64,{b64_str}"
    except Exception as ex:
        print(f"[POLLINATIONS TIMEOUT/LIMIT]: {ex}")

    # 2. High Quality SVG Visual Novel Scene Graphic Fallback (Guaranteed 100% success)
    genre_colors = {
        "Fantasy": ("#120c04", "#7a4f0d", "#d4a017", "🐉 FANTASY REALM"),
        "Sci-Fi": ("#020510", "#005090", "#00e8ff", "🚀 CYBERPUNK REALM"),
        "Mystery": ("#0a0812", "#4a2070", "#b060ff", "🏚️ GOTHIC MYSTERY"),
        "Horror": ("#100204", "#700010", "#ff3040", "👻 HORROR REALM"),
        "Adventure": ("#041008", "#106030", "#30ff80", "🌍 ADVENTURE REALM")
    }
    bg_dark, bg_mid, accent, title_tag = genre_colors.get(clean_genre, genre_colors["Fantasy"])
    
    snippet = html.escape(clean_scene[:120])
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{bg_dark}" />
          <stop offset="50%" stop-color="{bg_mid}" />
          <stop offset="100%" stop-color="#050810" />
        </linearGradient>
        <radialGradient id="glow" cx="50%" cy="30%" r="60%">
          <stop offset="0%" stop-color="{accent}" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="{bg_dark}" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="800" height="450" fill="url(#bg)"/>
      <rect width="800" height="450" fill="url(#glow)"/>
      <rect x="20" y="20" width="760" height="410" fill="none" stroke="{accent}" stroke-width="1.5" stroke-opacity="0.4" rx="8"/>
      <text x="40" y="60" font-family="'Orbitron', sans-serif" font-size="16" font-weight="bold" fill="{accent}" letter-spacing="2">{title_tag} — TURN {turn}</text>
      <line x1="40" y1="75" x2="760" y2="75" stroke="{accent}" stroke-opacity="0.3" stroke-width="1"/>
      <text x="40" y="210" font-family="'Rajdhani', sans-serif" font-size="22" font-weight="bold" fill="#ffffff" opacity="0.95">"{snippet}..."</text>
      <text x="40" y="400" font-family="'Share Tech Mono', monospace" font-size="13" fill="{accent}" opacity="0.7">WORLD: {clean_world[:40].upper()} | CINEMATIC SCENE ILLUSTRATION</text>
    </svg>"""

    b64_svg = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64_svg}"

if __name__ == "__main__":
    res = generate_scene_image("Arpita pushes past Julian toward heavy oak doors", "Sci-Fi", "Neon City Academy", 3)
    print("Result length:", len(res))
    print("Starts with:", res[:40])
