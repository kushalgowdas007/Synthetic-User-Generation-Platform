import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Dynamically locate the project root directory relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# 2. Force load_dotenv to read from the exact absolute path
load_dotenv(dotenv_path=ENV_PATH)

# 3. Read the environment keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")