from google import genai
from google.genai import errors
import logging

logger = logging.getLogger(__name__)

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

def generate_response(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite", contents=prompt
        )
        return response.text
    except errors.ClientError as e:
        logger.error(f"Gemini API Client Error: {e}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return "ERROR_RATE_LIMIT"
        return "ERROR_API"
    except Exception as e:
        logger.error(f"Unexpected error in Gemini service: {e}")
        return "ERROR_UNKNOWN"