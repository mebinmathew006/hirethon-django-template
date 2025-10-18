#!/usr/bin/env python
"""
Test script to verify SMTP email configuration
Run this with: python manage.py shell < test_email.py
"""

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    try:
        result = send_mail(
            'Test Email',
            'This is a test email to verify SMTP configuration.',
            settings.DEFAULT_FROM_EMAIL,
            ['test@example.com'],  # Replace with your test email
            fail_silently=False,
        )
        print(f"Email sent successfully! Result: {result}")
    except Exception as e:
        print(f"Email failed: {str(e)}")

if __name__ == "__main__":
    test_email()
