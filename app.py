import os
import io

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from vision import analyze_image
from agent import kitchen_agent


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing from your .env file.")
    st.stop()


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY,
    timeout=90.0
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="KitchenAI",
    page_icon="👨‍🍳",
    layout="centered"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .kitchen-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
        color: #18233a;
    }

    .kitchen-subtitle {
        font-size: 18px;
        color: #667085;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 28px;
        font-weight: 700;
        color: #18233a;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .recipe-box {
        background: #ffffff;
        border-radius: 15px;
        padding: 25px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-top: 15px;
    }

    .status-box {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

if "image_analysis" not in st.session_state:
    st.session_state.image_analysis = None

if "recipe_result" not in st.session_state:
    st.session_state.recipe_result = None

if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

if "image_type" not in st.session_state:
    st.session_state.image_type = "image/jpeg"


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="kitchen-title">👨‍🍳 KitchenAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="kitchen-subtitle">'
    'Your multimodal kitchen assistant — speak, show your ingredients, and discover what you can cook.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# VOICE INPUT
# ============================================================

st.markdown(
    '<div class="section-title">🎤 Tell KitchenAI What You Want</div>',
    unsafe_allow_html=True
)

st.write(
    "Describe the meal you want, your dietary preference, "
    "or any cooking constraint."
)

audio_value = st.audio_input(
    "Record your cooking request"
)


# ============================================================
# TRANSCRIBE VOICE
# ============================================================

if audio_value is not None:

    try:

        audio_bytes = audio_value.getvalue()

        with st.spinner(
            "🎤 Understanding your voice..."
        ):

            transcription = client.audio.transcriptions.create(
                file=(
                    "voice.wav",
                    audio_bytes,
                    "audio/wav"
                ),
                model="whisper-large-v3-turbo"
            )

        st.session_state.voice_text = (
            transcription.text.strip()
        )

        st.success(
            "✅ Voice successfully understood!"
        )

    except Exception as e:

        st.error(
            "❌ Voice transcription failed."
        )

        with st.expander(
            "Technical details"
        ):
            st.exception(e)


# ============================================================
# SHOW TRANSCRIPTION
# ============================================================

if st.session_state.voice_text:

    st.markdown(
        "### 📝 Your Request"
    )

    st.info(
        st.session_state.voice_text
    )


# ============================================================
# IMAGE INPUT
# ============================================================

st.markdown(
    '<div class="section-title">📷 Show Me Your Kitchen</div>',
    unsafe_allow_html=True
)

uploaded_image = st.file_uploader(
    "Upload a photo of your available ingredients",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
    help="Take a clear photo showing the ingredients you have."
)


# ============================================================
# IMAGE ANALYSIS
# ============================================================

if uploaded_image is not None:

    image_bytes = uploaded_image.getvalue()

    image_type = (
        uploaded_image.type
        or "image/jpeg"
    )

    # Save to session state
    st.session_state.image_bytes = image_bytes
    st.session_state.image_type = image_type

    st.image(
        image_bytes,
        caption="📷 Your kitchen image",
        use_container_width=True
    )


    # Analyze only if this is a new image
    image_identifier = (
        uploaded_image.name,
        len(image_bytes)
    )

    if (
        "last_image_identifier"
        not in st.session_state
        or
        st.session_state.last_image_identifier
        != image_identifier
    ):

        st.session_state.last_image_identifier = (
            image_identifier
        )

        with st.spinner(
            "👁️ KitchenAI is analyzing your ingredients..."
        ):

            try:

                analysis = analyze_image(
                    image_bytes=image_bytes,
                    image_type=image_type
                )

                st.session_state.image_analysis = analysis

            except Exception as e:

                st.session_state.image_analysis = {
                    "error": str(e)
                }


# ============================================================
# DISPLAY VISION RESULTS
# ============================================================

if st.session_state.image_analysis:

    analysis = st.session_state.image_analysis

    if analysis.get("error"):

        st.error(
            "❌ Vision analysis failed."
        )

        with st.expander(
            "Technical details"
        ):

            st.code(
                analysis["error"]
            )

    else:

        st.success(
            "✅ Image successfully analyzed!"
        )

        ingredients = analysis.get(
            "ingredients",
            []
        )

        kitchen_items = analysis.get(
            "kitchen_items",
            []
        )

        uncertain_items = analysis.get(
            "uncertain_items",
            []
        )


        # --------------------------------------------
        # INGREDIENTS
        # --------------------------------------------

        if ingredients:

            st.markdown(
                "### 🥕 Ingredients Detected"
            )

            for item in ingredients:

                if isinstance(item, dict):

                    name = item.get(
                        "name",
                        "Unknown"
                    )

                    quantity = item.get(
                        "quantity",
                        ""
                    )

                    confidence = item.get(
                        "confidence"
                    )

                    if confidence is not None:

                        try:

                            confidence_percent = (
                                float(confidence)
                                * 100
                            )

                            st.write(
                                f"• **{name}** "
                                f"— {quantity} "
                                f"({confidence_percent:.0f}% confidence)"
                            )

                        except:

                            st.write(
                                f"• **{name}** — {quantity}"
                            )

                    else:

                        st.write(
                            f"• **{name}** — {quantity}"
                        )

                else:

                    st.write(
                        f"• {item}"
                    )


        # --------------------------------------------
        # KITCHEN ITEMS
        # --------------------------------------------

        if kitchen_items:

            st.markdown(
                "### 🧂 Other Kitchen Items"
            )

            st.write(
                ", ".join(
                    str(x)
                    for x in kitchen_items
                )
            )


        # --------------------------------------------
        # UNCERTAIN ITEMS
        # --------------------------------------------

        if uncertain_items:

            with st.expander(
                "❓ Uncertain items"
            ):

                for item in uncertain_items:

                    st.write(
                        f"• {item}"
                    )


# ============================================================
# CHECK WHETHER USER IS READY
# ============================================================

voice_ready = bool(
    st.session_state.voice_text.strip()
)

image_ready = (
    st.session_state.image_analysis
    is not None
    and
    not st.session_state.image_analysis.get(
        "error"
    )
)


# ============================================================
# FIND WHAT I CAN COOK
# ============================================================

st.markdown("---")

if voice_ready and image_ready:

    st.markdown(
        "### 🍳 Ready to Cook?"
    )

    st.write(
        "KitchenAI has both your voice request and "
        "kitchen ingredients."
    )

    find_recipe = st.button(
        "🔎 Find What I Can Cook",
        use_container_width=True,
        type="primary"
    )

    if find_recipe:

        # Clear previous result
        st.session_state.recipe_result = None

        status = st.empty()

        try:

            status.info(
                "🧠 Understanding your request..."
            )

            status.info(
                "🔎 Searching for the best recipe..."
            )

            # ========================================
            # CALL KITCHEN AGENT
            # ========================================

            result = kitchen_agent(
                voice_transcript=(
                    st.session_state.voice_text
                ),
                image_analysis=(
                    st.session_state.image_analysis
                )
            )


            # ========================================
            # SAVE RESULT
            # ========================================

            st.session_state.recipe_result = result

            status.empty()

            # ========================================
            # IMPORTANT:
            # DO NOT USE st.rerun() HERE
            #
            # The result will be rendered below
            # during this same execution.
            # ========================================

        except Exception as e:

            status.empty()

            st.session_state.recipe_result = {
                "answer": "",
                "error": str(e)
            }


else:

    missing = []

    if not voice_ready:
        missing.append("🎤 voice request")

    if not image_ready:
        missing.append("📷 kitchen image")

    st.warning(
        "Please provide your "
        + " and ".join(missing)
        + " before searching for a recipe."
    )


# ============================================================
# DISPLAY RECIPE RESULT
#
# IMPORTANT:
# This is OUTSIDE the button.
# ============================================================

if st.session_state.recipe_result:

    result = st.session_state.recipe_result

    st.markdown("---")

    st.markdown(
        '<div class="section-title">'
        "🍽️ KitchenAI's Recommendation"
        "</div>",
        unsafe_allow_html=True
    )


    # ========================================================
    # ERROR
    # ========================================================

    if result.get("error"):

        st.error(
            "❌ I couldn't complete the recipe search."
        )

        with st.expander(
            "🔧 Technical details"
        ):

            st.code(
                result["error"]
            )


    # ========================================================
    # SUCCESS
    # ========================================================

    elif result.get("answer"):

        st.markdown(
            '<div class="recipe-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            result["answer"]
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        st.success(
            "🌐 KitchenAI successfully generated your recipe."
        )


    # ========================================================
    # EMPTY RESPONSE
    # ========================================================

    else:

        st.warning(
            "⚠️ KitchenAI completed the request, "
            "but returned an empty recipe."
        )


# ============================================================
# RESET BUTTON
# ============================================================

st.markdown("---")

if st.button(
    "🔄 Start Over",
    use_container_width=True
):

    st.session_state.voice_text = ""

    st.session_state.image_analysis = None

    st.session_state.recipe_result = None

    st.session_state.image_bytes = None

    st.session_state.last_image_identifier = None

    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "KitchenAI • Multimodal AI Kitchen Assistant"
)