import os
import base64
import json
import re

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Please add it to your .env file."
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=api_key
)


# ============================================================
# VISION PROMPT
# ============================================================

VISION_PROMPT = """
ROLE:
You are KitchenAI's Vision Analysis Agent.

OBJECTIVE:
Analyze the kitchen image and identify visible food ingredients
and useful kitchen items.

TASK:

1. Identify clearly visible ingredients.
2. Estimate quantity when visually reasonable.
3. Give a confidence score between 0 and 1.
4. Identify useful kitchen items.
5. Put unclear objects into uncertain_items.

VISUAL GROUNDING RULES:

- Only identify objects supported by visual evidence.
- Never hallucinate hidden ingredients.
- Do not infer ingredients from common recipes.
- Do not assume an ingredient exists because another ingredient
  is commonly paired with it.
- If identification is uncertain, put it in uncertain_items.
- Confidence must represent visual certainty.

OUTPUT RULE:

Return ONLY a valid JSON object.

Do NOT output:
- reasoning
- analysis
- chain of thought
- <think>
- </think>
- markdown
- ```json
- explanations before or after JSON

The response MUST follow this structure:

{
    "ingredients": [
        {
            "name": "red bell pepper",
            "quantity": "1",
            "confidence": 0.95
        }
    ],
    "kitchen_items": [
        "olive oil"
    ],
    "uncertain_items": []
}
"""


# ============================================================
# JSON CLEANER
# ============================================================

def clean_json_response(text):
    """
    Convert model output into a Python dictionary.
    """

    if not text:
        return None

    text = text.strip()

    # ----------------------------------------
    # Remove accidental <think> blocks
    # ----------------------------------------

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # ----------------------------------------
    # Remove markdown code fences
    # ----------------------------------------

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # ----------------------------------------
    # Extract JSON object
    # ----------------------------------------

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    json_text = text[
        start:end + 1
    ]

    # ----------------------------------------
    # Parse JSON
    # ----------------------------------------

    try:

        return json.loads(
            json_text
        )

    except json.JSONDecodeError:

        return None


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(
    image_bytes,
    image_type="image/jpeg"
):
    """
    Analyze an uploaded kitchen image using
    Qwen 3.6 27B Vision through Groq.
    """

    # ----------------------------------------
    # Base64 encode image
    # ----------------------------------------

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    # ----------------------------------------
    # Build data URL
    # ----------------------------------------

    image_url = (
        f"data:{image_type};base64,"
        f"{encoded_image}"
    )


    try:

        # ------------------------------------
        # Groq Vision Request
        # ------------------------------------

        response = client.chat.completions.create(

            model="qwen/qwen3.6-27b",

            messages=[
                {
                    "role": "system",
                    "content": VISION_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Carefully inspect this image "
                                "and identify the visible "
                                "kitchen ingredients."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],

            # --------------------------------
            # JSON MODE
            # --------------------------------

            response_format={
                "type": "json_object"
            },

            # --------------------------------
            # Hide Qwen reasoning
            # --------------------------------

            reasoning_format="hidden",

            reasoning_effort="none",

            # --------------------------------
            # Generation settings
            # --------------------------------

            temperature=0.7,

            max_completion_tokens=1200,

            stream=False
        )


        # ------------------------------------
        # Get model output
        # ------------------------------------

        raw_result = (
            response
            .choices[0]
            .message
            .content
        )


        # ------------------------------------
        # Parse JSON
        # ------------------------------------

        result = clean_json_response(
            raw_result
        )


        # ------------------------------------
        # Handle invalid JSON
        # ------------------------------------

        if result is None:

            return {
                "ingredients": [],
                "kitchen_items": [],
                "uncertain_items": [],
                "error": (
                    "Vision model returned an "
                    "invalid JSON response."
                ),
                "raw_response": raw_result
            }


        # ------------------------------------
        # Ensure required fields
        # ------------------------------------

        result.setdefault(
            "ingredients",
            []
        )

        result.setdefault(
            "kitchen_items",
            []
        )

        result.setdefault(
            "uncertain_items",
            []
        )


        return result


    except Exception as e:

        return {
            "ingredients": [],
            "kitchen_items": [],
            "uncertain_items": [],
            "error": str(e)
        }
