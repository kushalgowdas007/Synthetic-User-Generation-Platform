import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_response(prompt):

    for attempt in range(3):

        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )

            return response.text

        except ServerError as e:
            print(f"Gemini busy. Retry {attempt + 1}/3...")
            time.sleep(5)

        except Exception as e:
            print("Gemini Error:", e)
            return None

    return None