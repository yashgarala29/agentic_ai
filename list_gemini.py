from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


import os
load_dotenv()
from google import genai

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
for m in client.models.list():
    print(m.name)