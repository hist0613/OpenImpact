import os
from typing import Dict, Any

DEFAULT_GEMINI_CONFIG: Dict[str, Any] = {
    "name": "gemini-1.5-flash-latest",
    "model_name": "gemini-1.5-flash-latest",
    "api_key": os.getenv("GEMINI_API_KEY"),
    "api_base": os.getenv("GEMINI_API_BASE"),
    "timeout": 10,
    "max_retries": 3,
}

