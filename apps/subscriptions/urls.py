from django.urls import path
from . import views

urlpatterns = [
    path('initialize/', views.InitializeSubscriptionView.as_view(), name='subscription-initialize'),
    path('webhook/', views.PaystackWebhookView.as_view(), name='paystack-webhook'),
]
