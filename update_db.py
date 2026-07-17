import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:

    conn.execute(text("""
        ALTER TABLE recommendation_history
        ADD COLUMN IF NOT EXISTS crop_name VARCHAR(100);
    """))

    conn.commit()

print("Database Updated Successfully!")