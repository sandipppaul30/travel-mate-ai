import os
from dotenv import load_dotenv
from typing import Any

load_dotenv()  # <-- must call this

def get_env(env: str) -> Any:
    if env:
        value = os.getenv(env)
        if value is None:
            raise ValueError(f"{env} environment variable not set")
        return value
    else:
        raise ValueError("Environment variable name not provided")