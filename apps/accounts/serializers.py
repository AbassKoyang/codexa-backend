from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework import generics, serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'profile_pic_url', 'github', 'registration_method', 'plan', 'paystack_customer_code', 'paystack_subscription_code']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user