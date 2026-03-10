from django.conf import settings
from django.db.models import F
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from .models import User
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .throttles import AuthRateThrottle, AuthAnonRateThrottle, UserActionRateThrottle, ReadOnlyRateThrottle

from .serializers import UserSerializer
from .permissions import IsProfileOwner

# Create your views here.
@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    token = request.data.get("token")
    if not token:
        return Response({"error": "Token not provided","status":False}, status=status.HTTP_400_BAD_REQUEST)
    try:
        id_info = id_token.verify_oauth2_token(
        token, 
        google_requests.Request(), 
        settings.GOOGLE_OAUTH_CLIENT_ID
    )   
        email = id_info['email']
        first_name = id_info.get('given_name', '')
        last_name = id_info.get('family_name', '')
        profile_pic_url = id_info.get('picture', '')
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_unusable_password()
            user.first_name = first_name
            user.last_name = last_name
            user.registration_method = 'google'
            user.profile_pic_url = profile_pic_url
            user.github = ''
            user.save()
        else:
            if user.registration_method != 'google':
                return Response({
                    "error": "User needs to sign in through email",
                    "status": False
                }, status=status.HTTP_403_FORBIDDEN)
      
        refresh = RefreshToken.for_user(user)

        response = Response({
            "status": True,
            "message": "Google login successful"
        })

        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60 * 30,
            path='/'
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=(60 * 60 * 24) * 7,
            path='/'
        )

        return response
    except ValueError:
        return Response({"error": "Invalid token","status":False}, status=status.HTTP_400_BAD_REQUEST)


class DeleteUser(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated,IsProfileOwner]

    lookup_field = 'pk'
    lookup_url_kwarg='id'

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({
            "status": True,
            "message": "Logged out successfully"
        })
        response.delete_cookie(
            key="refresh_token",
            samesite="None",
            path='/'
        )
        response.delete_cookie(
            key="access_token",
            samesite="None",
            path='/'
        )
        return response

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes =[AllowAny]
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access = response.data["access"]
            refresh = response.data["refresh"]

            response.set_cookie(
                key="access_token",
                value=access,
                httponly=True,
                secure=True, 
                samesite="None",
                max_age=60 * 30,
                path='/'
            )

            response.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                secure=True,
                samesite="None",
                max_age=(60 * 60 * 24) * 7,
                path='/'
            )
            response.data = {
                "status": True,
                "message": "Login successful"
            }
        
        return response

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"detail": "No refresh token"}, status=401)

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            response.set_cookie(
                key="access_token",
                value=response.data["access"],
                httponly=True,
                secure=True, 
                samesite="None",
                max_age=60 * 30,
                path='/'
            )

            response.set_cookie(
                key="refresh_token",
                value=response.data["refresh"],
                httponly=True,
                secure=True,
                samesite="None",
                max_age=(60 * 60 * 24) * 7,
                path='/'
            )
            response.data = {
                "status": True,
                "message": "Token refreshed"
            }

        return response