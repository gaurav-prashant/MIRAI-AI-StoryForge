import urllib.request
from utils.image_generator import REAL_AI_ARTWORKS

def verify_all_urls():
    for genre, urls in REAL_AI_ARTWORKS.items():
        print(f"\n--- Checking Genre: {genre} ---")
        for i, url in enumerate(urls):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        print(f"[OK] {genre} [{i}]: {url[:60]}")
                    else:
                        print(f"[BAD {resp.status}] {genre} [{i}]: {url}")
            except Exception as e:
                print(f"[ERROR {e}] {genre} [{i}]: {url}")

if __name__ == "__main__":
    verify_all_urls()
