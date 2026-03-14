from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services.gemini import generate_response

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