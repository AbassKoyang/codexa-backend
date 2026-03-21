from google import genai
from google.genai import errors, types
import logging

logger = logging.getLogger(__name__)

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

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

def generate_multimodal_stream(prompt, file_tree, mode=None, file_bytes=None, mime_type=None, history=None):
    SYSTEM_INSTRUCTION = """
You are a professional software engineer and coding assistant. 
You are embedded in an IDE called Codexa.
Your goal is to help users write, debug, and understand code.
You will be provided with a prompt, the project's file structure (file tree), and potentially an image or PDF for context (e.g., a design mockup or documentation).
Provide clear, concise, and accurate technical advice.
"""
    # Prepare contents for the current turn
    # If it's a new chat, we include the file tree as context.
    # If it's an ongoing chat, we might just include the prompt, 
    # but the user requested file tree and prompts are required context.
    context_content = []
    if file_tree:
        context_content.append(f"Project File Tree:\n{file_tree}\n\n")
    
    if file_bytes and mime_type:
        context_content.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
    
    context_content.append(f"User Prompt: {prompt}")

    if mode and mode == 'agent':
        SYSTEM_INSTRUCTION = SYSTEM_INSTRUCTION + "[SYSTEM: You are in AGENT mode. If you need to modify any code, provide the FULL new content of each target file using this format: 'UPDATE: [filename]' followed by a code block. Then, provide a very brief summary of your changes. Avoid repeating the code outside of these blocks.]"

    try:
        # Create a chat session with history if provided
        chat = client.chats.create(
            model="gemini-3.1-flash-lite-preview",
            history=history or [],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )
        
        # Send the current context as a message
        response_stream = chat.send_message_stream(message=context_content)
        
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