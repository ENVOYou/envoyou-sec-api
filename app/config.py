from dotenv import load_dotenv
import os

load_dotenv()

def get_config() -> dict:
    return {
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "API_KEY": os.getenv("API_KEY"),
        "OTHER_CONFIG": os.getenv("OTHER_CONFIG"),
    }