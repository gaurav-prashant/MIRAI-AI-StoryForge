import urllib.request
import urllib.parse
import base64

def test_fetch_pollinations():
    prompt = "cinematic visual novel illustration King sits upon wooden throne surrounded by villagers fantasy RPG digital art"
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576&seed=101&nologo=true"
    
    print(f"Fetching: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            print(f"[SUCCESS] Downloaded {len(data)} bytes! Content-Type: {resp.headers.get('Content-Type')}")
            b64 = base64.b64encode(data).decode('utf-8')
            print("Base64 prefix:", b64[:50])
            return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

if __name__ == "__main__":
    test_fetch_pollinations()
