from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
import os
import time
import traceback
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

# ----------------------------
# Database Configuration
# ----------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ----------------------------
# Gemini Client
# ----------------------------
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# ----------------------------
# Farmer Model
# ----------------------------
class Farmer(db.Model):

    __tablename__ = "farmers"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    mobile = db.Column(db.String(15), unique=True, nullable=False)

    village = db.Column(db.String(100))

    district = db.Column(db.String(100))

    state = db.Column(db.String(100))

    land_area = db.Column(db.Float)

    password = db.Column(db.String(255), nullable=False)

# ----------------------------
# Recommendation History Model
# ----------------------------
class RecommendationHistory(db.Model):

    __tablename__ = "recommendation_history"

    id = db.Column(db.Integer, primary_key=True)

    farmer_id = db.Column(
        db.Integer,
        db.ForeignKey("farmers.id"),
        nullable=False
    )

    soil = db.Column(db.String(100))

    season = db.Column(db.String(100))

    water = db.Column(db.String(100))

    land_area = db.Column(db.Float)

    crop_name = db.Column(db.String(100))

    recommendation = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

#LandSurveyHitory
class LandSuitabilityHistory(db.Model):

    __tablename__ = "land_suitability_history"

    id = db.Column(db.Integer, primary_key=True)

    farmer_id = db.Column(db.Integer)

    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    village = db.Column(db.String(100))

    land_area = db.Column(db.Float)

    soil_type = db.Column(db.String(100))
    water = db.Column(db.String(100))
    season = db.Column(db.String(100))
    irrigation = db.Column(db.String(100))

    rainfall = db.Column(db.Float)

    previous_crop = db.Column(db.String(100))

    recommendation = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

# ----------------------------
# Home Route
# ----------------------------
@app.route("/")
def home():
    return "AgriSmart AI Backend Running Successfully!"

# ----------------------------
# Farmer Registration API
# ----------------------------
@app.route("/register", methods=["POST"])
def register_farmer():

    try:

        data = request.get_json(force=True)

        name = data.get("name")
        mobile = data.get("mobile")
        village = data.get("village")
        district = data.get("district")
        state = data.get("state")
        land_area = data.get("land_area")
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        # Validation
        if not all([
            name,
            mobile,
            village,
            district,
            state,
            land_area,
            password,
            confirm_password
        ]):
            return jsonify({
                "success": False,
                "message": "Please fill in all the required fields."
            }), 400
        
        if password != confirm_password:
            return jsonify({
                "success": False,
                "message": "Password and Confirm Password do not match."
            }), 400

        # Mobile validation
        if len(str(mobile)) != 10 or not str(mobile).isdigit():
            return jsonify({
                "success": False,
                "message": "Please enter a valid 10-digit mobile number."
            }), 400

        # Duplicate mobile check
        existing_farmer = Farmer.query.filter_by(mobile=mobile).first()

        if existing_farmer:
            return jsonify({
                "success": False,
                "message": "This mobile number is already registered. Please login instead."
            }), 409

        # Password Hash
        hashed_password = generate_password_hash(password)

        farmer = Farmer(
            name=name,
            mobile=mobile,
            village=village,
            district=district,
            state=state,
            land_area=float(land_area),
            password=hashed_password
        )

        db.session.add(farmer)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Welcome {name}! Your registration was successful."
        }), 201

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Please enter a valid land area."
        }), 400

    except Exception as e:

        # Actual error sirf server logs me
        print("Registration Error:", e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Something went wrong while creating your account. Please try again later."
        }), 500

# ----------------------------
# Farmer Login API
# ----------------------------
@app.route("/login", methods=["POST"])
def login_farmer():

    try:

        data = request.get_json(force=True)

        mobile = data.get("mobile")
        password = data.get("password")

        if not mobile or not password:
            return jsonify({
                "success": False,
                "message": "Please enter mobile number and password."
            }), 400

        farmer = Farmer.query.filter_by(mobile=mobile).first()

        if farmer is None:
            return jsonify({
                "success": False,
                "message": "Farmer not found."
            }), 404

        if not check_password_hash(farmer.password, password):
            return jsonify({
                "success": False,
                "message": "Incorrect password."
            }), 401

        return jsonify({

            "success": True,

            "message": f"Welcome {farmer.name}!",

            "farmer": {

                "id": farmer.id,

                "name": farmer.name,

                "mobile": farmer.mobile,

                "village": farmer.village,

                "district": farmer.district,

                "state": farmer.state,

                "land_area": farmer.land_area

            }

        }), 200

    except Exception as e:

        print(e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Unable to login. Please try again."
        }), 500

# ----------------------------
# Crop Recommendation API
# ----------------------------
@app.route("/crop-recommendation", methods=["POST"])
def crop_recommendation():

    try:

        # Read JSON
        data = request.get_json(force=True)

        farmer_id = data.get("farmer_id")

        soil = data.get("soil") or data.get("Soil")
        season = data.get("season") or data.get("Season")
        land = data.get("land") or data.get("Land")
        water = data.get("water") or data.get("Water")

        # Validation
        if not all([farmer_id, soil, season, land, water]):
            return jsonify({
                "success": False,
                "message": "Please fill in all required fields.",
                "recommendation": ""
            }), 200

        prompt = f"""
You are an experienced agricultural expert.

Based ONLY on the following inputs, recommend the most suitable crop.

Inputs:
- Soil Type: {soil}
- Season: {season}
- Land Area: {land} acres
- Water Availability: {water}

Important Rules:
1. Use ONLY the given inputs.
2. Water availability must strongly affect the recommendation.
3. If water is Low, never recommend Rice.
4. If water is Medium, Rice is allowed only when soil and season are suitable.
5. If water is High, Rice can be recommended.
6. Recommend Wheat only for Rabi season.
7. Recommend Maize, Bajra, Jowar, Cotton, Soybean, Groundnut etc. whenever they better match the inputs.
8. Every different input combination should produce a different recommendation whenever appropriate.

Return ONLY in this format:

Crop:
Reason:
Confidence:
Tips:
- Tip 1
- Tip 2
- Tip 3
"""

        # Retry Logic
        for attempt in range(5):

            try:

                print("=" * 60)
                print(f"Attempt {attempt + 1}")
                print("Using Model: gemini-3-flash-preview")

                response = client.models.generate_content(
                    model="models/gemini-3-flash-preview",
                    contents=prompt
                )

                recommendation = response.text.strip()

                if not recommendation:
                    raise Exception("Empty response received from Gemini.")

                crop_name = ""

                if recommendation.startswith("Crop:"):

                    first_line = recommendation.split("\n")[0]

                    crop_name = first_line.replace("Crop:", "").strip()

                print("Gemini Success")
                print("=" * 60)

                history = RecommendationHistory(

                    farmer_id=farmer_id,

                    soil=soil,

                    season=season,

                    water=water,

                    land_area=float(land),

                    crop_name=crop_name,

                    recommendation=recommendation

                )

                db.session.add(history)

                db.session.commit()

                return jsonify({
                    "success": True,
                    "message": "Recommendation generated successfully.",
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
                        "message": "AI service is temporarily unavailable. Please try again later.",
                        "recommendation": ""
                    }), 200

                # Gemini Busy
                if "503" in error_text or "UNAVAILABLE" in error_text:
                    if attempt == 4:
                        return jsonify({
                            "success": False,
                            "message": "AI service is temporarily unavailable. Please try again later.",
                            "recommendation": ""
                        }), 200

                # Retry
                if attempt < 4:
                    wait = 5 * (attempt + 1)
                    print(f"Retrying in {wait} seconds...")
                    time.sleep(wait)

        # All retries failed
        return jsonify({
            "success": False,
            "message": "AI service is temporarily unavailable. Please try again.",
            "recommendation": ""
        }), 200

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "AI service is temporarily unavailable. Please try again.",
            "recommendation": ""
        }), 200

#LandSurveyAPI
@app.route("/land-suitability", methods=["POST"])
def land_suitability():

    try:

        data = request.get_json(force=True)

        farmer_id = data.get("farmer_id")

        state = data.get("state")

        district = data.get("district")

        village = data.get("village")

        land_area = data.get("land_area")

        soil_type = data.get("soil_type")

        water = data.get("water")

        season = data.get("season")

        irrigation = data.get("irrigation")

        rainfall = data.get("rainfall")

        previous_crop = data.get("previous_crop")

        if not all([
            farmer_id,
            state,
            district,
            village,
            land_area,
            soil_type,
            water,
            season,
            irrigation,
            rainfall,
            previous_crop
        ]):
            return jsonify({
                "success": False,
                "message": "Please fill all required fields."
            }),400

        prompt = f"""
        You are an expert agricultural consultant.

        Analyze the following land details and recommend the best crop.

        Farmer Details:
        State: {state}
        District: {district}
        Village: {village}

        Land Area: {land_area} acres
        Soil Type: {soil_type}
        Water Availability: {water}
        Season: {season}
        Irrigation: {irrigation}
        Annual Rainfall: {rainfall} mm
        Previous Crop: {previous_crop}

        Based on these details provide:

        1. Recommended Crop
        2. Suitability Score (0-100)
        3. Fertilizer Recommendation
        4. Irrigation Advice
        5. Best Sowing Season
        6. Expected Yield (Quintal/Acre)
        7. Estimated Investment (₹)
        8. Estimated Revenue (₹)
        9. Estimated Profit (₹)
        10. AI Recommendation
        11. 3 Farming Tips

        Return ONLY valid JSON.

        Do not use markdown.
        Do not use ```json.
        Do not add any explanation.

        Use exactly this JSON format:

        {{
        "recommended_crop": "",
        "suitability_score": 0,
        "fertilizer": "",
        "irrigation_advice": "",
        "best_sowing_season": "",
        "expected_yield": "",
        "estimated_investment": "",
        "estimated_revenue": "",
        "estimated_profit": "",
        "reason": "",
        "tips": [
            "",
            "",
            ""
        ]
        }}
        """

        response = client.models.generate_content(
            model="models/gemini-3-flash-preview",
            contents=prompt
        )
        recommendation = response.text.strip()
        print(recommendation)
        return jsonify({
            "success": True,
            "recommendation": recommendation
        })


    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ----------------------------
# Recommendation History API
# ----------------------------
@app.route("/history/<int:farmer_id>", methods=["GET"])
def get_history(farmer_id):

    try:

        history = RecommendationHistory.query.filter_by(
            farmer_id=farmer_id
        ).order_by(
            RecommendationHistory.created_at.desc()
        ).all()

        result = []

        for item in history:

            result.append({

                "crop": item.crop_name,
                "soil": item.soil,
                "season": item.season,
                "water": item.water,
                "land_area": item.land_area,
                "recommendation": item.recommendation,
                "date": item.created_at.strftime("%d-%m-%Y %H:%M")

            })

        return jsonify({
            "success": True,
            "history": result
        }), 200

    except Exception as e:

        print(e)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Unable to fetch history."
        }), 500

with app.app_context():
    db.create_all()

# ----------------------------
# Run Server
# ----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )