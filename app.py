from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
import os
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@app.route("/")
def home():
    return "AgriSmart AI Backend Running"


@app.route("/crop-recommendation", methods=["POST"])
def crop_recommendation():
    try:
        data = request.get_json(force=True)

        # Handle both lowercase and uppercase JSON keys
        soil = data.get("soil") or data.get("Soil")
        season = data.get("season") or data.get("Season")
        land = data.get("land") or data.get("Land")
        water = data.get("water") or data.get("Water")

        if not all([soil, season, land, water]):
            return jsonify({
                "success": False,
                "message": "Missing required fields."
            }), 400

        prompt = f"""
Recommend the best crop for:

Soil: {soil}
Season: {season}
Land Area: {land} acres
Water Availability: {water}

Return only:

Crop:
Reason:
"""

        last_error = None

        # Retry if Gemini is busy
        for attempt in range(3):
            try:
               response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt
                )

                return jsonify({
                    "success": True,
                    "recommendation": response.text
                })

            except Exception as e:
                last_error = e
                print(f"Attempt {attempt+1} failed: {e}")

                if attempt < 2:
                    time.sleep(2)

        return jsonify({
            "success": False,
            "message": "Gemini server is busy. Please try again in a few seconds.",
            "error": str(last_error)
        }), 503

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Internal Server Error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)