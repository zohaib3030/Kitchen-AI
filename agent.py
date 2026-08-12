import os
import json

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing.")


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY,
    timeout=90.0
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are KitchenAI, a recipe research assistant.

Your task is to find a REAL recipe online using:

1. The user's cooking request.
2. Ingredients detected from their kitchen image.

You MUST use browser search.

Use the web results as the source of truth.

Do not invent websites or sources.

Do not expose chain-of-thought.

Use these principles internally:
- role prompting
- context injection
- task decomposition
- constraint satisfaction
- retrieval-augmented generation
- grounded generation
- uncertainty handling
- hallucination mitigation

Return a concise answer.

Format:

## 🍳 Recipe

Recipe name.

### Why?
One or two sentences.

### 🥕 You Have
List available ingredients.

### 🛒 You Need
List important missing ingredients.

### 👨‍🍳 Steps
Give concise numbered steps.

### ⏱️ Time
Give total cooking time.

### 🌐 Source
Give the source from the search.

Do not provide unnecessary explanations.
"""


# ============================================================
# PREPARE INGREDIENTS
# ============================================================

def prepare_ingredients(image_analysis):

    if not isinstance(image_analysis, dict):

        return str(image_analysis)[:1500]

    ingredients = image_analysis.get(
        "ingredients",
        []
    )

    confirmed = []

    for item in ingredients:

        if not isinstance(item, dict):
            continue

        name = item.get("name")

        quantity = item.get(
            "quantity",
            "unknown"
        )

        confidence = item.get(
            "confidence",
            0
        )

        try:
            confidence = float(confidence)
        except:
            confidence = 0

        if (
            name
            and
            confidence >= 0.70
        ):

            confirmed.append(
                f"{name} ({quantity})"
            )

    return ", ".join(
        confirmed[:15]
    )


# ============================================================
# KITCHEN AGENT
# ============================================================

def kitchen_agent(
    voice_transcript,
    image_analysis
):

    voice = str(
        voice_transcript
    ).strip()

    voice = voice[:1000]

    ingredients = prepare_ingredients(
        image_analysis
    )


    # --------------------------------------------------------
    # SMALL PROMPT
    # --------------------------------------------------------

    user_prompt = f"""
User request:
{voice}

Available ingredients:
{ingredients}

Search the web for ONE real recipe that best matches
the user's request and available ingredients.

Prefer recipes that use the ingredients already available.

After searching, give the recipe in the requested format.
"""


    print("\n==============================")
    print("KITCHEN AGENT STARTED")
    print("==============================")

    print("User:", voice)

    print("Ingredients:", ingredients)

    print("Searching web...")


    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],

            tools=[
                {
                    "type": "browser_search"
                }
            ],

            tool_choice="required",

            # Keep output small
            max_completion_tokens=1200,

            stream=False
        )


        message = (
            response
            .choices[0]
            .message
        )

        answer = (
            message.content
            or
            ""
        )


        print("\n==============================")
        print("RECIPE SEARCH COMPLETED")
        print("==============================")

        print(answer)


        return {
            "answer": answer,
            "executed_tools": getattr(
                message,
                "executed_tools",
                []
            )
        }


    except Exception as e:

        print("\n==============================")
        print("KITCHEN AGENT ERROR")
        print("==============================")

        print(repr(e))


        return {
            "answer": "",
            "executed_tools": [],
            "error": str(e)
        }