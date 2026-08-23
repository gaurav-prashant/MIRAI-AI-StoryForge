import urllib.request
import urllib.parse
import json
import re

def clean_for_ai_prompt(text):
    clean = re.sub(r'[^a-zA-Z0-9 ]+', ' ', str(text))
    return re.sub(r'\s+', ' ', clean).strip()

def get_real_ai_image_url(scene_text, genre, world, turn=1):
    scene_words = clean_for_ai_prompt(scene_text)[:80]
    genre_clean = clean_for_ai_prompt(genre)
    world_clean = clean_for_ai_prompt(world)[:40]
    
    # Simple clean AI prompt
    prompt = f"cinematic digital art {genre_clean} {scene_words}"
    encoded = urllib.parse.quote(prompt)

    # 1. Try Lexica AI Art API first (Returns real AI generated artwork!)
    try:
        lexica_url = f"https://lexica.art/api/v1/search?q={encoded}"
        req = urllib.request.Request(lexica_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                images = data.get("images", [])
                if images:
                    selected_img = images[(turn - 1) % len(images)]
                    print(f"[LEXICA AI SUCCESS] Found real AI image: {selected_img['src']}")
                    return selected_img['src']
    except Exception as e:
        print(f"[LEXICA FAILED]: {e}")

    # 2. Try Pollinations AI with short clean prompt
    pollin_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576&seed={turn}&nologo=true"
    print(f"[POLLINATIONS URL]: {pollin_url}")
    return pollin_url

if __name__ == "__main__":
    url = get_real_ai_image_url("King Aethelgard sits upon his throne surrounded by villagers", "Fantasy", "Oakhaven", 1)
    print("Final image URL:", url)
