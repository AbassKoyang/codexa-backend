from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .services.gemini import generate_response, generate_multimodal_stream

class AIChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get("prompt")
        
        if not prompt:
            return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

        response_text = generate_response(prompt)

        if response_text == "ERROR_RATE_LIMIT":
            return Response(
                {"error": "AI rate limit exceeded. Please try again in a few seconds."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        elif response_text.startswith("ERROR_"):
            return Response(
                {"error": "An error occurred with the AI service. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({"response": response_text})

class AICodeAssistantView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        prompt = request.data.get("prompt")
        file_tree = request.data.get("file_tree")
        uploaded_file = request.FILES.get("file")

        if not prompt or not file_tree:
            return Response(
                {"error": "Both 'prompt' and 'file_tree' are required fields."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        file_bytes = None
        mime_type = None
        if uploaded_file:
            file_bytes = uploaded_file.read()
            mime_type = uploaded_file.content_type

        def stream_generator():
            for chunk in generate_multimodal_stream(prompt, file_tree, file_bytes, mime_type):
                if chunk == "ERROR_RATE_LIMIT":
                    yield "AI rate limit exceeded. Please try again later.\n"
                    break
                elif chunk.startswith("ERROR_"):
                    yield "An error occurred with the AI service.\n"
                    break
                yield chunk

        return StreamingHttpResponse(stream_generator(), content_type="text/plain")