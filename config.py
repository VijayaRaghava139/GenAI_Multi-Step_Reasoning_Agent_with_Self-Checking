import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration - strip quotes if present
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().strip("'").strip('"')
MODEL_NAME = "gpt-4o-mini"

# Agent Configuration
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60
MAX_ITERATIONS = 20  

# Code Execution Safety
ALLOWED_IMPORTS = ['datetime', 'math']
MAX_CODE_LENGTH = 2000

# Debug Mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
