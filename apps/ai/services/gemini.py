from google import genai
from google.genai import errors, types
import logging

logger = logging.getLogger(__name__)

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

SYSTEM_INSTRUCTION = """
You are a professional software engineer and coding assistant. 
You are embedded in an IDE called Codexa.
Your goal is to help users write, debug, and understand code.
You will be provided with a prompt, the project's file structure (file tree), and potentially an image or PDF for context (e.g., a design mockup or documentation).
Provide clear, concise, and accurate technical advice.
"""

def generate_response(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview", contents=prompt
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

def generate_multimodal_stream(prompt, file_tree, file_bytes=None, mime_type=None):
    context_text = f"Project File Tree:\n{file_tree}\n\nUser Prompt: {prompt}"
    
    contents = []
    if file_bytes and mime_type:
        contents.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
    
    contents.append(context_text)
    print(contents)

    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-3.1-flash-lite-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )
        for chunk in response_stream:
            yield chunk.text
    except errors.ClientError as e:
        logger.error(f"Gemini API Client Error (Streaming): {e}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            yield "ERROR_RATE_LIMIT"
        else:
            yield "ERROR_API"
    except Exception as e:
        logger.error(f"Unexpected error in Gemini Streaming service: {e}")
        yield "ERROR_UNKNOWN"