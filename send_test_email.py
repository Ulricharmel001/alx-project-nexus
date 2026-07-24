#!/usr/bin/env python
"""
Test script to send a direct email to your configured email address
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/ulrich/ALX_PRODEV/alx-project-nexus')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce_api.settings')

django.setup()

from django.core.mail import send_mail
from django.conf import settings

def send_test_email():
    print("Sending test email directly via SMTP...")
    
    # Print the email configuration being used
    print(f"Using EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"Using EMAIL_PORT: {settings.EMAIL_PORT}")
    
    try:
        # Send a test email directly
        send_mail(
            subject="Test Email - SMTP Configuration Check",
            message="This is a test email to verify that SMTP configuration is working properly.\n\n"
                   "If you're receiving this email, your SMTP settings are correctly configured.\n\n"
                   "The verification code system should now work when you register.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        print(f"✅ Test email sent successfully to {settings.EMAIL_HOST_USER}")
        print("Check your inbox (and spam folder) for the test email.")
        return True
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        print("There might be an issue with your SMTP configuration in the .env file.")
        return False

if __name__ == "__main__":
    send_test_email()