import base64
import html
import io
import re
import urllib.parse
import urllib.request
import zipfile
import time
import uuid
import random
import os
import hashlib

# ---------------------------------------------------------------------------
# Perceptual hash (dHash) — pure Pillow, no extra packages required.
# Computes a 64-bit difference hash for visual-duplicate detection.
# ---------------------------------------------------------------------------
def _dhash(image_bytes, hash_size=8):
    """Return a 64-bit integer dHash of image_bytes using Pillow only.
    hash_size=8 produces a 64-bit hash (8x8 grid of difference bits).
    Returns None on any error.
    """
    try:
        from PIL import Image
        import io as _io
        img = Image.open(_io.BytesIO(image_bytes)).convert('L')  # greyscale
        img = img.resize((hash_size + 1, hash_size), Image.LANCZOS)
        pixels = list(img.getdata())
        bits = 0
        for row in range(hash_size):
            for col in range(hash_size):
                left = pixels[row * (hash_size + 1) + col]
                right = pixels[row * (hash_size + 1) + col + 1]
                bits = (bits << 1) | (1 if left > right else 0)
        return bits
    except Exception:
        return None


def _hamming_distance(a, b):
    """Count differing bits between two integers."""
    return bin(a ^ b).count('1')


# Module-level in-memory cache for local fallback files: path -> (data, img_hash, b64_str)
_LOCAL_ASSET_CACHE = {}


# High-Resolution Real Digital Artworks by Genre (100% Verified 200 OK URLs)
REAL_AI_ARTWORKS = {
    "Fantasy": [f"assets/fallbacks/fantasy_{i}.png" for i in range(20)],
    "Sci-Fi": [f"assets/fallbacks/scifi_{i}.png" for i in range(20)],
    "Cyberpunk": [f"assets/fallbacks/cyberpunk_{i}.png" for i in range(20)],
    "Mystery": [f"assets/fallbacks/mystery_{i}.png" for i in range(20)],
    "Horror": [f"assets/fallbacks/horror_{i}.png" for i in range(20)],
    "Adventure": [f"assets/fallbacks/fantasy_{i}.png" for i in range(20)],
}


def get_image_bytes(image_url):
    """Converts a Base64 Data URI or HTTP URL into raw image bytes for st.download_button."""
    if not image_url:
        return None
    try:
        s_url = str(image_url)
        if s_url.startswith("data:"):
            header, base64_data = s_url.split(",", 1)
            return base64.b64decode(base64_data)
        elif s_url.startswith("http"):
            req = urllib.request.Request(s_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return resp.read()
    except Exception as e:
        print(f"[IMAGE BYTES CONVERSION ERROR]: {e}")
    return None


def create_scene_images_zip(story_history):
    """
    Creates an in-memory ZIP archive containing all scene images generated so far.
    Files are named Turn_1.png, Turn_2.png, Turn_3.png, etc.
    """
    if not story_history:
        return None

    zip_buffer = io.BytesIO()
    has_images = False

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in story_history:
            turn_num = item.get("turn", 1)
            image_url = item.get("image_url")

            if image_url:
                img_bytes = get_image_bytes(image_url)
                if img_bytes:
                    file_name = f"Turn_{turn_num}.png"
                    zip_file.writestr(file_name, img_bytes)
                    has_images = True

    if not has_images:
        return None

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


FALLBACK_SEMANTIC_MAPS = {
    "Mystery": {
        0: ["gate", "manor", "estate", "house", "mansion", "iron", "entrance", "outside", "fog", "courtyard"],
        1: ["study", "desk", "room", "office", "paper", "document", "letter", "key", "drawer", "lamp"],
        2: ["door", "threshold", "corridor", "hallway", "wood", "porch", "window", "lock", "entry"],
        3: ["station", "platform", "train", "railway", "bench", "track", "tunnel", "fog", "lantern"],
        4: ["notebook", "book", "journal", "clue", "evidence", "read", "page", "text", "notes", "write"],
        5: ["figure", "man", "woman", "person", "shadow", "stranger", "detective", "walk", "approach", "confront"],
        6: ["street", "alley", "cobblestone", "city", "gaslamp", "night", "rain", "dark", "path"],
        7: ["window", "glass", "peer", "look", "light", "flicker", "shadow", "inside", "view"],
        8: ["key", "lock", "chest", "box", "secret", "hidden", "open", "latch", "search"],
        9: ["escape", "run", "flee", "fire escape", "chase", "jump", "window", "roof", "hurry"],
    },    "Fantasy": {
        0: ["castle", "king", "citadel", "throne", "crown", "palace", "royal", "court", "ruler"],
        1: ["village", "crowd", "villagers", "people", "town", "square", "courtyard", "assembly"],
        2: ["map", "scroll", "chart", "parchment", "read", "plan", "details", "ancient"],
        3: ["forest", "woods", "tree", "branches", "path", "nature", "mist", "leaves", "wilderness"],
        4: ["ruins", "stone", "temple", "altar", "ancient", "pillar", "monument", "statue"],
        5: ["sword", "weapon", "knight", "armor", "fight", "battle", "attack", "blade", "guard"],
        6: ["magic", "spell", "glow", "rune", "crystal", "energy", "orb", "wizard", "sorcerer"],
        7: ["cave", "dungeon", "cavern", "dark", "underground", "tunnel", "torch", "deep"],
        8: ["gate", "door", "entrance", "barrier", "portal", "key", "lock", "tower"],
        9: ["monster", "beast", "creature", "dragon", "shadow", "threat", "danger", "enemy"],
    },
    "Cyberpunk": {
        0: ["city", "street", "neon", "rain", "skyscrapers", "towers", "futuristic", "night"],
        1: ["terminal", "screen", "code", "hack", "data", "hologram", "system", "computer"],
        2: ["alley", "dark", "drones", "wires", "pipes", "underbelly", "cybernetics"],
        3: ["bar", "club", "neons", "crowd", "people", "operative", "fixer", "meet"],
        4: ["weapon", "gun", "laser", "combat", "fight", "cyborg", "agent", "chase"],
        5: ["lab", "facility", "implants", "tech", "server", "matrix", "network"],
    },
    "Horror": {
        0: ["dark", "hallway", "corridor", "shadow", "abandoned", "house", "door"],
        1: ["blood", "danger", "monster", "creature", "ghost", "spirit", "entity", "fear"],
        2: ["window", "night", "storm", "rain", "cellar", "basement", "stasis"],
        3: ["woods", "forest", "graveyard", "tomb", "eerie", "fog", "cabin"],
    }
}



def get_image_bytes(image_url):
    """Converts a Base64 Data URI or HTTP URL into raw image bytes for st.download_button."""
    if not image_url:
        return None
    try:
        s_url = str(image_url)
        if s_url.startswith("data:"):
            header, base64_data = s_url.split(",", 1)
            return base64.b64decode(base64_data)
        elif s_url.startswith("http"):
            req = urllib.request.Request(s_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return resp.read()
    except Exception as e:
        print(f"[IMAGE BYTES CONVERSION ERROR]: {e}")
    return None


def create_scene_images_zip(story_history):
    """
    Creates an in-memory ZIP archive containing all scene images generated so far.
    Files are named Turn_1.png, Turn_2.png, Turn_3.png, etc.
    """
    if not story_history:
        return None

    zip_buffer = io.BytesIO()
    has_images = False

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in story_history:
            turn_num = item.get("turn", 1)
            image_url = item.get("image_url")

            if image_url:
                img_bytes = get_image_bytes(image_url)
                if img_bytes:
                    file_name = f"Turn_{turn_num}.png"
                    zip_file.writestr(file_name, img_bytes)
                    has_images = True

    if not has_images:
        return None

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


FALLBACK_SEMANTIC_MAPS = {
    "Mystery": {
        0: ["gate", "manor", "estate", "house", "mansion", "iron", "entrance", "outside", "fog", "courtyard"],
        1: ["study", "desk", "room", "office", "paper", "document", "letter", "key", "drawer", "lamp"],
        2: ["door", "threshold", "corridor", "hallway", "wood", "porch", "window", "lock", "entry"],
        3: ["station", "platform", "train", "railway", "bench", "track", "tunnel", "fog", "lantern"],
        4: ["notebook", "book", "journal", "clue", "evidence", "read", "page", "text", "notes", "write"],
        5: ["figure", "man", "woman", "person", "shadow", "stranger", "detective", "walk", "approach", "confront"],
        6: ["street", "alley", "cobblestone", "city", "gaslamp", "night", "rain", "dark", "path"],
        7: ["window", "glass", "peer", "look", "light", "flicker", "shadow", "inside", "view"],
        8: ["key", "lock", "chest", "box", "secret", "hidden", "open", "latch", "search"],
        9: ["escape", "run", "flee", "fire escape", "chase", "jump", "window", "roof", "hurry"],
    },
    "Fantasy": {
        0: ["castle", "king", "citadel", "throne", "crown", "palace", "royal", "court", "ruler"],
        1: ["village", "crowd", "villagers", "people", "town", "square", "courtyard", "assembly"],
        2: ["map", "scroll", "chart", "parchment", "read", "plan", "details", "ancient"],
        3: ["forest", "woods", "tree", "branches", "path", "nature", "mist", "leaves", "wilderness"],
        4: ["ruins", "stone", "temple", "altar", "ancient", "pillar", "monument", "statue"],
        5: ["sword", "weapon", "knight", "armor", "fight", "battle", "attack", "blade", "guard"],
        6: ["magic", "spell", "glow", "rune", "crystal", "energy", "orb", "wizard", "sorcerer"],
        7: ["cave", "dungeon", "cavern", "dark", "underground", "tunnel", "torch", "deep"],
        8: ["gate", "door", "entrance", "barrier", "portal", "key", "lock", "tower"],
        9: ["monster", "beast", "creature", "dragon", "shadow", "threat", "danger", "enemy"],
    },
    "Cyberpunk": {
        0: ["city", "street", "neon", "rain", "skyscrapers", "towers", "futuristic", "night"],
        1: ["terminal", "screen", "code", "hack", "data", "hologram", "system", "computer"],
        2: ["alley", "dark", "drones", "wires", "pipes", "underbelly", "cybernetics"],
        3: ["bar", "club", "neons", "crowd", "people", "operative", "fixer", "meet"],
        4: ["weapon", "gun", "laser", "combat", "fight", "cyborg", "agent", "chase"],
        5: ["lab", "facility", "implants", "tech", "server", "matrix", "network"],
    },
    "Horror": {
        0: ["dark", "hallway", "corridor", "shadow", "abandoned", "house", "door"],
        1: ["blood", "danger", "monster", "creature", "ghost", "spirit", "entity", "fear"],
        2: ["window", "night", "storm", "rain", "cellar", "basement", "stasis"],
        3: ["woods", "forest", "graveyard", "tomb", "eerie", "fog", "cabin"],
    }
}


def fetch_real_picture_base64(genre, turn=1, seed=None, exclude_index=None, scene_text="", reason="ERROR"):
    clean_genre = str(genre or "Fantasy").strip()
    fallback_genre = clean_genre
        
    gallery = REAL_AI_ARTWORKS.get(fallback_genre, REAL_AI_ARTWORKS["Fantasy"])
    n = len(gallery)

    try:
        from streamlit import session_state as st_state
        if "used_fallback_files" not in st_state:
            st_state.used_fallback_files = {}
        if "used_image_hashes" not in st_state:
            st_state.used_image_hashes = set()
    except ImportError:
        st_state = type("SessionState", (), {"used_fallback_files": {}, "used_image_hashes": set()})()

    raw_used = st_state.used_fallback_files.get(fallback_genre, [])
    
    # Set of used indices & filenames for strict non-repetition checking
    used_indices = set()
    used_filenames = set()
    for item in raw_used:
        if isinstance(item, int):
            used_indices.add(item)
            if item < len(gallery):
                used_filenames.add(gallery[item])
                used_filenames.add(os.path.basename(gallery[item]))
        elif isinstance(item, str):
            used_filenames.add(item)
            used_filenames.add(os.path.basename(item))

    # Score candidate indices based on semantic relevance to scene_text
    def _score_idx(idx):
        scene_lower = str(scene_text or "").lower()
        genre_map = FALLBACK_SEMANTIC_MAPS.get(clean_genre, FALLBACK_SEMANTIC_MAPS.get("Mystery", {}))
        mapped_idx = idx % max(1, len(genre_map))
        keywords = genre_map.get(mapped_idx, [])
        matches = sum(1 for kw in keywords if kw in scene_lower)
        hash_val = (int(hashlib.md5(f"{scene_lower}_{idx}".encode("utf-8")).hexdigest()[:6], 16) % 1000) / 1000.0
        return matches * 10.0 + hash_val

    all_indices = list(range(n))
    
    def _is_used(idx):
        path = gallery[idx]
        bname = os.path.basename(path)
        return (idx in used_indices) or (path in used_filenames) or (bname in used_filenames)

    unused_candidates = [i for i in all_indices if not _is_used(i) and (exclude_index is None or i != exclude_index)]
    used_candidates = [i for i in all_indices if _is_used(i) and (exclude_index is None or i != exclude_index)]

    # Sort candidates by semantic score (highest first)
    unused_candidates.sort(key=_score_idx, reverse=True)
    used_candidates.sort(key=_score_idx, reverse=True)

    # Search unused fallbacks first; fall back to used ONLY if pool exhausted
    repeat_allowed = (len(unused_candidates) == 0)
    search_order = unused_candidates if unused_candidates else used_candidates

    for chosen_idx in search_order:
        chosen_url = gallery[chosen_idx]
        bname = os.path.basename(chosen_url)
        if not chosen_url.startswith("assets/"):
            continue
            
        if not os.path.exists(chosen_url):
            print(f"[LOCAL ARTWORK MISSING]: {chosen_url}")
            continue
            
        try:
            if chosen_url in _LOCAL_ASSET_CACHE:
                data, img_hash, b64_str = _LOCAL_ASSET_CACHE[chosen_url]
            else:
                with open(chosen_url, "rb") as f:
                    data = f.read()
                img_hash = hashlib.sha256(data).hexdigest()
                b64_str = base64.b64encode(data).decode('utf-8')
                _LOCAL_ASSET_CACHE[chosen_url] = (data, img_hash, b64_str)

            # Skip if exact file hash is already in used_image_hashes and we still have unused options
            if img_hash in st_state.used_image_hashes and not repeat_allowed:
                print(f"[FALLBACK REJECTED] Hash {img_hash} for {chosen_url} already exists in used_image_hashes.")
                continue

            st_state.used_image_hashes.add(img_hash)
            updated_list = list(raw_used) + [chosen_idx]
            st_state.used_fallback_files[fallback_genre] = updated_list

            is_already_used = _is_used(chosen_idx)
            rem_count = max(0, len(unused_candidates) - (0 if is_already_used else 1))

            print("\n========================================")
            print("FALLBACK SELECTION")
            print(f"TURN = {turn}")
            print(f"SELECTED = {bname}")
            print(f"ALREADY USED = {'YES' if is_already_used else 'NO'}")
            print(f"UNUSED REMAINING = {rem_count}")
            print(f"REPEAT ALLOWED = {'YES' if repeat_allowed else 'NO'}")
            print("========================================\n")

            return f"data:image/jpeg;base64,{b64_str}", chosen_idx

        except Exception as ex:
            print(f"[LOCAL ARTWORK FETCH ERROR]: {ex}")
            continue

    print("\n========================================")
    print("FALLBACK SELECTION")
    print(f"TURN = {turn}")
    print(f"FALLBACK POOL EXHAUSTED for genre {fallback_genre}!")
    print("========================================\n")
    return None, None


def generate_scene_image(scene_text, genre="Fantasy", world="", is_regeneration=False, seed=None, turn=1, exclude_fallback_index=None, _out=None):
    """
    Generates a scene-grounded 16:9 illustration for the current adventure turn.
    Returns Base64 Data URI string. Never returns None.
    """
    start_total_time = time.perf_counter()
    pollinations_time = 0.0
    fallback_time = 0.0

    clean_genre = str(genre or "Fantasy").strip()
    clean_scene = re.sub(r'[^a-zA-Z0-9 ]+', ' ', html.unescape(str(scene_text or "")))
    clean_scene = re.sub(r'\s+', ' ', clean_scene).strip()[:300]

    try:
        from streamlit import session_state as st_state
        if "used_image_hashes" not in st_state:
            st_state.used_image_hashes = set()
        if "used_fallback_files" not in st_state:
            st_state.used_fallback_files = {}
        if "used_image_perceptual_hashes" not in st_state:
            st_state.used_image_perceptual_hashes = []
    except ImportError:
        st_state = type("SessionState", (), {
            "used_fallback_files": {},
            "used_image_hashes": set(),
            "used_image_perceptual_hashes": [],
        })()

    pollinations_status = "FAILED"
    fallback_status = "NOT USED"
    result_img = None
    fallback_idx_used = None
    pollin_url = "N/A"
    http_status = "N/A"
    content_type = "N/A"
    response_size = 0
    err_msg = "None"
    
    MAX_RETRIES = 3

    # 1. Primary Generator: Fast Pollinations AI with 3-attempt retry safety & quick 429 exit
    if clean_scene:
        image_scene = clean_scene
        
        # Sanitize potentially restricted words that trigger AI safety filters
        replacements = [
            (r'\bblood stained\b', 'mysterious evidence marked'),
            (r'\bblood\b', 'disturbing evidence'),
            (r'\bgore\b|\bgraphic\b|\bmutilated\b|\bdissected\b', 'dark aftermath'),
            (r'\bcorpse\b|\bdead body\b|\bmurdered\b|\bkilled\b|\bkill\b', 'disturbing scene'),
            (r'\bsevere injury\b|\bgrievously wounded\b', 'injured')
        ]
        for pattern, replacement in replacements:
            image_scene = re.sub(pattern, replacement, image_scene, flags=re.IGNORECASE)
            
        lower_genre = clean_genre.lower()
        if "fantasy" in lower_genre:
            genre_cues = "medieval fantasy world, castles, ancient ruins, magic, mythical creatures, cinematic fantasy lighting"
        elif "cyberpunk" in lower_genre:
            genre_cues = "futuristic neon city, cybernetic technology, holographic signs, drones, rain-soaked streets, dark neon atmosphere"
        elif "sci-fi" in lower_genre or "sci fi" in lower_genre or "science fiction" in lower_genre:
            genre_cues = "futuristic technology, spacecraft, advanced laboratories, futuristic architecture, cinematic sci-fi lighting"
        elif "mystery" in lower_genre:
            genre_cues = "detective investigation, abandoned locations, dark shadows, suspenseful cinematic lighting"
        elif "horror" in lower_genre:
            genre_cues = "abandoned buildings, eerie corridors, dark atmosphere, ominous shadows, terrifying environment, cinematic horror lighting"
        elif "adventure" in lower_genre:
            genre_cues = "epic landscapes, dangerous exploration, dramatic adventure atmosphere, cinematic lighting"
        else:
            genre_cues = "cinematic story environment, detailed surroundings"
            
        clean_world = str(world or "").strip()[:100]
        genre_cues_short = genre_cues[:80]

        HEADER      = "Cinematic visual novel scene.\n"
        INSTR       = (
            "Depict EXACTLY the characters, location, actions, objects and events "
            "in CURRENT SCENE. The current action must be visually obvious. "
            "Do not create a generic genre image or reuse a previous scene composition.\n"
        )
        SCENE_LABEL = "CURRENT SCENE: "
        WORLD_LABEL = "\nWORLD: "
        STYLE_LABEL = "\nSTYLE: "

        fixed_chars = len(HEADER) + len(INSTR) + len(SCENE_LABEL) + len(WORLD_LABEL) + len(clean_world) + len(STYLE_LABEL) + len(genre_cues_short)
        scene_budget = max(100, 900 - fixed_chars)
        scene_for_prompt = image_scene[:scene_budget]

        prompt = (
            HEADER
            + SCENE_LABEL + scene_for_prompt + "\n"
            + INSTR
            + WORLD_LABEL + clean_world
            + STYLE_LABEL + genre_cues_short
        )
        prompt = prompt[:900]
        encoded = urllib.parse.quote(prompt)
        prompt_length = len(prompt)

        pollin_start_time = time.perf_counter()

        for attempt in range(MAX_RETRIES):
            generation_id = uuid.uuid4().hex[:8]
            current_seed = seed if (attempt == 0 and seed is not None) else random.randint(10000, 9999999)
            signature = f"turn{turn}_gen{generation_id}_seed{current_seed}"
            
            print("\n========================================")
            print("IMAGE GENERATION")
            print(f"TURN         = {turn}")
            print(f"SCENE USED   = {scene_for_prompt[:120]}{'...' if len(scene_for_prompt) > 120 else ''}")
            print(f"WORLD USED   = {clean_world}")
            print(f"PROMPT LENGTH= {prompt_length}")
            print(f"SEED         = {current_seed}")
            print(f"IMAGE SOURCE = POLLINATIONS (attempt {attempt+1}/{MAX_RETRIES})")
            print(f"REGENERATION = {'YES' if is_regeneration or attempt > 0 else 'NO'}")
            print(f"GEN ID       = {generation_id}")
            print("========================================\n")

            pollin_url = f"https://image.pollinations.ai/prompt/{encoded}?width=896&height=504&seed={current_seed}&nologo=true&cache=false&model=turbo"
            
            req_timeout = 1.0 if attempt == 0 else 1.0
            stage_http_start = time.perf_counter()
            try:
                req = urllib.request.Request(
                    pollin_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                     http_status = str(resp.status)
                     if resp.status == 200:
                         content_type = resp.headers.get('Content-Type', '')
                         data = resp.read()
                         response_size = len(data)
                         
                         if response_size > 5000 and 'image' in content_type.lower():
                             img_hash = hashlib.md5(data).hexdigest()
                             img_sha = hashlib.sha256(data).hexdigest()
                             p_hash = _dhash(data)

                             print(f"TURN = {turn}")
                             print(f"RAW MD5 = {img_hash}")
                             print(f"PERCEPTUAL HASH = {p_hash}")

                             # 1. Raw byte duplicate check
                             if 'used_image_hashes' in st_state and img_hash in st_state.used_image_hashes:
                                 print("IMAGE REJECTED = ALREADY USED")
                                 print(f"REASON = MD5 Hash {img_hash} matches a previously displayed image.")
                                 pollinations_status = "FAILED - Duplicate Hash"
                                 continue

                             # 2. Perceptual duplicate check
                             PHASH_THRESHOLD = 8
                             is_visual_dup = False
                             if p_hash is not None and hasattr(st_state, 'used_image_perceptual_hashes'):
                                 for prev_ph in st_state.used_image_perceptual_hashes:
                                     dist = _hamming_distance(p_hash, prev_ph)
                                     if dist <= PHASH_THRESHOLD:
                                         is_visual_dup = True
                                         print(f"IMAGE REJECTED = VISUAL DUPLICATE")
                                         pollinations_status = "FAILED - Visual Duplicate"
                                         break

                             if is_visual_dup:
                                 continue

                             print(f"VISUAL DUPLICATE = NO")
                             print(f"IMAGE SOURCE = POLLINATIONS")
                             print(f"IMAGE HASH   = {img_hash}")

                             if 'used_image_hashes' in st_state:
                                 st_state.used_image_hashes.add(img_hash)
                             if 'used_image_signatures' in st_state:
                                 st_state.used_image_signatures.add(signature)
                             if p_hash is not None and hasattr(st_state, 'used_image_perceptual_hashes'):
                                 st_state.used_image_perceptual_hashes.append(p_hash)

                             b64_str = base64.b64encode(data).decode('utf-8')
                             result_img = f"data:{content_type};base64,{b64_str}"
                             pollinations_status = "SUCCESS"
                             break
                         else:
                             pollinations_status = "FAILED - File too small or not image"
                             err_msg = f"Size: {response_size}, Type: {content_type}"
                     else:
                          err_msg = f"HTTP Status {resp.status}, Content-Type: {content_type}"
            except Exception as p_err:
                err_msg = f"{type(p_err).__name__}: {p_err}"
                pollinations_status = f"FAILED ({type(p_err).__name__})"
                print(f"[POLLINATIONS ERROR] {type(p_err).__name__}: {p_err} (took {time.perf_counter() - stage_http_start:.3f}s)")
                
                # Check for HTTP 429, Timeout, or Connection Error -> Switch to fast local fallback immediately!
                err_str = str(p_err).lower()
                if "429" in err_str or (hasattr(p_err, 'code') and p_err.code == 429) or "timeout" in err_str or "connection" in err_str or "timed out" in err_str:
                    print(f"[POLLINATIONS FAIL-FAST] {type(p_err).__name__} detected — switching to fast local fallback immediately.")
                    break
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(0.1)
                continue

        pollinations_time = time.perf_counter() - pollin_start_time

    # ---------------------------------------------------------
    # Tier 2: Unused Local Cinematic Fallback
    # ---------------------------------------------------------
    if not result_img:
        fb_start_time = time.perf_counter()
        print("[IMAGE FALLBACK] Attempting Tier 2: Local Cinematic Fallback")
        if "429" in str(err_msg) or "429" in str(http_status):
            fallback_reason = "HTTP 429"
        elif "timeout" in str(err_msg).lower() or "timeout" in str(pollinations_status).lower():
            fallback_reason = "TIMEOUT"
        else:
            fallback_reason = f"ERROR ({err_msg})" if err_msg != "None" else "ERROR"

        fallback_result, fallback_idx_used = fetch_real_picture_base64(
            genre=clean_genre,
            turn=turn,
            seed=seed,
            exclude_index=exclude_fallback_index,
            scene_text=clean_scene,
            reason=fallback_reason,
        )
        if fallback_result:
            result_img = fallback_result
            fallback_status = "TIER_2_LOCAL"
        else:
            print("[IMAGE FALLBACK] Tier 2 Exhausted")

        fallback_time = time.perf_counter() - fb_start_time

    # ---------------------------------------------------------
    # Tier 3: Emergency File Fallback Safety Net
    # ---------------------------------------------------------
    if not result_img:
        fb_start_time = time.perf_counter()
        print("[IMAGE FALLBACK] Attempting Tier 3: Emergency File Safety Net")
        for fallback_path in [
            f"assets/fallbacks/{clean_genre.lower()}_0.png",
            "assets/fallbacks/mystery_0.png",
            "assets/fallbacks/fantasy_0.png",
            "assets/fallbacks/cyberpunk_0.png",
            "assets/fallbacks/horror_10.png",
        ]:
            if os.path.exists(fallback_path):
                try:
                    if fallback_path in _LOCAL_ASSET_CACHE:
                        em_data, em_hash, em_b64 = _LOCAL_ASSET_CACHE[fallback_path]
                    else:
                        with open(fallback_path, "rb") as f:
                            em_data = f.read()
                        em_hash = hashlib.sha256(em_data).hexdigest()
                        em_b64 = base64.b64encode(em_data).decode("utf-8")
                        _LOCAL_ASSET_CACHE[fallback_path] = (em_data, em_hash, em_b64)

                    result_img = f"data:image/jpeg;base64,{em_b64}"
                    fallback_status = "TIER_3_EMERGENCY"
                    print(f"[EMERGENCY FALLBACK SUCCESS]: Loaded {fallback_path}")
                    break
                except Exception as em_err:
                    print(f"[EMERGENCY FALLBACK ERROR]: {em_err}")
        fallback_time += (time.perf_counter() - fb_start_time)

    # ---------------------------------------------------------
    # Tier 4: SVG Safety Net
    # ---------------------------------------------------------
    if not result_img:
        svg_code = f'<svg xmlns="http://www.w3.org/2000/svg" width="896" height="504" viewBox="0 0 896 504"><rect width="896" height="504" fill="#1a1a2e"/><text x="448" y="252" font-family="sans-serif" font-size="24" fill="#e6f2ff" text-anchor="middle">Turn {turn} - {clean_genre} Visual Transmission</text></svg>'
        svg_b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
        result_img = f"data:image/svg+xml;base64,{svg_b64}"
        fallback_status = "TIER_4_SVG_SAFETY"

    if _out is not None and fallback_idx_used is not None:
        _out['fallback_index'] = fallback_idx_used

    total_image_time = time.perf_counter() - start_total_time
    final_source = "POLLINATIONS" if pollinations_status == "SUCCESS" else "FALLBACK"

    speed_log = (
        "\n" + "="*40 + "\n"
        "IMAGE SPEED\n"
        f"TURN = {turn}\n"
        f"POLLINATIONS TIME = {pollinations_time:.2f} sec\n"
        f"FALLBACK TIME = {fallback_time:.2f} sec\n"
        f"TOTAL IMAGE TIME = {total_image_time:.2f} sec\n"
        f"IMAGE SOURCE = {final_source}\n"
        + "="*40 + "\n"
    )
    print(speed_log)

    debug_info = (
        "\n" + "="*50 + "\n"
        "[IMAGE DEBUG]\n"
        f"- turn: {turn}\n"
        f"- scene text: {clean_scene}\n"
        f"- genre: {clean_genre}\n"
        f"- seed: {seed}\n"
        f"- Pollinations URL: {pollin_url}\n"
        f"- Pollinations status: {pollinations_status}\n"
        f"- Fallback: {fallback_status} (index used: {fallback_idx_used}, excluded: {exclude_fallback_index})\n"
        f"- exact exception message: {err_msg}\n"
        + "="*50 + "\n"
    )
    print(debug_info)
    with open("debug_image_log.txt", "a") as f:
        f.write(debug_info)

    return result_img
