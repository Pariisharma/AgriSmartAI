from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
import os
import time
import traceback

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

# ----------------------------
# Gemini Client
# ----------------------------
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# ----------------------------
# Home Route
# ----------------------------
@app.route("/")
def home():
    return "AgriSmart AI Backend Running Successfully!"

# ----------------------------
# Crop Recommendation API
# ----------------------------
@app.route("/crop-recommendation", methods=["POST"])
def crop_recommendation():

    try:

        # Read JSON
        data = request.get_json(force=True)

        soil = data.get("soil") or data.get("Soil")
        season = data.get("season") or data.get("Season")
        land = data.get("land") or data.get("Land")
        water = data.get("water") or data.get("Water")

        # Validation
        if not all([soil, season, land, water]):
            return jsonify({
                "success": False,
                "message": "Missing required fields."
            }), 400

        # Prompt
        prompt = f"""
You are an agriculture expert.

Recommend the best crop based on:

Soil Type: {soil}
Season: {season}
Land Area: {land} acres
Water Availability: {water}

Return ONLY in this format:

Crop:
Reason:
"""

        # Retry Logic
        for attempt in range(5):

            try:

                print("=" * 60)
                print(f"Attempt {attempt + 1}")
                print("Using Model: gemini-2.5-flash-lite")

                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt
                )

                recommendation = getattr(response, "text", "").strip()

                if not recommendation:
                    raise Exception("Empty response received from Gemini.")

                print("Gemini Success")
                print("=" * 60)

                return jsonify({
                    "success": True,
                    "recommendation": recommendation
                }), 200

            except Exception as e:

                print("=" * 60)
                print(f"Attempt {attempt + 1} Failed")
                traceback.print_exc()
                print("=" * 60)

                error_text = str(e)

                # Quota Exceeded
                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    return jsonify({
                        "success": False,
                        "message": "Daily Gemini API quota exceeded. Please try again tomorrow or use another API key.",
                        "error": error_text
                    }), 429

                # Gemini Busy
                if "503" in error_text or "UNAVAILABLE" in error_text:
                    if attempt == 4:
                        return jsonify({
                            "success": False,
                            "message": "Gemini servers are currently busy. Please try again after a few seconds.",
                            "error": error_text
                        }), 503

                # Retry
                if attempt < 4:
                    wait = 5 * (attempt + 1)
                    print(f"Retrying in {wait} seconds...")
                    time.sleep(wait)

        # All retries failed
        return jsonify({
            "success": False,
            "message": "Failed to generate recommendation after multiple attempts."
        }), 500

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Internal Server Error",
            "error": str(e)
        }), 500

# ----------------------------
# Run Server
# ----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )