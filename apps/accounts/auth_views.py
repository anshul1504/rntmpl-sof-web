"""
JWT Authentication Views
Register, Login, Token Refresh, OTP verification, Tenant Onboarding
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.auth_serializers import (
    RegisterSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    TenantOnboardingSerializer,
    UserDetailSerializer,
)
from apps.accounts.models import User


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Register new user with email and password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Login with email and password, returns JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class RefreshTokenView(APIView):
    """
    POST /api/auth/refresh/
    Refresh JWT access token using refresh token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPRequestView(APIView):
    """
    POST /api/auth/otp/request/
    Request OTP via email only.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(APIView):
    """
    POST /api/auth/otp/verify/
    Verify OTP via email and login/register user.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    GET /api/auth/me/
    Get current authenticated user details.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TenantOnboardingView(APIView):
    """
    POST /api/auth/onboard-tenant/
    Create a new tenant/organization during onboarding.
    Requires: authenticated user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TenantOnboardingSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    POST /api/auth/verify-email/
    Verify user email (used after email verification via link).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.email_verified = True
        user.is_verified = user.email_verified or user.phone_verified
        user.save(update_fields=['email_verified', 'is_verified'])

        serializer = UserDetailSerializer(user)
        return Response({
            'message': 'Email verified successfully.',
            'user': serializer.data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Logout current user (token blacklist if enabled).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # TODO: Implement token blacklist if using drf-simplejwt extensions
        return Response(
            {'message': 'Logged out successfully.'},
            status=status.HTTP_200_OK
        )
