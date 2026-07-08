import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiService:
    def __init__(self):
        """Initializes the Gemini API client using the environment variable."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash as it's fast, cost-effective, and highly capable of JSON tasks
        self.model_name = "gemini-1.5-flash"

    def generate_personas(self, product_name: str, product_desc: str, target_audience: str, research_goal: str, num_personas: int = 3) -> list:
        """
        Generates a list of synthetic user personas based on product criteria.
        Returns a Python list of dictionaries.
        """
        
        # System instructions force the model into the exact mindset and output mode
        system_instruction = (
            "You are an expert UX Researcher and User Persona Generator. "
            "Your job is to generate highly realistic, distinct, and diverse synthetic user personas "
            "based on the provided product details. You must respond ONLY with a valid JSON array "
            "of objects matching the requested schema. Do not include markdown formatting like ```json ... ```, "
            "and do not include any introductory or concluding text."
        )

        prompt = f"""
        Generate exactly {num_personas} unique synthetic user personas for the following product:
        
        - Product Name: {product_name}
        - Description: {product_desc}
        - Target Audience: {target_audience}
        - Research Goal: {research_goal}
        
        Each persona object in the JSON array MUST have exactly these keys:
        - "name": (string, culturally appropriate name based on the target audience)
        - "age": (integer)
        - "occupation": (string)
        - "traits": (array of strings, 3-4 personality traits)
        - "goals": (array of strings, 2-3 user goals relative to this product)
        - "pain_points": (array of strings, 2-3 frustrations or barriers)
        - "behaviour": (array of strings, 2-3 typical behaviors or tech habits)
        """

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
            
            # Requesting JSON structured output explicitly
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse the string response into clean Python types
            personas_data = json.loads(response.text)
            return personas_data

        except json.JSONDecodeError as je:
            print(f"JSON Parsing Error: {je}")
            print(f"Raw Response was: {response.text}")
            return []
        except Exception as e:
            print(f"An error occurred during Gemini Generation: {e}")
            return []

# Quick local test block (Run this file directly to test your module)
if __name__ == "__main__":
    # Make sure you have GEMINI_API_KEY="your_key" in a .env file locally
    print("Testing Gemini Service...")
    try:
        service = GeminiService()
        test_personas = service.generate_personas(
            product_name="FitPulse AI",
            product_desc="A mobile app using AI to generate quick 15-minute home workouts for busy people.",
            target_audience="College students and busy young professionals",
            research_goal="Understand app retention barriers",
            num_personas=3
        )
        print(json.dumps(test_personas, indent=2))
    except Exception as e:
        print(f"Setup failed: {e}")