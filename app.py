from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")


app = Flask(__name__)
CORS(app)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@app.route("/")
def home():
    return "AgriSmart AI Backend Running"


@app.route("/crop-recommendation", methods=["POST"])
def crop_recommendation():
    try:
        data = request.json

        soil = data["soil"]
        season = data["season"]
        land = data["land"]
        water = data["water"]

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

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        return jsonify({
            "recommendation": response.text
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)