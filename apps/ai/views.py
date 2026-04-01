import json
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, generics
from apps.projects.models import Project
from .services.gemini import generate_response, generate_multimodal_stream
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from apps.accounts.throttles import AIRateThrottle

class AIChatView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIRateThrottle]

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
    throttle_classes = [AIRateThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        prompt = request.data.get("prompt")
        file_tree = request.data.get("file_tree")
        project_slug = request.data.get("project_slug")
        mode = request.data.get("mode")
        history_raw = request.data.get("history")
        uploaded_file = request.FILES.get("file")

        if not prompt or not file_tree or not project_slug:
            return Response(
                {"error": "Fields 'prompt', 'file_tree', and 'project_slug' are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = Project.objects.get(slug=project_slug, owner=request.user)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        # Save user message to database
        ChatMessage.objects.create(
            project=project,
            role='user',
            content=prompt
        )

        # Parse history if provided
        history = None
        if history_raw:
            try:
                history = json.loads(history_raw)
            except (ValueError, TypeError):
                return Response({"error": "Invalid JSON format for history"}, status=status.HTTP_400_BAD_REQUEST)

        file_bytes = None
        mime_type = None
        if uploaded_file:
            file_bytes = uploaded_file.read()
            mime_type = uploaded_file.content_type

        def stream_generator():
            full_response = []
            for chunk in generate_multimodal_stream(prompt, file_tree, mode, file_bytes, mime_type, history):
                if chunk == "ERROR_RATE_LIMIT":
                    yield "AI rate limit exceeded. Please try again later.\n"
                    break
                elif chunk.startswith("ERROR_"):
                    yield "An error occurred with the AI service.\n"
                    break
                
                full_response.append(chunk)
                yield chunk

            # Once streaming is done, save the assistant's message
            if full_response:
                ChatMessage.objects.create(
                    project=project,
                    role='agent',
                    content="".join(full_response)
                )

        return StreamingHttpResponse(stream_generator(), content_type="text/plain")

class ChatHistoryView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIRateThrottle]
    pagination_class = None

    def get_queryset(self):
        project_slug = self.kwargs.get('project_slug')
        project = Project.objects.get(slug=project_slug, owner=self.request.user)
        return ChatMessage.objects.filter(
            project_id=project.id
        ).order_by('timestamp')