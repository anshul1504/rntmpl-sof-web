import hashlib
import hmac
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def razorpay_is_configured():
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def amount_to_paise(amount):
    return int((Decimal(amount).quantize(Decimal('0.01'))) * 100)


def verify_razorpay_webhook_signature(raw_body, signature):
    if not razorpay_is_configured() or not signature:
        return False
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class RazorpayPaymentService:
    @staticmethod
    def create_order(*, amount, receipt, notes=None):
        if not razorpay_is_configured():
            raise ImproperlyConfigured('Razorpay keys are not configured.')
        try:
            import razorpay
        except ImportError as exc:
            raise ImproperlyConfigured('Install razorpay package to create payment orders.') from exc

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        return client.order.create({
            'amount': amount_to_paise(amount),
            'currency': getattr(settings, 'RAZORPAY_CURRENCY', 'INR'),
            'receipt': receipt,
            'payment_capture': 1,
            'notes': notes or {},
        })

    @staticmethod
    def verify_signature(*, order_id, payment_id, signature):
        if not razorpay_is_configured():
            return False
        payload = f'{order_id}|{payment_id}'.encode('utf-8')
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature or '')
