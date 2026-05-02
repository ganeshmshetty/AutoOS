import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEYS").split(",")[0]
client = genai.Client(api_key=api_key)

print("Available Models:")
for model in client.models.list():
    print(f"- {model.name}")
