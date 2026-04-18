from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def generate_with_groq(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        response_format={"type": "json_object"},
        messages=messages
    )

    return response.choices[0].message.content