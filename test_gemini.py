import os
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)

key = os.getenv("GEMINI_API_KEY")
print("KEY FOUND:", bool(key))
print("KEY LENGTH:", len(key) if key else 0)

if not key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit()

client = genai.Client(api_key=key)

test_models = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview"
]

for model_name in test_models:
    print(f"\n--- Testing model: {model_name} ---")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say hello in 3 words."
        )
        print(f"SUCCESS [{model_name}]:", response.text.strip() if response and response.text else "EMPTY")
    except Exception as e:
        print(f"FAILED [{model_name}]: {type(e).__name__}: {e}")