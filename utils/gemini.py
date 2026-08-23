import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv(override=True)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in .env file."
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=API_KEY
)


# =========================================================
# MODEL CONFIGURATION
# =========================================================

MODEL_NAME = "gemini-3.5-flash-lite"
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]


# =========================================================
# JSON SCHEMA
# =========================================================

STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "scene": {
            "type": "string"
        },
        "scene_hindi": {
            "type": "string"
        },
        "narration_en": {
            "type": "string"
        },
        "narration_hi": {
            "type": "string"
        },
        "choices": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "health_change": {
            "type": "integer"
        },
        "xp_change": {
            "type": "integer"
        },
        "gold_change": {
            "type": "integer"
        },
        "item": {
            "type": "string"
        },
        "clue": {
            "type": "string"
        },
        "relationship_change": {
            "type": "object",
            "properties": {
                "character": {"type": "string"},
                "trust_change": {"type": "integer"},
                "event": {"type": "string"}
            }
        },
        "quest_update": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "objective_completed": {"type": "string"},
                "status": {"type": "string"}
            }
        },
        "story_event": {
            "type": "string"
        }
    },
    "required": [
        "scene",
        "scene_hindi",
        "choices",
        "health_change",
        "xp_change",
        "gold_change",
        "item",
        "clue"
    ]
}





# =========================================================
# GENERATE CONTENT (OPTIMIZED FOR LOW LATENCY)
# =========================================================

def generate_content(prompt):

    models_to_try = [MODEL_NAME] + [m for m in FALLBACK_MODELS if m != MODEL_NAME]
    last_exception = None

    for current_model in models_to_try:

        max_retries = 2

        for attempt in range(max_retries):

            try:

                response = client.models.generate_content(

                    model=current_model,

                    contents=prompt,

                    config=types.GenerateContentConfig(

                        max_output_tokens=700,

                        response_mime_type="application/json",

                        response_schema=STORY_SCHEMA,

                    ),
                )

                # -------------------------------------------------
                # CHECK RESPONSE
                # -------------------------------------------------

                if response and response.text:

                    return response.text.strip()

                raise ValueError(
                    "Gemini returned an empty response."
                )

            except Exception as e:

                last_exception = e

                error_text = str(e)

                # If model is unavailable/not found, try next fallback model
                if ("404" in error_text or "NOT_FOUND" in error_text) and current_model != models_to_try[-1]:
                    break

                # Rate Limit / Server Error
                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "503" in error_text
                    or "UNAVAILABLE" in error_text
                ):

                    if attempt < max_retries - 1:

                        wait_time = 2 * (attempt + 1)

                        time.sleep(wait_time)

                        continue

                # If not retryable on this model, break to fallback
                if attempt == max_retries - 1 and current_model != models_to_try[-1]:
                    break

    raise ValueError(
        f"Gemini API generation failed: {type(last_exception).__name__}: {last_exception}"
    )