from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv("DATABASE_URL")
print(f"DATABASE_URL as seen by Python: {repr(db_url)}")