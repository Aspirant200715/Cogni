# backend/debug_url.py
import os
from dotenv import load_dotenv

# Force reload .env
load_dotenv(override=True)

base_url = os.getenv("HINDSIGHT_BASE_URL", "NOT SET")
print(f"🔍 Loaded HINDSIGHT_BASE_URL: '{base_url}'")
print(f"🔍 Contains 'hhindsight': {'hhindsight' in base_url}")
print(f"🔍 Contains 'hindsight': {'hindsight' in base_url}")