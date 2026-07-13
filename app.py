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

# Gemini Client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


@app.route("/")
def home():
    return "AgriSmart AI Backend Running Successfully!"


@app.route("/crop-recommendation", methods=["POST"])
def crop_recommendation():

    try:
        # ----------------------------
        # Read JSON
        # ----------------------------
        data = request.get_json(force=True)

        soil = data.get("soil") or data.get("Soil")
        season = data.get("season") or data.get("Season")
        land = data.get("land") or data.get("Land")
        water = data.get("water") or data.get("Water")

        # ----------------------------
        # Validation
        # ----------------------------
        if not all([soil, season, land, water]):
            return jsonify({
                "success": False,
                "message": "Missing required fields."
            }), 400

        # ----------------------------
        # Prompt
        # ----------------------------
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

        last_error = None

        # ----------------------------
        # Retry Logic
        # ----------------------------
        for attempt in range(5):

            try:

                print(f"\nAttempt {attempt+1}")

                print("Using Model: gemini-3.5-flash")

                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )

                recommendation = getattr(response, "text", "").strip()

                if not recommendation:
                    raise Exception("Empty response received from Gemini.")

                print("Gemini Success")

                return jsonify({
                    "success": True,
                    "recommendation": recommendation
                }), 200

            except Exception as e:

                last_error = e

                print("=" * 70)
                print(f"Attempt {attempt+1} Failed")
                traceback.print_exc()
                print("=" * 70)

                # Retry Delay
                if attempt < 4:
                    wait = 5 * (attempt + 1)
                    print(f"Retrying in {wait} seconds...")
                    time.sleep(wait)

        # ----------------------------
        # All retries failed
        # ----------------------------
        return jsonify({
            "success": False,
            "message": "AI server is currently busy. Please try again after a few seconds.",
            "error": str(last_error)
        }), 503

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Internal Server Error",
            "error": str(e)
        }), 500


# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )