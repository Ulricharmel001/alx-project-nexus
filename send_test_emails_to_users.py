#!/usr/bin/env python
"""
Test script to send a verification email to all registered users
"""
import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append('/home/ulrich/ALX_PRODEV/alx-project-nexus')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce_api.settings')

django.setup()

from accounts.models import CustomUser
from accounts.email_utils import store_verification_code
from accounts.tasks import send_verification_email_task

BLOCKED_DOMAINS = {"example.com", "test.com", "localhost.com", "localhost"}
BLOCKED_PREFIXES = {"test", "verify", "nobody", "dev", "admin"}

def is_placeholder_email(email):
    domain = email.split("@")[-1].lower()
    local_part = email.split("@")[0].lower()
    if domain in BLOCKED_DOMAINS:
        return True
    for prefix in BLOCKED_PREFIXES:
        if local_part.startswith(prefix):
            return True
    return False


def send_test_emails_to_all_users():
    print(f"Sending test verification emails to all users at {datetime.now()}...")
    
    # Get all registered users
    users = CustomUser.objects.all()
    
    if not users.exists():
        print("❌ No users found in the database.")
        return
    
    print(f"Found {users.count()} users in the database.")
    
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    for user in users:
        try:
            if is_placeholder_email(user.email):
                print(f"\n⏭️  Skipping placeholder email: {user.email}")
                skipped_count += 1
                continue

            print(f"\nProcessing user: {user.email}")
            
            # Generate a new verification code for the user
            code = store_verification_code(user.email)
            
            # Queue the email to be sent via Celery
            send_verification_email_task.delay(user.email, code)
            print(f"✅ Verification email queued for {user.email}")
            success_count += 1
                
        except Exception as e:
            print(f"❌ Error processing user {user.email}: {str(e)}")
            failure_count += 1
    
    print(f"\n--- Summary ---")
    print(f"Total users: {users.count()}")
    print(f"Skipped (placeholder): {skipped_count}")
    print(f"Emails queued: {success_count}")
    print(f"Errors: {failure_count}")
    
    if success_count > 0:
        print("\nNote: Emails have been queued for sending via Celery.")
        print("Check your email (including spam folder) for the verification codes.")
        print("You can also check Celery logs to see if the tasks were processed.")

if __name__ == "__main__":
    send_test_emails_to_all_users()