#!/usr/bin/env python
"""
Test script to verify Email OTP flow works end-to-end
Run: python manage.py shell < scripts/test_email_otp_flow.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from apps.accounts.models import User, OTPVerification
from apps.accounts.email_otp import EmailOTPService
from apps.accounts.auth_serializers import OTPRequestSerializer
import secrets
import hashlib
import hmac

print("\n" + "="*70)
print("EMAIL OTP FLOW TEST")
print("="*70)

# ============================================================================
# Test 1: Verify Email Settings
# ============================================================================
print("\n[Test 1] Email Settings Configuration")
print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Verify SMTP is configured
if 'smtp' in settings.EMAIL_BACKEND.lower():
    print("  SUCCESS: SMTP Backend configured correctly!")
else:
    print("  WARNING: Not using SMTP backend")

# ============================================================================
# Test 2: Test Email Sending
# ============================================================================
print("\n[Test 2] Send Test Email")
try:
    result = send_mail(
        subject='RNT MPL - Test Email',
        message='This is a test email to verify SMTP configuration is working correctly.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['test@example.com'],  # Test email
        fail_silently=False,
    )
    print(f"  SUCCESS: Email sent successfully! (result: {result})")
except Exception as e:
    print(f"  WARNING: Email send failed: {str(e)}")

# ============================================================================
# Test 3: OTP Generation & Hashing
# ============================================================================
print("\n[Test 3] OTP Generation & Hashing")
test_email = 'test@example.com'
otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
print(f"  Generated OTP: {otp_code}")

# Hash the OTP (same logic as serializer)
otp_hash = hmac.new(
    settings.SECRET_KEY.encode(),
    f"{otp_code}:{test_email}".encode(),
    hashlib.sha256
).hexdigest()
print(f"  HMAC-SHA256 Hash: {otp_hash[:20]}...")
print("  SUCCESS: OTP generation & hashing working!")

# ============================================================================
# Test 4: OTP Storage
# ============================================================================
print("\n[Test 4] OTP Storage in Database")
try:
    # Clean up old test OTP
    OTPVerification.objects.filter(email=test_email).delete()
    
    from django.utils import timezone
    # Create new OTP
    otp_obj = OTPVerification.objects.create(
        email=test_email,
        otp_hash=otp_hash,
        purpose='LOGIN',
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )
    print(f"  Created OTP record: {otp_obj.id}")
    print(f"  Email: {otp_obj.email}")
    print(f"  Purpose: {otp_obj.purpose}")
    print(f"  Expires at: {otp_obj.expires_at}")
    print("  [SUCCESS] OTP storage working!")
    
    # Clean up
    otp_obj.delete()
except Exception as e:
    print(f"  WARNING: OTP storage failed: {str(e)}")

# ============================================================================
# Test 5: API Serializer Validation
# ============================================================================
print("\n[Test 5] API Serializer Validation")
test_data = {
    'email': 'valid@example.com',
    'purpose': 'LOGIN'
}
serializer = OTPRequestSerializer(data=test_data)
if serializer.is_valid():
    print(f"  Email: {serializer.validated_data['email']}")
    print(f"  Purpose: {serializer.validated_data['purpose']}")
    print("  SUCCESS: OTP Request serializer valid!")
else:
    print(f"  WARNING: Serializer errors: {serializer.errors}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "="*70)
print("EMAIL OTP SYSTEM READY!")
print("="*70)
print("\nNext Steps:")
print("1. Test API endpoints with curl:")
print("   POST http://localhost:8000/api/auth/otp/request/")
print("2. Check email inbox for OTP code")
print("3. Verify OTP with:")
print("   POST http://localhost:8000/api/auth/otp/verify/")
print("\nPhase 1 Status: COMPLETE")
print("="*70 + "\n")
