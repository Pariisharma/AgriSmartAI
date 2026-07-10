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
        model="gemini-3-flash-preview",
        contents=prompt
    )

    return jsonify({
        "recommendation": response.text
    })


if __name__ == "__main__":
    app.run(debug=True)