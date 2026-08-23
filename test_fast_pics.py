import urllib.request
import urllib.parse
import json
import base64
import re

def get_real_cinematic_picture(scene_text, genre, world, turn=1):
    clean_scene = re.sub(r'[^a-zA-Z0-9 ]+', ' ', html.unescape(str(scene_text or "")))
    clean_scene = re.sub(r'\s+', ' ', clean_scene).strip()[:60]
    
    clean_genre = re.sub(r'[^a-zA-Z0-9 ]+', '', str(genre or "Fantasy")).strip()
    
    # 1. High Speed Lexica AI Art API
    prompt = f"cinematic visual novel {clean_genre} {clean_scene}"
    encoded = urllib.parse.quote(prompt)
    
    try:
        lexica_url = f"https://lexica.art/api/v1/search?q={encoded}"
        req = urllib.request.Request(lexica_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                images = data.get("images", [])
                if images:
                    img_url = images[(turn - 1) % len(images)]["src"]
                    print(f"[LEXICA SUCCESS]: {img_url}")
                    # Download bytes directly
                    img_req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(img_req, timeout=4) as img_resp:
                        if img_resp.status == 200:
                            b64 = base64.b64encode(img_resp.read()).decode('utf-8')
                            return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"[LEXICA ERROR]: {e}")

    # 2. High-speed curated Unsplash Visual Novel Art
    genre_keywords = {
        "Fantasy": ["fantasy-castle", "dragon-magic", "medieval-kingdom", "ancient-forest"],
        "Sci-Fi": ["cyberpunk-city", "futuristic-spaceship", "sci-fi-neon", "robot-future"],
        "Mystery": ["foggy-mansion", "detective-shadows", "mysterious-forest", "gothic-estate"],
        "Horror": ["spooky-haunted", "dark-gothic-castle", "creepy-forest", "nightmare-realm"],
        "Adventure": ["ancient-ruins", "jungle-expedition", "epic-mountain-landscape", "treasure-island"]
    }
    keywords = genre_keywords.get(clean_genre, genre_keywords["Fantasy"])
    selected_kw = keywords[(turn - 1) % len(keywords)]
    
    unsplash_url = f"https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1024&q=80"
    print(f"[UNSPLASH FALLBACK]: {unsplash_url}")
    return unsplash_url

if __name__ == "__main__":
    import html
    res = get_real_cinematic_picture("King sits upon wooden throne surrounded by villagers", "Fantasy", "Oakhaven", 1)
    print("Result len:", len(res))
