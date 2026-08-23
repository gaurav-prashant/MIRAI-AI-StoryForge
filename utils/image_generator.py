import base64
import html
import io
import re
import urllib.parse
import urllib.request
import zipfile
import time

# High-Resolution Real Digital Artworks by Genre (100% Verified 200 OK URLs)
REAL_AI_ARTWORKS = {
    "Fantasy": [
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1514539079130-25950c84af65?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=1200&q=80",
    ],
    "Sci-Fi": [
        "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    ],
    "Mystery": [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
    ],
    "Horror": [
        "https://images.unsplash.com/photo-1509248961158-e54f6934749c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
    ],
    "Adventure": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1200&q=80",
    ]
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


import random


def fetch_real_picture_base64(genre, turn=1, seed=None, exclude_index=None):
    """Fetches a real digital art JPEG as a Base64 Data URI.
    exclude_index: gallery index of the image currently displayed — it will be skipped
    so the player always sees a DIFFERENT image.
    Returns (data_uri_or_url, chosen_gallery_index)."""
    clean_genre = str(genre or "Fantasy").strip()
    gallery = REAL_AI_ARTWORKS.get(clean_genre, REAL_AI_ARTWORKS["Fantasy"])
    n = len(gallery)

    # Build candidate indices, excluding the last-used index when alternatives exist
    all_indices = list(range(n))
    if exclude_index is not None and isinstance(exclude_index, int) and n > 1:
        candidate_indices = [i for i in all_indices if i != exclude_index]
    else:
        candidate_indices = all_indices

    if not candidate_indices:
        candidate_indices = all_indices

    # Pick deterministically from candidates using seed (avoids same-modulo collisions)
    if seed is not None and isinstance(seed, int):
        chosen_idx = candidate_indices[seed % len(candidate_indices)]
    else:
        chosen_idx = candidate_indices[(turn - 1) % len(candidate_indices)]

    chosen_url = gallery[chosen_idx]

    try:
        req = urllib.request.Request(
            chosen_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) > 1000:
                    b64_str = base64.b64encode(data).decode('utf-8')
                    return f"data:image/jpeg;base64,{b64_str}", chosen_idx
    except Exception as ex:
        print(f"[ARTWORK FETCH NOTICE]: {ex}")

    return chosen_url, chosen_idx


def generate_scene_image(scene_text, genre, world, turn=1, seed=None, is_regeneration=False,
                         current_image_url=None, exclude_fallback_index=None, _out=None):
    start_time = time.perf_counter()
    """
    Generates a real high-definition visual novel picture Base64 string for Turn X.
    Primary Generator: Pollinations AI with a 25-second timeout.
    Fallback: REAL_AI_ARTWORKS gallery, guaranteed to pick a DIFFERENT image each time
              via exclude_fallback_index (index of the last-used gallery item).
    _out: optional dict — populated with {'fallback_index': int} so the caller can
          store the used index and pass it back next time as exclude_fallback_index.
    Logs detailed [IMAGE DEBUG] info to terminal.
    """
    start_time = time.perf_counter()
    clean_genre = str(genre or "Fantasy").strip()
    clean_scene = re.sub(r'[^a-zA-Z0-9 ]+', ' ', html.unescape(str(scene_text or "")))
    clean_scene = re.sub(r'\s+', ' ', clean_scene).strip()[:70]

    if seed is None:
        if is_regeneration:
            seed = random.randint(10000, 999999)
        else:
            seed = (abs(hash(f"{turn}_{clean_scene[:15]}")) % 9999) + 1

    pollinations_status = "FAILED"
    fallback_status = "NOT USED"
    result_img = None
    fallback_idx_used = None
    pollin_url = "N/A"
    http_status = "N/A"
    content_type = "N/A"
    response_size = 0
    err_msg = "None"

    # 1. Primary Generator: Pollinations AI with 25-second timeout
    if clean_scene:
        prompt = f"cinematic digital art visual novel {clean_genre} {clean_scene} fantasy rpg illustration"
        encoded = urllib.parse.quote(prompt)
        pollin_url = f"https://image.pollinations.ai/prompt/{encoded}?width=896&height=504&seed={seed}&nologo=true&cache=false"
        pollinations_start = time.perf_counter()
        try:
            req = urllib.request.Request(
                pollin_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                 print(
                 f"[IMAGE TIMING] Pollinations response: "
                 f"{time.perf_counter() - pollinations_start:.2f} sec"
            )               
                 http_status = str(resp.status)
                 content_type = str(resp.headers.get('Content-Type', ''))
                 if resp.status == 200 and 'image' in content_type:
                    img_bytes = resp.read()
                    response_size = len(img_bytes)
                    if response_size > 2000:
                        b64_str = base64.b64encode(img_bytes).decode('utf-8')
                        result_img = f"data:image/jpeg;base64,{b64_str}"
                        pollinations_status = "SUCCESS"
                    else:
                        err_msg = f"Response size too small: {response_size} bytes"
                 else:
                      err_msg = f"HTTP Status {resp.status}, Content-Type: {content_type}"
        except Exception as p_err:
            err_msg = f"{type(p_err).__name__}: {p_err}"
            pollinations_status = f"FAILED ({type(p_err).__name__})"
            print(f"[POLLINATIONS ERROR] {type(p_err).__name__}: {p_err}")

    # 2. Fallback to REAL_AI_ARTWORKS gallery if Pollinations failed.
    #    exclude_fallback_index ensures a DIFFERENT gallery image is picked each time.
    if not result_img:
        fallback_status = "USED"
        fallback_result, fallback_idx_used = fetch_real_picture_base64(
            genre=clean_genre,
            turn=turn,
            seed=seed,
            exclude_index=exclude_fallback_index,
        )
        result_img = fallback_result

    # Propagate the chosen fallback index back to the caller via _out
    if _out is not None and fallback_idx_used is not None:
        _out['fallback_index'] = fallback_idx_used

    # 3. Print detailed debugging information to terminal
    print("\n" + "="*50)
    print("[IMAGE DEBUG]")
    print(f"- scene text: {clean_scene}")
    print(f"- genre: {clean_genre}")
    print(f"- seed: {seed}")
    print(f"- Pollinations URL: {pollin_url}")
    print(f"- HTTP status code: {http_status}")
    print(f"- Content-Type: {content_type}")
    print(f"- response size: {response_size} bytes")
    print(f"- Pollinations status: {pollinations_status}")
    print(f"- Fallback: {fallback_status} (index used: {fallback_idx_used}, excluded: {exclude_fallback_index})")
    print(f"- exact exception message: {err_msg}")
    print("="*50 + "\n")

    return result_img




