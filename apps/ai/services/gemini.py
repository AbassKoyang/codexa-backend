from google import genai
from google.genai import errors, types
import logging
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union
import sys


logger = logging.getLogger(__name__)

client = genai.Client()

from typing import List, Union, Literal
from pydantic import BaseModel, Field

class File(BaseModel):
    id: str
    type: Literal["file", "folder"]
    name: str
    content: str

# class Folder(BaseModel):
#     id: str
#     type: Literal["folder"]
#     name: str
#     # Use a string forward reference here for the recursive part
#     children: List[Union[File, "Folder"]] = Field(default_factory=list)

class GeminiResponse(BaseModel):
    file_tree: List[File]
    modified_files: List[str]
    response: str

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
    context_content = []
    if file_tree:
        context_content.append(f"Project File Tree:\n{file_tree}\n\n")
    
    if file_bytes and mime_type:
        context_content.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
    
    context_content.append(f"User Prompt: {prompt}")

    if mode and mode == 'agent':
        SYSTEM_INSTRUCTION = SYSTEM_INSTRUCTION + " You are in AGENT mode. You can modify the file tree by adding, updating, or deleting files. Use the file_tree field in the response to represent the updated file tree. Also provide a brief summary of your changes in the response field. List out the files you are modifying in the modified_files field."

    try:
        # Create a chat session with history if provided
        if mode == "agent":
            response_schema = GeminiResponse.model_json_schema()
        else:
            response_schema = None
        chat = client.chats.create(
            model="gemini-3.1-flash-lite-preview",
            history=history or [],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        # Send the current context as a message
        response_stream = chat.send_message_stream(message=context_content)
        
        for chunk in response_stream:
            # When using response_schema, chunks contain parts of the JSON string.
            try:
                text = chunk.text
                if text:
                    print(text)
                    yield text
            except (AttributeError, IndexError):
                # Handle chunks that might not have text (e.g. only metadata)
                continue
            
    except errors.ClientError as e:
        logger.error(f"Gemini API Client Error (Streaming): {e}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            yield "ERROR_RATE_LIMIT"
        else:
            yield "ERROR_API"
    except Exception as e:
        logger.error(f"Unexpected error in Gemini Streaming service: {e}")
        yield "ERROR_UNKNOWN"