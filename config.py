# config.py - Load all configuration from environment variables

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/ai_analyzer"
)

# ============================================
# JWT CONFIGURATION
# ============================================
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ============================================
# OPENAI CONFIGURATION
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in .env file!")

# ============================================
# AWS CONFIGURATION
# ============================================
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# ============================================
# APP CONFIGURATION
# ============================================
DEBUG = os.getenv("DEBUG", "False") == "True"

print("✓ Configuration loaded successfully!")
