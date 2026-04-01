import json
import hashlib
import hmac
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.accounts.models import User
from .utils import PaystackProvider
from apps.accounts.throttles import PaymentRateThrottle

class InitializeSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [PaymentRateThrottle]

    def post(self, request):
        plan_code = settings.PAYSTACK_PLAN_CODE
        if not plan_code:
            return Response({"error": "PAYSTACK_PLAN_CODE is not configured on the server"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        provider = PaystackProvider()
        amount = request.data.get('amount', 10000)
        print(request.user.email, amount, plan_code)
        response = provider.initialize_transaction(request.user.email, amount, plan_code)
        print(response)
        
        if response.get('status'):
            return Response(response['data'])
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

class PaystackWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    PAYSTACK_IPS = [
        '52.31.139.75',
        '52.49.173.169',
        '52.214.14.220'
    ]

    def post(self, request):
        # 1. IP Whitelisting (Optional but recommended)
        remote_addr = request.META.get('REMOTE_ADDR')
        # In a real production env behind a proxy, you might need HTTP_X_FORWARDED_FOR
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = remote_addr

        if settings.DEBUG == False and ip not in self.PAYSTACK_IPS:
             return Response(status=status.HTTP_401_UNAUTHORIZED)

        payload = request.body
        signature = request.headers.get('x-paystack-signature')
        
        if not signature:
            # Always return 200 OK to acknowledge we received *something*, 
            # but log or handle failure internally if it's not a valid Paystack request.
            # However, doc says: "Veryfing the header signature should be done before processing"
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 2. Signature Validation
        hash = hmac.new(settings.PAYSTACK_SECRET_KEY.encode('utf-8'), payload, hashlib.sha512).hexdigest()
        if hash != signature:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # 3. Process Event
        data = json.loads(payload)
        event = data.get('event')
        
        # Acknowledge immediately if tasks are long-running. 
        # Here we process synchronously as it's just a DB update and email.
        self.process_event(event, data.get('data'))

        # 4. Final Acknowledgment
        return Response(status=status.HTTP_200_OK)

    def process_event(self, event, data_payload):
        customer_email = data_payload.get('customer', {}).get('email')
        if not customer_email:
             return
        
        user = User.objects.filter(email=customer_email).first()
        if not user:
             return

        if event in ['charge.success', 'subscription.create', 'invoice.update']:
            # For invoice.update, only act if it's successful
            if event == 'invoice.update' and data_payload.get('status') != 'success':
                return

            user.plan = 'paid'
            if 'customer_code' in data_payload.get('customer', {}):
                user.paystack_customer_code = data_payload['customer']['customer_code']
            
            # subscription.create and invoice.update usually have subscription details
            sub_data = data_payload.get('subscription', data_payload) if event == 'invoice.update' else data_payload
            if 'subscription_code' in sub_data:
                user.paystack_subscription_code = sub_data['subscription_code']
            
            user.save()
            
            # Send notification for new subscriptions
            if event == 'subscription.create':
                send_mail(
                    'Subscription Successful',
                    f'Hello {user.email}, your subscription to the paid plan was successful!',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
        
        elif event == 'subscription.disable':
            user.plan = 'free'
            user.save()
            send_mail(
                'Subscription Cancelled',
                f'Hello {user.email}, your subscription has been cancelled and your account has been moved to the free plan.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )

        elif event == 'subscription.not_renew':
            # Subscription is still active but won't renew
            # We can notify the user if we want
            pass

        elif event == 'invoice.payment_failed':
            # Payment failed for a recurring charge
            # We might want to warn the user
            send_mail(
                'Subscription Payment Failed',
                f'Hello {user.email}, we were unable to process your recurring payment. Please update your payment details to avoid interruption.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )

        elif event == 'invoice.create':
            # Invoice created 3 days before charge
            pass
