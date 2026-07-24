#!/usr/bin/env python
"""
Test script to send a greeting/welcome email to all registered users
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
from accounts.email_utils import send_welcome_email

def send_greetings_to_all_users():
    print(f"Sending greeting emails to all users at {datetime.now()}...")
    
    # Get all registered users
    users = CustomUser.objects.all()
    
    if not users.exists():
        print("❌ No users found in the database.")
        return
    
    print(f"Found {users.count()} users in the database.")
    
    success_count = 0
    failure_count = 0
    
    for user in users:
        try:
            print(f"\nSending greeting to user: {user.email}")
            
            # Send a welcome/greeting email to the user
            success, message = send_welcome_email(user.email, user.first_name or "Valued Customer")
            
            if success:
                print(f"✅ Greeting email queued for {user.email}")
                print(f"   Task message: {message}")
                success_count += 1
            else:
                print(f"❌ Failed to queue greeting email for {user.email}")
                print(f"   Error: {message}")
                failure_count += 1
                
        except Exception as e:
            print(f"❌ Error processing user {user.email}: {str(e)}")
            failure_count += 1
    
    print(f"\n--- Summary ---")
    print(f"Total users processed: {users.count()}")
    print(f"Greeting emails successfully queued: {success_count}")
    print(f"Greeting emails failed to send: {failure_count}")
    
    if success_count > 0:
        print("\nNote: Greeting emails have been queued for sending via Celery.")
        print("Check your email (including spam folder) for the greeting messages.")
        print("You can also check Celery logs to see if the tasks were processed.")

if __name__ == "__main__":
    send_greetings_to_all_users()