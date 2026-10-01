import os
import certifi
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from typing import Any

load_dotenv()  

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

def get_env(env: str) -> Any:
    if env:
        value = os.getenv(env)
        if value is None:
            raise ValueError(f"{env} environment variable not set")
        return value
    else:
        raise ValueError("Environment variable name not provided")

def get_database_url() -> str:

    db_url = get_env("DATABSE_URL")
    if "sslmode=" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require" 
    return db_url

def get_gemini_client() -> ChatGoogleGenerativeAI:

    return ChatGoogleGenerativeAI(
        api_key = get_env("GEMINI_API_KEY"),
        model = get_env("GEMINI_DEPLOYED_MODEL"),
        tempareture = 0.0
    )

def get_gemini_embedding_client() -> GoogleGenerativeAIEmbeddings:

    return GoogleGenerativeAIEmbeddings(
        api_key = get_env("GEMINI_API_KEY"),
        model = get_env("GoogleGenerativeAIEmbeddings")
    )
