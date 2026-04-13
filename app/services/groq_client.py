import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def generate_itinerary_with_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a travel itinerary generator. "
                    "You must return ONLY valid JSON. "
                    "Do not include markdown fences. "
                    "Do not include explanations. "
                    "Do not include any text before or after the JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_completion_tokens=800
    )

    return response.choices[0].message.content.strip()