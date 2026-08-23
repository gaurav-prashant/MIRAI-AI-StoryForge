import urllib.request
import urllib.parse
import re

def clean_prompt_for_url(text):
    """Cleans text so it only contains alphanumeric characters and simple spaces for image prompt URL safety."""
    if not text:
        return ""
    # Strip non-alphanumeric except spaces
    clean = re.sub(r'[^a-zA-Z0-9 ]+', ' ', str(text))
    # Collapse multiple spaces
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def test_special_chars():
    raw_prompt = 'Arpita lunges forward, forcefully shoving past Julian before he can react. "Get back!" he yells, catching completely off guard...'
    
    # Uncleaned vs Cleaned
    prompt_bad = f"Cinematic visual novel scene, Fantasy genre, world of Oakhaven, {raw_prompt[:120]}, digital art"
    encoded_bad = urllib.parse.quote(prompt_bad)
    url_bad = f"https://image.pollinations.ai/prompt/{encoded_bad}?width=800&height=450&nologo=true"
    
    cleaned_text = clean_prompt_for_url(raw_prompt[:100])
    prompt_good = f"Cinematic visual novel scene illustration Fantasy genre world of Oakhaven {cleaned_text} digital art high quality"
    encoded_good = urllib.parse.quote(prompt_good)
    url_good = f"https://image.pollinations.ai/prompt/{encoded_good}?width=800&height=450&nologo=true"

    print("Testing BAD URL...")
    try:
        req = urllib.request.Request(url_bad, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=8)
        print(f"[BAD URL] Status: {res.status}, Type: {res.headers.get('Content-Type')}")
    except Exception as e:
        print(f"[BAD URL FAILED] Error: {e}")

    print("Testing GOOD URL...")
    try:
        req = urllib.request.Request(url_good, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=8)
        print(f"[GOOD URL SUCCESS] Status: {res.status}, Type: {res.headers.get('Content-Type')}")
    except Exception as e:
        print(f"[GOOD URL FAILED] Error: {e}")

if __name__ == "__main__":
    test_special_chars()
