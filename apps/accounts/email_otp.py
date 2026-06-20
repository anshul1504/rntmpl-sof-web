"""
Email OTP Service
Send OTP via SMTP (configurable email provider)
"""
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


class EmailOTPService:
    """Send emails using configured SMTP with logo attachment."""

    @staticmethod
    def _send_html_email(subject: str, to_email: str, template_name: str, context: dict, fallback_text: str = "") -> tuple[bool, str]:
        """Send an HTML email with the inline logo attached."""
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.contrib.staticfiles import finders
            from email.mime.image import MIMEImage
            import os

            # Render HTML and plain text versions
            html_message = EmailOTPService._render_template(f'{template_name}.html', context)
            text_message = EmailOTPService._render_template(f'{template_name}.txt', context)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message or fallback_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email]
            )

            if html_message:
                msg.attach_alternative(html_message, "text/html")

                # Find and attach logo
                logo_path = finders.find('images/logo.png')
                if logo_path and os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        msg_img = MIMEImage(f.read())
                        msg_img.add_header('Content-ID', '<logo>')
                        msg_img.add_header('Content-Disposition', 'inline', filename='logo.png')
                        msg.attach(msg_img)

            msg.send(fail_silently=False)
            logger.info(f'Email sent successfully to {to_email} with template {template_name}')
            return True, 'Email sent successfully'
        except Exception as e:
            logger.error(f'Failed to send email to {to_email} with template {template_name}: {str(e)}')
            return False, str(e)

    @staticmethod
    def send_otp(email: str, otp: str, purpose: str = 'LOGIN') -> tuple[bool, str]:
        """Send OTP to email address."""
        context = {
            'email': email,
            'otp': otp,
            'purpose': purpose,
            'expiry_minutes': 10,
            'platform_name': 'RNT MPL Cricket Platform'
        }
        subject = f'Your OTP for {purpose} - RNT MPL Cricket Platform'
        fallback = f'Your OTP is: {otp}. Valid for 10 minutes.'
        return EmailOTPService._send_html_email(subject, email, 'otp_email', context, fallback)

    @staticmethod
    def send_welcome_email(email: str, full_name: str) -> tuple[bool, str]:
        """Send a premium welcome email to the user."""
        context = {
            'email': email,
            'full_name': full_name,
            'platform_name': 'RNT MPL Cricket Platform'
        }
        subject = f'Welcome to RNT MPL Cricket Platform, {full_name}!'
        fallback = f'Welcome to RNT MPL Cricket Platform! Your account has been successfully verified.'
        return EmailOTPService._send_html_email(subject, email, 'welcome_email', context, fallback)

    @staticmethod
    def _render_template(template_name: str, context: dict) -> str:
        """Render email template with context."""
        try:
            return render_to_string(f'emails/{template_name}', context)
        except Exception as e:
            logger.warning(f'Template {template_name} not found: {e}')
            return None
