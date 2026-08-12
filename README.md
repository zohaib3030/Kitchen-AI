# 👨‍🍳 Kitchen AI

### Multimodal AI Kitchen Support & Recipe Recommendation Agent

Kitchen AI is an AI-powered kitchen assistant that combines **voice input, computer vision, and LLM-based reasoning** to help users decide what they can cook with the ingredients they already have.

The user can describe what they want to cook using their **voice** and upload an **image of their available ingredients**. KitchenAI analyzes both inputs, identifies the available ingredients, understands the user's intent, and recommends a suitable recipe.

---

## ✨ Features

- 🎤 **Voice Input**
  - Accepts natural-language cooking requests.
  - Uses Groq Whisper for speech-to-text transcription.

- 📷 **Vision-Based Ingredient Detection**
  - Analyzes uploaded kitchen images.
  - Identifies visible ingredients and kitchen items.
  - Provides confidence scores for detected ingredients.
  - Handles uncertain visual detections.

- 🧠 **AI-Powered Recipe Reasoning**
  - Understands the user's cooking intent.
  - Considers available ingredients and constraints.
  - Uses prompt-engineering techniques to produce grounded recommendations.

- 🍳 **Recipe Recommendation**
  - Suggests recipes based on the user's request and available ingredients.
  - Provides ingredients, cooking steps, preparation/cooking time, substitutions, and source information.

- 🌐 **Recipe Retrieval**
  - Designed to retrieve real recipes from online sources rather than relying solely on model knowledge.

- 🛡️ **Hallucination Mitigation**
  - The vision agent is instructed not to assume ingredients that are not visually supported.
  - Uncertain ingredients are explicitly separated from confirmed ingredients.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │     Kitchen AI      │
                         └──────────┬──────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
                   ▼                                 ▼
             🎤 Voice Input                     📷 Image Input
                   │                                 │
                   ▼                                 ▼
             Groq Whisper                     Vision Agent
                   │                                 │
                   ▼                                 ▼
            Voice Transcript              Ingredient Detection
                   │                                 │
                   └────────────────┬────────────────┘
                                    │
                                    ▼
                         🧠 Recipe Recommendation
                                    │
                                    ▼
                           🌐 Recipe Retrieval
                                    │
                                    ▼
                         🔎 Recipe Evaluation
                                    │
                                    ▼
                              🍳 Final Recipe
